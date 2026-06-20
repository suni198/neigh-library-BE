import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime
from contextvars import ContextVar
from typing import Optional

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[int]] = ContextVar('user_id', default=None)
member_id_var: ContextVar[Optional[int]] = ContextVar('member_id', default=None)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes context variables"""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add context from context vars
        request_id = request_id_var.get()
        if request_id:
            log_record['request_id'] = request_id
            
        user_id = user_id_var.get()
        if user_id:
            log_record['user_id'] = user_id
            
        member_id = member_id_var.get()
        if member_id:
            log_record['member_id'] = member_id
        
        # Add source location
        log_record['module'] = record.module
        log_record['function'] = record.funcName

def setup_logging(log_level: str = "INFO"):
    """Setup structured JSON logging"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def set_request_context(request_id: str = None, user_id: int = None, member_id: int = None):
    """Set context variables for the current request"""
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if member_id:
        member_id_var.set(member_id)

def clear_request_context():
    """Clear all context variables"""
    request_id_var.set(None)
    user_id_var.set(None)
    member_id_var.set(None)

# Helper functions for common log patterns
def log_api_request(logger: logging.Logger, method: str, path: str, **kwargs):
    """Log API request with context"""
    logger.info(
        "API Request",
        extra={
            "event": "api_request",
            "method": method,
            "path": path,
            **kwargs
        }
    )

def log_api_response(logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
    """Log API response with context"""
    logger.info(
        "API Response",
        extra={
            "event": "api_response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **kwargs
        }
    )

def log_db_operation(logger: logging.Logger, operation: str, table: str, **kwargs):
    """Log database operation with context"""
    logger.info(
        "Database Operation",
        extra={
            "event": "db_operation",
            "operation": operation,
            "table": table,
            **kwargs
        }
    )

def log_business_event(logger: logging.Logger, event_name: str, **kwargs):
    """Log business event with context"""
    logger.info(
        f"Business Event: {event_name}",
        extra={
            "event": "business_event",
            "event_name": event_name,
            **kwargs
        }
    )

def log_error(logger: logging.Logger, error_message: str, exception: Exception = None, **kwargs):
    """Log error with context"""
    extra = {
        "event": "error",
        "error_message": error_message,
        **kwargs
    }
    
    if exception:
        extra["exception_type"] = type(exception).__name__
        extra["exception_message"] = str(exception)
    
    logger.error(error_message, extra=extra, exc_info=exception is not None)

def log_critical(logger: logging.Logger, error_message: str, exception: Exception = None, **kwargs):
    """Log critical error that requires immediate attention"""
    extra = {
        "event": "critical_error",
        "error_message": error_message,
        "requires_immediate_attention": True,
        **kwargs
    }
    
    if exception:
        extra["exception_type"] = type(exception).__name__
        extra["exception_message"] = str(exception)
        extra["exception_traceback"] = True
    
    logger.critical(error_message, extra=extra, exc_info=exception is not None)

def log_warning(logger: logging.Logger, warning_message: str, **kwargs):
    """Log warning with context"""
    logger.warning(
        warning_message,
        extra={
            "event": "warning",
            "warning_message": warning_message,
            **kwargs
        }
    )
