"""
Core conversion pipeline orchestrator.

Converts raw ocean mapping data into standardized formats with quality control,
anonymization, and environmental overlays.

Usage:
    job = ConvertJob(
        input_path="data.csv",
        sensor_type="mbes",
        output_format="netcdf",
        anonymize=True,
        add_overlay=True,
        qc_mode="auto"
    )
    result = job.run()
"""

import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog

from .formats.mbes import parse_mbes_file
from .formats.sbet import parse_sbet_file
from .formats.lidar import parse_lidar_file
from .exporters.netcdf_exporter import export_to_netcdf
from .exporters.bag_exporter import export_to_bag
from .exporters.geotiff_exporter import export_to_geotiff
from .anonymize import anonymize_data
from .overlay import apply_overlay
from ..qc.model_stub import predict_anomalies
from ..qc.rules import apply_qc_rules
from ..utils.geo import reproject_to_wgs84, create_bathymetric_surface

logger = structlog.get_logger(__name__)


class ConversionError(Exception):
    """Raised when conversion fails."""
    pass


class ConvertJob:
    """
    Ocean mapping data conversion job.
    
    Orchestrates the complete conversion pipeline from raw data to
    Seabed 2030-compliant outputs.
    """
    
    def __init__(
        self,
        input_path: str,
        sensor_type: str,
        output_format: str = "netcdf",
        anonymize: bool = True,
        add_overlay: bool = False,
        qc_mode: str = "auto",
        output_dir: Optional[str] = None
    ):
        """
        Initialize conversion job.
        
        Args:
            input_path: Path to input data file
            sensor_type: Type of sensor (mbes, sbes, lidar, singlebeam, auv)
            output_format: Output format (netcdf, bag, geotiff)
            anonymize: Whether to anonymize vessel data
            add_overlay: Whether to add environmental overlays
            qc_mode: QC mode (auto, manual, skip)
            output_dir: Output directory (defaults to ./out)
        """
        self.input_path = Path(input_path)
        self.sensor_type = sensor_type.lower()
        self.output_format = output_format.lower()
        self.anonymize = anonymize
        self.add_overlay = add_overlay
        self.qc_mode = qc_mode.lower()
        self.output_dir = Path(output_dir) if output_dir else Path("./out")
        
        # Validate inputs
        self._validate_inputs()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "Conversion job initialized",
            input_path=str(self.input_path),
            sensor_type=self.sensor_type,
            output_format=self.output_format,
            anonymize=self.anonymize,
            add_overlay=self.add_overlay,
            qc_mode=self.qc_mode
        )
    
    def _validate_inputs(self):
        """Validate input parameters."""
        # Check input file exists
        if not self.input_path.exists():
            raise ConversionError(f"Input file not found: {self.input_path}")
        
        # Validate sensor type
        valid_sensors = ["mbes", "sbes", "lidar", "singlebeam", "auv"]
        if self.sensor_type not in valid_sensors:
            raise ConversionError(
                f"Invalid sensor type: {self.sensor_type}. "
                f"Must be one of: {valid_sensors}"
            )
        
        # Validate output format
        valid_formats = ["netcdf", "bag", "geotiff"]
        if self.output_format not in valid_formats:
            raise ConversionError(
                f"Invalid output format: {self.output_format}. "
                f"Must be one of: {valid_formats}"
            )
        
        # Validate QC mode
        valid_qc_modes = ["auto", "manual", "skip"]
        if self.qc_mode not in valid_qc_modes:
            raise ConversionError(
                f"Invalid QC mode: {self.qc_mode}. "
                f"Must be one of: {valid_qc_modes}"
            )
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the complete conversion pipeline.
        
        Returns:
            Dictionary containing conversion results and metadata
        """
        try:
            logger.info("Starting conversion pipeline")
            
            # Step 1: Parse raw data
            logger.info("Parsing raw data", sensor_type=self.sensor_type)
            raw_data = self._parse_raw_data()
            
            # Step 2: Apply quality control
            if self.qc_mode != "skip":
                logger.info("Applying quality control", mode=self.qc_mode)
                qc_results = self._apply_quality_control(raw_data)
            else:
                qc_results = {"status": "skipped", "anomalies": []}
            
            # Step 3: Anonymize data
            if self.anonymize:
                logger.info("Anonymizing data")
                raw_data = anonymize_data(raw_data, self.sensor_type)
            
            # Step 4: Reproject to WGS84
            logger.info("Reprojecting to WGS84")
            projected_data = reproject_to_wgs84(raw_data)
            
            # Step 5: Create bathymetric surface
            logger.info("Creating bathymetric surface")
            surface_data = create_bathymetric_surface(projected_data)
            
            # Step 6: Apply environmental overlays
            if self.add_overlay:
                logger.info("Applying environmental overlays")
                surface_data = apply_overlay(surface_data, "deepseaguard")
            
            # Step 7: Export to target format
            logger.info("Exporting to target format", format=self.output_format)
            output_files = self._export_data(surface_data)
            
            # Compile results
            result = {
                "status": "completed",
                "input_file": str(self.input_path),
                "sensor_type": self.sensor_type,
                "output_format": self.output_format,
                "output_files": output_files,
                "qc_results": qc_results,
                "anonymized": self.anonymize,
                "overlay_applied": self.add_overlay,
                "processing_time_seconds": 0,  # TODO: Calculate actual time
                "data_points_processed": len(raw_data.get("points", [])),
                "metadata": self._generate_metadata(raw_data, qc_results)
            }
            
            logger.info("Conversion completed successfully", result=result)
            return result
            
        except Exception as e:
            logger.error("Conversion failed", error=str(e))
            raise ConversionError(f"Conversion failed: {str(e)}")
    
    def _parse_raw_data(self) -> Dict[str, Any]:
        """Parse raw data based on sensor type."""
        try:
            if self.sensor_type == "mbes":
                return parse_mbes_file(self.input_path)
            elif self.sensor_type == "sbes":
                return parse_sbet_file(self.input_path)
            elif self.sensor_type == "lidar":
                return parse_lidar_file(self.input_path)
            elif self.sensor_type == "singlebeam":
                return parse_sbet_file(self.input_path)  # Reuse SBET parser
            elif self.sensor_type == "auv":
                return parse_sbet_file(self.input_path)  # Reuse SBET parser
            else:
                raise ConversionError(f"Unsupported sensor type: {self.sensor_type}")
                
        except Exception as e:
            raise ConversionError(f"Failed to parse {self.sensor_type} data: {str(e)}")
    
    def _apply_quality_control(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply quality control rules and ML anomaly detection."""
        try:
            # Apply deterministic QC rules
            qc_rules_result = apply_qc_rules(data, self.sensor_type)
            
            # Apply ML anomaly detection if in auto mode
            ml_result = {"anomalies": [], "confidence": 0.0}
            if self.qc_mode == "auto":
                ml_result = predict_anomalies(data)
            
            # Combine results
            qc_results = {
                "status": "completed",
                "rules_applied": qc_rules_result,
                "ml_anomalies": ml_result,
                "total_anomalies": len(qc_rules_result.get("anomalies", [])) + len(ml_result.get("anomalies", [])),
                "quality_score": self._calculate_quality_score(qc_rules_result, ml_result)
            }
            
            return qc_results
            
        except Exception as e:
            logger.warning("QC processing failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "anomalies": [],
                "quality_score": 0.0
            }
    
    def _calculate_quality_score(self, rules_result: Dict, ml_result: Dict) -> float:
        """Calculate overall quality score from QC results."""
        # Simple quality scoring (0-1 scale)
        total_points = rules_result.get("total_points", 1)
        anomaly_count = len(rules_result.get("anomalies", [])) + len(ml_result.get("anomalies", []))
        
        if total_points == 0:
            return 0.0
        
        quality_ratio = 1.0 - (anomaly_count / total_points)
        return max(0.0, min(1.0, quality_ratio))
    
    def _export_data(self, data: Dict[str, Any]) -> List[str]:
        """Export processed data to target format."""
        try:
            if self.output_format == "netcdf":
                return export_to_netcdf(data, self.output_dir, self.sensor_type)
            elif self.output_format == "bag":
                return export_to_bag(data, self.output_dir, self.sensor_type)
            elif self.output_format == "geotiff":
                return export_to_geotiff(data, self.output_dir, self.sensor_type)
            else:
                raise ConversionError(f"Unsupported output format: {self.output_format}")
                
        except Exception as e:
            raise ConversionError(f"Export failed: {str(e)}")
    
    def _generate_metadata(self, raw_data: Dict, qc_results: Dict) -> Dict[str, Any]:
        """Generate metadata for the conversion."""
        return {
            "conversion_timestamp": "2024-01-01T00:00:00Z",  # TODO: Use actual timestamp
            "software_version": "1.0.0",
            "input_file_size_bytes": self.input_path.stat().st_size,
            "coordinate_system": "WGS84",
            "data_extent": self._calculate_extent(raw_data),
            "quality_metrics": {
                "quality_score": qc_results.get("quality_score", 0.0),
                "anomaly_count": qc_results.get("total_anomalies", 0),
                "qc_status": qc_results.get("status", "unknown")
            }
        }
    
    def _calculate_extent(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate spatial extent of the data."""
        points = data.get("points", [])
        if not points:
            return {"min_lat": 0, "max_lat": 0, "min_lon": 0, "max_lon": 0, "min_depth": 0, "max_depth": 0}
        
        lats = [p.get("latitude", 0) for p in points]
        lons = [p.get("longitude", 0) for p in points]
        depths = [p.get("depth", 0) for p in points]
        
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
            "min_depth": min(depths),
            "max_depth": max(depths)
        }
