from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import uuid
from app.core.logging import get_logger, set_request_context, clear_request_context, log_api_request, log_api_response

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses with context"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Set request context
        set_request_context(request_id=request_id)
        
        # Start timer
        start_time = time.time()
        
        # Log request
        log_api_request(
            logger,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None
        )
        
        # Process request
        try:
            response: Response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            log_api_response(
                logger,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "event": "request_error",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "exception_type": type(e).__name__
                },
                exc_info=True
            )
            raise
        finally:
            # Clear context
            clear_request_context()
