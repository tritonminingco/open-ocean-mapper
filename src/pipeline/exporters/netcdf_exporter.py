"""
NetCDF exporter for Seabed 2030 compliance.

Exports ocean mapping data to NetCDF format following Seabed 2030 standards.
Uses xarray and netCDF4 for robust data handling and metadata management.

NetCDF metadata template includes:
- Global attributes for Seabed 2030 compliance
- Variable attributes with CF conventions
- Coordinate system information
- Quality control metadata
- Processing history

Usage:
    output_files = export_to_netcdf(data, output_dir, "mbes")
    print(f"Exported to: {output_files}")
"""

import logging
import os
from typing import Dict, Any, List
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


def export_to_netcdf(data: Dict[str, Any], output_dir: Path, sensor_type: str) -> List[str]:
    """
    Export ocean mapping data to NetCDF format.
    
    Args:
        data: Processed ocean mapping data
        output_dir: Output directory
        sensor_type: Type of sensor (mbes, sbes, lidar, etc.)
        
    Returns:
        List of exported file paths
        
    Raises:
        ValueError: If data format is invalid
        IOError: If file writing fails
    """
    try:
        logger.info("Exporting to NetCDF format", sensor_type=sensor_type)
        
        # Extract points data
        points = data.get("points", [])
        if not points:
            raise ValueError("No points data to export")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(points)
        
        # Create xarray Dataset
        ds = _create_xarray_dataset(df, data, sensor_type)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sensor_type}_bathymetry_{timestamp}.nc"
        output_path = output_dir / filename
        
        # Write to NetCDF
        ds.to_netcdf(output_path, format='NETCDF4')
        
        logger.info("NetCDF export completed", output_path=str(output_path))
        
        return [str(output_path)]
        
    except Exception as e:
        logger.error("NetCDF export failed", error=str(e))
        raise


def _create_xarray_dataset(df: pd.DataFrame, data: Dict[str, Any], sensor_type: str) -> xr.Dataset:
    """Create xarray Dataset from processed data."""
    
    # Create coordinate arrays
    lats = df['latitude'].values
    lons = df['longitude'].values
    
    # Create depth/elevation array
    if sensor_type == "lidar":
        depth_var = df['elevation'].values
        depth_name = "elevation"
        depth_long_name = "Elevation above sea level"
        depth_units = "m"
    else:
        depth_var = df['depth'].values
        depth_name = "depth"
        depth_long_name = "Depth below sea level"
        depth_units = "m"
    
    # Create time array
    times = pd.to_datetime(df['timestamp']).values
    
    # Create data variables
    data_vars = {
        depth_name: (
            ['time'],
            depth_var,
            {
                'long_name': depth_long_name,
                'units': depth_units,
                'standard_name': 'sea_floor_depth_below_sea_level' if sensor_type != "lidar" else 'surface_altitude',
                'positive': 'down' if sensor_type != "lidar" else 'up',
                'valid_min': float(np.nanmin(depth_var)),
                'valid_max': float(np.nanmax(depth_var)),
                'coordinates': 'latitude longitude'
            }
        )
    }
    
    # Add sensor-specific variables
    if 'quality' in df.columns:
        data_vars['quality'] = (
            ['time'],
            df['quality'].values,
            {
                'long_name': 'Signal quality indicator',
                'units': '1',
                'valid_min': 0,
                'valid_max': 100,
                'coordinates': 'latitude longitude'
            }
        )
    
    if 'beam_angle' in df.columns:
        data_vars['beam_angle'] = (
            ['time'],
            df['beam_angle'].values,
            {
                'long_name': 'Beam angle from nadir',
                'units': 'degrees',
                'valid_min': -90,
                'valid_max': 90,
                'coordinates': 'latitude longitude'
            }
        )
    
    if 'intensity' in df.columns:
        data_vars['intensity'] = (
            ['time'],
            df['intensity'].values,
            {
                'long_name': 'Backscatter intensity',
                'units': 'dB',
                'coordinates': 'latitude longitude'
            }
        )
    
    # Create coordinate variables
    coords = {
        'time': (
            ['time'],
            times,
            {
                'long_name': 'Time',
                'standard_name': 'time',
                'axis': 'T'
            }
        ),
        'latitude': (
            ['time'],
            lats,
            {
                'long_name': 'Latitude',
                'standard_name': 'latitude',
                'units': 'degrees_north',
                'axis': 'Y',
                'valid_min': -90.0,
                'valid_max': 90.0
            }
        ),
        'longitude': (
            ['time'],
            lons,
            {
                'long_name': 'Longitude',
                'standard_name': 'longitude',
                'units': 'degrees_east',
                'axis': 'X',
                'valid_min': -180.0,
                'valid_max': 180.0
            }
        )
    }
    
    # Create Dataset
    ds = xr.Dataset(data_vars, coords=coords)
    
    # Add global attributes
    ds.attrs.update(_get_global_attributes(data, sensor_type))
    
    return ds


def _get_global_attributes(data: Dict[str, Any], sensor_type: str) -> Dict[str, str]:
    """Generate global attributes for Seabed 2030 compliance."""
    
    metadata = data.get("metadata", {})
    
    attrs = {
        # CF Convention attributes
        'Conventions': 'CF-1.8',
        'title': f'Ocean Mapping Data - {sensor_type.upper()}',
        'summary': f'Processed ocean mapping data from {sensor_type.upper()} sensor',
        'source': 'Open Ocean Mapper v1.0.0',
        'institution': 'Triton Mining Co.',
        'references': 'https://github.com/tritonmining/open-ocean-mapper',
        
        # Seabed 2030 specific attributes
        'seabed2030_compliant': 'true',
        'seabed2030_version': '1.0',
        'seabed2030_contributor': 'Triton Mining Co.',
        'seabed2030_data_type': sensor_type.upper(),
        
        # Processing information
        'processing_software': 'Open Ocean Mapper',
        'processing_version': '1.0.0',
        'processing_date': datetime.now().isoformat(),
        'processing_level': 'L2',
        
        # Data quality
        'quality_control_applied': 'true',
        'anonymization_applied': str(data.get("anonymized", False)),
        'environmental_overlay': str(data.get("overlay_applied", False)),
        
        # Geographic information
        'geospatial_lat_min': str(metadata.get("statistics", {}).get("latitude_range", [0, 0])[0]),
        'geospatial_lat_max': str(metadata.get("statistics", {}).get("latitude_range", [0, 0])[1]),
        'geospatial_lon_min': str(metadata.get("statistics", {}).get("longitude_range", [0, 0])[0]),
        'geospatial_lon_max': str(metadata.get("statistics", {}).get("longitude_range", [0, 0])[1]),
        'geospatial_vertical_min': str(metadata.get("statistics", {}).get("depth_range", [0, 0])[0]),
        'geospatial_vertical_max': str(metadata.get("statistics", {}).get("depth_range", [0, 0])[1]),
        
        # Coordinate system
        'crs': 'EPSG:4326',
        'crs_wkt': 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]',
        
        # Data statistics
        'total_points': str(len(data.get("points", []))),
        'data_points_processed': str(data.get("data_points_processed", 0)),
        
        # License and usage
        'license': 'Apache-2.0',
        'usage_restrictions': 'None',
        'data_availability': 'Public',
        
        # Contact information
        'contact': 'info@tritonmining.com',
        'contact_email': 'info@tritonmining.com',
        'contact_organization': 'Triton Mining Co.',
        
        # History
        'history': f'Created by Open Ocean Mapper v1.0.0 on {datetime.now().isoformat()}'
    }
    
    return attrs


def validate_netcdf_file(file_path: Path) -> bool:
    """
    Validate NetCDF file for Seabed 2030 compliance.
    
    Args:
        file_path: Path to NetCDF file
        
    Returns:
        True if file is valid and compliant
    """
    try:
        # Open NetCDF file
        ds = xr.open_dataset(file_path)
        
        # Check required global attributes
        required_attrs = [
            'Conventions', 'title', 'source', 'seabed2030_compliant',
            'geospatial_lat_min', 'geospatial_lat_max',
            'geospatial_lon_min', 'geospatial_lon_max'
        ]
        
        missing_attrs = [attr for attr in required_attrs if attr not in ds.attrs]
        if missing_attrs:
            logger.warning(f"Missing required attributes: {missing_attrs}")
            return False
        
        # Check required variables
        required_vars = ['latitude', 'longitude', 'time']
        missing_vars = [var for var in required_vars if var not in ds.variables]
        if missing_vars:
            logger.warning(f"Missing required variables: {missing_vars}")
            return False
        
        # Check for depth/elevation variable
        depth_vars = ['depth', 'elevation']
        has_depth = any(var in ds.variables for var in depth_vars)
        if not has_depth:
            logger.warning("No depth or elevation variable found")
            return False
        
        ds.close()
        return True
        
    except Exception as e:
        logger.error("NetCDF validation failed", error=str(e))
        return False
