# Okta CLI Installation Script for Windows
# This script installs the Okta CLI tool on Windows

param(
    [switch]$Dev,
    [string]$Method
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Okta CLI Installation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "Error: pyproject.toml not found. Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

# Function to check if a command exists
function Test-Command {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Function to install with pip
function Install-WithPip {
    param([bool]$Editable)

    Write-Host "Installing with pip..." -ForegroundColor Green
    if ($Editable) {
        pip install -e .
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installation complete! Installed in editable mode." -ForegroundColor Yellow
            Write-Host "Note: Make sure your Python Scripts directory is in PATH to use the 'okta' command." -ForegroundColor Yellow
        }
    } else {
        pip install .
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installation complete!" -ForegroundColor Green
            Write-Host "Note: Make sure your Python Scripts directory is in PATH to use the 'okta' command." -ForegroundColor Yellow
        }
    }
}

# Function to install with pipx
function Install-WithPipx {
    Write-Host "Installing with pipx..." -ForegroundColor Green
    pipx install .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Installation complete! The 'okta' command is now available globally." -ForegroundColor Green
    }
}

# Function to install with uv
function Install-WithUv {
    param([bool]$Editable)

    Write-Host "Installing with uv..." -ForegroundColor Green
    if ($Editable) {
        uv pip install -e .
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installation complete! Installed in editable mode." -ForegroundColor Yellow
            Write-Host "Note: Activate your virtual environment to use the 'okta' command." -ForegroundColor Yellow
        }
    } else {
        uv tool install .
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installation complete! The 'okta' command is now available globally." -ForegroundColor Green
        }
    }
}

# Check for Python
if (-not (Test-Command python)) {
    Write-Host "Error: Python not found. Please install Python 3.13 or higher from python.org" -ForegroundColor Red
    exit 1
}

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "Found $pythonVersion" -ForegroundColor Gray

# Handle installation based on parameters
if ($Dev) {
    Write-Host "Installing in development mode..." -ForegroundColor Yellow
    if (Test-Command uv) {
        Install-WithUv -Editable $true
    } else {
        Write-Host "uv not found. Installing with pip..." -ForegroundColor Yellow
        Install-WithPip -Editable $true
    }
} elseif ($Method) {
    switch ($Method.ToLower()) {
        "uv" {
            if (Test-Command uv) {
                uv tool install .
            } else {
                Write-Host "Error: uv not found. Please install uv first: https://github.com/astral-sh/uv" -ForegroundColor Red
                exit 1
            }
        }
        "pipx" {
            if (Test-Command pipx) {
                Install-WithPipx
            } else {
                Write-Host "Error: pipx not found. Please install pipx first: pip install pipx" -ForegroundColor Red
                exit 1
            }
        }
        "pip" {
            if (Test-Command pip) {
                Install-WithPip -Editable $false
            } else {
                Write-Host "Error: pip not found." -ForegroundColor Red
                exit 1
            }
        }
        default {
            Write-Host "Error: Unknown method '$Method'. Use: uv, pipx, or pip" -ForegroundColor Red
            exit 1
        }
    }
} else {
    # Auto-detect best installation method
    if (Test-Command uv) {
        Write-Host "Found uv package manager" -ForegroundColor Gray
        uv tool install .
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installation complete! The 'okta' command is now available globally." -ForegroundColor Green
        }
    } elseif (Test-Command pipx) {
        Write-Host "Found pipx" -ForegroundColor Gray
        Install-WithPipx
    } elseif (Test-Command pip) {
        Write-Host "Found pip" -ForegroundColor Gray
        Install-WithPip -Editable $false
    } else {
        Write-Host "Error: No suitable package manager found. Please install pip, pipx, or uv." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Testing installation..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Test the installation
if (Test-Command okta) {
    Write-Host "Success! The 'okta' command is available." -ForegroundColor Green
    Write-Host ""
    Write-Host "Try running: okta --help" -ForegroundColor White
} else {
    Write-Host "Installation completed, but 'okta' command not found in PATH." -ForegroundColor Yellow
    Write-Host "You may need to:" -ForegroundColor Yellow
    Write-Host "  1. Restart your PowerShell/Terminal" -ForegroundColor Yellow
    Write-Host "  2. Add Python Scripts directory to your PATH" -ForegroundColor Yellow
    Write-Host "  3. Or activate your virtual environment if using one" -ForegroundColor Yellow
}
