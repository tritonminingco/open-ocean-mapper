"""
Open Ocean Mapper - Convert raw ocean mapping data to Seabed 2030-compliant outputs.

This package provides tools for converting various ocean mapping data formats
(MBES, SBES, LiDAR, single-beam, AUV telemetry) into standardized outputs
(NetCDF, BAG, GeoTIFF) with anonymization, quality control, and environmental
overlay capabilities.
"""

__version__ = "1.0.0"
__author__ = "Triton Mining Co."
__email__ = "info@tritonmining.com"
__license__ = "Apache-2.0"

from .pipeline.converter import ConvertJob, ConversionError
from .qc.model_stub import load_model, predict_anomalies
from .adapters.seabed2030_adapter import Seabed2030Adapter

__all__ = [
    "ConvertJob",
    "ConversionError", 
    "load_model",
    "predict_anomalies",
    "Seabed2030Adapter",
]
