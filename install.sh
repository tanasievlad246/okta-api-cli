#!/bin/bash
# Okta CLI Installation Script
# This script installs the Okta CLI tool on your system

set -e

echo "=========================================="
echo "Okta CLI Installation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

# Function to install with uv
install_with_uv() {
    echo -e "${GREEN}Installing with uv...${NC}"
    if [ "$1" == "--editable" ]; then
        uv pip install -e .
        echo -e "${YELLOW}Note: Installed in editable mode. Activate your virtual environment with 'source .venv/bin/activate' to use the 'okta' command.${NC}"
    else
        uv tool install .
        echo -e "${GREEN}Installation complete! The 'okta' command is now available globally.${NC}"
    fi
}

# Function to install with pipx
install_with_pipx() {
    echo -e "${GREEN}Installing with pipx...${NC}"
    pipx install .
    echo -e "${GREEN}Installation complete! The 'okta' command is now available globally.${NC}"
}

# Function to install with pip
install_with_pip() {
    echo -e "${GREEN}Installing with pip...${NC}"
    pip install .
    echo -e "${GREEN}Installation complete!${NC}"
}

# Check for installation method preference
if [ "$1" == "--dev" ] || [ "$1" == "-d" ]; then
    echo "Installing in development mode..."
    if command -v uv &> /dev/null; then
        install_with_uv --editable
    else
        echo -e "${RED}Error: uv not found. Please install uv first: https://github.com/astral-sh/uv${NC}"
        exit 1
    fi
elif [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dev, -d      Install in development mode (editable install with uv)"
    echo "  --method METHOD Install with specific method (uv|pipx|pip)"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "Without options, the script will automatically detect and use the best available tool."
    exit 0
elif [ "$1" == "--method" ]; then
    case "$2" in
        uv)
            if command -v uv &> /dev/null; then
                uv tool install .
            else
                echo -e "${RED}Error: uv not found. Please install uv first.${NC}"
                exit 1
            fi
            ;;
        pipx)
            if command -v pipx &> /dev/null; then
                install_with_pipx
            else
                echo -e "${RED}Error: pipx not found. Please install pipx first.${NC}"
                exit 1
            fi
            ;;
        pip)
            if command -v pip &> /dev/null; then
                install_with_pip
            else
                echo -e "${RED}Error: pip not found.${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}Error: Unknown method '$2'. Use: uv, pipx, or pip${NC}"
            exit 1
            ;;
    esac
else
    # Auto-detect best installation method
    if command -v uv &> /dev/null; then
        echo "Found uv package manager"
        uv tool install .
        echo -e "${GREEN}Installation complete! The 'okta' command is now available globally.${NC}"
    elif command -v pipx &> /dev/null; then
        echo "Found pipx"
        install_with_pipx
    elif command -v pip &> /dev/null; then
        echo "Found pip"
        install_with_pip
        echo -e "${YELLOW}Note: If you're using a virtual environment, make sure it's activated to use the 'okta' command.${NC}"
    else
        echo -e "${RED}Error: No suitable package manager found. Please install uv, pipx, or pip.${NC}"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Testing installation..."
echo "=========================================="

# Test the installation
if command -v okta &> /dev/null; then
    echo -e "${GREEN}Success! The 'okta' command is available.${NC}"
    echo ""
    echo "Try running: okta --help"
elif [ -f ".venv/bin/okta" ]; then
    echo -e "${YELLOW}The 'okta' command was installed in the virtual environment.${NC}"
    echo -e "${YELLOW}Activate it with: source .venv/bin/activate${NC}"
    echo ""
    echo "Or run directly: .venv/bin/okta --help"
else
    echo -e "${YELLOW}Installation completed, but 'okta' command not found in PATH.${NC}"
    echo "You may need to restart your terminal or add the installation directory to your PATH."
fi
