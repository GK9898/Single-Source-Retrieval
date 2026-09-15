import os
import sys
import json
import logging
from typing import List, Dict, Any

# Ensure app package is in path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.document_processor import document_processor
from app.services.rag_pipeline import rag_pipeline
from app.services.evaluator import rag_evaluator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PDF_PATH = os.path.join(os.path.dirname(__file__), "data", "Cooking - Indian recipes II.pdf")
EVAL_DATASET_PATH = os.path.join(os.path.dirname(__file__), "data", "eval_dataset.json")


def run_batch_evaluation():
    """Run batch RAGAS metrics evaluation across labeled dataset (Step 8 checklist requirement)."""
    logger.info("Starting Batch RAGAS Evaluation...")

    # 1. Load labeled dataset
    if not os.path.exists(EVAL_DATASET_PATH):
        logger.error(f"Eval dataset not found at {EVAL_DATASET_PATH}")
        sys.exit(1)

    with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
        eval_items: List[Dict[str, Any]] = json.load(f)

    # 2. Ingest document if not already indexed
    doc_id = None
    if os.path.exists(PDF_PATH):
        logger.info(f"Ingesting target evaluation PDF: {os.path.basename(PDF_PATH)}")
        with open(PDF_PATH, "rb") as f:
            pdf_bytes = f.read()
        res = document_processor.process_and_index(pdf_bytes, os.path.basename(PDF_PATH))
        doc_id = res["document_id"]
        logger.info(f"Indexed document successfully. Document ID: {doc_id}, Chunks: {res['num_chunks']}")
    else:
        logger.warning("PDF file not found. Running with current indexed store.")

    results = []

    # 3. Process each evaluation item
    logger.info(f"Evaluating {len(eval_items)} question/ground-truth pairs...\n")
    for item in eval_items:
        q_id = item["id"]
        query = item["question"]
        ground_truth = item.get("ground_truth", "")

        # Execute query pipeline
        rag_res = rag_pipeline.execute_query(query=query, document_id=doc_id, top_k=3, use_reranker=True)
        answer = rag_res["answer"]
        contexts = [s["text"] for s in rag_res.get("sources", [])]

        # Evaluate response metrics & log to JSONL
        eval_res = rag_evaluator.evaluate_response(
            query=query,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth
        )
        metrics = eval_res["metrics"]

        results.append({
            "id": q_id,
            "query": query[:40] + "..." if len(query) > 40 else query,
            "faithfulness": metrics["faithfulness"],
            "relevance": metrics["answer_relevance"],
            "recall": metrics["context_recall"],
            "precision": metrics["context_precision"],
            "overall": metrics["overall_score"]
        })

    # 4. Print metrics summary table
    print("\n" + "=" * 90)
    print(f"{'BATCH RAGAS EVALUATION METRICS TABLE':^90}")
    print("=" * 90)
    header = f"{'ID':<8} | {'Query Preview':<43} | {'Faith':<6} | {'Relev':<6} | {'Recall':<6} | {'Precis':<6} | {'Overall':<7}"
    print(header)
    print("-" * 90)

    avg_faith = sum(r["faithfulness"] for r in results) / len(results)
    avg_relev = sum(r["relevance"] for r in results) / len(results)
    avg_recall = sum(r["recall"] for r in results) / len(results)
    avg_prec = sum(r["precision"] for r in results) / len(results)
    avg_overall = sum(r["overall"] for r in results) / len(results)

    for r in results:
        line = f"{r['id']:<8} | {r['query']:<43} | {r['faithfulness']:<6.2f} | {r['relevance']:<6.2f} | {r['recall']:<6.2f} | {r['precision']:<6.2f} | {r['overall']:<7.2f}"
        print(line)

    print("-" * 90)
    summary_line = f"{'AVERAGE':<8} | {'Across ' + str(len(results)) + ' Test Pairs':<43} | {avg_faith:<6.2f} | {avg_relev:<6.2f} | {avg_recall:<6.2f} | {avg_prec:<6.2f} | {avg_overall:<7.2f}"
    print(summary_line)
    print("=" * 90 + "\n")
    print(f"✅ Evaluation logs written to: {rag_evaluator.log_file}")


if __name__ == "__main__":
    run_batch_evaluation()
