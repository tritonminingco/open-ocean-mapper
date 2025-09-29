"""
Data anonymization module for ocean mapping data.

Provides deterministic anonymization of vessel identifiers and optional
GPS jittering for sensitive location data.

Features:
- Deterministic vessel ID hashing with salt
- Configurable GPS jittering with radius control
- Preserves data quality while removing identifying information
- Reversible anonymization for authorized users

Usage:
    anonymized_data = anonymize_data(raw_data, "mbes", salt="my_salt")
    print(f"Anonymized {len(anonymized_data['points'])} points")
"""

import logging
import hashlib
import random
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger(__name__)


def anonymize_data(data: Dict[str, Any], sensor_type: str, salt: str = "default_salt") -> Dict[str, Any]:
    """
    Anonymize ocean mapping data.
    
    Args:
        data: Raw ocean mapping data
        sensor_type: Type of sensor (mbes, sbes, lidar, etc.)
        salt: Salt for deterministic hashing
        
    Returns:
        Anonymized data with vessel IDs hashed and optional GPS jittering
    """
    try:
        logger.info("Anonymizing data", sensor_type=sensor_type, salt_provided=bool(salt))
        
        # Create anonymized copy
        anonymized_data = data.copy()
        points = data.get("points", [])
        
        if not points:
            logger.warning("No points data to anonymize")
            return anonymized_data
        
        # Anonymize each point
        anonymized_points = []
        for point in points:
            anonymized_point = _anonymize_point(point, salt)
            anonymized_points.append(anonymized_point)
        
        anonymized_data["points"] = anonymized_points
        
        # Update metadata
        anonymized_data["metadata"]["anonymization"] = {
            "applied": True,
            "salt_used": bool(salt),
            "vessel_ids_hashed": True,
            "gps_jittered": False,  # Can be enabled via config
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }
        
        logger.info("Data anonymization completed", 
                   total_points=len(anonymized_points))
        
        return anonymized_data
        
    except Exception as e:
        logger.error("Data anonymization failed", error=str(e))
        raise


def _anonymize_point(point: Dict[str, Any], salt: str) -> Dict[str, Any]:
    """Anonymize a single data point."""
    
    anonymized_point = point.copy()
    
    # Hash vessel identifier if present
    if "vessel_id" in point:
        anonymized_point["vessel_id"] = _hash_vessel_id(point["vessel_id"], salt)
    
    if "vessel_name" in point:
        anonymized_point["vessel_name"] = _hash_vessel_id(point["vessel_name"], salt)
    
    if "survey_id" in point:
        anonymized_point["survey_id"] = _hash_vessel_id(point["survey_id"], salt)
    
    # Apply GPS jittering if enabled (configurable)
    if "gps_jitter" in point and point["gps_jitter"]:
        anonymized_point = _apply_gps_jitter(anonymized_point, salt)
    
    return anonymized_point


def _hash_vessel_id(vessel_id: str, salt: str) -> str:
    """
    Create deterministic hash of vessel identifier.
    
    Args:
        vessel_id: Original vessel identifier
        salt: Salt for hashing
        
    Returns:
        Hashed vessel identifier
    """
    # Create deterministic hash
    hash_input = f"{vessel_id}_{salt}".encode('utf-8')
    hash_output = hashlib.sha256(hash_input).hexdigest()
    
    # Return first 8 characters for readability
    return f"VESSEL_{hash_output[:8].upper()}"


def _apply_gps_jitter(point: Dict[str, Any], salt: str) -> Dict[str, Any]:
    """
    Apply GPS jittering to coordinates.
    
    Args:
        point: Data point with coordinates
        salt: Salt for deterministic jittering
        
    Returns:
        Point with jittered coordinates
    """
    jittered_point = point.copy()
    
    # Jitter radius in meters (configurable)
    jitter_radius = 50  # meters
    
    # Convert to approximate degrees (rough approximation)
    lat_jitter = jitter_radius / 111000  # ~111km per degree latitude
    lon_jitter = jitter_radius / (111000 * abs(point.get("latitude", 0)) * 0.0174532925)  # Approximate longitude
    
    # Create deterministic random offset based on salt and coordinates
    random.seed(hash(f"{salt}_{point.get('latitude', 0)}_{point.get('longitude', 0)}"))
    
    # Apply jitter
    if "latitude" in point:
        lat_offset = random.uniform(-lat_jitter, lat_jitter)
        jittered_point["latitude"] = point["latitude"] + lat_offset
    
    if "longitude" in point:
        lon_offset = random.uniform(-lon_jitter, lon_jitter)
        jittered_point["longitude"] = point["longitude"] + lon_offset
    
    # Add jitter metadata
    jittered_point["gps_jitter_applied"] = True
    jittered_point["jitter_radius_meters"] = jitter_radius
    
    return jittered_point


def deanonimize_data(data: Dict[str, Any], salt: str, vessel_mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Reverse anonymization for authorized users.
    
    Args:
        data: Anonymized data
        salt: Salt used for anonymization
        vessel_mapping: Mapping from hashed IDs to original IDs
        
    Returns:
        De-anonymized data
    """
    try:
        logger.info("De-anonymizing data", salt_provided=bool(salt))
        
        # Create de-anonymized copy
        deanonymized_data = data.copy()
        points = data.get("points", [])
        
        if not points:
            logger.warning("No points data to de-anonymize")
            return deanonymized_data
        
        # De-anonymize each point
        deanonymized_points = []
        for point in points:
            deanonymized_point = _deanonymize_point(point, salt, vessel_mapping)
            deanonymized_points.append(deanonymized_point)
        
        deanonymized_data["points"] = deanonymized_points
        
        # Update metadata
        deanonymized_data["metadata"]["anonymization"]["reversed"] = True
        deanonymized_data["metadata"]["anonymization"]["reversal_timestamp"] = "2024-01-01T00:00:00Z"
        
        logger.info("Data de-anonymization completed", 
                   total_points=len(deanonymized_points))
        
        return deanonymized_data
        
    except Exception as e:
        logger.error("Data de-anonymization failed", error=str(e))
        raise


def _deanonymize_point(point: Dict[str, Any], salt: str, vessel_mapping: Dict[str, str]) -> Dict[str, Any]:
    """De-anonymize a single data point."""
    
    deanonymized_point = point.copy()
    
    # Reverse vessel ID hashing
    if "vessel_id" in point and point["vessel_id"] in vessel_mapping:
        deanonymized_point["vessel_id"] = vessel_mapping[point["vessel_id"]]
    
    if "vessel_name" in point and point["vessel_name"] in vessel_mapping:
        deanonymized_point["vessel_name"] = vessel_mapping[point["vessel_name"]]
    
    if "survey_id" in point and point["survey_id"] in vessel_mapping:
        deanonymized_point["survey_id"] = vessel_mapping[point["survey_id"]]
    
    # Note: GPS jittering is not easily reversible without original coordinates
    # This would require storing original coordinates separately
    
    return deanonymized_point


def generate_vessel_mapping(original_data: Dict[str, Any], anonymized_data: Dict[str, Any], salt: str) -> Dict[str, str]:
    """
    Generate mapping between original and anonymized vessel IDs.
    
    Args:
        original_data: Original data with vessel IDs
        anonymized_data: Anonymized data with hashed IDs
        salt: Salt used for anonymization
        
    Returns:
        Mapping from hashed IDs to original IDs
    """
    mapping = {}
    
    original_points = original_data.get("points", [])
    anonymized_points = anonymized_data.get("points", [])
    
    if len(original_points) != len(anonymized_points):
        logger.warning("Point count mismatch between original and anonymized data")
        return mapping
    
    for orig_point, anon_point in zip(original_points, anonymized_points):
        # Map vessel IDs
        if "vessel_id" in orig_point and "vessel_id" in anon_point:
            mapping[anon_point["vessel_id"]] = orig_point["vessel_id"]
        
        if "vessel_name" in orig_point and "vessel_name" in anon_point:
            mapping[anon_point["vessel_name"]] = orig_point["vessel_name"]
        
        if "survey_id" in orig_point and "survey_id" in anon_point:
            mapping[anon_point["survey_id"]] = orig_point["survey_id"]
    
    logger.info("Vessel mapping generated", mapping_count=len(mapping))
    
    return mapping


def validate_anonymization(data: Dict[str, Any]) -> bool:
    """
    Validate that data has been properly anonymized.
    
    Args:
        data: Data to validate
        
    Returns:
        True if data appears to be anonymized
    """
    try:
        # Check for anonymization metadata
        if "metadata" not in data:
            return False
        
        anonymization_info = data["metadata"].get("anonymization", {})
        if not anonymization_info.get("applied", False):
            return False
        
        # Check for hashed vessel IDs in points
        points = data.get("points", [])
        if not points:
            return True
        
        # Sample check - look for hashed vessel IDs
        sample_point = points[0]
        if "vessel_id" in sample_point:
            vessel_id = sample_point["vessel_id"]
            if not vessel_id.startswith("VESSEL_"):
                return False
        
        return True
        
    except Exception:
        return False
