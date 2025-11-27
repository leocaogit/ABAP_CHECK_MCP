# ABAP Syntax Checker MCP Server

A Model Context Protocol (MCP) server that provides ABAP REPORT program syntax checking capabilities for IDEs like Claude Code and Kiro.

## Overview

This MCP server connects to SAP ERP systems via RFC protocol to perform native ABAP syntax checking. It enables AI assistants to validate ABAP code without requiring direct access to SAP GUI.

## Features

- ✅ ABAP REPORT program syntax validation
- ✅ Detailed error reporting with line numbers and descriptions
- ✅ RFC-based communication with SAP ERP systems
- ✅ Standard MCP protocol implementation
- ✅ Comprehensive logging and error handling

## Prerequisites

- Python 3.9 or higher
- SAP NetWeaver RFC SDK
- Access to an SAP ERP system with appropriate credentials
- `pyrfc` library (requires SAP NW RFC SDK)

## Quick Start

1. **Install SAP NetWeaver RFC SDK** (see detailed instructions in Installation section)
2. **Clone this repository:**
   ```bash
   git clone https://github.com/leocaogit/ABAP_CHECK_MCP.git
   cd ABAP_CHECK_MCP
   ```
3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure SAP connection:**
   ```bash
   cp config/config.example.json config.json
   # Edit config.json with your SAP credentials
   ```
5. **Deploy ABAP function module** (see `abap/DEPLOYMENT_GUIDE.md`)
6. **Test the server:**
   ```bash
   python -m src.main --config config.json
   ```

## Installation

### 1. Install SAP NetWeaver RFC SDK

The `pyrfc` library requires the SAP NetWeaver RFC SDK to be installed on your system.

**Download:**
- Visit the SAP Support Portal: https://support.sap.com/en/product/connectors/nwrfcsdk.html
- Download the appropriate version for your operating system (requires SAP S-user)

**Installation:**

**macOS:**
```bash
# Extract the SDK
unzip nwrfc750P_8-70002752.zip -d /usr/local/sap

# Set environment variables (add to ~/.zshrc or ~/.bash_profile)
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export DYLD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$DYLD_LIBRARY_PATH
```

**Linux:**
```bash
# Extract the SDK
unzip nwrfc750P_8-70002752.zip -d /usr/local/sap

# Set environment variables (add to ~/.bashrc)
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH
```

**Windows:**
```powershell
# Extract the SDK to C:\nwrfcsdk
# Add C:\nwrfcsdk\lib to your PATH environment variable
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Verify installation:**
```bash
python -c "from pyrfc import Connection; print('pyrfc installed successfully')"
```

## Configuration

The server can be configured using environment variables or a JSON configuration file.

### Option 1: Environment Variables

Copy the example environment file and edit it with your SAP credentials:

```bash
cp config/.env.example .env
```

Edit `.env`:

```bash
# SAP RFC Connection Configuration
SAP_HOST=your-sap-host.example.com
SAP_SYSNR=00
SAP_CLIENT=100
SAP_USER=your-username
SAP_PASSWORD=your-password

# Logging Configuration (optional)
LOG_LEVEL=INFO
```

### Option 2: Configuration File

Copy the example configuration file and edit it with your SAP credentials:

```bash
cp config/config.example.json config.json
```

Edit `config.json`:

```json
{
  "rfc": {
    "host": "your-sap-host.example.com",
    "sysnr": "00",
    "client": "100",
    "user": "your-username",
    "password": "your-password"
  },
  "log_level": "INFO"
}
```

**Security Note:** Never commit files containing real credentials to version control.

## Usage

### Starting the MCP Server

**Using a configuration file:**
```bash
python -m src.main --config config.json
```

**With custom log level:**
```bash
python -m src.main --config config.json --log-level DEBUG
```

### MCP Client Configuration

#### For Claude Desktop

Edit your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "abap-syntax-checker": {
      "command": "python",
      "args": ["-m", "src.main", "--config", "config.json"],
      "cwd": "/absolute/path/to/ABAP_CHECK_MCP"
    }
  }
}
```

#### For Kiro

Create or edit `.kiro/settings/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "abap-syntax-checker": {
      "command": "python",
      "args": ["-m", "src.main", "--config", "config.json"],
      "cwd": "/absolute/path/to/ABAP_CHECK_MCP",
      "disabled": false,
      "autoApprove": ["check_abap_syntax"]
    }
  }
}
```

### Using the Tool

Once configured, the `check_abap_syntax` tool will be available in your IDE.

**Example Usage:**

```
Check this ABAP code for syntax errors:

REPORT ztest.
DATA: lv_test TYPE string.
lv_undefined = 'test'.
WRITE: / lv_test.
```

**Response:**
```json
{
  "success": true,
  "has_errors": true,
  "errors": [
    {
      "line": 3,
      "type": "E",
      "message": "Field \"LV_UNDEFINED\" is unknown."
    }
  ],
  "message": "Syntax check completed with errors"
}
```

## SAP Backend Setup

The MCP server requires an ABAP function module to be deployed in your SAP ERP system.

**Quick deployment summary:**
1. Create structure `ZSYNTAX_ERROR` in SE11
2. Create function group `ZSYNTAX_CHECK` in SE80
3. Create function module `Z_CHECK_ABAP_SYNTAX` in SE37
4. Copy implementation code and activate

For detailed step-by-step instructions, see:
- **Deployment Guide**: `abap/DEPLOYMENT_GUIDE.md`
- **ABAP README**: `abap/README.md`

## Project Structure

```
.
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── server.py          # MCP server implementation
│   ├── rfc_client.py      # RFC client wrapper
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── tool_handler.py    # MCP tool handler
│   └── logger.py          # Logging configuration
├── tests/                  # Test files
│   ├── __init__.py
│   └── test_tool_handler.py
├── abap/                   # ABAP artifacts
│   ├── function_module/
│   ├── function_group/
│   ├── types/
│   ├── DEPLOYMENT_GUIDE.md
│   └── README.md
├── config/                 # Configuration files
│   ├── .env.example
│   └── config.example.json
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
```

## Troubleshooting

### RFC Connection Issues

**Problem:** `Error: Cannot connect to SAP system`

**Solutions:**
- Verify SAP system is accessible from your network
- Check credentials and client number are correct
- Ensure SAP NetWeaver RFC SDK is properly installed
- Check firewall settings for RFC ports

### Syntax Check Errors

**Problem:** `Function module Z_CHECK_ABAP_SYNTAX not found`

**Solutions:**
- Verify the ABAP function module is deployed (see `abap/DEPLOYMENT_GUIDE.md`)
- Check the function module name is exactly `Z_CHECK_ABAP_SYNTAX`
- Ensure the function module is activated in SE37

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

For issues and questions, please open an issue on the GitHub repository.
