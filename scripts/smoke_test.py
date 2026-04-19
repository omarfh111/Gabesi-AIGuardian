"""
smoke_test.py

Quick retrieval smoke test for gabes_knowledge collection.
Runs 6 targeted queries that MUST return relevant results if ingestion worked correctly.
Each query tests a different document group and a different type of knowledge.

Usage:
    python smoke_test.py

No arguments needed. Reads .env for credentials.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

load_dotenv()

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60,
    prefer_grpc=False,
)
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

COLLECTION = "gabes_knowledge"
TOP_K = 3


def embed(text: str) -> list[float]:
    response = openai.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    )
    return response.data[0].embedding


def search(query: str) -> list[dict]:
    vector = embed(query)
    results = qdrant.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=TOP_K,
        with_payload=True,
    ).points
    return [
        {
            "score": round(r.score, 4),
            "doc": r.payload.get("doc_name", "?"),
            "source_type": r.payload.get("source_type", "?"),
            "language": r.payload.get("language", "?"),
            "text_preview": r.payload.get("text", "")[:200].replace("\n", " "),
        }
        for r in results
    ]


# -- test cases ----------------------------------------------------------------
TESTS = [
    {
        "name": "Test 1 -- Oasis data (PDL, Table 21)",
        "query": "superficie oasis Bahria nombre exploitants irrigation",
        "expect_doc": "PDL_GABES_clean.md",
        "expect_keyword": "Bahria",
    },
    {
        "name": "Test 2 -- GCT pollution (PDL, Table 28)",
        "query": "GCT production phosphogypse pollution industrielle Gabes",
        "expect_doc": "PDL_GABES_clean.md",
        "expect_keyword": "GCT",
    },
    {
        "name": "Test 3 -- Scientific pollution evidence",
        "query": "heavy metal contamination sediments Gabes Gulf phosphate industry",
        "expect_doc": None,  # any scientific paper
        "expect_source_type": "scientific_paper",
    },
    {
        "name": "Test 4 -- Fluoride damage to vegetation",
        "query": "fluoride concentration soil vegetation Gabes pollution oasis",
        "expect_doc": "Screening_biological_traits_and_fluoride.pdf",
        "expect_keyword": "fluoride",
    },
    {
        "name": "Test 5 -- FAO irrigation crop coefficients",
        "query": "crop coefficient date palm evapotranspiration irrigation Kc",
        "expect_doc": None,
        "expect_source_type": "reference",
    },
    {
        "name": "Test 6 -- Structured JSON data",
        "query": "oasis zones coordinates Bahria Chenini salinity risk",
        "expect_doc": "oasis_zones.json",
        "expect_source_type": "structured_data",
    },
]

# -- run tests -----------------------------------------------------------------
print("\n" + "=" * 70)
print("  SMOKE TEST -- gabes_knowledge retrieval")
print("=" * 70)

passed = 0
failed = 0

for test in TESTS:
    print(f"\n{test['name']}")
    print(f"  Query: \"{test['query']}\"")

    try:
        results = search(test["query"])
    except Exception as e:
        print(f"  [FAIL] -- search error: {e}")
        failed += 1
        continue

    if not results:
        print("  [FAIL] -- no results returned")
        failed += 1
        continue

    top = results[0]
    print(f"  Top result:")
    print(f"    Score      : {top['score']}")
    print(f"    Doc        : {top['doc']}")
    print(f"    Source type: {top['source_type']}")
    print(f"    Language   : {top['language']}")
    print(f"    Preview    : {top['text_preview'][:150].encode('ascii', 'replace').decode('ascii')}...")

    # check expectations
    ok = True

    if test.get("expect_doc") and top["doc"] != test["expect_doc"]:
        # check if expected doc appears in top 3
        docs_in_top3 = [r["doc"] for r in results]
        if test["expect_doc"] not in docs_in_top3:
            print(f"  [WARN] Expected doc '{test['expect_doc']}' not in top {TOP_K}")
            ok = False

    if test.get("expect_source_type"):
        types_in_top3 = [r["source_type"] for r in results]
        if test["expect_source_type"] not in types_in_top3:
            print(f"  [WARN] Expected source_type '{test['expect_source_type']}' not in top {TOP_K}")
            ok = False

    if test.get("expect_keyword"):
        keyword = test["expect_keyword"].lower()
        combined_text = " ".join(r["text_preview"].lower() for r in results)
        if keyword not in combined_text:
            print(f"  [WARN] Keyword '{test['expect_keyword']}' not found in top {TOP_K} results")
            ok = False

    if ok:
        print(f"  [PASS]")
        passed += 1
    else:
        print(f"  [FAIL]")
        failed += 1

# -- summary -------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"  RESULTS: {passed}/{len(TESTS)} passed")
if failed == 0:
    print("  [PASS] All smoke tests passed. Retrieval is working correctly.")
elif failed <= 2:
    print("  [WARN] Minor issues -- retrieval mostly works but check failed tests.")
else:
    print("  [FAIL] Multiple failures -- investigate before building the agent.")
print("=" * 70 + "\n")