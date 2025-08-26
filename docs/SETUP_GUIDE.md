# Nest Protect MCP Setup Guide

This guide will walk you through setting up the Nest Protect MCP server with real Nest Protect devices.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Google Cloud Project Setup](#google-cloud-project-setup)
3. [OAuth 2.0 Credentials](#oauth-20-credentials)
4. [Nest Protect Device Types](#nest-protect-device-types)
5. [Configuration](#configuration)
6. [Running the Server](#running-the-server)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.8 or higher
- A Google account
- One or more Nest Protect devices connected to your Nest/Google Home account
- Basic familiarity with command line and Python

## Google Cloud Project Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown and select "New Project"
3. Enter a project name (e.g., "Nest Protect MCP") and click "Create"
4. Once created, make sure the project is selected in the top navigation bar

## Enable Required APIs

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Smart Device Management API" and click on it
3. Click "Enable"
4. Search for "OAuth Consent Screen" and click on it
5. Select "External" user type and click "Create"
6. Fill in the required information (app name, user support email, developer contact email)
7. Click "Save and Continue"
8. Add the following scopes:
   - `https://www.googleapis.com/auth/sdm.service`
   - `https://www.googleapis.com/auth/pubsub`
9. Click "Save and Continue"
10. Add test users (your Google account email)
11. Click "Save and Continue" then "Back to Dashboard"

## OAuth 2.0 Credentials

1. In the Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop app" as the application type
4. Give it a name (e.g., "Nest Protect MCP Client")
5. Click "Create"
6. Note down the Client ID and Client Secret (you'll need these later)
7. Click "OK"

## Get Refresh Token

1. Open a terminal and install the required package:
   ```bash
   pip install google-auth-oauthlib
   ```

2. Run the following Python script to get a refresh token:
   ```python
   from google_auth_oauthlib.flow import InstalledAppFlow
   
   CLIENT_ID = 'YOUR_CLIENT_ID'
   CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
   
   flow = InstalledAppFlow.from_client_config(
       {"installed": {
           "client_id": CLIENT_ID,
           "client_secret": CLIENT_SECRET,
           "auth_uri": "https://accounts.google.com/o/oauth2/auth",
           "token_uri": "https://oauth2.googleapis.com/token",
           "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
           "redirect_uris": ["http://localhost:8080"]
       }},
       scopes=['https://www.googleapis.com/auth/sdm.service']
   )
   
   creds = flow.run_local_server(port=8080)
   print(f"Refresh token: {creds.refresh_token}")
   ```

3. Note down the refresh token that's printed

## Nest Protect Device Types

### 1. Nest Protect (2nd Generation)
- **Model**: Topaz
- **Power**: Wired or Battery
- **Features**:
  - Smoke detection
  - Carbon monoxide detection
  - Speech and light alarms
  - Night light
  - Pathlight feature
  - Wireless interconnect

### 2. Nest Protect (3rd Generation)
- **Model**: Topaz-B
- **Power**: Wired or Battery
- **Features**:
  - All 2nd gen features plus:
  - Improved sensor technology
  - Better battery life
  - Enhanced wireless connectivity
  - Faster response times

### 3. Nest Protect (Wired)
- **Model**: Topaz-L
- **Power**: Wired only
- **Features**:
  - Same features as battery models
  - No battery to replace
  - Hardwired power with battery backup

### 4. Nest Protect (Battery)
- **Model**: Topaz-L
- **Power**: Battery only
- **Features**:
  - Same features as wired models
  - 3-year battery life
  - Easy installation

## Configuration

1. Copy the example config file:
   ```bash
   cp config/default.toml.example config/default.toml
   ```

2. Edit the `config/default.toml` file with your credentials:
   ```toml
   [nest]
   project_id = "your-google-cloud-project-id"
   client_id = "your-oauth-client-id"
   client_secret = "your-oauth-client-secret"
   refresh_token = "your-refresh-token"
   
   [server]
   host = "0.0.0.0"
   port = 8080
   log_level = "INFO"
   update_interval = 60  # seconds
   ```

## Running the Server

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python -m nest_protect_mcp
   ```

3. The server will start and begin discovering your Nest Protect devices

## Testing the Connection

1. List all devices:
   ```bash
   curl http://localhost:8080/api/devices
   ```

2. Get device status:
   ```bash
   curl http://localhost:8080/api/device/YOUR_DEVICE_ID/status
   ```

3. Hush an alarm:
   ```bash
   curl -X POST http://localhost:8080/api/device/YOUR_DEVICE_ID/hush
   ```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify your OAuth credentials are correct
   - Ensure the refresh token hasn't expired
   - Check that the required scopes are enabled

2. **Device Not Found**:
   - Make sure the device is online in the Google Home app
   - Check that your Google account has access to the device

3. **API Rate Limiting**:
   - The Nest API has rate limits
   - Implement proper error handling in your application
   - Consider adding delays between API calls

4. **Connection Issues**:
   - Verify your internet connection
   - Check that the Nest service is operational at [Nest Status](https://www.googleneststatus.com/)

## Security Considerations

- Never commit your OAuth credentials to version control
- Use environment variables for sensitive information
- Regularly rotate your refresh tokens
- Follow the principle of least privilege when setting up API access

## Support

For additional help, please open an issue in the [GitHub repository](https://github.com/yourusername/nest-protect-mcp).

---
*Last updated: August 26, 2025*
