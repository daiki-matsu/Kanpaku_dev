# Kanpaku Python Project

Python development environment with modern tooling and best practices.

## Project Structure

```
kanpaku_py/
|
|-- src/              # Source code
|-- tests/            # Test files
|-- docs/             # Documentation
|-- requirements.txt  # Dependencies
|-- pyproject.toml    # Project configuration
|-- .gitignore        # Git ignore rules
|-- setup_env.ps1     # Virtual environment setup script
```

## Getting Started

### 1. Set up Virtual Environment

```powershell
# Run the setup script
.\setup_env.ps1

# Or manually:
python -m venv venv
.\venv\Scripts\Activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Development Tools

This project includes several development tools:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pytest**: Testing framework
- **Coverage**: Test coverage

### Usage Examples

#### Code Formatting
```bash
black src/
```

#### Linting
```bash
flake8 src/
```

#### Type Checking
```bash
mypy src/
```

#### Running Tests
```bash
pytest
```

#### Test Coverage
```bash
pytest --cov=src --cov-report=html
```

## Development Workflow

1. Make changes to source code in `src/`
2. Run tests: `pytest`
3. Format code: `black src/`
4. Check linting: `flake8 src/`
5. Type check: `mypy src/`

## Python Version

This project supports Python 3.8 and above.

## License

MIT License
