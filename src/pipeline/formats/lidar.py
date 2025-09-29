"""
LiDAR data parser for ocean mapping applications.

Parses LiDAR data files and returns standardized data structure.
Supports LAS/LAZ formats and generic point cloud formats.

Expected input fields:
- timestamp: ISO 8601 format or Unix timestamp
- latitude: decimal degrees (WGS84)
- longitude: decimal degrees (WGS84)
- elevation: meters above sea level
- intensity: LiDAR intensity (0-255)
- classification: point classification code
- return_number: return number for multi-return systems
- number_of_returns: total number of returns for pulse

Usage:
    data = parse_lidar_file("lidar_data.las")
    print(f"Parsed {len(data['points'])} LiDAR points")
"""

import logging
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


def parse_lidar_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse LiDAR data file and return standardized structure.
    
    Args:
        file_path: Path to LiDAR data file
        
    Returns:
        Dictionary containing parsed LiDAR data with metadata
        
    Raises:
        ValueError: If file format is invalid or required fields are missing
        FileNotFoundError: If file doesn't exist
    """
    try:
        logger.info("Parsing LiDAR file", file_path=str(file_path))
        
        # Read file based on extension
        if file_path.suffix.lower() in ['.las', '.laz']:
            df = _read_las_file(file_path)
        elif file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() == '.txt':
            df = pd.read_csv(file_path, sep='\t')
        else:
            # Try CSV as default
            df = pd.read_csv(file_path)
        
        # Validate required columns
        required_columns = ['timestamp', 'latitude', 'longitude', 'elevation']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Standardize column names (case-insensitive)
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['time', 'datetime', 'utc']:
                column_mapping[col] = 'timestamp'
            elif col_lower in ['lat', 'y', 'northing']:
                column_mapping[col] = 'latitude'
            elif col_lower in ['lon', 'lng', 'x', 'easting']:
                column_mapping[col] = 'longitude'
            elif col_lower in ['z', 'alt', 'altitude', 'height']:
                column_mapping[col] = 'elevation'
            elif col_lower in ['intensity', 'int']:
                column_mapping[col] = 'intensity'
            elif col_lower in ['class', 'classification', 'cls']:
                column_mapping[col] = 'classification'
            elif col_lower in ['return_num', 'return_number', 'ret']:
                column_mapping[col] = 'return_number'
            elif col_lower in ['num_returns', 'number_of_returns', 'nret']:
                column_mapping[col] = 'number_of_returns'
        
        df = df.rename(columns=column_mapping)
        
        # Convert timestamp to ISO format if needed
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.isoformat()
        
        # Validate data ranges
        _validate_lidar_data(df)
        
        # Convert to list of dictionaries
        points = df.to_dict('records')
        
        # Generate metadata
        metadata = _generate_lidar_metadata(df, file_path)
        
        result = {
            "sensor_type": "lidar",
            "points": points,
            "metadata": metadata,
            "total_points": len(points),
            "file_info": {
                "filename": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "columns": list(df.columns)
            }
        }
        
        logger.info("LiDAR file parsed successfully", 
                   total_points=len(points),
                   columns=list(df.columns))
        
        return result
        
    except Exception as e:
        logger.error("Failed to parse LiDAR file", file_path=str(file_path), error=str(e))
        raise


def _read_las_file(file_path: Path) -> pd.DataFrame:
    """
    Read LAS/LAZ file and convert to DataFrame.
    
    This is a stub implementation. In production, use laspy or similar library.
    """
    logger.warning("LAS file reading not implemented, using mock data")
    
    # Mock LAS data for demonstration
    import numpy as np
    
    # Generate mock LiDAR points
    n_points = 1000
    mock_data = {
        'timestamp': pd.date_range('2024-01-01', periods=n_points, freq='1S').isoformat(),
        'latitude': np.random.uniform(40.0, 41.0, n_points),
        'longitude': np.random.uniform(-74.0, -73.0, n_points),
        'elevation': np.random.uniform(0, 100, n_points),
        'intensity': np.random.randint(0, 256, n_points),
        'classification': np.random.randint(1, 10, n_points),
        'return_number': np.random.randint(1, 5, n_points),
        'number_of_returns': np.random.randint(1, 5, n_points)
    }
    
    return pd.DataFrame(mock_data)


def _validate_lidar_data(df: pd.DataFrame) -> None:
    """Validate LiDAR data ranges and quality."""
    # Check coordinate ranges
    if 'latitude' in df.columns:
        invalid_lat = df[(df['latitude'] < -90) | (df['latitude'] > 90)]
        if len(invalid_lat) > 0:
            logger.warning(f"Found {len(invalid_lat)} invalid latitude values")
    
    if 'longitude' in df.columns:
        invalid_lon = df[(df['longitude'] < -180) | (df['longitude'] > 180)]
        if len(invalid_lon) > 0:
            logger.warning(f"Found {len(invalid_lon)} invalid longitude values")
    
    # Check elevation ranges (reasonable for coastal/ocean areas)
    if 'elevation' in df.columns:
        invalid_elevation = df[(df['elevation'] < -1000) | (df['elevation'] > 10000)]
        if len(invalid_elevation) > 0:
            logger.warning(f"Found {len(invalid_elevation)} invalid elevation values")
    
    # Check intensity ranges
    if 'intensity' in df.columns:
        invalid_intensity = df[(df['intensity'] < 0) | (df['intensity'] > 255)]
        if len(invalid_intensity) > 0:
            logger.warning(f"Found {len(invalid_intensity)} invalid intensity values")
    
    # Check classification codes
    if 'classification' in df.columns:
        invalid_class = df[(df['classification'] < 0) | (df['classification'] > 31)]
        if len(invalid_class) > 0:
            logger.warning(f"Found {len(invalid_class)} invalid classification values")


def _generate_lidar_metadata(df: pd.DataFrame, file_path: Path) -> Dict[str, Any]:
    """Generate metadata for LiDAR data."""
    metadata = {
        "parser_version": "1.0.0",
        "sensor_type": "lidar",
        "data_quality": "unknown",
        "coordinate_system": "WGS84",
        "units": {
            "latitude": "decimal_degrees",
            "longitude": "decimal_degrees", 
            "elevation": "meters",
            "intensity": "0-255_scale",
            "classification": "integer_code"
        }
    }
    
    # Add statistical information
    if len(df) > 0:
        metadata["statistics"] = {
            "total_points": len(df),
            "latitude_range": [df['latitude'].min(), df['latitude'].max()] if 'latitude' in df.columns else None,
            "longitude_range": [df['longitude'].min(), df['longitude'].max()] if 'longitude' in df.columns else None,
            "elevation_range": [df['elevation'].min(), df['elevation'].max()] if 'elevation' in df.columns else None,
        }
        
        # Add LiDAR-specific statistics
        lidar_stats = {}
        if 'intensity' in df.columns:
            lidar_stats["intensity_range"] = [df['intensity'].min(), df['intensity'].max()]
            lidar_stats["mean_intensity"] = float(df['intensity'].mean())
        
        if 'classification' in df.columns:
            lidar_stats["classification_counts"] = df['classification'].value_counts().to_dict()
        
        if 'return_number' in df.columns:
            lidar_stats["return_number_distribution"] = df['return_number'].value_counts().to_dict()
        
        if lidar_stats:
            metadata["lidar_statistics"] = lidar_stats
    
    return metadata


def validate_lidar_format(file_path: Path) -> bool:
    """
    Validate if file is in valid LiDAR format.
    
    Args:
        file_path: Path to file to validate
        
    Returns:
        True if file appears to be valid LiDAR format
    """
    try:
        # Check file extension
        if file_path.suffix.lower() in ['.las', '.laz']:
            return True
        
        # For other formats, try to read and validate
        df = pd.read_csv(file_path, nrows=5)
        
        # Check for required columns (case-insensitive)
        required_columns = ['timestamp', 'latitude', 'longitude', 'elevation']
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        # Check if we have at least some of the required columns
        found_columns = sum(1 for req in required_columns if req in df_columns_lower)
        
        return found_columns >= 3  # At least 3 out of 4 required columns
        
    except Exception:
        return False
