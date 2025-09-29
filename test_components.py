#!/usr/bin/env python3
"""
Simple test script to validate Open Ocean Mapper components.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        # Test basic imports
        import pandas as pd
        import numpy as np
        print("pandas and numpy imported successfully")
        
        # Test our modules
        from pipeline.converter import ConvertJob, ConversionError
        print("Converter module imported successfully")
        
        from qc.model_stub import load_model, predict_anomalies
        print("QC module imported successfully")
        
        from adapters.seabed2030_adapter import Seabed2030Adapter
        print("Seabed 2030 adapter imported successfully")
        
        from utils.logging import setup_logging, get_logger
        print("Logging module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False

def test_converter():
    """Test converter functionality."""
    print("\nTesting converter...")
    
    try:
        from pipeline.converter import ConvertJob
        
        # Test initialization
        job = ConvertJob(
            input_path="data/mock/mock_mbes_ping.csv",
            sensor_type="mbes",
            output_format="netcdf",
            anonymize=True,
            add_overlay=False,
            qc_mode="auto"
        )
        print("ConvertJob initialized successfully")
        
        # Test validation
        assert job.sensor_type == "mbes"
        assert job.output_format == "netcdf"
        assert job.anonymize is True
        print("ConvertJob validation passed")
        
        return True
        
    except Exception as e:
        print(f"Converter test failed: {e}")
        return False

def test_qc():
    """Test QC functionality."""
    print("\nTesting QC...")
    
    try:
        from qc.model_stub import load_model, predict_anomalies
        
        # Test model loading
        model = load_model()
        print("Model loaded successfully")
        
        # Test anomaly prediction
        test_data = {
            "points": [
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.5},
                {"latitude": 40.7130, "longitude": -74.0058, "depth": 12.3}
            ]
        }
        
        result = predict_anomalies(test_data)
        print("Anomaly prediction completed")
        
        # Validate result structure
        assert "anomalies" in result
        assert "confidence" in result
        assert "total_points" in result
        print("QC result validation passed")
        
        return True
        
    except Exception as e:
        print(f"QC test failed: {e}")
        return False

def test_seabed2030():
    """Test Seabed 2030 adapter."""
    print("\nTesting Seabed 2030 adapter...")
    
    try:
        from adapters.seabed2030_adapter import Seabed2030Adapter
        
        # Test adapter initialization
        adapter = Seabed2030Adapter()
        print("Seabed2030Adapter initialized successfully")
        
        # Test payload building
        metadata = {
            "title": "Test Data",
            "description": "Test ocean mapping data",
            "sensor_type": "mbes",
            "quality_score": 0.95,
            "anomaly_count": 0,
            "bounds": {
                "min_lat": 40.0,
                "max_lat": 41.0,
                "min_lon": -74.0,
                "max_lon": -73.0
            }
        }
        
        # Create a dummy NetCDF file for testing
        test_nc_path = Path("test.nc")
        test_nc_path.touch()  # Create empty file
        
        payload = adapter.build_payload(metadata, test_nc_path)
        print("Payload built successfully")
        
        # Clean up
        test_nc_path.unlink()
        
        # Test dry run
        result = adapter.dry_run_upload(payload)
        print("Dry run upload completed")
        
        # Validate result structure
        assert "status" in result
        assert "validation" in result
        print("Seabed 2030 result validation passed")
        
        return True
        
    except Exception as e:
        print(f"Seabed 2030 test failed: {e}")
        return False

def test_data_files():
    """Test that mock data files exist."""
    print("\nTesting data files...")
    
    try:
        data_files = [
            "data/mock/mock_mbes_ping.csv",
            "data/mock/mock_singlebeam.txt",
            "data/mock/sample_metadata.json"
        ]
        
        for file_path in data_files:
            if Path(file_path).exists():
                print(f"{file_path} exists")
            else:
                print(f"{file_path} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"Data files test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Open Ocean Mapper - Component Validation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_converter,
        test_qc,
        test_seabed2030,
        test_data_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("All tests passed! Open Ocean Mapper is ready.")
        return 0
    else:
        print("Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
