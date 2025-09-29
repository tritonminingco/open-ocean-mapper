"""
File ingestion API endpoints.

Handles uploading and processing of raw ocean mapping data files.
Supports various formats: MBES, SBES, LiDAR, single-beam, AUV telemetry.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog

from ...pipeline.converter import ConvertJob, ConversionError
from ...utils.logging import setup_logging

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sensor_type: str = Form(...),
    metadata: str = Form("{}"),
    output_format: str = Form("netcdf"),
    anonymize: bool = Form(True),
    add_overlay: bool = Form(False),
    qc_mode: str = Form("auto")
):
    """
    Upload and queue ocean mapping data file for processing.
    
    Args:
        file: Raw data file (CSV, TXT, etc.)
        sensor_type: Type of sensor (mbes, sbes, lidar, singlebeam, auv)
        metadata: JSON metadata string
        output_format: Output format (netcdf, bag, geotiff)
        anonymize: Whether to anonymize vessel data
        add_overlay: Whether to add environmental overlays
        qc_mode: QC mode (auto, manual, skip)
    
    Returns:
        Job ID and initial status
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate sensor type
        valid_sensors = ["mbes", "sbes", "lidar", "singlebeam", "auv"]
        if sensor_type.lower() not in valid_sensors:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sensor type. Must be one of: {valid_sensors}"
            )
        
        # Validate output format
        valid_formats = ["netcdf", "bag", "geotiff"]
        if output_format.lower() not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output format. Must be one of: {valid_formats}"
            )
        
        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Parse metadata
        import json
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Store job information
        job_info = {
            "job_id": job_id,
            "filename": file.filename,
            "sensor_type": sensor_type.lower(),
            "output_format": output_format.lower(),
            "anonymize": anonymize,
            "add_overlay": add_overlay,
            "qc_mode": qc_mode.lower(),
            "metadata": metadata_dict,
            "status": "uploaded",
            "progress": 0,
            "message": "File uploaded successfully"
        }
        
        # Queue processing task
        background_tasks.add_task(
            process_uploaded_file,
            job_id,
            file,
            job_info
        )
        
        logger.info(
            "File uploaded and queued for processing",
            job_id=job_id,
            filename=file.filename,
            sensor_type=sensor_type
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": "uploaded",
                "message": "File uploaded and queued for processing"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload file", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def process_uploaded_file(job_id: str, file: UploadFile, job_info: Dict[str, Any]):
    """Background task to process uploaded file."""
    try:
        # Update job status
        job_info["status"] = "processing"
        job_info["progress"] = 10
        job_info["message"] = "Reading uploaded file"
        
        # Read file content
        content = await file.read()
        
        # Create temporary file
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(
            mode='wb', 
            delete=False, 
            suffix=f".{file.filename.split('.')[-1]}"
        ) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Update progress
            job_info["progress"] = 30
            job_info["message"] = "Converting data"
            
            # Create conversion job
            job = ConvertJob(
                input_path=tmp_file_path,
                sensor_type=job_info["sensor_type"],
                output_format=job_info["output_format"],
                anonymize=job_info["anonymize"],
                add_overlay=job_info["add_overlay"],
                qc_mode=job_info["qc_mode"]
            )
            
            # Run conversion
            result = job.run()
            
            # Update job status
            job_info["status"] = "completed"
            job_info["progress"] = 100
            job_info["message"] = "Conversion completed successfully"
            job_info["result"] = result
            
            logger.info("File processing completed", job_id=job_id, result=result)
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except ConversionError as e:
        job_info["status"] = "failed"
        job_info["message"] = f"Conversion failed: {str(e)}"
        logger.error("File processing failed", job_id=job_id, error=str(e))
        
    except Exception as e:
        job_info["status"] = "failed"
        job_info["message"] = f"Unexpected error: {str(e)}"
        logger.error("Unexpected file processing error", job_id=job_id, error=str(e))


@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported input and output formats."""
    return {
        "input_formats": {
            "mbes": ["csv", "txt", "all"],
            "sbes": ["csv", "txt", "all"],
            "lidar": ["las", "laz", "txt"],
            "singlebeam": ["csv", "txt"],
            "auv": ["csv", "txt", "json"]
        },
        "output_formats": {
            "netcdf": {
                "description": "NetCDF format for Seabed 2030 compliance",
                "extensions": [".nc"]
            },
            "bag": {
                "description": "Bathymetric Attributed Grid format",
                "extensions": [".bag"]
            },
            "geotiff": {
                "description": "GeoTIFF raster format",
                "extensions": [".tif", ".tiff"]
            }
        }
    }


@router.get("/validation-rules")
async def get_validation_rules():
    """Get validation rules for different sensor types."""
    return {
        "mbes": {
            "required_fields": ["timestamp", "latitude", "longitude", "depth", "beam_angle"],
            "optional_fields": ["quality", "intensity", "backscatter"],
            "coordinate_range": {
                "latitude": [-90, 90],
                "longitude": [-180, 180],
                "depth": [0, 12000]  # meters
            }
        },
        "sbes": {
            "required_fields": ["timestamp", "latitude", "longitude", "depth"],
            "optional_fields": ["quality", "frequency"],
            "coordinate_range": {
                "latitude": [-90, 90],
                "longitude": [-180, 180],
                "depth": [0, 12000]
            }
        },
        "lidar": {
            "required_fields": ["timestamp", "latitude", "longitude", "elevation"],
            "optional_fields": ["intensity", "classification"],
            "coordinate_range": {
                "latitude": [-90, 90],
                "longitude": [-180, 180],
                "elevation": [-1000, 10000]  # meters
            }
        },
        "singlebeam": {
            "required_fields": ["timestamp", "latitude", "longitude", "depth"],
            "optional_fields": ["quality"],
            "coordinate_range": {
                "latitude": [-90, 90],
                "longitude": [-180, 180],
                "depth": [0, 12000]
            }
        },
        "auv": {
            "required_fields": ["timestamp", "latitude", "longitude", "depth"],
            "optional_fields": ["heading", "pitch", "roll", "velocity"],
            "coordinate_range": {
                "latitude": [-90, 90],
                "longitude": [-180, 180],
                "depth": [0, 6000]
            }
        }
    }
