"""
Tests for the quality control module.

Tests both deterministic QC rules and ML anomaly detection.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from src.qc.rules import apply_qc_rules, _check_coordinate_range, _check_depth_range
from src.qc.model_stub import AnomalyDetector, predict_anomalies, validate_model_file


class TestQCRules:
    """Test deterministic QC rules."""
    
    def create_test_data(self, sensor_type="mbes"):
        """Create test data for QC rules testing."""
        if sensor_type == "mbes":
            return pd.DataFrame({
                'timestamp': ['2024-01-01T00:00:00Z', '2024-01-01T00:01:00Z', '2024-01-01T00:02:00Z'],
                'latitude': [40.7128, 40.7130, 40.7132],
                'longitude': [-74.0060, -74.0058, -74.0056],
                'depth': [10.5, 12.3, 15.7],
                'beam_angle': [0.0, 5.0, 10.0],
                'quality': [95, 87, 92]
            })
        elif sensor_type == "sbes":
            return pd.DataFrame({
                'timestamp': ['2024-01-01T00:00:00Z', '2024-01-01T00:01:00Z'],
                'latitude': [40.7128, 40.7130],
                'longitude': [-74.0060, -74.0058],
                'depth': [10.5, 12.3],
                'quality': [95, 87],
                'heading': [180.0, 185.0],
                'pitch': [2.0, 1.5],
                'roll': [0.5, 0.8]
            })
        elif sensor_type == "lidar":
            return pd.DataFrame({
                'timestamp': ['2024-01-01T00:00:00Z', '2024-01-01T00:01:00Z'],
                'latitude': [40.7128, 40.7130],
                'longitude': [-74.0060, -74.0058],
                'elevation': [5.2, 7.8],
                'intensity': [150, 200],
                'classification': [1, 2]
            })
    
    def test_apply_qc_rules_mbes_success(self):
        """Test successful QC rules application for MBES data."""
        df = self.create_test_data("mbes")
        data = {"points": df.to_dict('records')}
        
        result = apply_qc_rules(data, "mbes")
        
        assert result['status'] == 'completed'
        assert result['quality_score'] > 0
        assert 'anomalies' in result
        assert 'rules_applied' in result
        assert 'statistics' in result
        assert len(result['rules_applied']) > 0
    
    def test_apply_qc_rules_sbes_success(self):
        """Test successful QC rules application for SBES data."""
        df = self.create_test_data("sbes")
        data = {"points": df.to_dict('records')}
        
        result = apply_qc_rules(data, "sbes")
        
        assert result['status'] == 'completed'
        assert result['quality_score'] > 0
        assert 'anomalies' in result
        assert 'rules_applied' in result
        assert 'statistics' in result
    
    def test_apply_qc_rules_lidar_success(self):
        """Test successful QC rules application for LiDAR data."""
        df = self.create_test_data("lidar")
        data = {"points": df.to_dict('records')}
        
        result = apply_qc_rules(data, "lidar")
        
        assert result['status'] == 'completed'
        assert result['quality_score'] > 0
        assert 'anomalies' in result
        assert 'rules_applied' in result
        assert 'statistics' in result
    
    def test_apply_qc_rules_no_data(self):
        """Test QC rules with no data."""
        data = {"points": []}
        
        result = apply_qc_rules(data, "mbes")
        
        assert result['status'] == 'no_data'
        assert result['quality_score'] == 0.0
        assert result['total_points'] == 0
    
    def test_apply_qc_rules_invalid_sensor_type(self):
        """Test QC rules with invalid sensor type."""
        df = self.create_test_data("mbes")
        data = {"points": df.to_dict('records')}
        
        result = apply_qc_rules(data, "invalid")
        
        # Should fall back to generic rules
        assert result['status'] == 'completed'
        assert result['quality_score'] > 0
    
    def test_coordinate_range_check_valid(self):
        """Test coordinate range check with valid data."""
        df = pd.DataFrame({
            'latitude': [40.0, 50.0, 60.0],
            'longitude': [-100.0, -80.0, -60.0]
        })
        
        anomalies = _check_coordinate_range(df, 'latitude', -90, 90)
        assert len(anomalies) == 0
        
        anomalies = _check_coordinate_range(df, 'longitude', -180, 180)
        assert len(anomalies) == 0
    
    def test_coordinate_range_check_invalid(self):
        """Test coordinate range check with invalid data."""
        df = pd.DataFrame({
            'latitude': [40.0, 95.0, 60.0],  # 95.0 is invalid
            'longitude': [-100.0, -200.0, -60.0]  # -200.0 is invalid
        })
        
        anomalies = _check_coordinate_range(df, 'latitude', -90, 90)
        assert len(anomalies) == 1
        assert anomalies[0]['type'] == 'coordinate_range'
        assert anomalies[0]['severity'] == 'high'
        
        anomalies = _check_coordinate_range(df, 'longitude', -180, 180)
        assert len(anomalies) == 1
        assert anomalies[0]['type'] == 'coordinate_range'
    
    def test_depth_range_check_valid(self):
        """Test depth range check with valid data."""
        df = pd.DataFrame({
            'depth': [10.0, 100.0, 1000.0]
        })
        
        anomalies = _check_depth_range(df, 'depth', 0, 12000)
        assert len(anomalies) == 0
    
    def test_depth_range_check_invalid(self):
        """Test depth range check with invalid data."""
        df = pd.DataFrame({
            'depth': [10.0, -5.0, 15000.0]  # -5.0 and 15000.0 are invalid
        })
        
        anomalies = _check_depth_range(df, 'depth', 0, 12000)
        assert len(anomalies) == 2
        assert all(anomaly['type'] == 'depth_range' for anomaly in anomalies)
        assert all(anomaly['severity'] == 'high' for anomaly in anomalies)


class TestAnomalyDetector:
    """Test ML anomaly detection."""
    
    def create_test_data(self):
        """Create test data for anomaly detection."""
        return {
            "points": [
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.5},
                {"latitude": 40.7130, "longitude": -74.0058, "depth": 12.3},
                {"latitude": 40.7132, "longitude": -74.0056, "depth": 15.7},
                {"latitude": 40.7134, "longitude": -74.0054, "depth": 200.0},  # Anomaly
                {"latitude": 40.7136, "longitude": -74.0052, "depth": 18.2}
            ]
        }
    
    def test_anomaly_detector_initialization(self):
        """Test AnomalyDetector initialization."""
        detector = AnomalyDetector()
        
        assert detector.model_path is None
        assert detector.model_loaded is False
        assert detector.model_type == "deterministic_stub"
    
    def test_anomaly_detector_with_model_path(self):
        """Test AnomalyDetector with model path."""
        detector = AnomalyDetector("test_model.onnx")
        
        assert detector.model_path == "test_model.onnx"
        assert detector.model_loaded is False
    
    def test_load_model_success(self):
        """Test successful model loading."""
        detector = AnomalyDetector()
        
        result = detector.load_model()
        
        assert result is True
        assert detector.model_loaded is True
    
    def test_predict_anomalies_success(self):
        """Test successful anomaly prediction."""
        detector = AnomalyDetector()
        data = self.create_test_data()
        
        result = detector.predict(data)
        
        assert 'anomalies' in result
        assert 'confidence' in result
        assert 'total_points' in result
        assert 'anomaly_rate' in result
        assert 'model_type' in result
        assert 'detection_method' in result
        
        assert result['total_points'] == 5
        assert result['model_type'] == "deterministic_stub"
        assert result['detection_method'] == "deterministic_rules"
    
    def test_predict_anomalies_empty_data(self):
        """Test anomaly prediction with empty data."""
        detector = AnomalyDetector()
        data = {"points": []}
        
        result = detector.predict(data)
        
        assert result['anomalies'] == []
        assert result['confidence'] == 0.0
        assert result['total_points'] == 0
    
    def test_predict_anomalies_with_depth_jump(self):
        """Test anomaly detection with depth jump."""
        detector = AnomalyDetector()
        data = self.create_test_data()
        
        result = detector.predict(data)
        
        # Should detect the depth jump anomaly
        assert len(result['anomalies']) > 0
        assert any(anomaly['type'] == 'depth_jump' for anomaly in result['anomalies'])
    
    def test_predict_anomalies_with_unrealistic_depth(self):
        """Test anomaly detection with unrealistic depth."""
        detector = AnomalyDetector()
        data = {
            "points": [
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.5},
                {"latitude": 40.7130, "longitude": -74.0058, "depth": -5.0},  # Invalid depth
                {"latitude": 40.7132, "longitude": -74.0056, "depth": 15000.0}  # Invalid depth
            ]
        }
        
        result = detector.predict(data)
        
        # Should detect unrealistic depth anomalies
        assert len(result['anomalies']) > 0
        assert any(anomaly['type'] == 'unrealistic_depth' for anomaly in result['anomalies'])
    
    def test_predict_anomalies_with_duplicate_coordinates(self):
        """Test anomaly detection with duplicate coordinates."""
        detector = AnomalyDetector()
        data = {
            "points": [
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.5},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.6},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.7},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.8},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.9},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 11.0},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 11.1},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 11.2},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 11.3},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 11.4},
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 11.5},  # 11th duplicate
                {"latitude": 40.7130, "longitude": -74.0058, "depth": 12.3}
            ]
        }
        
        result = detector.predict(data)
        
        # Should detect coordinate duplicate anomaly
        assert len(result['anomalies']) > 0
        assert any(anomaly['type'] == 'coordinate_duplicate' for anomaly in result['anomalies'])


class TestPredictAnomaliesFunction:
    """Test the predict_anomalies function."""
    
    def test_predict_anomalies_function_success(self):
        """Test predict_anomalies function."""
        data = {
            "points": [
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.5},
                {"latitude": 40.7130, "longitude": -74.0058, "depth": 12.3}
            ]
        }
        
        result = predict_anomalies(data)
        
        assert 'anomalies' in result
        assert 'confidence' in result
        assert 'total_points' in result
        assert result['total_points'] == 2
    
    def test_predict_anomalies_function_with_model_path(self):
        """Test predict_anomalies function with model path."""
        data = {
            "points": [
                {"latitude": 40.7128, "longitude": -74.0060, "depth": 10.5}
            ]
        }
        
        result = predict_anomalies(data, "test_model.onnx")
        
        assert 'anomalies' in result
        assert 'confidence' in result
        assert 'total_points' in result


class TestModelValidation:
    """Test model file validation."""
    
    def test_validate_model_file_valid_extensions(self):
        """Test model validation with valid extensions."""
        valid_extensions = ['.onnx', '.pb', '.h5', '.pkl', '.joblib']
        
        for ext in valid_extensions:
            # Mock file existence
            with patch('os.path.exists', return_value=True), \
                 patch('os.path.getsize', return_value=1024):
                
                result = validate_model_file(f"test_model{ext}")
                assert result is True
    
    def test_validate_model_file_invalid_extension(self):
        """Test model validation with invalid extension."""
        with patch('os.path.exists', return_value=True):
            result = validate_model_file("test_model.txt")
            assert result is False
    
    def test_validate_model_file_nonexistent(self):
        """Test model validation with non-existent file."""
        with patch('os.path.exists', return_value=False):
            result = validate_model_file("nonexistent.onnx")
            assert result is False
    
    def test_validate_model_file_empty(self):
        """Test model validation with empty file."""
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=0):
            
            result = validate_model_file("empty.onnx")
            assert result is False


if __name__ == '__main__':
    pytest.main([__file__])
