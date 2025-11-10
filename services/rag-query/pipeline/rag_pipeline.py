"""
Complete RAG pipeline for question answering.
"""
import time
import asyncio
from typing import AsyncIterator, Dict, Any
from retrieval.pinecone_retriever import PineconeRetriever
from llm.openai_client import OpenAIClient
from cache.redis_cache import ResponseCache
from security.prompt_injection_filter import PromptInjectionFilter
from prompts.educational_prompts import create_rag_prompt
from shared.observability.langfuse_client import langfuse_client
from shared.logging.logger import get_logger

logger = get_logger("rag_pipeline")


class RAGPipeline:
    """Complete RAG pipeline for educational question answering."""
    
    def __init__(
        self,
        retriever: PineconeRetriever,
        llm_client: OpenAIClient,
        cache: ResponseCache
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            retriever: Pinecone retriever instance
            llm_client: OpenAI client instance
            cache: Response cache instance
        """
        self.retriever = retriever
        self.llm_client = llm_client
        self.cache = cache
        self.filter = PromptInjectionFilter()
    
    async def process_query_stream(
        self,
        content_id: str,
        question: str,
        user_id: str,
        session_id: str = None,
        student_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> AsyncIterator[str]:
        """
        Process a query and stream the response.
        
        Args:
            content_id: Content ID to query
            question: User's question
            user_id: User ID for tracking
            session_id: Session ID for grouping conversations
            student_id: Student ID for tracking
            metadata: Additional metadata (subject, grade_level, etc.)
        
        Yields:
            Chunks of generated response
        """
        start_time = time.time()
        additional_metadata = metadata or {}
        
        # Prepare tags for Langfuse
        tags = ["rag", "streaming"]
        if additional_metadata.get("subject"):
            tags.append(additional_metadata["subject"].lower())
        if additional_metadata.get("grade_level"):
            tags.append(f"grade_{additional_metadata['grade_level']}")
        
        # Start Langfuse trace with context manager
        trace = None
        if langfuse_client.is_enabled():
            try:
                trace = langfuse_client.client.trace(
                    name="rag_query_stream",
                    user_id=user_id,
                    session_id=session_id,
                    metadata={
                        "content_id": content_id,
                        "question": question,  # Store full question
                        "question_length": len(question),
                        "student_id": student_id or user_id,
                        **additional_metadata
                    },
                    tags=tags
                )
            except Exception as e:
                logger.warning(f"Failed to create Langfuse trace: {str(e)}")
        
        try:
            # 1. Validate and sanitize question
            logger.info(f"Processing query for content {content_id}")
            
            with langfuse_client.create_observation(
                name="validate_question",
                trace_id=trace.id if trace else None,
                input_data={"question": question, "length": len(question)}
            ) as validation_obs:
                sanitized_question = self.filter.validate_question(question)
                validation_obs.set_output({"sanitized_question": sanitized_question, "is_safe": True})
            
            # 2. Check cache
            with langfuse_client.create_observation(
                name="check_cache",
                trace_id=trace.id if trace else None,
                input_data={"content_id": content_id, "question": sanitized_question}
            ) as cache_obs:
                cached_response = await self.cache.get_cached_response(content_id, sanitized_question)
                cache_obs.set_output({"cache_hit": cached_response is not None})
            
            if cached_response:
                logger.info("Returning cached response")
                
                # Update trace with cache hit info
                if trace:
                    trace.update(
                        output={"response": cached_response['response'], "cached": True},
                        metadata={
                            "content_id": content_id,
                            "question": question,
                            "cached": True,
                            **additional_metadata
                        }
                    )
                
                # Stream cached response
                response_text = cached_response['response']
                # Split into chunks for streaming effect
                chunk_size = 50
                for i in range(0, len(response_text), chunk_size):
                    yield response_text[i:i+chunk_size]
                
                return
            
            # 3. Generate query embedding
            with langfuse_client.create_observation(
                name="generate_query_embedding",
                trace_id=trace.id if trace else None,
                input_data={"question": sanitized_question},
                metadata={"embedding_model": "text-embedding-3-large"}
            ) as embedding_obs:
                query_embedding = await self.llm_client.generate_embedding(sanitized_question)
                embedding_obs.set_output({"embedding_dimension": len(query_embedding)})
            
            # 4. Retrieve relevant chunks
            with langfuse_client.create_observation(
                name="retrieve_chunks",
                trace_id=trace.id if trace else None,
                input_data={"content_id": content_id, "query": sanitized_question}
            ) as retrieval_obs:
                chunks = await self.retriever.retrieve(
                    query_embedding=query_embedding,
                    content_id=content_id
                )
                
                # Enhanced logging: retrieval quality metrics
                if chunks:
                    scores = [chunk.get('score', 0) for chunk in chunks]
                    avg_score = sum(scores) / len(scores) if scores else 0
                    max_score = max(scores) if scores else 0
                    min_score = min(scores) if scores else 0
                    chunk_ids = [chunk.get('id', f'chunk_{i}') for i, chunk in enumerate(chunks)]
                    
                    logger.info(
                        f"[OK] Retrieved {len(chunks)} chunks | "
                        f"Avg score: {avg_score:.3f} | "
                        f"Max score: {max_score:.3f} | "
                        f"Min score: {min_score:.3f}",
                        extra={
                            "content_id": content_id,
                            "chunks_retrieved": len(chunks),
                            "avg_similarity": round(avg_score, 3),
                            "max_similarity": round(max_score, 3),
                            "min_similarity": round(min_score, 3),
                            "retrieval_quality": "good" if avg_score > 0.7 else "moderate" if avg_score > 0.5 else "low"
                        }
                    )
                    
                    # Set output for Langfuse
                    retrieval_obs.set_output({
                        "chunks_retrieved": len(chunks),
                        "avg_similarity": round(avg_score, 3),
                        "max_similarity": round(max_score, 3),
                        "min_similarity": round(min_score, 3),
                        "chunk_ids": chunk_ids,
                        "retrieval_quality": "good" if avg_score > 0.7 else "moderate" if avg_score > 0.5 else "low"
                    })
                else:
                    logger.warning(
                        f"[WARNING] No chunks retrieved for content {content_id}",
                        extra={"content_id": content_id, "question_length": len(sanitized_question)}
                    )
                    retrieval_obs.set_output({"chunks_retrieved": 0, "warning": "No chunks found"})
            
            # If no chunks, yield helpful message instead of trying to generate
            if not chunks or len(chunks) == 0:
                no_vectors_message = """I don't have searchable content for this document yet.

To enable chat: Upload this document through the "Upload New" button, wait for processing (1-2 min), then chat will work!

Why: Documents need to be vectorized before I can search and answer questions."""
                
                # Yield the message word by word for streaming effect
                words = no_vectors_message.split()
                for word in words:
                    yield word + " "
                    await asyncio.sleep(0.05)  # Small delay for streaming effect
                return
            
            # 5. Create prompt with context
            messages = create_rag_prompt(sanitized_question, chunks)
            
            # 6. Generate streaming response
            response_text = ""
            generation_start = time.time()
            
            # Create generation span
            generation_span = None
            if langfuse_client.is_enabled() and trace:
                try:
                    generation_span = langfuse_client.client.generation(
                        name="llm_generation",
                        model=self.llm_client.model,
                        input=messages,  # Full prompt with context
                        trace_id=trace.id,
                        metadata={
                            "temperature": 0.7,
                            "max_tokens": 1000,
                            "chunks_used": len(chunks),
                            "streaming": True
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to create generation span: {str(e)}")
            
            # Stream response and accumulate
            async for chunk in self.llm_client.generate_completion_stream(messages):
                response_text += chunk
                yield chunk
            
            # Update generation span with complete response
            generation_time = time.time() - generation_start
            if generation_span:
                try:
                    generation_span.end(
                        output=response_text,
                        metadata={
                            "temperature": 0.7,
                            "max_tokens": 1000,
                            "chunks_used": len(chunks),
                            "streaming": True,
                            "generation_time_seconds": round(generation_time, 3),
                            "response_length": len(response_text)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update generation span: {str(e)}")
            
            # 7. Validate response safety
            if not self.filter.check_response_safety(response_text):
                logger.warning("Unsafe response detected, not caching")
            else:
                # 8. Cache response
                response_time = time.time() - start_time
                
                await self.cache.cache_response(
                    content_id=content_id,
                    question=sanitized_question,
                    response=response_text,
                    metadata={
                        "chunks_used": len(chunks),
                        "response_time_ms": int(response_time * 1000)
                    }
                )
            
            # Update trace with final output
            response_time = time.time() - start_time
            if trace:
                try:
                    trace.update(
                        output={
                            "response": response_text,
                            "cached": False
                        },
                        metadata={
                            "content_id": content_id,
                            "question": question,
                            "response_length": len(response_text),
                            "chunks_used": len(chunks),
                            "response_time_seconds": round(response_time, 3),
                            **additional_metadata
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update trace: {str(e)}")
            
            logger.info(f"Query processed in {response_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            
            # Log error to trace
            if trace:
                try:
                    trace.update(
                        level="ERROR",
                        status_message=str(e),
                        metadata={
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
                except Exception as update_error:
                    logger.warning(f"Failed to log error to trace: {str(update_error)}")
            
            error_message = f"\n\nI apologize, but I encountered an error processing your question. Please try again or rephrase your question."
            yield error_message
    
    async def process_query(
        self,
        content_id: str,
        question: str,
        user_id: str,
        session_id: str = None,
        student_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a query and return complete response (non-streaming).
        
        Args:
            content_id: Content ID to query
            question: User's question
            user_id: User ID for tracking
            session_id: Session ID for grouping conversations
            student_id: Student ID for tracking
            metadata: Additional metadata (subject, grade_level, etc.)
        
        Returns:
            Response with answer and metadata
        """
        start_time = time.time()
        additional_metadata = metadata or {}
        
        # Prepare tags for Langfuse
        tags = ["rag", "complete"]
        if additional_metadata.get("subject"):
            tags.append(additional_metadata["subject"].lower())
        if additional_metadata.get("grade_level"):
            tags.append(f"grade_{additional_metadata['grade_level']}")
        
        # Start Langfuse trace
        trace = None
        if langfuse_client.is_enabled():
            try:
                trace = langfuse_client.client.trace(
                    name="rag_query_complete",
                    user_id=user_id,
                    session_id=session_id,
                    metadata={
                        "content_id": content_id,
                        "question": question,  # Store full question
                        "question_length": len(question),
                        "student_id": student_id or user_id,
                        **additional_metadata
                    },
                    tags=tags
                )
            except Exception as e:
                logger.warning(f"Failed to create Langfuse trace: {str(e)}")
        
        try:
            # Validate question
            with langfuse_client.create_observation(
                name="validate_question",
                trace_id=trace.id if trace else None,
                input_data={"question": question, "length": len(question)}
            ) as validation_obs:
                sanitized_question = self.filter.validate_question(question)
                validation_obs.set_output({"sanitized_question": sanitized_question, "is_safe": True})
            
            # Check cache
            with langfuse_client.create_observation(
                name="check_cache",
                trace_id=trace.id if trace else None,
                input_data={"content_id": content_id, "question": sanitized_question}
            ) as cache_obs:
                cached_response = await self.cache.get_cached_response(content_id, sanitized_question)
                cache_obs.set_output({"cache_hit": cached_response is not None})
            
            if cached_response:
                # Update trace with cache hit info
                if trace:
                    trace.update(
                        output={"response": cached_response['response'], "cached": True},
                        metadata={
                            "content_id": content_id,
                            "question": question,
                            "cached": True,
                            **additional_metadata
                        }
                    )
                return cached_response
            
            # Generate embedding
            with langfuse_client.create_observation(
                name="generate_query_embedding",
                trace_id=trace.id if trace else None,
                input_data={"question": sanitized_question},
                metadata={"embedding_model": "text-embedding-3-large"}
            ) as embedding_obs:
                query_embedding = await self.llm_client.generate_embedding(sanitized_question)
                embedding_obs.set_output({"embedding_dimension": len(query_embedding)})
            
            # Retrieve chunks
            with langfuse_client.create_observation(
                name="retrieve_chunks",
                trace_id=trace.id if trace else None,
                input_data={"content_id": content_id, "query": sanitized_question}
            ) as retrieval_obs:
                chunks = await self.retriever.retrieve(
                    query_embedding=query_embedding,
                    content_id=content_id
                )
                
                # Enhanced logging: retrieval quality metrics
                if chunks:
                    scores = [chunk.get('score', 0) for chunk in chunks]
                    avg_score = sum(scores) / len(scores) if scores else 0
                    chunk_ids = [chunk.get('id', f'chunk_{i}') for i, chunk in enumerate(chunks)]
                    
                    logger.info(
                        f"[OK] Retrieved {len(chunks)} chunks (avg score: {avg_score:.3f})",
                        extra={
                            "content_id": content_id,
                            "chunks_retrieved": len(chunks),
                            "avg_similarity": round(avg_score, 3)
                        }
                    )
                    
                    retrieval_obs.set_output({
                        "chunks_retrieved": len(chunks),
                        "avg_similarity": round(avg_score, 3),
                        "chunk_ids": chunk_ids
                    })
                else:
                    # No chunks found - document not vectorized
                    logger.warning(f"No vectors found for content {content_id}")
                    retrieval_obs.set_output({"chunks_retrieved": 0, "warning": "No vectors in Pinecone"})
            
            # If no chunks, return helpful message instead of trying to generate
            if not chunks or len(chunks) == 0:
                no_vectors_response = """I don't have searchable content for this document yet.

**To enable chat with this document:**
1. This document needs to be uploaded through the "Upload New" button
2. The system will process and vectorize it (takes 1-2 minutes)
3. You'll see a "Ready" status badge when complete
4. Then you can ask questions and I'll provide answers with sources!

**Why this happens:** Documents need to be converted into searchable vectors before I can find relevant information. Directly added database entries don't have these vectors yet."""
                
                response_time = time.time() - start_time
                return {
                    "response": no_vectors_response,
                    "cached": False,
                    "metadata": {
                        "chunks_used": 0,
                        "response_time_ms": int(response_time * 1000),
                        "llm_time_ms": 0,
                        "tokens_used": {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0
                        }
                    },
                    "sources": []
                }
            
            # Create prompt
            messages = create_rag_prompt(sanitized_question, chunks)
            
            # Generate response
            gen_start = time.time()
            
            # Create generation span
            generation_span = None
            if langfuse_client.is_enabled() and trace:
                try:
                    generation_span = langfuse_client.client.generation(
                        name="llm_generation",
                        model=self.llm_client.model,
                        input=messages,  # Full prompt with context
                        trace_id=trace.id,
                        metadata={
                            "temperature": 0.7,
                            "max_tokens": 1000,
                            "chunks_used": len(chunks)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to create generation span: {str(e)}")
            
            response_data = await self.llm_client.generate_completion(messages)
            gen_time = time.time() - gen_start
            
            # Update generation span with output and usage
            if generation_span:
                try:
                    generation_span.end(
                        output=response_data['content'],
                        usage={
                            "prompt_tokens": response_data['usage'].get('prompt_tokens', 0),
                            "completion_tokens": response_data['usage'].get('completion_tokens', 0),
                            "total_tokens": response_data['usage'].get('total_tokens', 0)
                        },
                        metadata={
                            "temperature": 0.7,
                            "max_tokens": 1000,
                            "chunks_used": len(chunks),
                            "generation_time_seconds": round(gen_time, 3)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update generation span: {str(e)}")
            
            response_time = time.time() - start_time
            
            # Log performance metrics
            logger.info(
                f"[OK] Response generated | "
                f"Total: {response_time:.2f}s | "
                f"LLM: {gen_time:.2f}s | "
                f"Tokens: {response_data['usage'].get('total_tokens', 0)}",
                extra={
                    "response_time_ms": int(response_time * 1000),
                    "llm_time_ms": int(gen_time * 1000),
                    "tokens_used": response_data['usage'].get('total_tokens', 0),
                    "prompt_tokens": response_data['usage'].get('prompt_tokens', 0),
                    "completion_tokens": response_data['usage'].get('completion_tokens', 0)
                }
            )
            
            # Extract source references from chunks
            sources = []
            for i, chunk in enumerate(chunks):
                metadata = chunk.get('metadata', {})
                sources.append({
                    "source_id": i + 1,
                    "document_title": metadata.get('document_title', 'Unknown'),
                    "uploader_name": metadata.get('uploader_name', 'Unknown'),
                    "uploader_id": metadata.get('uploader_id', 'unknown'),
                    "upload_date": metadata.get('upload_date', 'Unknown')[:10] if metadata.get('upload_date') else 'Unknown',
                    "chunk_index": metadata.get('chunk_index', 0),
                    "similarity_score": chunk.get('score', 0.0)
                })
            
            result = {
                "response": response_data['content'],
                "sources": sources,
                "metadata": {
                    "chunks_used": len(chunks),
                    "response_time_ms": int(response_time * 1000),
                    "llm_time_ms": int(gen_time * 1000),
                    "tokens_used": response_data['usage'],
                    "model": response_data['model']
                },
                "cached": False
            }
            
            # Update trace with final output
            if trace:
                try:
                    trace.update(
                        output={
                            "response": response_data['content'],
                            "cached": False
                        },
                        metadata={
                            "content_id": content_id,
                            "question": question,
                            "response_length": len(response_data['content']),
                            "chunks_used": len(chunks),
                            "response_time_seconds": round(response_time, 3),
                            "tokens_used": response_data['usage'].get('total_tokens', 0),
                            **additional_metadata
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update trace: {str(e)}")
            
            # Cache response
            if self.filter.check_response_safety(response_data['content']):
                await self.cache.cache_response(
                    content_id=content_id,
                    question=sanitized_question,
                    response=response_data['content'],
                    metadata=result['metadata']
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            
            # Log error to trace
            if trace:
                try:
                    trace.update(
                        level="ERROR",
                        status_message=str(e),
                        metadata={
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
                except Exception as update_error:
                    logger.warning(f"Failed to log error to trace: {str(update_error)}")
            
            raise

