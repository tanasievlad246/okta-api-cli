# Okta API CLI

A powerful command-line interface for managing Okta users with local SQLite caching and multi-threaded synchronization.

## Features

- **User Management**: Full CRUD operations for Okta users
- **Local Caching**: SQLite database for offline access and faster queries
- **Multi-threaded Sync**: Efficient bulk synchronization using ThreadPoolExecutor
- **Dual-source Queries**: Fetch data from local database or Okta API
- **Pretty Output**: Rich formatted tables and progress indicators
- **Secure Configuration**: XDG-compliant config storage with file permissions

## Prerequisites

- Python 3.13 or higher
- Okta account with API access
- Okta API key (SSWS token)

## Quick Install

### Linux / macOS (One-liner)

```bash
curl -sSL https://raw.githubusercontent.com/tanasievlad246/okta-api-cli/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/tanasievlad246/okta-api-cli/main/install.ps1 | iex
```

## Installation

### Option 1: Using the Install Script (Recommended)

**Linux / macOS:**
```bash
git clone https://github.com/tanasievlad246/okta-api-cli.git
cd okta-api-cli
./install.sh
```

For development mode (editable install):
```bash
./install.sh --dev
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/tanasievlad246/okta-api-cli.git
cd okta-api-cli
.\install.ps1
```

For development mode:
```powershell
.\install.ps1 -Dev
```

### Option 2: Manual Installation

**With uv (recommended):**
```bash
uv tool install .
```

**With pipx:**
```bash
pipx install .
```

**With pip:**
```bash
pip install .
```

## Configuration

Before using the CLI, configure your Okta credentials:

```bash
okta config --okta-api-key YOUR_API_KEY --okta-org-url https://your-org.okta.com
```

The configuration is stored securely in `~/.config/okta-cli/config.json` with restricted file permissions (0600).

## Usage

### Sync Users

Sync all users from Okta to local database:

```bash
okta users sync
```

### Get User Information

Get user by ID from local database:
```bash
okta users get --id USER_ID
```

Get user by email from Okta API and sync to local database:
```bash
okta users get --email user@example.com --source api
```

### Update User Profile

Update user profile fields:
```bash
okta users update --id USER_ID --profile '{"firstName": "John", "lastName": "Doe"}'
```

### Delete User

Delete user by ID:
```bash
okta users delete --id USER_ID
```

Delete user by email:
```bash
okta users delete --email user@example.com
```

## Command Reference

| Command | Description |
|---------|-------------|
| `config` | Configure Okta API credentials |
| `users sync` | Sync all users from Okta to local database |
| `users get` | Get user information by ID or email |
| `users update` | Update user profile |
| `users delete` | Delete user from Okta and local database |

### Global Options

- `-v, --verbose`: Enable verbose logging (DEBUG level)

## Architecture

The CLI follows clean code principles with clear separation of concerns:

- **CLI Layer** (`cli/main.py`): Argument parsing and command routing
- **Business Logic** (`cli/users/`): User management operations
- **API Client** (`cli/okta/`): Okta API communication with pagination
- **Data Layer** (`cli/database/`): SQLite repository pattern
- **Utilities** (`cli/utils/`): Logging and helper functions

### Database Schema

- **users**: Core user data (id, status, timestamps)
- **user_profiles**: User profile information (name, email, phone)
- **user_types**: User type references

## Development

### Project Structure

```
okta-api-cli/
   cli/
       main.py             # Entry point
       config/             # Configuration management
       users/              # User operations
       okta/               # Okta API client
       database/           # SQLite repository
       utils/              # Logging and utilities
       exceptions.py       # Custom exceptions
       validation.py       # Pydantic models
   pyproject.toml          # Project configuration
   install.sh              # Linux/macOS install script
   install.ps1             # Windows install script
   README.md               # This file
```

### Running with Verbose Logging

```bash
okta -v users sync
```

Logs are written to `oktacli.log` in the current directory.

## Security

- API keys are stored with secure file permissions (0600)
- Configuration follows XDG Base Directory specification
- All HTTP requests include 30-second timeouts
- Input validation using Pydantic models

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please [open an issue](https://github.com/tanasievlad246/okta-api-cli/issues).
