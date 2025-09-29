#!/usr/bin/env python3
"""
Open Ocean Mapper CLI Tool

Command-line interface for ocean mapping data processing.
Provides commands for conversion, quality control, and Seabed 2030 upload.

Usage:
    python cli/open_ocean_mapper.py convert --input data.csv --format netcdf --anonymize
    python cli/open_ocean_mapper.py qc --input data.csv
    python cli/open_ocean_mapper.py upload --payload manifest.json --dry-run
    python cli/open_ocean_mapper.py serve
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import click
import json
import yaml
from datetime import datetime

# Add src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    # Import modules directly
    import pipeline.converter as converter_module
    import qc.model_stub as qc_module
    import adapters.seabed2030_adapter as seabed_module
    import utils.logging as logging_module
    
    ConvertJob = converter_module.ConvertJob
    ConversionError = converter_module.ConversionError
    load_model = qc_module.load_model
    predict_anomalies = qc_module.predict_anomalies
    Seabed2030Adapter = seabed_module.Seabed2030Adapter
    setup_logging = logging_module.setup_logging
    get_logger = logging_module.get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Project root: {project_root}")
    print(f"Source path: {src_path}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="Open Ocean Mapper")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx, verbose, config):
    """Open Ocean Mapper - Transform ocean mapping data for Seabed 2030 compliance."""
    
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)
    
    # Load configuration
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config(config)
    ctx.obj['verbose'] = verbose
    
    logger.info("Open Ocean Mapper CLI started", verbose=verbose)


def load_config(config_path: Optional[str]) -> dict:
    """Load configuration from file."""
    if not config_path:
        # Look for default config files
        default_paths = [
            Path("config/config.yml"),
            Path("config/config_template.yml"),
            Path("~/.open-ocean-mapper/config.yml").expanduser()
        ]
        
        for path in default_paths:
            if path.exists():
                config_path = str(path)
                break
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f)
        except Exception as e:
            logger.warning("Failed to load config file", config_path=config_path, error=str(e))
    
    return {}


@cli.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True), 
              help='Input data file path')
@click.option('--sensor-type', '-s', 
              type=click.Choice(['mbes', 'sbes', 'lidar', 'singlebeam', 'auv']),
              default='mbes', help='Type of sensor data')
@click.option('--format', '-f', 
              type=click.Choice(['netcdf', 'bag', 'geotiff']),
              default='netcdf', help='Output format')
@click.option('--output', '-o', type=click.Path(), default='./out',
              help='Output directory')
@click.option('--anonymize', is_flag=True, default=True,
              help='Anonymize vessel data')
@click.option('--no-anonymize', is_flag=True, default=False,
              help='Disable anonymization')
@click.option('--overlay', is_flag=True, default=False,
              help='Add environmental overlays')
@click.option('--qc-mode', 
              type=click.Choice(['auto', 'manual', 'skip']),
              default='auto', help='Quality control mode')
@click.option('--config-file', type=click.Path(exists=True),
              help='Additional configuration file')
@click.pass_context
def convert(ctx, input, sensor_type, format, output, anonymize, no_anonymize, 
           overlay, qc_mode, config_file):
    """Convert ocean mapping data to standardized formats."""
    
    # Override anonymize if explicitly disabled
    if no_anonymize:
        anonymize = False
    
    # Load additional config if provided
    additional_config = {}
    if config_file:
        additional_config = load_config(config_file)
    
    try:
        logger.info("Starting conversion", 
                   input=input, 
                   sensor_type=sensor_type, 
                   output_format=format)
        
        # Create conversion job
        job = ConvertJob(
            input_path=input,
            sensor_type=sensor_type,
            output_format=format,
            anonymize=anonymize,
            add_overlay=overlay,
            qc_mode=qc_mode,
            output_dir=output
        )
        
        # Run conversion
        result = job.run()
        
        # Display results
        click.echo("\n" + "="*60)
        click.echo("CONVERSION COMPLETED SUCCESSFULLY")
        click.echo("="*60)
        click.echo(f"Input file: {input}")
        click.echo(f"Sensor type: {sensor_type.upper()}")
        click.echo(f"Output format: {format.upper()}")
        click.echo(f"Output directory: {output}")
        click.echo(f"Total points processed: {result['data_points_processed']:,}")
        click.echo(f"Quality score: {result['qc_results']['quality_score']:.3f}")
        click.echo(f"Anomalies found: {result['qc_results']['total_anomalies']}")
        click.echo(f"Processing time: {result['processing_time_seconds']:.2f}s")
        
        click.echo("\nOutput files:")
        for file_path in result['output_files']:
            click.echo(f"  - {file_path}")
        
        if result['anonymized']:
            click.echo("\n⚠️  Data has been anonymized")
        
        if result['overlay_applied']:
            click.echo("🌍 Environmental overlays applied")
        
        click.echo("\n✅ Conversion completed successfully!")
        
    except ConversionError as e:
        logger.error("Conversion failed", error=str(e))
        click.echo(f"\n❌ Conversion failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True),
              help='Input data file path')
@click.option('--model', '-m', type=click.Path(exists=True),
              help='ML model file path')
@click.option('--output', '-o', type=click.Path(),
              help='Output QC report file')
@click.option('--format', 
              type=click.Choice(['json', 'yaml', 'text']),
              default='text', help='Output format')
@click.pass_context
def qc(ctx, input, model, output, format):
    """Run quality control on ocean mapping data."""
    
    try:
        logger.info("Starting quality control", input=input)
        
        # Load data (simplified - in real implementation, parse the file)
        # For now, create mock data structure
        data = {
            "points": [],
            "metadata": {"sensor_type": "unknown"}
        }
        
        # Load ML model
        detector = load_model(model)
        
        # Run anomaly detection
        anomalies = predict_anomalies(data, model)
        
        # Display results
        click.echo("\n" + "="*60)
        click.echo("QUALITY CONTROL RESULTS")
        click.echo("="*60)
        click.echo(f"Input file: {input}")
        click.echo(f"Total points: {anomalies['total_points']:,}")
        click.echo(f"Anomalies found: {len(anomalies['anomalies'])}")
        click.echo(f"Confidence: {anomalies['confidence']:.3f}")
        click.echo(f"Anomaly rate: {anomalies['anomaly_rate']:.2%}")
        
        if anomalies['anomalies']:
            click.echo("\nAnomalies detected:")
            for i, anomaly in enumerate(anomalies['anomalies'][:10], 1):  # Show first 10
                click.echo(f"  {i}. {anomaly['description']}")
                click.echo(f"     Type: {anomaly['type']}, Severity: {anomaly['severity']}")
            
            if len(anomalies['anomalies']) > 10:
                click.echo(f"  ... and {len(anomalies['anomalies']) - 10} more")
        
        # Save report if output specified
        if output:
            report = {
                "timestamp": datetime.now().isoformat(),
                "input_file": input,
                "model_path": model,
                "results": anomalies
            }
            
            with open(output, 'w') as f:
                if format == 'json':
                    json.dump(report, f, indent=2)
                elif format == 'yaml':
                    yaml.dump(report, f, default_flow_style=False)
                else:
                    f.write(f"QC Report - {datetime.now().isoformat()}\n")
                    f.write(f"Input: {input}\n")
                    f.write(f"Anomalies: {len(anomalies['anomalies'])}\n")
                    f.write(f"Confidence: {anomalies['confidence']:.3f}\n")
            
            click.echo(f"\n📄 Report saved to: {output}")
        
        click.echo("\n✅ Quality control completed!")
        
    except Exception as e:
        logger.error("QC failed", error=str(e))
        click.echo(f"\n❌ Quality control failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--payload', '-p', type=click.Path(exists=True),
              help='Payload file path')
@click.option('--netcdf', '-n', type=click.Path(exists=True),
              help='NetCDF file path')
@click.option('--metadata', '-m', type=click.Path(exists=True),
              help='Metadata file path')
@click.option('--dry-run', is_flag=True, default=True,
              help='Perform dry-run upload (default)')
@click.option('--live', is_flag=True, default=False,
              help='Perform live upload (requires API credentials)')
@click.option('--output', '-o', type=click.Path(),
              help='Output directory for generated files')
@click.pass_context
def upload(ctx, payload, netcdf, metadata, dry_run, live, output):
    """Prepare and upload data to Seabed 2030."""
    
    if not payload and not netcdf:
        click.echo("❌ Either --payload or --netcdf must be specified", err=True)
        sys.exit(1)
    
    try:
        logger.info("Starting Seabed 2030 upload preparation")
        
        # Initialize adapter
        adapter = Seabed2030Adapter(ctx.obj['config'].get('seabed2030', {}))
        
        if payload:
            # Use existing payload
            with open(payload, 'r') as f:
                payload_data = json.load(f)
        else:
            # Generate payload from NetCDF file
            if not metadata:
                click.echo("❌ --metadata required when using --netcdf", err=True)
                sys.exit(1)
            
            with open(metadata, 'r') as f:
                metadata_dict = json.load(f)
            
            payload_data = adapter.build_payload(metadata_dict, Path(netcdf))
        
        # Perform upload (dry-run or live)
        if dry_run:
            result = adapter.dry_run_upload(payload_data)
            
            click.echo("\n" + "="*60)
            click.echo("SEABED 2030 DRY-RUN UPLOAD")
            click.echo("="*60)
            click.echo(f"Status: {result['status']}")
            click.echo(f"Validation: {result['validation']['status']}")
            
            if result['validation']['checks']:
                click.echo("\nValidation checks:")
                for check in result['validation']['checks']:
                    status_icon = "✅" if check['status'] == 'valid' else "❌"
                    click.echo(f"  {status_icon} {check['field']}: {check['message']}")
            
            if result['warnings']:
                click.echo("\n⚠️  Warnings:")
                for warning in result['warnings']:
                    click.echo(f"  - {warning}")
            
            if result['upload_simulation']['steps']:
                click.echo("\nSimulated upload steps:")
                for step in result['upload_simulation']['steps']:
                    click.echo(f"  ✅ {step['step']}: {step['message']}")
            
            click.echo(f"\nTotal duration: {result['upload_simulation']['total_duration_ms']}ms")
            
            if result['legal_notices']:
                click.echo("\n📋 Legal notices:")
                for notice in result['legal_notices']:
                    click.echo(f"  - {notice}")
            
            click.echo("\n✅ Dry-run upload completed!")
            
        else:
            click.echo("❌ Live upload not implemented in this version", err=True)
            click.echo("Use --dry-run to test upload preparation", err=True)
            sys.exit(1)
        
    except Exception as e:
        logger.error("Upload preparation failed", error=str(e))
        click.echo(f"\n❌ Upload preparation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--workers', default=1, help='Number of worker processes')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.pass_context
def serve(ctx, host, port, workers, reload):
    """Start the Open Ocean Mapper API server."""
    
    try:
        logger.info("Starting API server", host=host, port=port)
        
        import uvicorn
        from src.main import app
        
        click.echo(f"\n🚀 Starting Open Ocean Mapper API server...")
        click.echo(f"   Host: {host}")
        click.echo(f"   Port: {port}")
        click.echo(f"   Workers: {workers}")
        click.echo(f"   Reload: {reload}")
        click.echo(f"\n📖 API Documentation: http://{host}:{port}/docs")
        click.echo(f"🔍 Health Check: http://{host}:{port}/health")
        click.echo(f"\nPress Ctrl+C to stop the server")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        click.echo("\n\n👋 Server stopped")
    except Exception as e:
        logger.error("Server failed to start", error=str(e))
        click.echo(f"\n❌ Server failed to start: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True),
              help='Input data file path')
@click.option('--sensor-type', '-s', 
              type=click.Choice(['mbes', 'sbes', 'lidar', 'singlebeam', 'auv']),
              default='mbes', help='Type of sensor data')
@click.option('--output', '-o', type=click.Path(), default='./out',
              help='Output directory')
@click.pass_context
def demo(ctx, input, sensor_type, output):
    """Run end-to-end demo: convert -> qc -> upload dry-run."""
    
    try:
        logger.info("Starting end-to-end demo")
        
        click.echo("\n" + "="*60)
        click.echo("OPEN OCEAN MAPPER - END-TO-END DEMO")
        click.echo("="*60)
        
        # Step 1: Convert
        click.echo("\n🔄 Step 1: Converting data...")
        ctx.invoke(convert, 
                  input=input, 
                  sensor_type=sensor_type, 
                  format='netcdf',
                  output=output,
                  anonymize=True,
                  overlay=False,
                  qc_mode='auto')
        
        # Step 2: QC
        click.echo("\n🔍 Step 2: Running quality control...")
        ctx.invoke(qc, input=input, output=f"{output}/qc_report.json")
        
        # Step 3: Upload preparation
        click.echo("\n📤 Step 3: Preparing Seabed 2030 upload...")
        
        # Create mock metadata for upload
        metadata = {
            "title": f"Demo {sensor_type.upper()} Data",
            "description": "Demo ocean mapping data for testing",
            "sensor_type": sensor_type,
            "quality_score": 0.95,
            "anomaly_count": 0,
            "bounds": {
                "min_lat": 40.0,
                "max_lat": 41.0,
                "min_lon": -74.0,
                "max_lon": -73.0
            }
        }
        
        # Find the generated NetCDF file
        output_path = Path(output)
        netcdf_files = list(output_path.glob("*.nc"))
        
        if netcdf_files:
            netcdf_file = netcdf_files[0]
            ctx.invoke(upload, netcdf=str(netcdf_file), metadata=None, dry_run=True)
        else:
            click.echo("⚠️  No NetCDF file found for upload preparation")
        
        click.echo("\n" + "="*60)
        click.echo("🎉 DEMO COMPLETED SUCCESSFULLY!")
        click.echo("="*60)
        click.echo(f"All outputs saved to: {output}")
        click.echo("\nNext steps:")
        click.echo("  1. Review the generated files")
        click.echo("  2. Check the QC report")
        click.echo("  3. Configure API credentials for live upload")
        click.echo("  4. Run 'open-ocean-mapper serve' to start the API")
        
    except Exception as e:
        logger.error("Demo failed", error=str(e))
        click.echo(f"\n❌ Demo failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
