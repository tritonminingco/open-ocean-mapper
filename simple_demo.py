#!/usr/bin/env python3
"""
Simple demo script for Open Ocean Mapper.
Demonstrates core functionality without complex imports.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def demo_qc():
    """Demonstrate QC functionality."""
    print("\n=== Quality Control Demo ===")
    
    try:
        from qc.model_stub import predict_anomalies
        
        # Create test data with some anomalies
        test_data = {
            "points": [
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.5},
                {"latitude": 40.7130, "longitude": -74.0058, "depth": 12.3},
                {"latitude": 40.7132, "longitude": -74.0056, "depth": 200.0},  # Anomaly
                {"latitude": 40.7134, "longitude": -74.0054, "depth": 15.7},
                {"latitude": 40.7136, "longitude": -74.0052, "depth": -5.0}   # Anomaly
            ]
        }
        
        result = predict_anomalies(test_data)
        
        print(f"Total points: {result['total_points']}")
        print(f"Anomalies found: {len(result['anomalies'])}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Anomaly rate: {result['anomaly_rate']:.2%}")
        
        if result['anomalies']:
            print("\nAnomalies detected:")
            for i, anomaly in enumerate(result['anomalies'], 1):
                print(f"  {i}. {anomaly['type']}: {anomaly['description']}")
        
        return True
        
    except Exception as e:
        print(f"QC demo failed: {e}")
        return False

def demo_seabed2030():
    """Demonstrate Seabed 2030 functionality."""
    print("\n=== Seabed 2030 Demo ===")
    
    try:
        from adapters.seabed2030_adapter import Seabed2030Adapter
        
        # Create test metadata
        metadata = {
            "title": "Demo Ocean Mapping Data",
            "description": "Sample ocean mapping data for demonstration",
            "sensor_type": "mbes",
            "quality_score": 0.95,
            "anomaly_count": 2,
            "bounds": {
                "min_lat": 40.7128,
                "max_lat": 40.7136,
                "min_lon": -74.0060,
                "max_lon": -74.0052
            }
        }
        
        # Create dummy NetCDF file
        test_nc_path = Path("demo_output.nc")
        test_nc_path.touch()
        
        # Initialize adapter
        adapter = Seabed2030Adapter()
        
        # Build payload
        payload = adapter.build_payload(metadata, test_nc_path)
        print(f"Payload built successfully")
        
        # Perform dry run
        result = adapter.dry_run_upload(payload)
        
        print(f"Upload status: {result['status']}")
        print(f"Validation: {result['validation']['status']}")
        
        if result['validation']['checks']:
            print("\nValidation checks:")
            for check in result['validation']['checks']:
                status = "PASS" if check['status'] == 'valid' else "FAIL"
                print(f"  {status}: {check['field']} - {check['message']}")
        
        if result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        # Clean up
        test_nc_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"Seabed 2030 demo failed: {e}")
        return False

def demo_data_processing():
    """Demonstrate basic data processing."""
    print("\n=== Data Processing Demo ===")
    
    try:
        # Load mock data
        mbes_data = pd.read_csv("data/mock/mock_mbes_ping.csv")
        print(f"Loaded MBES data: {len(mbes_data)} points")
        
        # Basic statistics
        print(f"Depth range: {mbes_data['depth'].min():.1f}m - {mbes_data['depth'].max():.1f}m")
        print(f"Latitude range: {mbes_data['latitude'].min():.4f} - {mbes_data['latitude'].max():.4f}")
        print(f"Longitude range: {mbes_data['longitude'].min():.4f} - {mbes_data['longitude'].max():.4f}")
        print(f"Average quality: {mbes_data['quality'].mean():.1f}")
        
        # Load SBES data
        sbes_data = pd.read_csv("data/mock/mock_singlebeam.txt", comment='#', sep=' ')
        print(f"\nLoaded SBES data: {len(sbes_data)} points")
        if len(sbes_data.columns) > 3:
            print(f"Depth range: {sbes_data.iloc[:, 3].min():.1f}m - {sbes_data.iloc[:, 3].max():.1f}m")
        else:
            print("SBES data loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"Data processing demo failed: {e}")
        return False

def demo_anonymization():
    """Demonstrate anonymization functionality."""
    print("\n=== Anonymization Demo ===")
    
    try:
        import hashlib
        import random
        
        # Test vessel ID hashing
        original_id = "RV_OCEAN_EXPLORER"
        salt = "demo_salt"
        hashed_id = hashlib.sha256(f"{original_id}{salt}".encode()).hexdigest()[:16]
        print(f"Original vessel ID: {original_id}")
        print(f"Hashed vessel ID: {hashed_id}")
        
        # Test GPS jittering
        original_lat = 40.7128
        original_lon = -74.0060
        jitter_radius = 50  # meters
        
        # Convert to meters and add jitter
        lat_offset = random.uniform(-jitter_radius, jitter_radius) / 111000  # ~111km per degree
        lon_offset = random.uniform(-jitter_radius, jitter_radius) / (111000 * np.cos(np.radians(original_lat)))
        
        jittered_lat = original_lat + lat_offset
        jittered_lon = original_lon + lon_offset
        
        print(f"Original coordinates: ({original_lat:.6f}, {original_lon:.6f})")
        print(f"Jittered coordinates: ({jittered_lat:.6f}, {jittered_lon:.6f})")
        print(f"Jitter distance: {np.sqrt(lat_offset**2 + lon_offset**2) * 111000:.1f}m")
        
        return True
        
    except Exception as e:
        print(f"Anonymization demo failed: {e}")
        return False

def main():
    """Run all demos."""
    print("Open Ocean Mapper - Simple Demo")
    print("=" * 40)
    
    demos = [
        demo_data_processing,
        demo_qc,
        demo_anonymization,
        demo_seabed2030
    ]
    
    passed = 0
    total = len(demos)
    
    for demo in demos:
        if demo():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Demos completed: {passed}/{total}")
    
    if passed == total:
        print("All demos completed successfully!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e .")
        print("2. Start API server: python cli/open_ocean_mapper.py serve")
        print("3. Open web interface: http://localhost:3000")
        print("4. Run full demo: ./examples/run_demo.sh")
        return 0
    else:
        print("Some demos failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
