"""
Multi-Beam Echo Sounder (MBES) data parser.

Parses MBES data files and returns standardized data structure.
Supports common MBES formats including Kongsberg, Reson, and generic CSV formats.

Expected input fields:
- timestamp: ISO 8601 format or Unix timestamp
- latitude: decimal degrees (WGS84)
- longitude: decimal degrees (WGS84)
- depth: meters (positive down)
- beam_angle: degrees from nadir (-90 to +90)
- quality: signal quality indicator (0-100)
- intensity: backscatter intensity (dB)
- backscatter: backscatter strength (dB)

Usage:
    data = parse_mbes_file("mbes_data.csv")
    print(f"Parsed {len(data['points'])} MBES points")
"""

import logging
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


def parse_mbes_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse MBES data file and return standardized structure.
    
    Args:
        file_path: Path to MBES data file
        
    Returns:
        Dictionary containing parsed MBES data with metadata
        
    Raises:
        ValueError: If file format is invalid or required fields are missing
        FileNotFoundError: If file doesn't exist
    """
    try:
        logger.info("Parsing MBES file", file_path=str(file_path))
        
        # Read file based on extension
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() == '.txt':
            df = pd.read_csv(file_path, sep='\t')
        else:
            # Try CSV as default
            df = pd.read_csv(file_path)
        
        # Validate required columns
        required_columns = ['timestamp', 'latitude', 'longitude', 'depth']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Standardize column names (case-insensitive)
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['time', 'datetime', 'utc']:
                column_mapping[col] = 'timestamp'
            elif col_lower in ['lat', 'y']:
                column_mapping[col] = 'latitude'
            elif col_lower in ['lon', 'lng', 'x']:
                column_mapping[col] = 'longitude'
            elif col_lower in ['z', 'elevation']:
                column_mapping[col] = 'depth'
            elif col_lower in ['beam', 'angle']:
                column_mapping[col] = 'beam_angle'
            elif col_lower in ['qual', 'quality_factor']:
                column_mapping[col] = 'quality'
            elif col_lower in ['intensity', 'backscatter']:
                column_mapping[col] = 'intensity'
        
        df = df.rename(columns=column_mapping)
        
        # Convert timestamp to ISO format if needed
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.isoformat()
        
        # Validate data ranges
        _validate_mbes_data(df)
        
        # Convert to list of dictionaries
        points = df.to_dict('records')
        
        # Generate metadata
        metadata = _generate_mbes_metadata(df, file_path)
        
        result = {
            "sensor_type": "mbes",
            "points": points,
            "metadata": metadata,
            "total_points": len(points),
            "file_info": {
                "filename": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "columns": list(df.columns)
            }
        }
        
        logger.info("MBES file parsed successfully", 
                   total_points=len(points),
                   columns=list(df.columns))
        
        return result
        
    except Exception as e:
        logger.error("Failed to parse MBES file", file_path=str(file_path), error=str(e))
        raise


def _validate_mbes_data(df: pd.DataFrame) -> None:
    """Validate MBES data ranges and quality."""
    # Check coordinate ranges
    if 'latitude' in df.columns:
        invalid_lat = df[(df['latitude'] < -90) | (df['latitude'] > 90)]
        if len(invalid_lat) > 0:
            logger.warning(f"Found {len(invalid_lat)} invalid latitude values")
    
    if 'longitude' in df.columns:
        invalid_lon = df[(df['longitude'] < -180) | (df['longitude'] > 180)]
        if len(invalid_lon) > 0:
            logger.warning(f"Found {len(invalid_lon)} invalid longitude values")
    
    # Check depth ranges (reasonable ocean depths)
    if 'depth' in df.columns:
        invalid_depth = df[(df['depth'] < 0) | (df['depth'] > 12000)]
        if len(invalid_depth) > 0:
            logger.warning(f"Found {len(invalid_depth)} invalid depth values")
    
    # Check beam angle ranges
    if 'beam_angle' in df.columns:
        invalid_angle = df[(df['beam_angle'] < -90) | (df['beam_angle'] > 90)]
        if len(invalid_angle) > 0:
            logger.warning(f"Found {len(invalid_angle)} invalid beam angle values")


def _generate_mbes_metadata(df: pd.DataFrame, file_path: Path) -> Dict[str, Any]:
    """Generate metadata for MBES data."""
    metadata = {
        "parser_version": "1.0.0",
        "sensor_type": "mbes",
        "data_quality": "unknown",
        "coordinate_system": "WGS84",
        "units": {
            "latitude": "decimal_degrees",
            "longitude": "decimal_degrees", 
            "depth": "meters",
            "beam_angle": "degrees"
        }
    }
    
    # Add statistical information
    if len(df) > 0:
        metadata["statistics"] = {
            "total_points": len(df),
            "latitude_range": [df['latitude'].min(), df['latitude'].max()] if 'latitude' in df.columns else None,
            "longitude_range": [df['longitude'].min(), df['longitude'].max()] if 'longitude' in df.columns else None,
            "depth_range": [df['depth'].min(), df['depth'].max()] if 'depth' in df.columns else None,
            "beam_angle_range": [df['beam_angle'].min(), df['beam_angle'].max()] if 'beam_angle' in df.columns else None
        }
        
        # Add quality metrics
        if 'quality' in df.columns:
            metadata["quality_metrics"] = {
                "mean_quality": float(df['quality'].mean()),
                "min_quality": float(df['quality'].min()),
                "max_quality": float(df['quality'].max()),
                "quality_std": float(df['quality'].std())
            }
    
    return metadata


def validate_mbes_format(file_path: Path) -> bool:
    """
    Validate if file is in valid MBES format.
    
    Args:
        file_path: Path to file to validate
        
    Returns:
        True if file appears to be valid MBES format
    """
    try:
        # Quick validation by reading first few rows
        df = pd.read_csv(file_path, nrows=5)
        
        # Check for required columns (case-insensitive)
        required_columns = ['timestamp', 'latitude', 'longitude', 'depth']
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        # Check if we have at least some of the required columns
        found_columns = sum(1 for req in required_columns if req in df_columns_lower)
        
        return found_columns >= 3  # At least 3 out of 4 required columns
        
    except Exception:
        return False
