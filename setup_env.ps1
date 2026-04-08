# Python 3.8+  virtual environment setup script
#  PowerShell script for setting up Python development environment

Write-Host "=== Python Development Environment Setup ===" -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Virtual environment created successfully" -ForegroundColor Green
    } else {
        Write-Host "Error creating virtual environment" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Cyan
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Requirements installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Error installing requirements" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "requirements.txt not found, skipping package installation" -ForegroundColor Yellow
}

# Create initial source file if src directory is empty
if ((Get-ChildItem "src" -File).Count -eq 0) {
    Write-Host "Creating initial source file..." -ForegroundColor Yellow
    $initialContent = @"
# Main module for Kanpaku Python Project

def hello_world() -> str:
    \"\"\"Return a greeting message.
    
    Returns:
        str: A friendly greeting message.
    \"\"\"
    return "Hello, World from Kanpaku Project!"

def main() -> None:
    \"\"\"Main entry point of the application.\"\"\"
    print(hello_world())

if __name__ == "__main__":
    main()
"@
    Set-Content -Path "src\main.py" -Value $initialContent
    Write-Host "Created src/main.py" -ForegroundColor Green
}

# Create initial test file if tests directory is empty
if ((Get-ChildItem "tests" -File).Count -eq 0) {
    Write-Host "Creating initial test file..." -ForegroundColor Yellow
    $testContent = @"
import pytest
from src.main import hello_world

def test_hello_world():
    \"\"\"Test the hello_world function.\"\"\"
    result = hello_world()
    assert result == "Hello, World from Kanpaku Project!"
    assert isinstance(result, str)

def test_main_output(capsys):
    \"\"\"Test the main function output.\"\"\"
    from src.main import main
    main()
    captured = capsys.readouterr()
    assert "Hello, World from Kanpaku Project!" in captured.out
"@
    Set-Content -Path "tests\test_main.py" -Value $testContent
    Write-Host "Created tests/test_main.py" -ForegroundColor Green
}

Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Activate the virtual environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Run tests: pytest" -ForegroundColor White
Write-Host "3. Format code: black src/" -ForegroundColor White
Write-Host "4. Check linting: flake8 src/" -ForegroundColor White
Write-Host "5. Type check: mypy src/" -ForegroundColor White
