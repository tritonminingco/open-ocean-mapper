#!/bin/bash

# Open Ocean Mapper Demo Script
# This script demonstrates the complete ocean mapping data processing pipeline

set -e  # Exit on any error

echo "🌊 Open Ocean Mapper - End-to-End Demo"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create output directory
OUTPUT_DIR="./demo_output"
mkdir -p "$OUTPUT_DIR"
print_status "Created output directory: $OUTPUT_DIR"

# Install dependencies if needed
print_status "Checking dependencies..."
if ! python3 -c "import click, pandas, numpy" &> /dev/null; then
    print_warning "Installing required dependencies..."
    pip install -e .
fi

# Demo 1: MBES Data Conversion
echo ""
echo "🔄 Demo 1: MBES Data Conversion"
echo "-------------------------------"

print_status "Converting MBES data to NetCDF format..."
python3 cli/open_ocean_mapper.py convert \
    --input data/mock/mock_mbes_ping.csv \
    --sensor-type mbes \
    --format netcdf \
    --output "$OUTPUT_DIR/mbes_conversion" \
    --anonymize \
    --qc-mode auto

if [ $? -eq 0 ]; then
    print_success "MBES conversion completed successfully"
else
    print_error "MBES conversion failed"
    exit 1
fi

# Demo 2: SBES Data Conversion
echo ""
echo "🔄 Demo 2: SBES Data Conversion"
echo "-------------------------------"

print_status "Converting SBES data to BAG format..."
python3 cli/open_ocean_mapper.py convert \
    --input data/mock/mock_singlebeam.txt \
    --sensor-type sbes \
    --format bag \
    --output "$OUTPUT_DIR/sbes_conversion" \
    --anonymize \
    --qc-mode auto

if [ $? -eq 0 ]; then
    print_success "SBES conversion completed successfully"
else
    print_error "SBES conversion failed"
    exit 1
fi

# Demo 3: Quality Control
echo ""
echo "🔍 Demo 3: Quality Control Analysis"
echo "-----------------------------------"

print_status "Running quality control on MBES data..."
python3 cli/open_ocean_mapper.py qc \
    --input data/mock/mock_mbes_ping.csv \
    --output "$OUTPUT_DIR/qc_report.json" \
    --format json

if [ $? -eq 0 ]; then
    print_success "Quality control completed successfully"
else
    print_error "Quality control failed"
    exit 1
fi

# Demo 4: Seabed 2030 Upload Preparation
echo ""
echo "📤 Demo 4: Seabed 2030 Upload Preparation"
echo "------------------------------------------"

# Find the generated NetCDF file
NETCDF_FILE=$(find "$OUTPUT_DIR/mbes_conversion" -name "*.nc" | head -1)

if [ -n "$NETCDF_FILE" ]; then
    print_status "Preparing Seabed 2030 upload with file: $NETCDF_FILE"
    python3 cli/open_ocean_mapper.py upload \
        --netcdf "$NETCDF_FILE" \
        --metadata data/mock/sample_metadata.json \
        --dry-run \
        --output "$OUTPUT_DIR/seabed2030_prep"
    
    if [ $? -eq 0 ]; then
        print_success "Seabed 2030 upload preparation completed successfully"
    else
        print_error "Seabed 2030 upload preparation failed"
        exit 1
    fi
else
    print_warning "No NetCDF file found for Seabed 2030 upload preparation"
fi

# Demo 5: End-to-End Pipeline
echo ""
echo "🎯 Demo 5: Complete End-to-End Pipeline"
echo "----------------------------------------"

print_status "Running complete end-to-end pipeline..."
python3 cli/open_ocean_mapper.py demo \
    --input data/mock/mock_mbes_ping.csv \
    --sensor-type mbes \
    --output "$OUTPUT_DIR/complete_demo"

if [ $? -eq 0 ]; then
    print_success "Complete end-to-end pipeline completed successfully"
else
    print_error "Complete end-to-end pipeline failed"
    exit 1
fi

# Summary
echo ""
echo "📊 Demo Summary"
echo "==============="
echo ""

print_status "Output files generated in: $OUTPUT_DIR"
echo ""

# List generated files
if [ -d "$OUTPUT_DIR" ]; then
    print_status "Generated files:"
    find "$OUTPUT_DIR" -type f -name "*.nc" -o -name "*.bag" -o -name "*.tif" -o -name "*.json" -o -name "*.txt" | while read -r file; do
        echo "  - $file"
    done
fi

echo ""
print_success "All demos completed successfully! 🎉"
echo ""
echo "Next steps:"
echo "  1. Review the generated files in $OUTPUT_DIR"
echo "  2. Check the QC report for data quality metrics"
echo "  3. Examine the Seabed 2030 upload preparation results"
echo "  4. Start the API server with: python cli/open_ocean_mapper.py serve"
echo "  5. Open the web interface at: http://localhost:3000"
echo ""
echo "For more information, see the README.md file."
