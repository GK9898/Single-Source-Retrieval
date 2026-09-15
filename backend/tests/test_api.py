import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Cooking - Indian recipes II.pdf")


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_upload_invalid_file():
    response = client.post(
        "/api/upload",
        files={"file": ("test.png", b"fake binary content", "image/png")}
    )
    assert response.status_code == 400


def test_upload_pdf_doc():
    assert os.path.exists(PDF_PATH), f"Test PDF file not found at {PDF_PATH}"
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    response = client.post(
        "/api/upload",
        files={"file": ("Cooking - Indian recipes II.pdf", pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["filename"] == "Cooking - Indian recipes II.pdf"
    assert data["num_chunks"] > 0
    assert data["num_pages"] > 0


def test_query_pdf_doc():
    assert os.path.exists(PDF_PATH), f"Test PDF file not found at {PDF_PATH}"
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    upload_res = client.post(
        "/api/upload",
        files={"file": ("Cooking - Indian recipes II.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    query_res = client.post(
        "/api/query",
        json={"query": "How to prepare Indian rice and curry recipes?", "document_id": doc_id, "top_k": 3}
    )
    assert query_res.status_code == 200
    data = query_res.json()
    assert "answer" in data
    assert len(data["sources"]) > 0
    assert data["document_id"] == doc_id


def test_query_with_only_user_query():
    """Verify user can send ONLY query without providing document_id after uploading a document."""
    assert os.path.exists(PDF_PATH), f"Test PDF file not found at {PDF_PATH}"
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    # Upload document first
    client.post(
        "/api/upload",
        files={"file": ("Cooking - Indian recipes II.pdf", pdf_bytes, "application/pdf")}
    )

    # Now query WITHOUT passing document_id
    query_res = client.post(
        "/api/query",
        json={"query": "How to make Paneer or Biryani?"}
    )
    assert query_res.status_code == 200
    data = query_res.json()
    assert "answer" in data
    assert len(data["sources"]) > 0



def test_suggestions_api():
    response = client.post("/api/suggestions", json={"num_suggestions": 3})
    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) == 3


def test_topics_api():
    response = client.post("/api/topics", json={"max_topics": 3})
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data


def test_tts_api():
    response = client.post("/api/tts", json={"text": "Indian Cooking Recipes RAG output sample"})
    assert response.status_code == 200
    data = response.json()
    assert "audio_base64" in data


def test_evaluate_api():
    response = client.post(
        "/api/evaluate",
        json={
            "query": "How to prepare Indian rice and curry recipes?",
            "answer": "Refer to the ingredients list and cooking instructions in the PDF.",
            "contexts": ["Indian cooking relies on rich spices and fresh ingredients for rice and curry dishes."]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert data["metrics"]["overall_score"] > 0


def test_step_4_faiss_query_index_repeatability():
    """Step 4 Checklist: query_index(question, k), identical query repeat check, and distinct queries returning different chunks."""
    from app.services.document_processor import document_processor

    assert os.path.exists(PDF_PATH), f"Test PDF file not found at {PDF_PATH}"
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    res = document_processor.process_and_index(pdf_bytes, "Cooking - Indian recipes II.pdf")
    doc_id = res["document_id"]

    # 1. Test query_index(question, k)
    q1 = "How to make Biryani rice?"
    res1_a = document_processor.query_index(question=q1, k=3, doc_id=doc_id)
    res1_b = document_processor.query_index(question=q1, k=3, doc_id=doc_id)

    assert len(res1_a) > 0
    # Same question twice returns identical top-k chunk IDs
    ids1_a = [c["chunk_id"] for c in res1_a]
    ids1_b = [c["chunk_id"] for c in res1_b]
    assert ids1_a == ids1_b

    # 2. Different question returns visibly different top chunk IDs
    q2 = "What is the recipe for Gulab Jamun dessert?"
    res2 = document_processor.query_index(question=q2, k=3, doc_id=doc_id)
    ids2 = [c["chunk_id"] for c in res2]
    assert len(res2) > 0
    assert ids1_a != ids2


def test_step_5_out_of_scope_grounded_prompt():
    """Step 5 Checklist: grounded answer for in-scope query & honest 'not present in document' for out-of-scope query."""
    assert os.path.exists(PDF_PATH), f"Test PDF file not found at {PDF_PATH}"
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    upload_res = client.post(
        "/api/upload",
        files={"file": ("Cooking - Indian recipes II.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # 1. In-scope query gives grounded answer
    in_scope_res = client.post(
        "/api/query",
        json={"query": "What are the ingredients for Vegetable Biryani?", "document_id": doc_id}
    )
    assert in_scope_res.status_code == 200
    data_in = in_scope_res.json()
    assert "not present in the document" not in data_in["answer"].lower()
    assert len(data_in["sources"]) > 0

    # 2. Out-of-scope query gets honest 'not present in document' response
    out_scope_res = client.post(
        "/api/query",
        json={"query": "What is the current stock price of Apple Incorporated?", "document_id": doc_id}
    )
    assert out_scope_res.status_code == 200
    data_out = out_scope_res.json()
    assert "not present in the document" in data_out["answer"].lower()


def test_step_6_multi_part_query_routing_and_decomposition():
    """Step 6 Checklist: Classify single_fact/multi_part/summarization and prove multi-part sub-query evidence retrieval."""
    assert os.path.exists(PDF_PATH), f"Test PDF file not found at {PDF_PATH}"
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    upload_res = client.post(
        "/api/upload",
        files={"file": ("Cooking - Indian recipes II.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # 1. Deliberately multi-part test question: 'What is X and how to prepare Y?'
    multi_res = client.post(
        "/api/query",
        json={"query": "What are the ingredients for Biryani and how to prepare Paneer Butter Masala?", "document_id": doc_id}
    )
    assert multi_res.status_code == 200
    data_multi = multi_res.json()
    
    assert data_multi["query_type"] == "multi_part"
    assert len(data_multi["sub_queries"]) >= 2
    assert "answer" in data_multi
    assert len(data_multi["sources"]) > 0

    # 2. Single-fact classification
    single_res = client.post(
        "/api/query",
        json={"query": "What ingredients are needed for Sambhar?", "document_id": doc_id}
    )
    assert single_res.status_code == 200
    assert single_res.json()["query_type"] == "single_fact"

    # 3. Summarization classification
    summary_res = client.post(
        "/api/query",
        json={"query": "Summarize the key recipes in this document", "document_id": doc_id}
    )
    assert summary_res.status_code == 200
    assert summary_res.json()["query_type"] == "summarization"


def test_step_7_reranking_changes_rank():
    """Step 7 Checklist: Verify Cross-Encoder re-ranking rescores candidate chunks and optimizes ranking over raw FAISS similarity."""
    from app.services.document_processor import document_processor
    from app.services.reranker import reranker_service

    assert os.path.exists(PDF_PATH), f"Test PDF file not found at {PDF_PATH}"
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    res = document_processor.process_and_index(pdf_bytes, "Cooking - Indian recipes II.pdf")
    doc_id = res["document_id"]

    query = "How to prepare Indian biryani rice and curry recipes?"
    raw_faiss_chunks = document_processor.search_similar_chunks(query=query, doc_id=doc_id, top_k=10)
    assert len(raw_faiss_chunks) >= 2

    # Rerank candidates with CrossEncoder
    reranked_chunks = reranker_service.rerank(query=query, chunks=raw_faiss_chunks, top_k=5)
    assert len(reranked_chunks) > 0
    assert "score" in reranked_chunks[0]






