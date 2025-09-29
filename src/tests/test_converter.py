"""
Tests for the converter module.

Tests the core conversion pipeline including format parsing,
quality control, anonymization, and export functionality.
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

from src.pipeline.converter import ConvertJob, ConversionError
from src.pipeline.formats.mbes import parse_mbes_file, validate_mbes_format
from src.pipeline.formats.sbet import parse_sbet_file, validate_sbet_format
from src.pipeline.formats.lidar import parse_lidar_file, validate_lidar_format


class TestConvertJob:
    """Test the ConvertJob class."""
    
    def test_convert_job_initialization(self):
        """Test ConvertJob initialization with valid parameters."""
        job = ConvertJob(
            input_path="test.csv",
            sensor_type="mbes",
            output_format="netcdf",
            anonymize=True,
            add_overlay=False,
            qc_mode="auto"
        )
        
        assert job.sensor_type == "mbes"
        assert job.output_format == "netcdf"
        assert job.anonymize is True
        assert job.add_overlay is False
        assert job.qc_mode == "auto"
    
    def test_convert_job_invalid_sensor_type(self):
        """Test ConvertJob with invalid sensor type."""
        with pytest.raises(ConversionError, match="Invalid sensor type"):
            ConvertJob(
                input_path="test.csv",
                sensor_type="invalid",
                output_format="netcdf"
            )
    
    def test_convert_job_invalid_output_format(self):
        """Test ConvertJob with invalid output format."""
        with pytest.raises(ConversionError, match="Invalid output format"):
            ConvertJob(
                input_path="test.csv",
                sensor_type="mbes",
                output_format="invalid"
            )
    
    def test_convert_job_invalid_qc_mode(self):
        """Test ConvertJob with invalid QC mode."""
        with pytest.raises(ConversionError, match="Invalid QC mode"):
            ConvertJob(
                input_path="test.csv",
                sensor_type="mbes",
                output_format="netcdf",
                qc_mode="invalid"
            )
    
    def test_convert_job_nonexistent_file(self):
        """Test ConvertJob with non-existent input file."""
        with pytest.raises(ConversionError, match="Input file not found"):
            ConvertJob(
                input_path="nonexistent.csv",
                sensor_type="mbes",
                output_format="netcdf"
            )


class TestMBESParser:
    """Test MBES data parser."""
    
    def create_mock_mbes_data(self):
        """Create mock MBES data for testing."""
        return pd.DataFrame({
            'timestamp': ['2024-01-01T00:00:00Z', '2024-01-01T00:01:00Z'],
            'latitude': [40.7128, 40.7130],
            'longitude': [-74.0060, -74.0058],
            'depth': [10.5, 12.3],
            'beam_angle': [0.0, 5.0],
            'quality': [95, 87],
            'intensity': [-45.2, -42.1]
        })
    
    def test_parse_mbes_file_success(self):
        """Test successful MBES file parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df = self.create_mock_mbes_data()
            df.to_csv(tmp_file.name, index=False)
            tmp_path = Path(tmp_file.name)
        
        try:
            result = parse_mbes_file(tmp_path)
            
            assert result['sensor_type'] == 'mbes'
            assert len(result['points']) == 2
            assert result['total_points'] == 2
            assert 'metadata' in result
            assert 'file_info' in result
            
            # Check first point
            point = result['points'][0]
            assert point['latitude'] == 40.7128
            assert point['longitude'] == -74.0060
            assert point['depth'] == 10.5
            
        finally:
            tmp_path.unlink()
    
    def test_parse_mbes_file_missing_columns(self):
        """Test MBES file parsing with missing required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df = pd.DataFrame({
                'timestamp': ['2024-01-01T00:00:00Z'],
                'latitude': [40.7128]
                # Missing longitude and depth
            })
            df.to_csv(tmp_file.name, index=False)
            tmp_path = Path(tmp_file.name)
        
        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                parse_mbes_file(tmp_path)
        finally:
            tmp_path.unlink()
    
    def test_validate_mbes_format_valid(self):
        """Test MBES format validation with valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df = self.create_mock_mbes_data()
            df.to_csv(tmp_file.name, index=False)
            tmp_path = Path(tmp_file.name)
        
        try:
            assert validate_mbes_format(tmp_path) is True
        finally:
            tmp_path.unlink()
    
    def test_validate_mbes_format_invalid(self):
        """Test MBES format validation with invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df = pd.DataFrame({
                'invalid_column': [1, 2, 3]
            })
            df.to_csv(tmp_file.name, index=False)
            tmp_path = Path(tmp_file.name)
        
        try:
            assert validate_mbes_format(tmp_path) is False
        finally:
            tmp_path.unlink()


class TestSBETParser:
    """Test SBES data parser."""
    
    def create_mock_sbet_data(self):
        """Create mock SBES data for testing."""
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
    
    def test_parse_sbet_file_success(self):
        """Test successful SBES file parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df = self.create_mock_sbet_data()
            df.to_csv(tmp_file.name, index=False)
            tmp_path = Path(tmp_file.name)
        
        try:
            result = parse_sbet_file(tmp_path)
            
            assert result['sensor_type'] == 'sbes'
            assert len(result['points']) == 2
            assert result['total_points'] == 2
            
            # Check first point
            point = result['points'][0]
            assert point['latitude'] == 40.7128
            assert point['longitude'] == -74.0060
            assert point['depth'] == 10.5
            assert point['heading'] == 180.0
            
        finally:
            tmp_path.unlink()


class TestLiDARParser:
    """Test LiDAR data parser."""
    
    def create_mock_lidar_data(self):
        """Create mock LiDAR data for testing."""
        return pd.DataFrame({
            'timestamp': ['2024-01-01T00:00:00Z', '2024-01-01T00:01:00Z'],
            'latitude': [40.7128, 40.7130],
            'longitude': [-74.0060, -74.0058],
            'elevation': [5.2, 7.8],
            'intensity': [150, 200],
            'classification': [1, 2],
            'return_number': [1, 1],
            'number_of_returns': [1, 1]
        })
    
    def test_parse_lidar_file_success(self):
        """Test successful LiDAR file parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df = self.create_mock_lidar_data()
            df.to_csv(tmp_file.name, index=False)
            tmp_path = Path(tmp_file.name)
        
        try:
            result = parse_lidar_file(tmp_path)
            
            assert result['sensor_type'] == 'lidar'
            assert len(result['points']) == 2
            assert result['total_points'] == 2
            
            # Check first point
            point = result['points'][0]
            assert point['latitude'] == 40.7128
            assert point['longitude'] == -74.0060
            assert point['elevation'] == 5.2
            assert point['intensity'] == 150
            
        finally:
            tmp_path.unlink()


class TestConversionPipeline:
    """Test the complete conversion pipeline."""
    
    @patch('src.pipeline.converter.parse_mbes_file')
    @patch('src.pipeline.converter.apply_qc_rules')
    @patch('src.pipeline.converter.anonymize_data')
    @patch('src.pipeline.converter.reproject_to_wgs84')
    @patch('src.pipeline.converter.create_bathymetric_surface')
    @patch('src.pipeline.converter.apply_overlay')
    @patch('src.pipeline.converter.export_to_netcdf')
    def test_conversion_pipeline_success(self, mock_export, mock_overlay, mock_surface, 
                                       mock_reproject, mock_anonymize, mock_qc, mock_parse):
        """Test successful conversion pipeline execution."""
        
        # Setup mocks
        mock_parse.return_value = {
            'points': [{'latitude': 40.7128, 'longitude': -74.0060, 'depth': 10.5}],
            'metadata': {'sensor_type': 'mbes'}
        }
        mock_qc.return_value = {
            'status': 'completed',
            'quality_score': 0.95,
            'anomalies': [],
            'total_points': 1
        }
        mock_anonymize.return_value = {
            'points': [{'latitude': 40.7128, 'longitude': -74.0060, 'depth': 10.5}],
            'metadata': {'anonymization': {'applied': True}}
        }
        mock_reproject.return_value = {
            'points': [{'latitude': 40.7128, 'longitude': -74.0060, 'depth': 10.5}],
            'metadata': {'coordinate_system': 'WGS84'}
        }
        mock_surface.return_value = {
            'points': [{'latitude': 40.7128, 'longitude': -74.0060, 'depth': 10.5}],
            'metadata': {'surface_generation': {'method': 'scipy'}}
        }
        mock_overlay.return_value = {
            'points': [{'latitude': 40.7128, 'longitude': -74.0060, 'depth': 10.5}],
            'metadata': {'environmental_overlay': {'applied': False}}
        }
        mock_export.return_value = ['/app/out/test.nc']
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write("timestamp,latitude,longitude,depth\n")
            tmp_file.write("2024-01-01T00:00:00Z,40.7128,-74.0060,10.5\n")
            tmp_path = Path(tmp_file.name)
        
        try:
            # Create conversion job
            job = ConvertJob(
                input_path=tmp_path,
                sensor_type="mbes",
                output_format="netcdf",
                anonymize=True,
                add_overlay=False,
                qc_mode="auto",
                output_dir="./out"
            )
            
            # Run conversion
            result = job.run()
            
            # Verify result
            assert result['status'] == 'completed'
            assert result['sensor_type'] == 'mbes'
            assert result['output_format'] == 'netcdf'
            assert result['anonymized'] is True
            assert result['overlay_applied'] is False
            assert len(result['output_files']) == 1
            assert result['output_files'][0] == '/app/out/test.nc'
            
            # Verify all mocks were called
            mock_parse.assert_called_once()
            mock_qc.assert_called_once()
            mock_anonymize.assert_called_once()
            mock_reproject.assert_called_once()
            mock_surface.assert_called_once()
            mock_overlay.assert_called_once()
            mock_export.assert_called_once()
            
        finally:
            tmp_path.unlink()


class TestErrorHandling:
    """Test error handling in the conversion pipeline."""
    
    @patch('src.pipeline.converter.parse_mbes_file')
    def test_conversion_pipeline_parse_error(self, mock_parse):
        """Test conversion pipeline with parsing error."""
        
        # Setup mock to raise exception
        mock_parse.side_effect = Exception("Parse error")
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write("invalid,data\n")
            tmp_path = Path(tmp_file.name)
        
        try:
            # Create conversion job
            job = ConvertJob(
                input_path=tmp_path,
                sensor_type="mbes",
                output_format="netcdf"
            )
            
            # Run conversion and expect error
            with pytest.raises(ConversionError, match="Conversion failed"):
                job.run()
                
        finally:
            tmp_path.unlink()


if __name__ == '__main__':
    pytest.main([__file__])
