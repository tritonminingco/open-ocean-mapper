# Contributing to Open Ocean Mapper

Thank you for your interest in contributing to Open Ocean Mapper! This document provides guidelines for contributing to the project.

## Development Workflow

### Getting Started

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install dependencies:
   ```bash
   # Backend
   cd src && pip install -e .
   
   # Frontend
   cd frontend && npm install
   ```

### Commit Style

We follow conventional commits:
- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `test:` adding or updating tests
- `refactor:` code refactoring
- `ci:` CI/CD changes
- `chore:` maintenance tasks

Example: `feat: add MBES parser for Kongsberg format`

### Pull Request Process

1. Ensure all tests pass: `python -m pytest tests/`
2. Run linting: `./scripts/format.sh`
3. Update documentation if needed
4. Submit PR with clear description and test coverage

## Adding New Sonar Formats

### Checklist for New Format Support

1. **Sample File**: Add representative data file to `data/mock/`
2. **Parser Module**: Create parser in `src/pipeline/formats/`
3. **Unit Test**: Add tests in `src/tests/test_formats.py`
4. **Example Fixture**: Include in test fixtures
5. **NetCDF Mapping**: Document variable mapping in `docs/seabed2030.md`

### Parser Template

```python
# src/pipeline/formats/your_format.py
"""
Parser for [Format Name] sonar data.

Expected input fields:
- timestamp: ISO 8601 format
- latitude: decimal degrees
- longitude: decimal degrees
- depth: meters (positive down)
- quality: signal quality indicator
- beam_angle: degrees from nadir
"""

def parse_file(file_path: str) -> dict:
    """Parse [Format Name] file and return standardized data structure."""
    # Implementation here
    pass
```

### Testing Requirements

- Unit tests must cover happy path and error cases
- Include sample data validation
- Test NetCDF export compatibility
- Verify anonymization works correctly

## Adding New Overlays

### DeepSeaGuard Plugin Interface

1. **Plugin Class**: Inherit from `OverlayPlugin` base class
2. **Configuration**: Add overlay config to `config_template.yml`
3. **Documentation**: Update overlay documentation
4. **Tests**: Add overlay-specific tests

### Example Overlay

```python
# src/pipeline/overlay.py
class YourOverlayPlugin(OverlayPlugin):
    def apply(self, data: dict, config: dict) -> dict:
        """Apply environmental overlay to bathymetric data."""
        # Implementation here
        pass
```

## Code Quality Standards

### Python
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Document public functions with docstrings
- Maintain test coverage above 80%

### Frontend
- Use ESLint configuration
- Follow React best practices
- Include PropTypes or TypeScript types
- Test user interactions

### Documentation
- Update README for new features
- Include usage examples
- Document configuration options
- Add architecture diagrams for complex features

## Testing Guidelines

### Backend Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_converter.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
- Test end-to-end conversion pipeline
- Verify Docker Compose setup
- Test CLI commands with sample data

## Performance Considerations

- Profile conversion pipeline for large datasets
- Implement chunked processing for files >100MB
- Use multiprocessing for CPU-intensive operations
- Cache intermediate results when appropriate

## Security Guidelines

- Never commit API keys or credentials
- Use environment variables for sensitive config
- Validate all input data
- Follow OWASP guidelines for web security

## Release Process

1. Update version in `pyproject.toml` and `package.json`
2. Update CHANGELOG.md
3. Create release tag
4. Update documentation
5. Deploy to staging environment

## Getting Help

- Check existing issues and discussions
- Join our community chat (if available)
- Create detailed issue reports with reproduction steps
- Ask questions in discussions

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to Open Ocean Mapper!
