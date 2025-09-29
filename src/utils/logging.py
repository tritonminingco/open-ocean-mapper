"""
Structured logging configuration for Open Ocean Mapper.

Provides JSON-formatted logging with proper context and correlation IDs.
Uses structlog for structured logging and proper log formatting.

Features:
- JSON structured logging
- Request correlation IDs
- Log level configuration
- File and console output
- Performance metrics logging

Usage:
    from src.utils.logging import setup_logging
    setup_logging()
"""

import logging
import sys
from typing import Dict, Any, Optional
import structlog
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True
) -> None:
    """
    Setup structured logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_format: Whether to use JSON formatting
    """
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        stream=sys.stdout
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        
        # Add file handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def log_performance(func_name: str, duration: float, **kwargs) -> None:
    """
    Log performance metrics.
    
    Args:
        func_name: Function name
        duration: Execution duration in seconds
        **kwargs: Additional context
    """
    logger = get_logger("performance")
    logger.info(
        "Performance metric",
        function=func_name,
        duration_seconds=duration,
        **kwargs
    )


def log_data_processing(
    operation: str,
    input_size: int,
    output_size: int,
    duration: float,
    **kwargs
) -> None:
    """
    Log data processing metrics.
    
    Args:
        operation: Processing operation name
        input_size: Input data size
        output_size: Output data size
        duration: Processing duration in seconds
        **kwargs: Additional context
    """
    logger = get_logger("data_processing")
    logger.info(
        "Data processing completed",
        operation=operation,
        input_size=input_size,
        output_size=output_size,
        duration_seconds=duration,
        efficiency=output_size / input_size if input_size > 0 else 0,
        **kwargs
    )


def log_conversion_job(
    job_id: str,
    status: str,
    sensor_type: str,
    output_format: str,
    **kwargs
) -> None:
    """
    Log conversion job events.
    
    Args:
        job_id: Job identifier
        status: Job status
        sensor_type: Type of sensor
        output_format: Output format
        **kwargs: Additional context
    """
    logger = get_logger("conversion_job")
    logger.info(
        "Conversion job event",
        job_id=job_id,
        status=status,
        sensor_type=sensor_type,
        output_format=output_format,
        **kwargs
    )


def log_qc_results(
    sensor_type: str,
    total_points: int,
    anomalies_found: int,
    quality_score: float,
    **kwargs
) -> None:
    """
    Log quality control results.
    
    Args:
        sensor_type: Type of sensor
        total_points: Total number of data points
        anomalies_found: Number of anomalies detected
        quality_score: Overall quality score
        **kwargs: Additional context
    """
    logger = get_logger("quality_control")
    logger.info(
        "Quality control completed",
        sensor_type=sensor_type,
        total_points=total_points,
        anomalies_found=anomalies_found,
        quality_score=quality_score,
        anomaly_rate=anomalies_found / total_points if total_points > 0 else 0,
        **kwargs
    )


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration: float,
    **kwargs
) -> None:
    """
    Log API request metrics.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration: Request duration in seconds
        **kwargs: Additional context
    """
    logger = get_logger("api_request")
    logger.info(
        "API request completed",
        method=method,
        path=path,
        status_code=status_code,
        duration_seconds=duration,
        **kwargs
    )


def log_error(
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log error events.
    
    Args:
        error_type: Type of error
        error_message: Error message
        context: Additional context
    """
    logger = get_logger("error")
    logger.error(
        "Error occurred",
        error_type=error_type,
        error_message=error_message,
        context=context or {}
    )


def log_security_event(
    event_type: str,
    severity: str,
    details: str,
    **kwargs
) -> None:
    """
    Log security events.
    
    Args:
        event_type: Type of security event
        severity: Event severity
        details: Event details
        **kwargs: Additional context
    """
    logger = get_logger("security")
    logger.warning(
        "Security event",
        event_type=event_type,
        severity=severity,
        details=details,
        **kwargs
    )
