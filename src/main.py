"""
FastAPI application for Open Ocean Mapper.

Provides REST API endpoints for:
- File ingestion and conversion
- Quality control processing
- Seabed 2030 upload preparation
- Job status monitoring

Usage:
    uvicorn src.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from .api.v1.ingest import router as ingest_router
from .api.v1.status import router as status_router
from .utils.logging import setup_logging
from .pipeline.converter import ConvertJob, ConversionError
from .qc.model_stub import load_model
from .adapters.seabed2030_adapter import Seabed2030Adapter

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global state for job tracking
job_status: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Open Ocean Mapper API")
    
    # Initialize ML model
    try:
        model = load_model()
        logger.info("ML model loaded successfully")
    except Exception as e:
        logger.warning("Failed to load ML model", error=str(e))
    
    yield
    
    logger.info("Shutting down Open Ocean Mapper API")


app = FastAPI(
    title="Open Ocean Mapper API",
    description="Convert raw ocean mapping data to Seabed 2030-compliant outputs",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(ingest_router, prefix="/api/v1")
app.include_router(status_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Open Ocean Mapper API",
        "version": "1.0.0",
        "description": "Convert raw ocean mapping data to Seabed 2030-compliant outputs",
        "endpoints": {
            "ingest": "/api/v1/ingest",
            "status": "/api/v1/status",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/api/v1/convert")
async def convert_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sensor_type: str = Form(...),
    output_format: str = Form("netcdf"),
    anonymize: bool = Form(True),
    add_overlay: bool = Form(False),
    qc_mode: str = Form("auto")
):
    """
    Convert uploaded ocean mapping data file.
    
    Args:
        file: Raw data file (CSV, TXT, etc.)
        sensor_type: Type of sensor (mbes, sbes, lidar, singlebeam, auv)
        output_format: Output format (netcdf, bag, geotiff)
        anonymize: Whether to anonymize vessel data
        add_overlay: Whether to add environmental overlays
        qc_mode: QC mode (auto, manual, skip)
    
    Returns:
        Job ID for tracking conversion progress
    """
    try:
        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        job_status[job_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Job queued for processing",
            "created_at": "2024-01-01T00:00:00Z",  # TODO: Use actual timestamp
            "sensor_type": sensor_type,
            "output_format": output_format,
            "anonymize": anonymize,
            "add_overlay": add_overlay,
            "qc_mode": qc_mode,
            "filename": file.filename,
        }
        
        # Queue background task
        background_tasks.add_task(
            process_conversion,
            job_id,
            file,
            sensor_type,
            output_format,
            anonymize,
            add_overlay,
            qc_mode
        )
        
        logger.info("Conversion job queued", job_id=job_id, filename=file.filename)
        
        return {"job_id": job_id, "status": "queued"}
        
    except Exception as e:
        logger.error("Failed to queue conversion job", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def process_conversion(
    job_id: str,
    file: UploadFile,
    sensor_type: str,
    output_format: str,
    anonymize: bool,
    add_overlay: bool,
    qc_mode: str
):
    """Background task to process file conversion."""
    try:
        # Update job status
        job_status[job_id]["status"] = "processing"
        job_status[job_id]["progress"] = 10
        job_status[job_id]["message"] = "Reading input file"
        
        # Read file content
        content = await file.read()
        
        # Create temporary file
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Update progress
            job_status[job_id]["progress"] = 30
            job_status[job_id]["message"] = "Converting data"
            
            # Create conversion job
            job = ConvertJob(
                input_path=tmp_file_path,
                sensor_type=sensor_type,
                output_format=output_format,
                anonymize=anonymize,
                add_overlay=add_overlay,
                qc_mode=qc_mode
            )
            
            # Run conversion
            result = job.run()
            
            # Update job status
            job_status[job_id]["status"] = "completed"
            job_status[job_id]["progress"] = 100
            job_status[job_id]["message"] = "Conversion completed successfully"
            job_status[job_id]["result"] = result
            
            logger.info("Conversion completed", job_id=job_id, result=result)
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except ConversionError as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = f"Conversion failed: {str(e)}"
        logger.error("Conversion failed", job_id=job_id, error=str(e))
        
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = f"Unexpected error: {str(e)}"
        logger.error("Unexpected conversion error", job_id=job_id, error=str(e))


@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a conversion job."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status[job_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
