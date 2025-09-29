# Mock Data Directory

This directory contains sample ocean mapping data files for testing and demonstration purposes.

## Files

### `mock_mbes_ping.csv`
- **Format**: CSV
- **Sensor Type**: Multi-Beam Echo Sounder (MBES)
- **Description**: Simulated MBES ping data with 51 data points
- **Columns**:
  - `timestamp`: ISO 8601 timestamp
  - `latitude`: Latitude in decimal degrees (WGS84)
  - `longitude`: Longitude in decimal degrees (WGS84)
  - `depth`: Water depth in meters
  - `beam_angle`: Beam angle in degrees
  - `quality`: Data quality score (0-100)
  - `intensity`: Acoustic intensity in dB
  - `backscatter`: Backscatter strength in dB

### `mock_singlebeam.txt`
- **Format**: Text file with space-separated values
- **Sensor Type**: Single-Beam Echo Sounder (SBES)
- **Description**: Simulated single-beam data with 31 data points
- **Columns**:
  - `timestamp`: ISO 8601 timestamp
  - `latitude`: Latitude in decimal degrees (WGS84)
  - `longitude`: Longitude in decimal degrees (WGS84)
  - `depth`: Water depth in meters
  - `quality`: Data quality score (0-100)
  - `heading`: Vessel heading in degrees
  - `pitch`: Vessel pitch in degrees
  - `roll`: Vessel roll in degrees
  - `velocity`: Vessel velocity in knots

### `sample_metadata.json`
- **Format**: JSON
- **Description**: Sample metadata file containing survey information
- **Contents**:
  - Survey identification and vessel information
  - Spatial and temporal bounds
  - Data quality metrics
  - Processing information
  - Contact and licensing details

## Usage

These files can be used for:

1. **Testing the conversion pipeline**:
   ```bash
   python cli/open_ocean_mapper.py convert -i data/mock/mock_mbes_ping.csv -s mbes -f netcdf
   ```

2. **Running quality control**:
   ```bash
   python cli/open_ocean_mapper.py qc -i data/mock/mock_mbes_ping.csv
   ```

3. **Testing Seabed 2030 upload preparation**:
   ```bash
   python cli/open_ocean_mapper.py upload -n output.nc -m data/mock/sample_metadata.json --dry-run
   ```

4. **Running end-to-end demo**:
   ```bash
   python cli/open_ocean_mapper.py demo -i data/mock/mock_mbes_ping.csv -s mbes
   ```

## Data Characteristics

### MBES Data (`mock_mbes_ping.csv`)
- **Spatial Coverage**: New York Harbor area (40.71°N, 74.00°W)
- **Depth Range**: 10.5m to 223.4m
- **Beam Angles**: 0° to 90°
- **Quality Scores**: 1 to 95
- **Temporal Span**: 50 seconds

### SBES Data (`mock_singlebeam.txt`)
- **Spatial Coverage**: Same area as MBES data
- **Depth Range**: 10.5m to 96.7m
- **Vessel Motion**: Includes heading, pitch, roll, and velocity
- **Quality Scores**: 4 to 95
- **Temporal Span**: 30 seconds

## Notes

- All data is simulated and should not be used for navigation or scientific purposes
- Coordinates are in WGS84 datum
- Timestamps are in UTC
- Depth values are positive (below sea level)
- Quality scores are arbitrary and for demonstration only

## File Formats

The mock data demonstrates various input formats that the Open Ocean Mapper can process:

- **CSV**: Comma-separated values with headers
- **TXT**: Space-separated values with comments
- **JSON**: Structured metadata

These formats represent common ways ocean mapping data is stored and shared in the industry.
