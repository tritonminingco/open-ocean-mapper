"""
Deterministic quality control rules for ocean mapping data.

Provides rule-based quality control for various sensor types.
Includes validation rules, range checks, and consistency checks.

Features:
- Sensor-specific validation rules
- Range and consistency checks
- Statistical outlier detection
- Data quality scoring

Usage:
    qc_results = apply_qc_rules(data, "mbes")
    print(f"QC score: {qc_results['quality_score']}")
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


def apply_qc_rules(data: Dict[str, Any], sensor_type: str) -> Dict[str, Any]:
    """
    Apply quality control rules to ocean mapping data.
    
    Args:
        data: Ocean mapping data with points
        sensor_type: Type of sensor (mbes, sbes, lidar, etc.)
        
    Returns:
        Dictionary with QC results and quality score
    """
    try:
        logger.info("Applying QC rules", sensor_type=sensor_type)
        
        points = data.get("points", [])
        if not points:
            return {
                "status": "no_data",
                "quality_score": 0.0,
                "anomalies": [],
                "total_points": 0
            }
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(points)
        
        # Apply sensor-specific rules
        if sensor_type == "mbes":
            qc_results = _apply_mbes_rules(df)
        elif sensor_type == "sbes":
            qc_results = _apply_sbes_rules(df)
        elif sensor_type == "lidar":
            qc_results = _apply_lidar_rules(df)
        elif sensor_type == "singlebeam":
            qc_results = _apply_singlebeam_rules(df)
        elif sensor_type == "auv":
            qc_results = _apply_auv_rules(df)
        else:
            qc_results = _apply_generic_rules(df)
        
        # Calculate overall quality score
        quality_score = _calculate_quality_score(qc_results, len(points))
        
        result = {
            "status": "completed",
            "quality_score": quality_score,
            "anomalies": qc_results["anomalies"],
            "total_points": len(points),
            "rules_applied": qc_results["rules_applied"],
            "statistics": qc_results["statistics"]
        }
        
        logger.info("QC rules applied successfully", 
                   quality_score=quality_score,
                   anomalies_found=len(qc_results["anomalies"]))
        
        return result
        
    except Exception as e:
        logger.error("QC rules application failed", error=str(e))
        return {
            "status": "failed",
            "quality_score": 0.0,
            "anomalies": [],
            "error": str(e)
        }


def _apply_mbes_rules(df: pd.DataFrame) -> Dict[str, Any]:
    """Apply MBES-specific quality control rules."""
    
    anomalies = []
    rules_applied = []
    
    # Rule 1: Check coordinate ranges
    if "latitude" in df.columns:
        lat_anomalies = _check_coordinate_range(df, "latitude", -90, 90)
        anomalies.extend(lat_anomalies)
        rules_applied.append("latitude_range_check")
    
    if "longitude" in df.columns:
        lon_anomalies = _check_coordinate_range(df, "longitude", -180, 180)
        anomalies.extend(lon_anomalies)
        rules_applied.append("longitude_range_check")
    
    # Rule 2: Check depth ranges
    if "depth" in df.columns:
        depth_anomalies = _check_depth_range(df, "depth", 0, 12000)
        anomalies.extend(depth_anomalies)
        rules_applied.append("depth_range_check")
    
    # Rule 3: Check beam angle ranges
    if "beam_angle" in df.columns:
        angle_anomalies = _check_beam_angle_range(df, "beam_angle", -90, 90)
        anomalies.extend(angle_anomalies)
        rules_applied.append("beam_angle_range_check")
    
    # Rule 4: Check quality indicators
    if "quality" in df.columns:
        quality_anomalies = _check_quality_range(df, "quality", 0, 100)
        anomalies.extend(quality_anomalies)
        rules_applied.append("quality_range_check")
    
    # Rule 5: Check for duplicate timestamps
    if "timestamp" in df.columns:
        timestamp_anomalies = _check_duplicate_timestamps(df, "timestamp")
        anomalies.extend(timestamp_anomalies)
        rules_applied.append("duplicate_timestamp_check")
    
    # Rule 6: Check depth consistency
    if "depth" in df.columns:
        consistency_anomalies = _check_depth_consistency(df, "depth")
        anomalies.extend(consistency_anomalies)
        rules_applied.append("depth_consistency_check")
    
    # Calculate statistics
    statistics = _calculate_mbes_statistics(df)
    
    return {
        "anomalies": anomalies,
        "rules_applied": rules_applied,
        "statistics": statistics
    }


def _apply_sbes_rules(df: pd.DataFrame) -> Dict[str, Any]:
    """Apply SBES-specific quality control rules."""
    
    anomalies = []
    rules_applied = []
    
    # Rule 1: Check coordinate ranges
    if "latitude" in df.columns:
        lat_anomalies = _check_coordinate_range(df, "latitude", -90, 90)
        anomalies.extend(lat_anomalies)
        rules_applied.append("latitude_range_check")
    
    if "longitude" in df.columns:
        lon_anomalies = _check_coordinate_range(df, "longitude", -180, 180)
        anomalies.extend(lon_anomalies)
        rules_applied.append("longitude_range_check")
    
    # Rule 2: Check depth ranges
    if "depth" in df.columns:
        depth_anomalies = _check_depth_range(df, "depth", 0, 12000)
        anomalies.extend(depth_anomalies)
        rules_applied.append("depth_range_check")
    
    # Rule 3: Check navigation parameters
    if "heading" in df.columns:
        heading_anomalies = _check_navigation_range(df, "heading", 0, 360)
        anomalies.extend(heading_anomalies)
        rules_applied.append("heading_range_check")
    
    if "pitch" in df.columns:
        pitch_anomalies = _check_navigation_range(df, "pitch", -90, 90)
        anomalies.extend(pitch_anomalies)
        rules_applied.append("pitch_range_check")
    
    if "roll" in df.columns:
        roll_anomalies = _check_navigation_range(df, "roll", -90, 90)
        anomalies.extend(roll_anomalies)
        rules_applied.append("roll_range_check")
    
    # Rule 4: Check velocity ranges
    if "velocity" in df.columns:
        velocity_anomalies = _check_velocity_range(df, "velocity", 0, 50)
        anomalies.extend(velocity_anomalies)
        rules_applied.append("velocity_range_check")
    
    # Calculate statistics
    statistics = _calculate_sbes_statistics(df)
    
    return {
        "anomalies": anomalies,
        "rules_applied": rules_applied,
        "statistics": statistics
    }


def _apply_lidar_rules(df: pd.DataFrame) -> Dict[str, Any]:
    """Apply LiDAR-specific quality control rules."""
    
    anomalies = []
    rules_applied = []
    
    # Rule 1: Check coordinate ranges
    if "latitude" in df.columns:
        lat_anomalies = _check_coordinate_range(df, "latitude", -90, 90)
        anomalies.extend(lat_anomalies)
        rules_applied.append("latitude_range_check")
    
    if "longitude" in df.columns:
        lon_anomalies = _check_coordinate_range(df, "longitude", -180, 180)
        anomalies.extend(lon_anomalies)
        rules_applied.append("longitude_range_check")
    
    # Rule 2: Check elevation ranges
    if "elevation" in df.columns:
        elevation_anomalies = _check_elevation_range(df, "elevation", -1000, 10000)
        anomalies.extend(elevation_anomalies)
        rules_applied.append("elevation_range_check")
    
    # Rule 3: Check intensity ranges
    if "intensity" in df.columns:
        intensity_anomalies = _check_intensity_range(df, "intensity", 0, 255)
        anomalies.extend(intensity_anomalies)
        rules_applied.append("intensity_range_check")
    
    # Rule 4: Check classification codes
    if "classification" in df.columns:
        classification_anomalies = _check_classification_range(df, "classification", 0, 31)
        anomalies.extend(classification_anomalies)
        rules_applied.append("classification_range_check")
    
    # Calculate statistics
    statistics = _calculate_lidar_statistics(df)
    
    return {
        "anomalies": anomalies,
        "rules_applied": rules_applied,
        "statistics": statistics
    }


def _apply_singlebeam_rules(df: pd.DataFrame) -> Dict[str, Any]:
    """Apply single-beam specific quality control rules."""
    # Single-beam rules are similar to SBES
    return _apply_sbes_rules(df)


def _apply_auv_rules(df: pd.DataFrame) -> Dict[str, Any]:
    """Apply AUV-specific quality control rules."""
    # AUV rules are similar to SBES with additional navigation checks
    return _apply_sbes_rules(df)


def _apply_generic_rules(df: pd.DataFrame) -> Dict[str, Any]:
    """Apply generic quality control rules."""
    
    anomalies = []
    rules_applied = []
    
    # Basic coordinate checks
    if "latitude" in df.columns:
        lat_anomalies = _check_coordinate_range(df, "latitude", -90, 90)
        anomalies.extend(lat_anomalies)
        rules_applied.append("latitude_range_check")
    
    if "longitude" in df.columns:
        lon_anomalies = _check_coordinate_range(df, "longitude", -180, 180)
        anomalies.extend(lon_anomalies)
        rules_applied.append("longitude_range_check")
    
    # Basic depth/elevation checks
    if "depth" in df.columns:
        depth_anomalies = _check_depth_range(df, "depth", 0, 12000)
        anomalies.extend(depth_anomalies)
        rules_applied.append("depth_range_check")
    
    if "elevation" in df.columns:
        elevation_anomalies = _check_elevation_range(df, "elevation", -1000, 10000)
        anomalies.extend(elevation_anomalies)
        rules_applied.append("elevation_range_check")
    
    # Calculate basic statistics
    statistics = _calculate_generic_statistics(df)
    
    return {
        "anomalies": anomalies,
        "rules_applied": rules_applied,
        "statistics": statistics
    }


def _check_coordinate_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check coordinate values are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "coordinate_range",
            "severity": "high",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}",
            "description": f"Invalid {column} value: {df.loc[idx, column]}"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_depth_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check depth values are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "depth_range",
            "severity": "high",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}m",
            "description": f"Invalid depth value: {df.loc[idx, column]}m"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_beam_angle_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check beam angle values are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "beam_angle_range",
            "severity": "medium",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}°",
            "description": f"Invalid beam angle: {df.loc[idx, column]}°"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_quality_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check quality indicator values are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "quality_range",
            "severity": "medium",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}",
            "description": f"Invalid quality value: {df.loc[idx, column]}"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_navigation_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check navigation parameter values are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "navigation_range",
            "severity": "medium",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}°",
            "description": f"Invalid {column} value: {df.loc[idx, column]}°"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_velocity_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check velocity values are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "velocity_range",
            "severity": "medium",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}m/s",
            "description": f"Invalid velocity value: {df.loc[idx, column]}m/s"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_elevation_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check elevation values are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "elevation_range",
            "severity": "high",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}m",
            "description": f"Invalid elevation value: {df.loc[idx, column]}m"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_intensity_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check intensity values are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "intensity_range",
            "severity": "low",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}",
            "description": f"Invalid intensity value: {df.loc[idx, column]}"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_classification_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Check classification codes are within valid range."""
    anomalies = []
    
    invalid_mask = (df[column] < min_val) | (df[column] > max_val)
    invalid_indices = df[invalid_mask].index.tolist()
    
    for idx in invalid_indices:
        anomaly = {
            "index": int(idx),
            "type": "classification_range",
            "severity": "medium",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"{min_val}-{max_val}",
            "description": f"Invalid classification code: {df.loc[idx, column]}"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_duplicate_timestamps(df: pd.DataFrame, column: str) -> List[Dict[str, Any]]:
    """Check for duplicate timestamps."""
    anomalies = []
    
    duplicates = df[df.duplicated(subset=[column], keep=False)]
    if len(duplicates) > 0:
        anomaly = {
            "index": "multiple",
            "type": "duplicate_timestamp",
            "severity": "medium",
            "column": column,
            "value": len(duplicates),
            "threshold": 0,
            "description": f"Found {len(duplicates)} duplicate timestamps"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _check_depth_consistency(df: pd.DataFrame, column: str) -> List[Dict[str, Any]]:
    """Check depth consistency using statistical methods."""
    anomalies = []
    
    if len(df) < 10:  # Need minimum data for statistical analysis
        return anomalies
    
    # Calculate depth statistics
    depth_values = df[column].dropna()
    if len(depth_values) < 5:
        return anomalies
    
    mean_depth = depth_values.mean()
    std_depth = depth_values.std()
    
    # Find outliers using 3-sigma rule
    outlier_mask = np.abs(depth_values - mean_depth) > 3 * std_depth
    outlier_indices = depth_values[outlier_mask].index.tolist()
    
    for idx in outlier_indices:
        anomaly = {
            "index": int(idx),
            "type": "depth_outlier",
            "severity": "medium",
            "column": column,
            "value": float(df.loc[idx, column]),
            "threshold": f"3σ from mean ({mean_depth:.2f}±{std_depth:.2f})",
            "description": f"Depth outlier: {df.loc[idx, column]}m"
        }
        anomalies.append(anomaly)
    
    return anomalies


def _calculate_quality_score(qc_results: Dict[str, Any], total_points: int) -> float:
    """Calculate overall quality score from QC results."""
    
    if total_points == 0:
        return 0.0
    
    anomalies = qc_results.get("anomalies", [])
    anomaly_count = len(anomalies)
    
    # Base score calculation
    anomaly_rate = anomaly_count / total_points
    
    # Quality score decreases with anomaly rate
    if anomaly_rate == 0:
        quality_score = 1.0
    elif anomaly_rate < 0.01:  # Less than 1% anomalies
        quality_score = 0.9
    elif anomaly_rate < 0.05:  # Less than 5% anomalies
        quality_score = 0.8
    elif anomaly_rate < 0.1:   # Less than 10% anomalies
        quality_score = 0.7
    elif anomaly_rate < 0.2:   # Less than 20% anomalies
        quality_score = 0.5
    else:  # More than 20% anomalies
        quality_score = 0.2
    
    # Adjust for severity
    high_severity_count = sum(1 for a in anomalies if a.get("severity") == "high")
    if high_severity_count > 0:
        quality_score = min(quality_score, 0.6)
    
    return round(quality_score, 3)


def _calculate_mbes_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate MBES-specific statistics."""
    stats = {}
    
    if "depth" in df.columns:
        depth_values = df["depth"].dropna()
        if len(depth_values) > 0:
            stats["depth"] = {
                "min": float(depth_values.min()),
                "max": float(depth_values.max()),
                "mean": float(depth_values.mean()),
                "std": float(depth_values.std())
            }
    
    if "beam_angle" in df.columns:
        angle_values = df["beam_angle"].dropna()
        if len(angle_values) > 0:
            stats["beam_angle"] = {
                "min": float(angle_values.min()),
                "max": float(angle_values.max()),
                "mean": float(angle_values.mean()),
                "std": float(angle_values.std())
            }
    
    return stats


def _calculate_sbes_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate SBES-specific statistics."""
    stats = {}
    
    if "depth" in df.columns:
        depth_values = df["depth"].dropna()
        if len(depth_values) > 0:
            stats["depth"] = {
                "min": float(depth_values.min()),
                "max": float(depth_values.max()),
                "mean": float(depth_values.mean()),
                "std": float(depth_values.std())
            }
    
    return stats


def _calculate_lidar_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate LiDAR-specific statistics."""
    stats = {}
    
    if "elevation" in df.columns:
        elevation_values = df["elevation"].dropna()
        if len(elevation_values) > 0:
            stats["elevation"] = {
                "min": float(elevation_values.min()),
                "max": float(elevation_values.max()),
                "mean": float(elevation_values.mean()),
                "std": float(elevation_values.std())
            }
    
    return stats


def _calculate_generic_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate generic statistics."""
    stats = {}
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_columns:
        values = df[col].dropna()
        if len(values) > 0:
            stats[col] = {
                "min": float(values.min()),
                "max": float(values.max()),
                "mean": float(values.mean()),
                "std": float(values.std())
            }
    
    return stats
