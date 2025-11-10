"""
Global query service - orchestrates global chat retrieval with detailed diagnostics.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from shared.logging.logger import get_logger

logger = get_logger("global_query_service")


class GlobalQueryDiagnostics:
    """Holds step-by-step diagnostics for a global query run."""

    def __init__(self, question_id: str, user_id: str):
        self.question_id = question_id
        self.user_id = user_id
        self.timings: Dict[str, int] = {}
        self.details: Dict[str, Any] = {}
        self.errors: List[Dict[str, Any]] = []

    def record_timing(self, name: str, start: float):
        self.timings[name] = int((time.time() - start) * 1000)

    def set_detail(self, key: str, value: Any):
        self.details[key] = value

    def add_error(self, where: str, error: Exception):
        self.errors.append({"where": where, "type": type(error).__name__, "message": str(error)})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "user_id": self.user_id,
            "timings_ms": self.timings,
            "details": self.details,
            "errors": self.errors,
        }


class GlobalQueryService:
    """
    Isolated global query pipeline with structured logging and diagnostics.
    Depends on the same RAG pipeline components already initialized in main.py.
    """

    def __init__(self, rag_pipeline, create_global_prompt):
        self.rag_pipeline = rag_pipeline
        self.create_global_prompt = create_global_prompt
        self.logger = logger

    async def run(
        self,
        question_id: str,
        user_id: str,
        question: str,
        doc_ids: List[str],
        selected_doc_ids: Optional[List[str]] = None,
        max_per_doc: int = 2,
        max_total: int = 8,
    ) -> Tuple[str, List[Any], Dict[str, Any], GlobalQueryDiagnostics]:
        """
        Execute the global retrieval and answer generation.
        Returns: (answer, sources, metadata, diagnostics)
        """
        diag = GlobalQueryDiagnostics(question_id, user_id)
        diag.set_detail("documents_provided", len(doc_ids))
        diag.set_detail("selected_doc_ids", selected_doc_ids or [])

        # 1) Sanitize and embed question
        t0 = time.time()
        sanitized_question = self.rag_pipeline.filter.validate_question(question)
        diag.set_detail("sanitized_question_length", len(sanitized_question))
        try:
            embed_start = time.time()
            query_embedding = await self.rag_pipeline.llm_client.generate_embedding(sanitized_question)
            diag.record_timing("embedding", embed_start)
            diag.set_detail("embedding_dimension", len(query_embedding))
        except Exception as e:
            diag.add_error("embedding", e)
            raise
        diag.record_timing("sanitize_and_embed", t0)

        # 2) If narrowed to a single doc, reuse per-document path (fast path)
        if selected_doc_ids and len(doc_ids) == 1:
            single_cid = doc_ids[0]
            fast_start = time.time()
            result = await self.rag_pipeline.process_query(
                content_id=single_cid,
                question=question,
                user_id=user_id,
                session_id=None,
                student_id=user_id,
                metadata={},
            )
            diag.record_timing("single_doc_fast_path", fast_start)
            diag.set_detail("fast_path_doc_id", single_cid)
            return (
                result["response"],
                result.get("sources", []),
                {
                    **result["metadata"],
                    "documents_searched": 1,
                },
                diag,
            )

        # 3) Global search across namespaces
        retrieval_start = time.time()
        try:
            results = await self.rag_pipeline.retriever.search_global(
                query_vector=query_embedding,
                content_ids=doc_ids,
                top_k=10,
            )
        except Exception as e:
            diag.add_error("search_global", e)
            results = []
        diag.record_timing("search_global", retrieval_start)
        diag.set_detail("initial_global_matches", len(results))

        # 4) Diversify
        diversify_start = time.time()
        try:
            diverse_results = self._diversify(results, max_per_doc=max_per_doc, max_total=max_total)
        except Exception as e:
            diag.add_error("diversify_initial", e)
            diverse_results = []
        diag.record_timing("diversify_initial", diversify_start)
        diag.set_detail("diverse_initial", len(diverse_results))

        # 5) Fallback: per-document retrieve when empty
        if (not diverse_results or len(diverse_results) == 0) and doc_ids:
            perdoc_start = time.time()
            per_doc_results = []
            perdoc_counts = {}
            for cid in doc_ids:
                try:
                    chunks = await self.rag_pipeline.retriever.retrieve(
                        query_embedding=query_embedding, content_id=cid, top_k=2
                    )
                    perdoc_counts[cid] = len(chunks)
                    for ch in chunks:
                        per_doc_results.append(self._normalize_chunk(ch))
                except Exception as e:
                    self.logger.warning(f"[global_fallback] failed for {cid}: {e}")
                    perdoc_counts[cid] = 0
            diverse_results = self._diversify(per_doc_results, max_per_doc=max_per_doc, max_total=max_total)
            diag.record_timing("fallback_per_doc", perdoc_start)
            diag.set_detail("fallback_per_doc_counts", perdoc_counts)
            diag.set_detail("diverse_after_fallback", len(diverse_results))

        # 6) If still nothing, return empty with diagnostics
        if not diverse_results or len(diverse_results) == 0:
            return (
                "",
                [],
                {
                    "chunks_used": 0,
                    "documents_searched": len(doc_ids),
                    "retrieval_time_ms": diag.timings.get("search_global", 0),
                },
                diag,
            )

        # 7) Build context
        context_start = time.time()
        context = "\n\n---\n\n".join(
            [f"[Source {i+1} - {r.metadata.get('document_title', 'Unknown')}]\n{r.metadata.get('text','')}" for i, r in enumerate(diverse_results)]
        )
        diag.record_timing("build_context", context_start)
        diag.set_detail("context_sources", len(diverse_results))

        # 8) LLM answer
        llm_start = time.time()
        messages = self.create_global_prompt(context, sanitized_question, len(doc_ids))
        llm_resp = await self.rag_pipeline.llm_client.generate_completion(messages)
        diag.record_timing("llm_generation", llm_start)
        diag.set_detail("llm_model", llm_resp.get("model"))
        diag.set_detail("llm_tokens", llm_resp.get("usage", {}))
        answer = llm_resp["content"]

        # 9) Build sources and metadata
        sources = []
        for i, result in enumerate(diverse_results):
            sources.append(
                {
                    "source_id": i + 1,
                    "document_title": result.metadata.get("document_title", "Unknown"),
                    "uploader_name": result.metadata.get("uploader_name", "Unknown"),
                    "uploader_id": result.metadata.get("uploader_id", ""),
                    "upload_date": result.metadata.get("upload_date", "")[:10]
                    if result.metadata.get("upload_date")
                    else "",
                    "chunk_index": result.metadata.get("chunk_index", 0),
                    "similarity_score": getattr(result, "score", 0.0),
                }
            )

        metadata = {
            "chunks_used": len(diverse_results),
            "documents_searched": len(doc_ids),
            "llm_time_ms": diag.timings.get("llm_generation", 0),
            "retrieval_time_ms": diag.timings.get("search_global", 0),
            "tokens_used": llm_resp.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
            "model": llm_resp.get("model", "gpt-4"),
        }

        return answer, sources, metadata, diag

    @staticmethod
    def _normalize_chunk(chunk: Dict[str, Any]):
        """Normalize per-document chunk dict into a SearchResult-like object."""
        class SearchResult:
            def __init__(self, item):
                self.id = item.get("id")
                self.score = item.get("score", 0.0)
                md = item.get("metadata", {})
                if "text" not in md:
                    md["text"] = item.get("text", "")
                self.metadata = md

        return SearchResult(chunk)

    @staticmethod
    def _diversify(results: List[Any], max_per_doc: int, max_total: int) -> List[Any]:
        """Round-robin diversify across content_id."""
        by_doc: Dict[str, List[Any]] = {}
        for match in results:
            doc_id = match.metadata.get("content_id")
            by_doc.setdefault(doc_id, []).append(match)
        diverse: List[Any] = []
        while len(diverse) < max_total and any(by_doc.values()):
            for doc_id, matches in list(by_doc.items()):
                if not matches:
                    continue
                doc_count = len([m for m in diverse if m.metadata.get("content_id") == doc_id])
                if doc_count < max_per_doc:
                    diverse.append(matches.pop(0))
                    if len(diverse) >= max_total:
                        break
        return diverse[:max_total]


