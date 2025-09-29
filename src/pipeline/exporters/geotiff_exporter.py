"""
GeoTIFF exporter for bathymetric raster data.

Exports ocean mapping data to GeoTIFF format using rasterio.
Creates raster grids with proper georeferencing and metadata.

GeoTIFF features:
- Georeferenced raster data
- Multiple bands (elevation, uncertainty, density)
- Proper coordinate system information
- Compression and optimization options

Usage:
    output_files = export_to_geotiff(data, output_dir, "mbes")
    print(f"Exported to: {output_files}")
"""

import logging
import os
from typing import Dict, Any, List
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


def export_to_geotiff(data: Dict[str, Any], output_dir: Path, sensor_type: str) -> List[str]:
    """
    Export ocean mapping data to GeoTIFF format.
    
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
        logger.info("Exporting to GeoTIFF format", sensor_type=sensor_type)
        
        # Extract points data
        points = data.get("points", [])
        if not points:
            raise ValueError("No points data to export")
        
        # Convert to DataFrame
        df = pd.DataFrame(points)
        
        # Create raster grid
        raster_data = _create_raster_grid(df, data, sensor_type)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sensor_type}_bathymetry_{timestamp}.tif"
        output_path = output_dir / filename
        
        # Write GeoTIFF file
        _write_geotiff_file(raster_data, output_path, sensor_type)
        
        logger.info("GeoTIFF export completed", output_path=str(output_path))
        
        return [str(output_path)]
        
    except Exception as e:
        logger.error("GeoTIFF export failed", error=str(e))
        raise


def _create_raster_grid(df: pd.DataFrame, data: Dict[str, Any], sensor_type: str) -> Dict[str, Any]:
    """Create raster grid structure from point data."""
    
    # Get coordinate bounds
    min_lat, max_lat = df['latitude'].min(), df['latitude'].max()
    min_lon, max_lon = df['longitude'].min(), df['longitude'].max()
    
    # Define grid resolution (degrees)
    resolution = 0.001  # ~100m at equator
    
    # Create grid coordinates
    lon_grid = np.arange(min_lon, max_lon + resolution, resolution)
    lat_grid = np.arange(min_lat, max_lat + resolution, resolution)
    
    # Create meshgrid
    lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
    
    # Initialize grids
    elevation_grid = np.full_like(lon_mesh, np.nan)
    uncertainty_grid = np.full_like(lon_mesh, np.nan)
    density_grid = np.zeros_like(lon_mesh)
    
    # Grid the data points
    for _, point in df.iterrows():
        lat_idx = int((point['latitude'] - min_lat) / resolution)
        lon_idx = int((point['longitude'] - min_lon) / resolution)
        
        if 0 <= lat_idx < elevation_grid.shape[0] and 0 <= lon_idx < elevation_grid.shape[1]:
            # Use depth or elevation based on sensor type
            if sensor_type == "lidar":
                depth_value = point.get('elevation', np.nan)
            else:
                depth_value = point.get('depth', np.nan)
            
            # Simple gridding (in production, use proper interpolation)
            if np.isnan(elevation_grid[lat_idx, lon_idx]):
                elevation_grid[lat_idx, lon_idx] = depth_value
                uncertainty_grid[lat_idx, lon_idx] = 1.0  # Default uncertainty
            else:
                # Average multiple points in same grid cell
                elevation_grid[lat_idx, lon_idx] = (elevation_grid[lat_idx, lon_idx] + depth_value) / 2
            
            density_grid[lat_idx, lon_idx] += 1
    
    # Create raster structure
    raster_data = {
        'elevation': elevation_grid,
        'uncertainty': uncertainty_grid,
        'density': density_grid,
        'bounds': (min_lon, min_lat, max_lon, max_lat),
        'resolution': resolution,
        'shape': elevation_grid.shape,
        'metadata': _get_geotiff_metadata(data, sensor_type)
    }
    
    return raster_data


def _write_geotiff_file(raster_data: Dict[str, Any], output_path: Path, sensor_type: str) -> None:
    """Write GeoTIFF file using rasterio."""
    
    # Get raster data
    elevation = raster_data['elevation']
    uncertainty = raster_data['uncertainty']
    density = raster_data['density']
    bounds = raster_data['bounds']
    shape = raster_data['shape']
    
    # Create transform
    transform = from_bounds(*bounds, shape[1], shape[0])
    
    # Define CRS (WGS84)
    crs = CRS.from_epsg(4326)
    
    # Prepare metadata
    metadata = raster_data['metadata']
    
    # Write GeoTIFF with multiple bands
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=shape[0],
        width=shape[1],
        count=3,  # elevation, uncertainty, density
        dtype=rasterio.float32,
        crs=crs,
        transform=transform,
        compress='lzw',
        nodata=np.nan,
        **metadata
    ) as dst:
        # Write elevation band
        dst.write(elevation.astype(np.float32), 1)
        dst.set_band_description(1, 'Elevation')
        
        # Write uncertainty band
        dst.write(uncertainty.astype(np.float32), 2)
        dst.set_band_description(2, 'Uncertainty')
        
        # Write density band
        dst.write(density.astype(np.float32), 3)
        dst.set_band_description(3, 'Point Density')


def _get_geotiff_metadata(data: Dict[str, Any], sensor_type: str) -> Dict[str, Any]:
    """Generate GeoTIFF metadata."""
    
    metadata = data.get("metadata", {})
    
    geotiff_metadata = {
        'TIFFTAG_SOFTWARE': 'Open Ocean Mapper v1.0.0',
        'TIFFTAG_DATETIME': datetime.now().isoformat(),
        'TIFFTAG_ARTIST': 'Triton Mining Co.',
        'TIFFTAG_COPYRIGHT': 'Apache-2.0 License',
        
        # GDAL metadata
        'GDAL_DATATYPE': 'Float32',
        'GDAL_NODATA': 'nan',
        
        # Custom metadata
        'SENSOR_TYPE': sensor_type.upper(),
        'DATA_SOURCE': 'Ocean Mapping',
        'COORDINATE_SYSTEM': 'WGS84',
        'VERTICAL_DATUM': 'Mean Sea Level',
        'HORIZONTAL_DATUM': 'WGS84',
        
        # Processing information
        'PROCESSING_SOFTWARE': 'Open Ocean Mapper',
        'PROCESSING_VERSION': '1.0.0',
        'PROCESSING_DATE': datetime.now().isoformat(),
        'QUALITY_CONTROL': 'Applied',
        'ANONYMIZATION': str(data.get("anonymized", False)),
        'ENVIRONMENTAL_OVERLAY': str(data.get("overlay_applied", False)),
        
        # Data statistics
        'TOTAL_POINTS': str(len(data.get("points", []))),
        'GRID_RESOLUTION': str(data.get("metadata", {}).get("statistics", {}).get("total_points", 0)),
        
        # Quality metrics
        'QUALITY_SCORE': str(data.get("qc_results", {}).get("quality_score", 0.0)),
        'ANOMALY_COUNT': str(data.get("qc_results", {}).get("total_anomalies", 0)),
        
        # Band descriptions
        'BAND_1_DESCRIPTION': 'Elevation/Depth',
        'BAND_1_UNITS': 'meters',
        'BAND_2_DESCRIPTION': 'Uncertainty',
        'BAND_2_UNITS': 'meters',
        'BAND_3_DESCRIPTION': 'Point Density',
        'BAND_3_UNITS': 'points_per_cell'
    }
    
    return geotiff_metadata


def validate_geotiff_file(file_path: Path) -> bool:
    """
    Validate GeoTIFF file format.
    
    Args:
        file_path: Path to GeoTIFF file
        
    Returns:
        True if file is valid GeoTIFF format
    """
    try:
        # Check file extension
        if file_path.suffix.lower() not in ['.tif', '.tiff']:
            return False
        
        # Try to open with rasterio
        with rasterio.open(file_path) as src:
            # Check basic properties
            if src.count < 1:
                return False
            
            # Check CRS
            if src.crs is None:
                logger.warning("No CRS information found")
            
            # Check transform
            if src.transform is None:
                logger.warning("No geotransform found")
            
            return True
        
    except Exception as e:
        logger.error("GeoTIFF validation failed", error=str(e))
        return False


def get_geotiff_info(file_path: Path) -> Dict[str, Any]:
    """
    Get information about GeoTIFF file.
    
    Args:
        file_path: Path to GeoTIFF file
        
    Returns:
        Dictionary with GeoTIFF file information
    """
    try:
        if not validate_geotiff_file(file_path):
            raise ValueError("Invalid GeoTIFF file")
        
        with rasterio.open(file_path) as src:
            info = {
                'filename': file_path.name,
                'file_size_bytes': file_path.stat().st_size,
                'format': 'GeoTIFF',
                'driver': src.driver,
                'width': src.width,
                'height': src.height,
                'count': src.count,
                'dtype': str(src.dtypes[0]),
                'crs': str(src.crs) if src.crs else None,
                'transform': src.transform.to_gdal(),
                'bounds': src.bounds,
                'nodata': src.nodata,
                'metadata': dict(src.tags()),
                'band_descriptions': [src.get_band_description(i) for i in range(1, src.count + 1)]
            }
            
            return info
        
    except Exception as e:
        logger.error("Failed to get GeoTIFF info", error=str(e))
        raise
