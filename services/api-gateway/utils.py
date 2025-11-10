"""
Utility functions for API Gateway.
"""
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from shared.logging.logger import get_logger

logger = get_logger("api_gateway_utils")


def get_correlation_headers(request: Any) -> Dict[str, str]:
    """
    Extract correlation ID from request and create headers for downstream services.
    
    Args:
        request: FastAPI/Starlette request object
    
    Returns:
        Dictionary with correlation ID header
    """
    correlation_id = getattr(request.state, "correlation_id", None)
    headers = {}
    
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    
    return headers


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError)),
    reraise=True
)
async def make_service_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    request: Any,
    **kwargs
) -> httpx.Response:
    """
    Make a request to a downstream service with retry logic and correlation ID.
    
    Args:
        client: httpx AsyncClient
        method: HTTP method
        url: Service URL
        request: Original request object for correlation ID
        **kwargs: Additional arguments for httpx request
    
    Returns:
        httpx Response object
    """
    # Add correlation ID to headers
    headers = kwargs.get("headers", {})
    headers.update(get_correlation_headers(request))
    kwargs["headers"] = headers
    
    try:
        response = await client.request(method, url, **kwargs)
        return response
    except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError) as e:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        logger.warning(
            f"Service request failed: {method} {url}",
            extra={"correlation_id": correlation_id, "error": str(e)}
        )
        raise

