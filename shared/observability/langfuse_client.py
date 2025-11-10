"""
Langfuse client wrapper for LLM observability and tracing.
"""
from typing import Optional, Dict, Any, List
from langfuse import Langfuse
from contextlib import contextmanager
import time
from shared.logging.logger import get_logger

logger = get_logger("langfuse_client")


class LangfuseObservation:
    """Context manager for spans with automatic output capture and timing."""
    
    def __init__(self, client: 'LangfuseClient', name: str, trace_id: Optional[str] = None,
                 input_data: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None):
        self.client = client
        self.name = name
        self.trace_id = trace_id
        self.input_data = input_data
        self.metadata = metadata or {}
        self.start_time = None
        self.output_data = None
        self.span_obj = None
    
    def __enter__(self):
        """Start timing and create span."""
        self.start_time = time.time()
        if self.client.is_enabled():
            try:
                # Create span with input
                self.span_obj = self.client.client.span(
                    name=self.name,
                    input=self.input_data,
                    metadata=self.metadata,
                    trace_id=self.trace_id
                )
            except Exception as e:
                logger.warning(f"Failed to create observation span: {str(e)}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Capture output, duration, and complete span."""
        if self.client.is_enabled() and self.span_obj:
            try:
                duration = time.time() - self.start_time
                
                # Update span with output and duration
                update_data = {
                    "output": self.output_data,
                    "metadata": {
                        **self.metadata,
                        "duration_seconds": round(duration, 3)
                    }
                }
                
                # Add error information if exception occurred
                if exc_type:
                    update_data["level"] = "ERROR"
                    update_data["status_message"] = str(exc_val)
                    update_data["metadata"]["error_type"] = exc_type.__name__
                
                self.span_obj.end(**update_data)
            except Exception as e:
                logger.warning(f"Failed to complete observation span: {str(e)}")
        
        return False  # Don't suppress exceptions
    
    def set_output(self, output: Any):
        """Set the output data for this observation."""
        self.output_data = output


class LangfuseClient:
    """Langfuse client wrapper for tracing and observability."""
    
    def __init__(self):
        self.client: Optional[Langfuse] = None
        self._enabled = False
    
    def initialize(
        self,
        public_key: Optional[str],
        secret_key: Optional[str],
        host: str = "https://cloud.langfuse.com"
    ):
        """
        Initialize Langfuse client.
        
        Args:
            public_key: Langfuse public key
            secret_key: Langfuse secret key
            host: Langfuse host URL
        """
        if not public_key or not secret_key:
            logger.warning("Langfuse keys not provided. Tracing will be disabled.")
            self._enabled = False
            return
        
        try:
            self.client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            self._enabled = True
            logger.info("Langfuse client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {str(e)}")
            self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Langfuse tracing is enabled."""
        return self._enabled
    
    def trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None
    ):
        """
        Create a new trace.
        
        Args:
            name: Trace name
            user_id: User ID for tracking
            session_id: Session ID for grouping
            metadata: Additional metadata
            tags: Tags for categorization
        
        Returns:
            Trace object or None if disabled
        """
        if not self._enabled:
            return None
        
        try:
            return self.client.trace(
                name=name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {},
                tags=tags or []
            )
        except Exception as e:
            logger.error(f"Failed to create trace: {str(e)}")
            return None
    
    def generation(
        self,
        name: str,
        model: str,
        input: Any,
        output: Any,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        """
        Log a generation (LLM call).
        
        Args:
            name: Generation name
            model: Model name
            input: Input to the model
            output: Output from the model
            usage: Token usage statistics
            metadata: Additional metadata
            trace_id: Parent trace ID
        """
        if not self._enabled:
            return
        
        try:
            self.client.generation(
                name=name,
                model=model,
                model_parameters={},
                input=input,
                output=output,
                usage=usage or {},
                metadata=metadata or {},
                trace_id=trace_id
            )
        except Exception as e:
            logger.error(f"Failed to log generation: {str(e)}")
    
    def span(
        self,
        name: str,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        """
        Log a span (operation within a trace).
        
        Args:
            name: Span name
            input: Input data
            output: Output data
            metadata: Additional metadata
            trace_id: Parent trace ID
        """
        if not self._enabled:
            return
        
        try:
            self.client.span(
                name=name,
                input=input,
                output=output,
                metadata=metadata or {},
                trace_id=trace_id
            )
        except Exception as e:
            logger.error(f"Failed to log span: {str(e)}")
    
    def score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None
    ):
        """
        Add a score to a trace.
        
        Args:
            trace_id: Trace ID
            name: Score name
            value: Score value
            comment: Optional comment
        """
        if not self._enabled:
            return
        
        try:
            self.client.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment
            )
        except Exception as e:
            logger.error(f"Failed to log score: {str(e)}")
    
    def flush(self):
        """Flush pending traces to Langfuse."""
        if self._enabled and self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Failed to flush traces: {str(e)}")
    
    def shutdown(self):
        """
        Shutdown the client and flush all pending traces.
        Should be called during application shutdown.
        """
        logger.info("Shutting down Langfuse client...")
        self.flush()
        if self._enabled:
            logger.info("Langfuse client shutdown complete")
    
    @contextmanager
    def create_trace_context(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Context manager for creating and auto-completing traces.
        
        Usage:
            with langfuse_client.create_trace_context(
                name="my_operation",
                user_id="user123",
                metadata={"key": "value"}
            ) as trace:
                # Your code here
                pass
        
        Args:
            name: Trace name
            user_id: User ID for tracking
            session_id: Session ID for grouping
            metadata: Additional metadata
            tags: Tags for categorization
        
        Yields:
            Trace object or None if disabled
        """
        trace = None
        start_time = time.time()
        
        if self._enabled:
            try:
                trace = self.client.trace(
                    name=name,
                    user_id=user_id,
                    session_id=session_id,
                    metadata=metadata or {},
                    tags=tags or []
                )
            except Exception as e:
                logger.error(f"Failed to create trace context: {str(e)}")
        
        try:
            yield trace
        except Exception as e:
            # Log error to trace
            if trace:
                try:
                    trace.update(
                        level="ERROR",
                        status_message=str(e),
                        metadata={
                            **(metadata or {}),
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
                except Exception as update_error:
                    logger.warning(f"Failed to update trace with error: {str(update_error)}")
            raise
        finally:
            # Add duration to trace
            if trace:
                try:
                    duration = time.time() - start_time
                    trace.update(
                        metadata={
                            **(metadata or {}),
                            "total_duration_seconds": round(duration, 3)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to finalize trace: {str(e)}")
    
    def create_observation(
        self,
        name: str,
        trace_id: Optional[str] = None,
        input_data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LangfuseObservation:
        """
        Create an observation context manager for automatic span tracking.
        
        Usage:
            with langfuse_client.create_observation(
                name="retrieval",
                trace_id=trace.id,
                input_data={"query": "test"}
            ) as obs:
                result = do_work()
                obs.set_output(result)
        
        Args:
            name: Observation name
            trace_id: Parent trace ID
            input_data: Input data
            metadata: Additional metadata
        
        Returns:
            LangfuseObservation context manager
        """
        return LangfuseObservation(
            client=self,
            name=name,
            trace_id=trace_id,
            input_data=input_data,
            metadata=metadata
        )


# Global Langfuse client instance
langfuse_client = LangfuseClient()


def get_langfuse() -> LangfuseClient:
    """
    Get Langfuse client instance.
    
    Returns:
        Langfuse client
    """
    return langfuse_client

