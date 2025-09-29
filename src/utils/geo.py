"""
Geographic utilities for ocean mapping data processing.

Provides coordinate system transformations, spatial operations,
and bathymetric surface generation using pyproj and scipy.

Features:
- Coordinate system transformations (WGS84, UTM, etc.)
- Spatial interpolation and gridding
- Bathymetric surface generation
- Distance and bearing calculations

Usage:
    projected_data = reproject_to_wgs84(data)
    surface = create_bathymetric_surface(data)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import structlog

logger = structlog.get_logger(__name__)

# Try to import pyproj, fall back to mock if not available
try:
    import pyproj
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    logger.warning("pyproj not available, using mock coordinate transformations")

# Try to import scipy for spatial operations
try:
    from scipy.spatial import Delaunay
    from scipy.interpolate import griddata
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available, using mock spatial operations")


def reproject_to_wgs84(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reproject coordinates to WGS84 (EPSG:4326).
    
    Args:
        data: Ocean mapping data with coordinates
        
    Returns:
        Data with coordinates reprojected to WGS84
    """
    try:
        logger.info("Reprojecting coordinates to WGS84")
        
        points = data.get("points", [])
        if not points:
            logger.warning("No points data to reproject")
            return data
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(points)
        
        # Check if coordinates are already in WGS84
        if _is_wgs84(df):
            logger.info("Coordinates already in WGS84")
            return data
        
        # Determine source coordinate system
        source_crs = _detect_coordinate_system(df)
        logger.info("Detected coordinate system", crs=source_crs)
        
        # Reproject coordinates
        if PYPROJ_AVAILABLE and source_crs != "EPSG:4326":
            df = _reproject_coordinates(df, source_crs, "EPSG:4326")
        else:
            logger.warning("Coordinate reprojection not available, using original coordinates")
        
        # Convert back to list of dictionaries
        reprojected_points = df.to_dict('records')
        
        # Create reprojected data
        reprojected_data = data.copy()
        reprojected_data["points"] = reprojected_points
        
        # Update metadata
        reprojected_data["metadata"]["coordinate_system"] = "WGS84"
        reprojected_data["metadata"]["reprojection"] = {
            "applied": True,
            "source_crs": source_crs,
            "target_crs": "EPSG:4326",
            "method": "pyproj" if PYPROJ_AVAILABLE else "none"
        }
        
        logger.info("Coordinate reprojection completed", 
                   total_points=len(reprojected_points))
        
        return reprojected_data
        
    except Exception as e:
        logger.error("Coordinate reprojection failed", error=str(e))
        return data


def _is_wgs84(df: pd.DataFrame) -> bool:
    """Check if coordinates are already in WGS84."""
    if "latitude" not in df.columns or "longitude" not in df.columns:
        return False
    
    # Check coordinate ranges
    lat_range = df["latitude"].max() - df["latitude"].min()
    lon_range = df["longitude"].max() - df["longitude"].min()
    
    # WGS84 coordinates should be in degrees
    if lat_range > 180 or lon_range > 360:
        return False
    
    # Check if values are within WGS84 bounds
    if (df["latitude"].min() < -90 or df["latitude"].max() > 90 or
        df["longitude"].min() < -180 or df["longitude"].max() > 180):
        return False
    
    return True


def _detect_coordinate_system(df: pd.DataFrame) -> str:
    """Detect coordinate system from data."""
    
    if "latitude" not in df.columns or "longitude" not in df.columns:
        return "EPSG:4326"  # Default to WGS84
    
    # Check coordinate ranges
    lat_range = df["latitude"].max() - df["latitude"].min()
    lon_range = df["longitude"].max() - df["longitude"].min()
    
    # If coordinates are in degrees, assume WGS84
    if lat_range <= 180 and lon_range <= 360:
        return "EPSG:4326"
    
    # If coordinates are in meters, assume UTM
    if lat_range > 1000 and lon_range > 1000:
        return "EPSG:32633"  # UTM Zone 33N (example)
    
    # Default to WGS84
    return "EPSG:4326"


def _reproject_coordinates(df: pd.DataFrame, source_crs: str, target_crs: str) -> pd.DataFrame:
    """Reproject coordinates using pyproj."""
    
    if not PYPROJ_AVAILABLE:
        logger.warning("pyproj not available, skipping reprojection")
        return df
    
    try:
        # Create transformer
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        
        # Reproject coordinates
        x, y = transformer.transform(df["longitude"].values, df["latitude"].values)
        
        # Update DataFrame
        df_reprojected = df.copy()
        df_reprojected["longitude"] = x
        df_reprojected["latitude"] = y
        
        logger.info("Coordinates reprojected", 
                   source_crs=source_crs,
                   target_crs=target_crs)
        
        return df_reprojected
        
    except Exception as e:
        logger.error("Coordinate reprojection failed", error=str(e))
        return df


def create_bathymetric_surface(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create bathymetric surface from point data.
    
    Args:
        data: Ocean mapping data with points
        
    Returns:
        Data with bathymetric surface information
    """
    try:
        logger.info("Creating bathymetric surface")
        
        points = data.get("points", [])
        if not points:
            logger.warning("No points data for surface creation")
            return data
        
        # Convert to DataFrame
        df = pd.DataFrame(points)
        
        # Extract coordinates and depths
        if "latitude" not in df.columns or "longitude" not in df.columns:
            logger.error("Missing coordinate columns")
            return data
        
        # Determine depth column
        depth_col = "depth" if "depth" in df.columns else "elevation"
        if depth_col not in df.columns:
            logger.error("Missing depth/elevation column")
            return data
        
        # Create surface
        if SCIPY_AVAILABLE:
            surface_data = _create_surface_scipy(df, depth_col)
        else:
            surface_data = _create_surface_mock(df, depth_col)
        
        # Add surface information to data
        surface_data["points"] = points  # Keep original points
        surface_data["metadata"] = data.get("metadata", {})
        surface_data["metadata"]["surface_generation"] = {
            "method": "scipy" if SCIPY_AVAILABLE else "mock",
            "total_points": len(points),
            "surface_resolution": surface_data.get("resolution", 0.001),
            "surface_bounds": surface_data.get("bounds", {})
        }
        
        logger.info("Bathymetric surface created", 
                   method="scipy" if SCIPY_AVAILABLE else "mock",
                   total_points=len(points))
        
        return surface_data
        
    except Exception as e:
        logger.error("Surface creation failed", error=str(e))
        return data


def _create_surface_scipy(df: pd.DataFrame, depth_col: str) -> Dict[str, Any]:
    """Create bathymetric surface using scipy."""
    
    # Extract coordinates and depths
    x = df["longitude"].values
    y = df["latitude"].values
    z = df[depth_col].values
    
    # Remove NaN values
    valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    z_valid = z[valid_mask]
    
    if len(x_valid) < 3:
        logger.warning("Insufficient valid points for surface creation")
        return _create_surface_mock(df, depth_col)
    
    # Define grid resolution
    resolution = 0.001  # degrees (~100m at equator)
    
    # Create grid
    x_min, x_max = x_valid.min(), x_valid.max()
    y_min, y_max = y_valid.min(), y_valid.max()
    
    x_grid = np.arange(x_min, x_max + resolution, resolution)
    y_grid = np.arange(y_min, y_max + resolution, resolution)
    X_grid, Y_grid = np.meshgrid(x_grid, y_grid)
    
    # Interpolate depths
    try:
        Z_grid = griddata(
            (x_valid, y_valid), 
            z_valid, 
            (X_grid, Y_grid), 
            method='linear',
            fill_value=np.nan
        )
    except Exception as e:
        logger.warning("Grid interpolation failed, using nearest neighbor", error=str(e))
        Z_grid = griddata(
            (x_valid, y_valid), 
            z_valid, 
            (X_grid, Y_grid), 
            method='nearest',
            fill_value=np.nan
        )
    
    # Create Delaunay triangulation
    try:
        points_2d = np.column_stack((x_valid, y_valid))
        tri = Delaunay(points_2d)
    except Exception as e:
        logger.warning("Delaunay triangulation failed", error=str(e))
        tri = None
    
    return {
        "surface_type": "gridded",
        "method": "scipy",
        "resolution": resolution,
        "bounds": {
            "min_lon": float(x_min),
            "max_lon": float(x_max),
            "min_lat": float(y_min),
            "max_lat": float(y_max)
        },
        "grid": {
            "x": X_grid,
            "y": Y_grid,
            "z": Z_grid
        },
        "triangulation": tri,
        "valid_points": len(x_valid)
    }


def _create_surface_mock(df: pd.DataFrame, depth_col: str) -> Dict[str, Any]:
    """Create mock bathymetric surface."""
    
    # Extract coordinates and depths
    x = df["longitude"].values
    y = df["latitude"].values
    z = df[depth_col].values
    
    # Calculate bounds
    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()
    
    # Create simple grid
    resolution = 0.001  # degrees
    x_grid = np.arange(x_min, x_max + resolution, resolution)
    y_grid = np.arange(y_min, y_max + resolution, resolution)
    X_grid, Y_grid = np.meshgrid(x_grid, y_grid)
    
    # Simple nearest neighbor interpolation
    Z_grid = np.full_like(X_grid, np.nan)
    
    for i in range(X_grid.shape[0]):
        for j in range(X_grid.shape[1]):
            # Find nearest point
            distances = np.sqrt((x - X_grid[i, j])**2 + (y - Y_grid[i, j])**2)
            nearest_idx = np.argmin(distances)
            Z_grid[i, j] = z[nearest_idx]
    
    return {
        "surface_type": "gridded",
        "method": "mock",
        "resolution": resolution,
        "bounds": {
            "min_lon": float(x_min),
            "max_lon": float(x_max),
            "min_lat": float(y_min),
            "max_lat": float(y_max)
        },
        "grid": {
            "x": X_grid,
            "y": Y_grid,
            "z": Z_grid
        },
        "triangulation": None,
        "valid_points": len(x)
    }


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in meters
    """
    try:
        # Convert to radians
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth radius in meters
        earth_radius = 6371000
        
        return earth_radius * c
        
    except Exception as e:
        logger.error("Distance calculation failed", error=str(e))
        return 0.0


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate bearing between two points.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Bearing in degrees (0-360)
    """
    try:
        # Convert to radians
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # Calculate bearing
        dlon = lon2_rad - lon1_rad
        
        y = np.sin(dlon) * np.cos(lat2_rad)
        x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)
        
        bearing = np.degrees(np.arctan2(y, x))
        
        # Normalize to 0-360
        bearing = (bearing + 360) % 360
        
        return bearing
        
    except Exception as e:
        logger.error("Bearing calculation failed", error=str(e))
        return 0.0


def get_utm_zone(longitude: float) -> str:
    """
    Get UTM zone for a given longitude.
    
    Args:
        longitude: Longitude in degrees
        
    Returns:
        UTM zone string (e.g., "EPSG:32633")
    """
    try:
        # Calculate UTM zone
        zone = int((longitude + 180) / 6) + 1
        
        # Determine hemisphere
        if longitude >= 0:
            hemisphere = "N"
            epsg_code = 32600 + zone
        else:
            hemisphere = "S"
            epsg_code = 32700 + zone
        
        return f"EPSG:{epsg_code}"
        
    except Exception as e:
        logger.error("UTM zone calculation failed", error=str(e))
        return "EPSG:4326"  # Default to WGS84
