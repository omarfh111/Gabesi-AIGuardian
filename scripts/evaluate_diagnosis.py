import os
import sys
import json
import argparse
import logging
import time
import httpx
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from openai import OpenAI

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EVAL_DATA_DIR = BASE_DIR / "eval_data"
EVAL_RESULTS_DIR = BASE_DIR / "eval_results"
DIAGNOSIS_INPUTS_PATH = EVAL_DATA_DIR / "diagnosis_inputs.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="DeepEval diagnosis agent evaluation")
    parser.add_argument("--synthesize-only", action="store_true")
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--n-inputs", type=int, default=15)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--agent-url", type=str, default="http://localhost:8000")
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args()

# ── Step 1: Synthesize test inputs ──────────────────────────────────────────
def synthesize_test_inputs(n_inputs: int):
    log.info(f"Synthesizing {n_inputs} test inputs using GPT-4o-mini...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    system_prompt = f"""You are generating test data for an AI system that helps oasis farmers in Gabès, Tunisia diagnose crop problems. Gabès is severely polluted by the GCT phosphate complex which emits SO₂, fluoride, and phosphogypsum.

Generate exactly {n_inputs} farmer symptom descriptions with this distribution:

- 3 inputs [category=pollution, expected_pollution_link=true, language=en]:
  Symptoms that strongly suggest GCT industrial pollution. The farmer notices unusual patterns affecting the ENTIRE oasis zone, mentions other farmers having the same problem, or describes symptoms appearing after wind from the industrial zone direction. Example: white powder on leaves after windy days near the factory, metallic smell, soil that turns white near irrigation.

- 1 input [category=pollution, expected_pollution_link=true, language=fr]:
  Same as above but in realistic farmer French.

- 2 inputs [category=irrigation, expected_pollution_link=false, language=en]:
  Pure irrigation problems - waterlogging, insufficient water frequency, drip system blockage. NO white crust or soil crystal symptoms (those are salinization = pollution-linked).

- 1 input [category=irrigation, expected_pollution_link=true, language=fr]:
  Dry soil despite irrigation WITH white crystalline crust forming. This IS pollution-linked (salinization from industrial discharge). Label expected_pollution_link=true.

- 2 inputs [category=pest_disease, expected_pollution_link=false, language=en]:
  Classic palm pest/disease: larvae in trunk (RPW), brittle breaking leaves (BLD), white scale insects, Phytophthora root rot with fermentation smell.

- 1 input [category=pest_disease, expected_pollution_link=false, language=fr]:
  Same as above in French.

- 2 inputs [category=mixed, expected_pollution_link=true, language=en]:
  Symptoms that could be EITHER pollution OR disease — mention both a structural symptom (yellowing/dying fronds) AND an environmental observation (nearby plots also affected, smell from factory direction). Label expected_pollution_link=true because pollution is a confirmed contributing factor in the Gabès oasis context.

- 1 input [category=vague, expected_pollution_link=false, language=en]:
  Extremely vague: 'my plants don't look good' — tests fallback.

- 1 input [category=pollution, expected_pollution_link=true, language=ar]:
  Arabic text. A Tunisian farmer describing yellowing palm leaves and white soil crust near the industrial zone. Use Tunisian Arabic dialect mixed with standard Arabic.

- 1 input [category=pest_disease, expected_pollution_link=false, language=ar]:
  Arabic text. A farmer describing larvae or insects on palm trees.

Return JSON with exactly {n_inputs} inputs matching this schema:
{{
  "inputs": [
    {{
      "symptom_description": "...",
      "language": "en" | "fr" | "ar",
      "category": "pollution" | "irrigation" | "pest_disease" | "mixed" | "vague",
      "expected_pollution_link": true | false
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate {n_inputs} test inputs."}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("inputs", [])
    except Exception as e:
        log.error(f"Synthesis failed: {e}")
        sys.exit(1)

def inspect_inputs(inputs):
    print("\n" + "=" * 70)
    print("  DIAGNOSIS TEST INPUT INSPECTION")
    print("=" * 70)
    print(f"  Total inputs generated: {len(inputs)}")
    print("  Showing all inputs for review:\n")
    
    categories = {}
    languages = {}
    
    for i, inp in enumerate(inputs):
        cat = inp["category"]
        lang = inp["language"]
        poll = inp["expected_pollution_link"]
        print(f"  [{i+1}] [{cat} | {lang} | pollution_link: {poll}]")
        print(f"      Input: \"{inp['symptom_description']}\"\n")
        
        categories[cat] = categories.get(cat, 0) + 1
        languages[lang] = languages.get(lang, 0) + 1
        
    print("=" * 70)
    print("  Category distribution:")
    for cat, count in categories.items():
        print(f"    {cat:<15}: {count}/{len(inputs)}")
    print("  Language distribution:")
    print("    " + "  ".join([f"{l}: {c}" for l, c in languages.items()]))
    print("=" * 70)
    return input("  Proceed with evaluation? (y/n): ").strip().lower() == "y"

# ── Step 2: Save inputs to disk ──────────────────────────────────────────────
def save_inputs(inputs):
    EVAL_DATA_DIR.mkdir(exist_ok=True)
    with open(DIAGNOSIS_INPUTS_PATH, "w", encoding="utf-8") as f:
        json.dump(inputs, f, ensure_ascii=False, indent=2)
    log.info(f"Inputs saved to {DIAGNOSIS_INPUTS_PATH}")

def load_inputs():
    if not DIAGNOSIS_INPUTS_PATH.exists():
        print(f"\n[ERROR] {DIAGNOSIS_INPUTS_PATH.name} not found. Run without --eval-only first.")
        sys.exit(1)
    with open(DIAGNOSIS_INPUTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ── Step 3: Run agent on each input ─────────────────────────────────────────
def call_agent(input_item, agent_url, timeout):
    url = f"{agent_url}/api/v1/diagnosis"
    payload = {
        "symptom_description": input_item["symptom_description"],
        "language": input_item["language"]
    }
    try:
        start = time.time()
        resp = httpx.post(url, json=payload, timeout=timeout)
        duration = int((time.time() - start) * 1000)
        if resp.status_code == 200:
            return resp.json(), duration, None
        else:
            return None, duration, f"HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return None, 0, str(e)

def run_agent_parallel(inputs, agent_url, timeout):
    log.info(f"Running agent on {len(inputs)} inputs (5 workers)...")
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(call_agent, inp, agent_url, timeout) for inp in inputs]
        for i, future in enumerate(futures):
            resp, duration, error = future.result()
            if resp:
                print(f"  [{i+1}/{len(inputs)}] OK ({duration}ms)")
                results.append(resp)
            else:
                print(f"  [{i+1}/{len(inputs)}] FAIL {error}")
                results.append(None)
    
    succeeded = sum(1 for r in results if r is not None)
    log.info(f"Agent calls complete: {succeeded}/{len(inputs)} succeeded")
    return results

# ── Step 8 helpers from evaluate_retrieval.py ───────────────────────────────
def _extract_cost(result) -> float:
    if result is None: return 0.0
    for attr in ("evaluation_cost", "total_cost", "cost", "token_cost"):
        val = getattr(result, attr, None)
        if val is not None: return float(val)
    if hasattr(result, "test_results"):
        for tr in (result.test_results or []):
            for attr in ("evaluation_cost", "cost"):
                val = getattr(tr, attr, None)
                if val is not None: return float(val)
    return 0.0

def _extract_scores(result, metric_name: str) -> list[float]:
    scores = []
    if result and hasattr(result, "test_results"):
        for tr in (result.test_results or []):
            for md in (tr.metrics_data or []):
                if metric_name in (md.name or "") and md.score is not None:
                    scores.append(md.score)
    return scores

# ── Step 5: Run DeepEval evaluation ──────────────────────────────────────────
def run_evaluation(inputs, responses, threshold):
    from deepeval.test_case import LLMTestCase
    from deepeval import evaluate
    from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
    from deepeval.evaluate.configs import DisplayConfig, ErrorConfig

    test_cases = []
    valid_indices = []
    for i, (inp, resp) in enumerate(zip(inputs, responses)):
        if resp:
            test_cases.append(LLMTestCase(
                input=inp["symptom_description"],
                actual_output=resp["probable_cause"] + ". " + resp["recommended_action"],
                retrieval_context=[chunk["text"] for chunk in resp["retrieved_chunks"]]
            ))
            valid_indices.append(i)

    if not test_cases:
        log.error("No valid responses to evaluate.")
        sys.exit(1)

    judge_model = "gpt-4o-mini"
    faithfulness_metric = FaithfulnessMetric(model=judge_model, threshold=threshold, include_reason=True)
    relevancy_metric = AnswerRelevancyMetric(model=judge_model, threshold=threshold, include_reason=True)

    _display = DisplayConfig(show_indicator=True, print_results=True)
    _error = ErrorConfig(ignore_errors=True)

    log.info("Running FaithfulnessMetric...")
    result_faith = evaluate(test_cases=test_cases, metrics=[faithfulness_metric], display_config=_display, error_config=_error)
    
    log.info("Running AnswerRelevancyMetric...")
    result_rel = evaluate(test_cases=test_cases, metrics=[relevancy_metric], display_config=_display, error_config=_error)

    faith_scores = _extract_scores(result_faith, "Faithfulness")
    rel_scores = _extract_scores(result_rel, "Answer Relevancy")

    # Fallback score extraction if needed
    if not faith_scores:
        for tc in test_cases:
            for md in (getattr(tc, "metrics_data", None) or []):
                if md.score is not None and "Faithfulness" in (getattr(md, "name", "") or ""):
                    faith_scores.append(md.score)
    if not rel_scores:
        for tc in test_cases:
            for md in (getattr(tc, "metrics_data", None) or []):
                if md.score is not None and "Answer Relevancy" in (getattr(md, "name", "") or ""):
                    rel_scores.append(md.score)

    total_cost = _extract_cost(result_faith) + _extract_cost(result_rel)
    return faith_scores, rel_scores, total_cost, valid_indices

def main():
    args = parse_args()
    
    if args.eval_only:
        try:
            r = httpx.get(f"{args.agent_url}/api/v1/health", timeout=5)
            r.raise_for_status()
        except Exception:
            print(f"[ERROR] Agent not reachable at {args.agent_url}")
            print("        Start the backend: cd backend && uvicorn app.main:app --reload --port 8000")
            sys.exit(1)
        inputs = load_inputs()
    else:
        inputs = synthesize_test_inputs(args.n_inputs)
        save_inputs(inputs)
        if not inspect_inputs(inputs):
            print("  Evaluation cancelled. Inputs saved. Run with --eval-only later.")
            sys.exit(0)
        if args.synthesize_only:
            print("  --synthesize-only: stopping before evaluation.")
            sys.exit(0)

    responses = run_agent_parallel(inputs, args.agent_url, args.timeout)
    succeeded_indices = [i for i, r in enumerate(responses) if r is not None]
    
    if len(succeeded_indices) < 3:
        log.error("Not enough successful agent responses for evaluation (min 3).")
        sys.exit(1)

    faith_scores, rel_scores, total_cost, valid_indices = run_evaluation(inputs, responses, args.threshold)
    
    # Pollution accuracy
    pollution_correct = sum(1 for i in valid_indices if inputs[i]["expected_pollution_link"] == responses[i]["pollution_link"])
    pollution_accuracy = pollution_correct / len(valid_indices)

    # Save and Print Results
    EVAL_RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = EVAL_RESULTS_DIR / f"diagnosis_{timestamp}.json"

    safe_mean = lambda s: sum(s) / len(s) if s else 0.0
    safe_pass = lambda s, t: sum(1 for x in s if x >= t) / len(s) if s else 0.0

    f_mean, r_mean = safe_mean(faith_scores), safe_mean(rel_scores)
    f_pass, r_pass = safe_pass(faith_scores, args.threshold), safe_pass(rel_scores, args.threshold)
    
    overall_verdict = "PASS" if (f_mean >= 0.7 and r_mean >= 0.7 and pollution_accuracy >= 0.7) else "FAIL"

    failed_cases = [{"input": inputs[i]["symptom_description"], "category": inputs[i]["category"], "error": "AGENT_ERROR"} 
                   for i, r in enumerate(responses) if r is None]
    
    low_scoring_cases = []
    for idx, (f_score, r_score) in enumerate(zip(faith_scores, rel_scores)):
        if f_score < 0.5 or r_score < 0.5:
            orig_idx = valid_indices[idx]
            low_scoring_cases.append({
                "input": inputs[orig_idx]["symptom_description"],
                "category": inputs[orig_idx]["category"],
                "faithfulness_score": round(f_score, 2),
                "answer_relevancy_score": round(r_score, 2),
                "probable_cause": responses[orig_idx]["probable_cause"],
                "pollution_link": responses[orig_idx]["pollution_link"]
            })

    summary = {
        "timestamp": timestamp, "n_inputs": len(inputs), "n_succeeded": len(valid_indices), "n_failed": len(failed_cases),
        "judge_model": "gpt-4o-mini", "evaluation_cost_usd": round(total_cost, 6), "threshold": args.threshold,
        "faithfulness": {"mean": round(f_mean, 4), "pass_rate": round(f_pass, 4), "n_scored": len(faith_scores)},
        "answer_relevancy": {"mean": round(r_mean, 4), "pass_rate": round(r_pass, 4), "n_scored": len(rel_scores)},
        "pollution_link_accuracy": round(pollution_accuracy, 4), "overall_verdict": overall_verdict,
        "failed_cases": failed_cases, "low_scoring_cases": low_scoring_cases
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("  DIAGNOSIS AGENT EVALUATION RESULTS")
    print("=" * 70)
    print(f"  Test inputs           : {len(inputs)}")
    print(f"  Agent calls succeeded : {len(valid_indices)} / {len(inputs)}")
    print(f"  Judge model           : gpt-4o-mini")
    print(f"  Evaluation cost       : ${total_cost:.6f} USD")
    print(f"  Threshold             : {args.threshold}")
    print("-" * 70)
    print(f"  Faithfulness          : {f_mean:.2f} mean  |  {f_pass:.1%} pass rate")
    print(f"  Answer Relevancy      : {r_mean:.2f} mean  |  {r_pass:.1%} pass rate")
    print(f"  Pollution Link Acc    : {pollution_accuracy:.1%}")
    print("-" * 70)
    print(f"  Overall verdict       : {overall_verdict}")
    print(f"  Results saved to      : {results_path.relative_to(BASE_DIR)}")
    print("=" * 70)
    print("\nTargets:")
    print("  Faithfulness    >= 0.7 : diagnoses grounded in retrieved evidence")
    print("  Answer Relevancy>= 0.7 : responses address what the farmer asked")
    print("  Pollution Link  >= 0.7 : correct pollution attribution")
    print(f"\nLow-scoring cases requiring attention: {len(low_scoring_cases)}")
    for i, case in enumerate(low_scoring_cases[:3]):
        print(f"  [{i+1}] \"{case['input'][:50]}...\" → f: {case['faithfulness_score']}, r: {case['answer_relevancy_score']}")
    print()

if __name__ == "__main__":
    main()
