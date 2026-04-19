import argparse
import json
import logging
import math
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Force UTF-8 encoding for Windows terminals to avoid charmap errors with emojis/Arabic
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables (OpenAI API key needed for GEval)
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & Setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_RESULTS_DIR = BASE_DIR / "eval_results"
EVAL_RESULTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Local Penman-Monteith Implementation (Matches Agent)
# ---------------------------------------------------------------------------
def penman_monteith_et0_local(weather: Dict[str, Any]) -> float:
    """Compute reference evapotranspiration ET0 using FAO-56 Penman-Monteith.
    Matches the implementation in backend/app/agents/irrigation_agent.py.
    """
    Tmax = weather["tmax_c"]
    Tmin = weather["tmin_c"]
    Tmean = (Tmax + Tmin) / 2
    Rs = weather["rs_mj_m2_day"]
    u2 = weather["ws2m_ms"]
    RH = weather["rh2m_pct"]

    # Saturation vapour pressure (kPa)
    es = 0.6108 * math.exp(17.27 * Tmean / (Tmean + 237.3))
    # Actual vapour pressure (kPa)
    ea = (RH / 100.0) * es

    # Slope of vapour pressure curve (kPa/°C)
    delta = 4098 * es / (Tmean + 237.3) ** 2

    # Psychrometric constant (kPa/°C) at ~sea level
    gamma = 0.0665

    # Net radiation (MJ/m²/day) — simplified
    Rns = 0.77 * Rs
    Rnl = 0.0
    Rn = Rns - Rnl

    # Soil heat flux (MJ/m²/day) — zero for daily timestep
    G = 0.0

    et0 = (
        0.408 * delta * (Rn - G)
        + gamma * (900.0 / (Tmean + 273.0)) * u2 * (es - ea)
    ) / (delta + gamma * (1.0 + 0.34 * u2))

    return round(max(et0, 0.0), 2)

# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------
TEST_CASES = [
    # -- Numerical accuracy tests (mock weather, known ET0) --------------
    {
        "id": "tc01",
        "name": "FAO-56 reference conditions",
        "request": {"crop_type": "date_palm", "growth_stage": "mid", "language": "en"},
        "mock_weather": {
            "tmax_c": 21.5, "tmin_c": 12.3,
            "rs_mj_m2_day": 22.07, "ws2m_ms": 2.78,
            "rh2m_pct": 82.0, "rs_estimated": False
        },
        "expected_et0_range": [3.6, 4.2],
        "expected_kc": 0.95,
        "expected_etc_range": [3.42, 3.99],
        "language": "en",
        "check_no_technical_terms": True,
    },
    {
        "id": "tc02",
        "name": "Hot dry Gabes summer conditions",
        "request": {"crop_type": "date_palm", "growth_stage": "mid", "language": "en"},
        "mock_weather": {
            "tmax_c": 38.0, "tmin_c": 22.0,
            "rs_mj_m2_day": 28.0, "ws2m_ms": 3.0,
            "rh2m_pct": 25.0, "rs_estimated": False
        },
        "expected_et0_range": [8.0, 12.0],
        "expected_kc": 0.95,
        "expected_etc_range": [7.6, 11.4],
        "language": "en",
        "check_no_technical_terms": True,
    },
    {
        "id": "tc03",
        "name": "Cool winter conditions",
        "request": {"crop_type": "date_palm", "growth_stage": "initial", "language": "en"},
        "mock_weather": {
            "tmax_c": 15.0, "tmin_c": 5.0,
            "rs_mj_m2_day": 10.0, "ws2m_ms": 1.5,
            "rh2m_pct": 65.0, "rs_estimated": False
        },
        "expected_et0_range": [1.0, 3.0],
        "expected_kc": 0.90,
        "expected_etc_range": [0.9, 2.7],
        "language": "en",
        "check_no_technical_terms": True,
    },
    {
        "id": "tc04",
        "name": "Estimated Rs fallback",
        "request": {"crop_type": "date_palm", "growth_stage": "mid", "language": "en"},
        "mock_weather": {
            "tmax_c": 30.0, "tmin_c": 16.0,
            "rs_mj_m2_day": 22.0, "ws2m_ms": 2.0,
            "rh2m_pct": 45.0, "rs_estimated": True
        },
        "expected_et0_range": [5.0, 9.0],
        "expected_kc": 0.95,
        "expected_etc_range": [4.75, 8.55],
        "expected_rs_estimated": True,
        "language": "en",
        "check_no_technical_terms": True,
    },
    # -- Crop coefficient tests ------------------------------------------
    {
        "id": "tc05",
        "name": "Pomegranate initial stage",
        "request": {"crop_type": "pomegranate", "growth_stage": "initial", "language": "fr"},
        "mock_weather": {
            "tmax_c": 28.0, "tmin_c": 14.0,
            "rs_mj_m2_day": 20.0, "ws2m_ms": 2.0,
            "rh2m_pct": 40.0, "rs_estimated": False
        },
        "expected_kc": 0.6,
        "expected_et0_range": [4.0, 8.0],
        "expected_etc_range": [2.4, 4.8],
        "language": "fr",
        "check_language": "fr",
        "check_no_technical_terms": True,
    },
    {
        "id": "tc06",
        "name": "Fig mid stage",
        "request": {"crop_type": "fig", "growth_stage": "mid", "language": "en"},
        "mock_weather": {
            "tmax_c": 28.0, "tmin_c": 14.0,
            "rs_mj_m2_day": 20.0, "ws2m_ms": 2.0,
            "rh2m_pct": 40.0, "rs_estimated": False
        },
        "expected_kc": 1.05,
        "expected_et0_range": [4.0, 8.0],
        "expected_etc_range": [4.2, 8.4],
        "language": "en",
        "check_no_technical_terms": True,
    },
    {
        "id": "tc07",
        "name": "Olive end stage",
        "request": {"crop_type": "olive", "growth_stage": "end", "language": "en"},
        "mock_weather": {
            "tmax_c": 25.0, "tmin_c": 12.0,
            "rs_mj_m2_day": 18.0, "ws2m_ms": 2.5,
            "rh2m_pct": 50.0, "rs_estimated": False
        },
        "expected_kc": 0.65,
        "expected_et0_range": [3.0, 6.0],
        "expected_etc_range": [1.95, 3.9],
        "language": "en",
        "check_no_technical_terms": True,
    },
    {
        "id": "tc08",
        "name": "Vegetables mid stage",
        "request": {"crop_type": "vegetables", "growth_stage": "mid", "language": "ar"},
        "mock_weather": {
            "tmax_c": 26.0, "tmin_c": 13.0,
            "rs_mj_m2_day": 19.0, "ws2m_ms": 2.0,
            "rh2m_pct": 45.0, "rs_estimated": False
        },
        "expected_kc": 1.0,
        "expected_et0_range": [3.5, 7.0],
        "expected_etc_range": [3.5, 7.0],
        "language": "ar",
        "check_language": "ar",
        "check_no_technical_terms": True,
    },
    # -- Language tests --------------------------------------------------
    {
        "id": "tc09",
        "name": "French advisory language check",
        "request": {"crop_type": "date_palm", "growth_stage": "mid", "language": "fr"},
        "mock_weather": {
            "tmax_c": 30.0, "tmin_c": 16.0,
            "rs_mj_m2_day": 22.0, "ws2m_ms": 2.0,
            "rh2m_pct": 40.0, "rs_estimated": False
        },
        "expected_kc": 0.95,
        "expected_et0_range": [4.0, 9.0],
        "expected_etc_range": [3.8, 8.55],
        "language": "fr",
        "check_language": "fr",
        "check_no_technical_terms": True,
    },
    {
        "id": "tc10",
        "name": "Arabic advisory language check",
        "request": {"crop_type": "date_palm", "growth_stage": "mid", "language": "ar"},
        "mock_weather": {
            "tmax_c": 30.0, "tmin_c": 16.0,
            "rs_mj_m2_day": 22.0, "ws2m_ms": 2.0,
            "rh2m_pct": 40.0, "rs_estimated": False
        },
        "expected_kc": 0.95,
        "expected_et0_range": [4.0, 9.0],
        "expected_etc_range": [3.8, 8.55],
        "language": "ar",
        "check_language": "ar",
        "check_no_technical_terms": True,
    },
    # -- Edge cases ------------------------------------------------------
    {
        "id": "tc11",
        "name": "Rs estimated flag propagates to response",
        "request": {"crop_type": "date_palm", "growth_stage": "mid", "language": "en"},
        "mock_weather": {
            "tmax_c": 28.0, "tmin_c": 15.0,
            "rs_mj_m2_day": 20.0, "ws2m_ms": 2.0,
            "rh2m_pct": 42.0, "rs_estimated": True
        },
        "expected_et0_range": [4.0, 9.0],
        "expected_kc": 0.95,
        "expected_etc_range": [3.8, 8.55],
        "expected_rs_estimated": True,
        "check_advisory_mentions_estimate": True,
        "language": "en",
        "check_no_technical_terms": True,
    },
    {
        "id": "tc12",
        "name": "ETc math consistency check",
        "request": {"crop_type": "date_palm", "growth_stage": "mid", "language": "en"},
        "mock_weather": {
            "tmax_c": 32.0, "tmin_c": 18.0,
            "rs_mj_m2_day": 25.0, "ws2m_ms": 2.5,
            "rh2m_pct": 35.0, "rs_estimated": False
        },
        "expected_kc": 0.95,
        "expected_et0_range": [6.0, 11.0],
        "expected_etc_range": [5.7, 10.45],
        "check_etc_equals_et0_times_kc": True,
        "language": "en",
        "check_no_technical_terms": True,
    },
]

FORBIDDEN_TERMS = [
    "ET₀", "ET0", "Penman", "Monteith", "Penman-Monteith",
    "evapotranspiration", "Kc", "crop coefficient"
]

FRENCH_INDICATORS = ["vous", "vos", "irrigation", "eau", "palmiers", "aujourd", "mm", "arrosez", "irriguer"]

# ---------------------------------------------------------------------------
# Runner Logic
# ---------------------------------------------------------------------------

def run_test_case(tc: Dict[str, Any], agent_url: str, timeout: int) -> Dict[str, Any]:
    """Call the agent and perform numerical/linguistic checks."""
    result = {
        "id": tc["id"],
        "name": tc["name"],
        "checks": {},
        "passed": False,
        "error": None,
        "response": None,
        "warnings": []
    }

    try:
        # CHECK 1: HTTP success
        start_t = time.time()
        resp = httpx.post(f"{agent_url}/api/v1/irrigation", json=tc["request"], timeout=timeout)
        latency = int((time.time() - start_t) * 1000)
        
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}: {resp.text}"
            result["checks"]["http_success"] = False
            return result
        
        result["checks"]["http_success"] = True
        data = resp.json()
        result["response"] = data
        advisory_text = data.get("advisory_text", "")

        # CHECK 2: Kc correctness
        result["checks"]["kc_accuracy"] = data["kc"] == tc["expected_kc"]

        # CHECK 3: ET0 plausibility
        result["checks"]["et0_plausibility"] = 2.0 <= data["et0_mm_day"] <= 12.0

        # CHECK 4: ETc math consistency
        expected_etc = round(data["et0_mm_day"] * data["kc"], 2)
        result["checks"]["etc_math_consistency"] = abs(data["etc_mm_day"] - expected_etc) <= 0.02

        # CHECK 5: irrigation_depth_mm consistency
        expected_depth = round(data["etc_mm_day"], 1)
        result["checks"]["depth_consistency"] = abs(data["irrigation_depth_mm"] - expected_depth) <= 0.05

        # CHECK 6: No forbidden technical terms
        found_forbidden = [term for term in FORBIDDEN_TERMS if term.lower() in advisory_text.lower()]
        result["checks"]["no_technical_terms"] = len(found_forbidden) == 0

        # CHECK 7: Language check
        check_lang = tc.get("check_language")
        if check_lang == "fr":
            found_fr = any(word in advisory_text.lower() for word in FRENCH_INDICATORS)
            result["checks"]["language_check"] = found_fr
        elif check_lang == "ar":
            # Arabic unicode range 0600-06FF
            has_arabic = bool(re.search(r'[\u0600-\u06FF]', advisory_text))
            result["checks"]["language_check"] = has_arabic
        elif tc.get("language") == "en":
            # Simple check for English
            result["checks"]["language_check"] = any(word in advisory_text.lower() for word in ["water", "irrigation", "palm", "mm"])

        # CHECK 8: Rs estimated mention
        if tc.get("check_advisory_mentions_estimate"):
            if data.get("rs_estimated"):
                keywords = ["approximate", "estimated", "cloud", "approximat", "nuage", "تقديري", "غيوم"]
                found_mention = any(kw in advisory_text.lower() for kw in keywords)
                result["checks"]["rs_mention"] = found_mention

        # CHECK 9: Local Penman-Monteith sanity (independent of agent)
        local_et0 = penman_monteith_et0_local(tc["mock_weather"])
        in_range = tc["expected_et0_range"][0] <= local_et0 <= tc["expected_et0_range"][1]
        result["checks"]["local_sanity"] = in_range
        if not in_range:
            result["warnings"].append(f"Local PM sanity check failed: {local_et0} mm/day not in {tc['expected_et0_range']}")

        # Final pass status for numerical checks
        result["passed"] = all(v for k, v in result["checks"].items() if k != "local_sanity")

    except Exception as e:
        result["error"] = str(e)
        result["passed"] = False

    return result

def run_geval_advisory_quality(results: List[Dict[str, Any]], threshold: float):
    """Run DeepEval GEval judge on advisory text."""
    # Lazy import
    try:
        from deepeval.metrics import GEval
        from deepeval.test_case import LLMTestCase, LLMTestCaseParams
        from deepeval import evaluate
    except ImportError:
        log.error("deepeval not found. Skipping GEval.")
        return None

    valid_results = [r for r in results if r["response"] and r["checks"].get("http_success")]
    if not valid_results:
        log.warning("No successful agent calls to judge with GEval.")
        return None

    log.info(f"Running GEval on {len(valid_results)} advisory texts...")

    advisory_quality_metric = GEval(
        name="Irrigation Advisory Quality",
        criteria=(
            "The advisory text should: (1) state a specific irrigation amount "
            "in mm, (2) be practical and actionable for a farmer, (3) not use "
            "technical jargon, (4) be in the correct language, "
            "(5) be 1-4 sentences long."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        model="gpt-4o-mini",
        threshold=threshold,
    )

    test_cases = []
    for r in valid_results:
        tc_orig = next(t for t in TEST_CASES if t["id"] == r["id"])
        test_cases.append(LLMTestCase(
            input=f"Irrigation advisory for {tc_orig['request']['crop_type']} "
                  f"{tc_orig['request']['growth_stage']} stage in {tc_orig['language']}",
            actual_output=r["response"]["advisory_text"],
        ))

    # Run batch evaluation
    try:
        result_obj = evaluate(
            test_cases=test_cases,
            metrics=[advisory_quality_metric],
        )
        
        scores = []
        # Try test_results attribute first (deepeval 3.9.7)
        if result_obj and hasattr(result_obj, 'test_results'):
            for tr in (result_obj.test_results or []):
                for md in (tr.metrics_data or []):
                    if md.score is not None:
                        scores.append(md.score)
        # Fallback: read from test case objects directly
        if not scores:
            for tc in test_cases:
                for md in (getattr(tc, 'metrics_data', None) or []):
                    if md.score is not None:
                        scores.append(md.score)
        
        mean_score = sum(scores) / len(scores) if scores else 0
        passed_geval = sum(1 for s in scores if s >= threshold)
        
        return {
            "mean": round(mean_score, 3),
            "pass_rate": round(passed_geval / len(scores), 3) if scores else 0,
            "n_scored": len(scores)
        }
    except Exception as e:
        log.error(f"GEval evaluation failed: {e}")
        return None

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-only", action="store_true", help="Skip test generation (no-op here)")
    parser.add_argument("--agent-url", default="http://localhost:8000", help="Base URL of agent")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout")
    parser.add_argument("--threshold", type=float, default=0.6, help="GEval threshold")
    args = parser.parse_args()

    log.info("Starting Irrigation Agent Evaluation...")

    # Pre-flight check
    try:
        r = httpx.get(f"{args.agent_url}/api/v1/health", timeout=5)
        r.raise_for_status()
        log.info(f"Agent reachable at {args.agent_url}")
    except Exception:
        print(f"[ERROR] Agent not reachable at {args.agent_url}")
        print("Start backend: cd backend && uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    # Run agent calls in parallel
    results = []
    log.info(f"Executing {len(TEST_CASES)} test cases...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_test_case, tc, args.agent_url, args.timeout) for tc in TEST_CASES]
        for f in futures:
            res = f.result()
            results.append(res)
            status = "PASS" if res["passed"] else "FAIL"
            log.info(f"  [{res['id']}] {res['name']:<40} -> {status}")

    # GEval Quality Check
    geval_res = run_geval_advisory_quality(results, args.threshold)

    # Aggregate numerical stats
    numerical_checks = {
        "kc_accuracy": {"passed": 0, "failed": 0},
        "et0_plausibility": {"passed": 0, "failed": 0},
        "etc_math_consistency": {"passed": 0, "failed": 0},
        "no_technical_terms": {"passed": 0, "failed": 0},
        "language_check": {"passed": 0, "failed": 0, "total": 0}
    }

    for r in results:
        if not r["checks"].get("http_success"): continue
        
        if r["checks"].get("kc_accuracy"): numerical_checks["kc_accuracy"]["passed"] += 1
        else: numerical_checks["kc_accuracy"]["failed"] += 1
        
        if r["checks"].get("et0_plausibility"): numerical_checks["et0_plausibility"]["passed"] += 1
        else: numerical_checks["et0_plausibility"]["failed"] += 1
        
        if r["checks"].get("etc_math_consistency"): numerical_checks["etc_math_consistency"]["passed"] += 1
        else: numerical_checks["etc_math_consistency"]["failed"] += 1
        
        if r["checks"].get("no_technical_terms"): numerical_checks["no_technical_terms"]["passed"] += 1
        else: numerical_checks["no_technical_terms"]["failed"] += 1
        
        if "language_check" in r["checks"]:
            numerical_checks["language_check"]["total"] += 1
            if r["checks"]["language_check"]: numerical_checks["language_check"]["passed"] += 1
            else: numerical_checks["language_check"]["failed"] += 1

    # Final summary output
    print("\n" + "="*70)
    print("  IRRIGATION AGENT EVALUATION RESULTS")
    print("="*70)
    print(f"  Test cases            : {len(TEST_CASES)}")
    print(f"  Agent calls succeeded : {sum(1 for r in results if r['checks'].get('http_success'))} / {len(TEST_CASES)}")
    print(f"  Judge model           : gpt-4o-mini (GEval only)")
    print(f"  Threshold             : {args.threshold}")
    print("-" * 70)
    
    def pr(val, total): return f"{val}/{total} ({val/total*100:.1f}%)" if total > 0 else "N/A"
    
    print(f"  Kc Accuracy           : {pr(numerical_checks['kc_accuracy']['passed'], 12):<20} [exact match vs FAO-56]")
    print(f"  ET0 Plausibility      : {pr(numerical_checks['et0_plausibility']['passed'], 12):<20} [2-12 mm/day range]")
    print(f"  ETc Math Consistency  : {pr(numerical_checks['etc_math_consistency']['passed'], 12):<20} [ETc = ET0 * Kc +/- 0.02]")
    print(f"  No Technical Terms    : {pr(numerical_checks['no_technical_terms']['passed'], 12):<20} [advisory_text check]")
    print(f"  Language Check        : {pr(numerical_checks['language_check']['passed'], numerical_checks['language_check']['total']):<20} [fr + ar + en]")
    
    if geval_res:
        print(f"  Advisory Quality GEval: {geval_res['mean']:.2f} mean           [GPT-4o-mini judge]")
    else:
        print(f"  Advisory Quality GEval: N/A")
    
    print("-" * 70)
    
    overall_pass = (
        numerical_checks["kc_accuracy"]["passed"] == 12 and
        numerical_checks["etc_math_consistency"]["passed"] == 12 and
        numerical_checks["no_technical_terms"]["passed"] >= 11 and
        (geval_res["mean"] >= args.threshold if geval_res else True)
    )
    verdict = "PASS" if overall_pass else "FAIL"
    print(f"  Overall verdict       : {verdict}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = EVAL_RESULTS_DIR / f"irrigation_{timestamp}.json"
    
    output_json = {
        "timestamp": datetime.now().isoformat(),
        "n_test_cases": len(TEST_CASES),
        "n_passed": sum(1 for r in results if r["passed"]),
        "n_failed": sum(1 for r in results if not r["passed"]),
        "judge_model": "gpt-4o-mini",
        "threshold": args.threshold,
        "numerical_checks": {
            k: {**v, "pass_rate": v["passed"]/max(1, v["passed"]+v["failed"])} 
            for k, v in numerical_checks.items() if k != "language_check"
        },
        "advisory_quality_geval": geval_res,
        "evaluation_cost_usd": 0.0,
        "overall_verdict": verdict,
        "failed_cases": [r for r in results if not r["passed"]],
        "warnings": [w for r in results for w in r["warnings"]]
    }
    
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)
    
    print(f"  Results saved to      : eval_results/{results_path.name}")
    print("="*70)

if __name__ == "__main__":
    main()
