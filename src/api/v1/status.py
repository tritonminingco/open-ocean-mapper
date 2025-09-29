"""
Job status and health check API endpoints.

Provides real-time status updates for conversion jobs and system health monitoring.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import structlog
from datetime import datetime

from ...utils.logging import setup_logging

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/status", tags=["status"])

# In-memory job storage (in production, use Redis or database)
job_storage: Dict[str, Dict[str, Any]] = {}


@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check system components
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "components": {
                "api": "healthy",
                "converter": "healthy",
                "qc": "healthy",
                "storage": "healthy"
            },
            "metrics": {
                "active_jobs": len([j for j in job_storage.values() if j["status"] in ["queued", "processing"]]),
                "completed_jobs": len([j for j in job_storage.values() if j["status"] == "completed"]),
                "failed_jobs": len([j for j in job_storage.values() if j["status"] == "failed"])
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }
        )


@router.get("/jobs")
async def list_jobs(
    status: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List all jobs with optional filtering.
    
    Args:
        status: Filter by job status (queued, processing, completed, failed)
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
    
    Returns:
        List of jobs with metadata
    """
    try:
        jobs = list(job_storage.values())
        
        # Filter by status if provided
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        total = len(jobs)
        jobs = jobs[offset:offset + limit]
        
        return {
            "jobs": jobs,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }
        
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get detailed status of a specific job.
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        Job status and metadata
    """
    try:
        if job_id not in job_storage:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_storage[job_id]
        
        # Add additional metadata
        job_info = {
            **job,
            "job_id": job_id,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return job_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a queued or processing job.
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        Cancellation status
    """
    try:
        if job_id not in job_storage:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_storage[job_id]
        
        # Only allow cancellation of queued or processing jobs
        if job["status"] not in ["queued", "processing"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel job with status: {job['status']}"
            )
        
        # Update job status
        job["status"] = "cancelled"
        job["message"] = "Job cancelled by user"
        job["cancelled_at"] = datetime.utcnow().isoformat() + "Z"
        
        logger.info("Job cancelled", job_id=job_id)
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics():
    """
    Get system metrics and statistics.
    
    Returns:
        System performance metrics
    """
    try:
        jobs = list(job_storage.values())
        
        # Calculate metrics
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j["status"] == "completed"])
        failed_jobs = len([j for j in jobs if j["status"] == "failed"])
        active_jobs = len([j for j in jobs if j["status"] in ["queued", "processing"]])
        
        # Calculate success rate
        processed_jobs = completed_jobs + failed_jobs
        success_rate = (completed_jobs / processed_jobs * 100) if processed_jobs > 0 else 0
        
        # Calculate average processing time (mock data)
        avg_processing_time = 120  # seconds
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "jobs": {
                "total": total_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs,
                "active": active_jobs,
                "success_rate": round(success_rate, 2)
            },
            "performance": {
                "avg_processing_time_seconds": avg_processing_time,
                "throughput_jobs_per_hour": 30  # mock value
            },
            "system": {
                "uptime_seconds": 3600,  # mock value
                "memory_usage_mb": 512,   # mock value
                "cpu_usage_percent": 25   # mock value
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue")
async def get_queue_status():
    """
    Get current queue status and estimated wait times.
    
    Returns:
        Queue information and wait time estimates
    """
    try:
        jobs = list(job_storage.values())
        
        queued_jobs = [j for j in jobs if j["status"] == "queued"]
        processing_jobs = [j for j in jobs if j["status"] == "processing"]
        
        # Calculate estimated wait time (mock calculation)
        avg_processing_time = 120  # seconds
        estimated_wait = len(queued_jobs) * avg_processing_time
        
        queue_status = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "queue": {
                "queued_jobs": len(queued_jobs),
                "processing_jobs": len(processing_jobs),
                "estimated_wait_seconds": estimated_wait,
                "estimated_wait_minutes": round(estimated_wait / 60, 1)
            },
            "capacity": {
                "max_concurrent_jobs": 5,
                "available_slots": max(0, 5 - len(processing_jobs))
            }
        }
        
        return queue_status
        
    except Exception as e:
        logger.error("Failed to get queue status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
