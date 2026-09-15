import os
import io
import uuid
import logging
from typing import List, Dict, Any, Tuple
import numpy as np

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import faiss
except ImportError:
    faiss = None

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

from app.config import settings
from app.services.embeddings import embedding_service

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self):
        self.documents_store: Dict[str, Dict[str, Any]] = {}
        # Simple in-memory FAISS fallback store
        self.vector_indices: Dict[str, Any] = {}

    def extract_text_from_pdf(self, file_bytes: bytes) -> Tuple[List[str], int]:
        """Extract text per page from PDF bytes."""
        pages = []
        if PdfReader is not None:
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                num_pages = len(reader.pages)
                for page in reader.pages:
                    text = page.extract_text() or ""
                    pages.append(text)
                return pages, num_pages
            except Exception as e:
                logger.warning(f"Error reading PDF with pypdf: {e}. Using plain text decoder fallback.")

        text_content = file_bytes.decode('utf-8', errors='ignore')
        pages = [text_content]
        num_pages = 1
        return pages, num_pages

    def chunk_text(
        self,
        pages: List[str],
        filename: str = "",
        chunk_size: int = settings.CHUNK_SIZE,
        overlap: int = settings.CHUNK_OVERLAP
    ) -> List[Dict[str, Any]]:
        """Split page texts into overlapping chunks with RecursiveCharacterTextSplitter preserving metadata."""
        chunks = []
        global_chunk_idx = 0

        # Initialize recursive character text splitter (~500-800 tokens/chars, ~10-15% overlap)
        if RecursiveCharacterTextSplitter is not None:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        else:
            splitter = None

        for page_num, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue

            if splitter is not None:
                sub_texts = splitter.split_text(page_text)
            else:
                words = page_text.split()
                step = max(1, chunk_size - overlap)
                sub_texts = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), step)]

            for sub_text in sub_texts:
                clean_text = sub_text.strip()
                if clean_text:
                    chunk_obj = {
                        "chunk_id": f"chk_{global_chunk_idx}",
                        "text": clean_text,
                        "page_number": page_num,
                        "source_filename": filename,
                        "metadata": {
                            "source_filename": filename,
                            "page_number": page_num,
                            "chunk_index": global_chunk_idx
                        }
                    }
                    chunks.append(chunk_obj)
                    global_chunk_idx += 1

        return chunks

    def process_and_index(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Process uploaded file, generate chunks, embed, and store in FAISS index."""
        doc_id = str(uuid.uuid4())
        pages, num_pages = self.extract_text_from_pdf(file_bytes)
        chunks = self.chunk_text(pages, filename=filename)

        # Step 3 Checklist: Print list of chunk objects with correct page numbers to console
        logger.info(f"=== INGESTED PDF CHUNKS ({filename}) ===")
        print(f"\n[Ingestion & Chunking] Uploaded '{filename}': Total {len(chunks)} chunks produced across {num_pages} pages.")
        for idx, c in enumerate(chunks[:5]):
            print(f"  Chunk {c['chunk_id']} | Page {c['page_number']} | Snippet: {c['text'][:70]}...")
            logger.info(f"Chunk {c['chunk_id']} | Page {c['page_number']} | Index {c['metadata']['chunk_index']}")
        if len(chunks) > 5:
            print(f"  ... and {len(chunks) - 5} more chunks.")
        print("=" * 60 + "\n")

        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_texts(texts)

        index = None
        if faiss is not None:
            try:
                dimension = embeddings.shape[1] if len(embeddings.shape) > 1 else 384
                index = faiss.IndexFlatIP(dimension)
                if len(embeddings) > 0:
                    # Normalize for cosine similarity via inner product
                    faiss.normalize_L2(embeddings)
                    index.add(embeddings)
                    
                    # Persist FAISS index file
                    os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)
                    index_file_path = os.path.join(settings.FAISS_INDEX_PATH, f"{doc_id}.index")
                    faiss.write_index(index, index_file_path)
            except Exception as e:
                logger.warning(f"FAISS init/persist failed: {e}. Utilizing fallback memory store.")
                index = None

        self.documents_store[doc_id] = {
            "filename": filename,
            "num_pages": num_pages,
            "chunks": chunks,
            "embeddings": embeddings,
            "index": index
        }

        return {
            "document_id": doc_id,
            "filename": filename,
            "num_chunks": len(chunks),
            "num_pages": num_pages,
            "status": "indexed",
            "message": f"Successfully indexed {len(chunks)} chunks from {filename}."
        }


    def search_similar_chunks(self, query: str, doc_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search vector index for top_k similar chunks."""
        target_doc_id = doc_id
        if not target_doc_id:
            if not self.documents_store:
                return []
            target_doc_id = list(self.documents_store.keys())[-1]

        doc_data = self.documents_store.get(target_doc_id)
        if not doc_data or not doc_data["chunks"]:
            return []

        query_emb = embedding_service.embed_query(query).astype(np.float32)
        query_emb = np.expand_dims(query_emb, axis=0)

        chunks = doc_data["chunks"]
        embeddings = doc_data["embeddings"]
        index = doc_data.get("index")

        # If index in doc_data is None, attempt loading persisted .index file from disk
        if index is None and faiss is not None:
            index_path = os.path.join(settings.FAISS_INDEX_PATH, f"{target_doc_id}.index")
            if os.path.exists(index_path):
                try:
                    index = faiss.read_index(index_path)
                    doc_data["index"] = index
                    logger.info(f"Loaded persisted FAISS index from {index_path}")
                except Exception as e:
                    logger.warning(f"Could not load persisted FAISS index ({e})")

        results = []
        if index is not None and hasattr(index, "search") and faiss is not None:
            faiss.normalize_L2(query_emb)
            scores, indices = index.search(query_emb, min(top_k, len(chunks)))
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(chunks) and idx >= 0:
                    item = chunks[idx].copy()
                    item["score"] = float(score)
                    results.append(item)
        else:
            # Fallback dot product similarity search
            if len(embeddings) > 0:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1e-10
                norm_embs = embeddings / norms
                q_norm = query_emb / (np.linalg.norm(query_emb) or 1e-10)
                sims = np.dot(norm_embs, q_norm.T).flatten()
                top_indices = np.argsort(sims)[::-1][:top_k]
                for idx in top_indices:
                    item = chunks[idx].copy()
                    item["score"] = float(sims[idx])
                    results.append(item)

        return results

    def query_index(self, question: str, k: int = 5, doc_id: str = None) -> List[Dict[str, Any]]:
        """
        Step 4 Requirement: query_index(question, k) function that returns the top-k chunks with similarity scores.
        """
        return self.search_similar_chunks(query=question, doc_id=doc_id, top_k=k)


    def get_expanded_chunks_context(self, doc_id: str, retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stitch adjacent sequential chunks (chunk_index + 1) to prevent cut-off procedures/recipes."""
        target_doc_id = doc_id or (list(self.documents_store.keys())[-1] if self.documents_store else None)
        if not target_doc_id or target_doc_id not in self.documents_store:
            return retrieved_chunks

        all_chunks = self.documents_store[target_doc_id]["chunks"]
        seen_indices = set()
        expanded = []

        for chunk in retrieved_chunks:
            c_idx = chunk.get("metadata", {}).get("chunk_index")
            if c_idx is not None and isinstance(c_idx, int):
                # Include current chunk
                if c_idx not in seen_indices:
                    seen_indices.add(c_idx)
                    expanded.append(chunk)
                # Include next adjacent chunk if available to ensure full procedure text
                next_idx = c_idx + 1
                if next_idx < len(all_chunks) and next_idx not in seen_indices:
                    seen_indices.add(next_idx)
                    next_chunk = all_chunks[next_idx].copy()
                    next_chunk["score"] = round(chunk.get("score", 0.5) * 0.95, 4)
                    expanded.append(next_chunk)
            else:
                expanded.append(chunk)

        return expanded


document_processor = DocumentProcessor()

