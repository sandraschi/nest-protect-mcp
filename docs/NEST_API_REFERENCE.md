# Nest API Reference

This document provides detailed information about the Nest API integration used in the Nest Protect MCP server.

## Authentication

The Nest API uses OAuth 2.0 for authentication. The integration supports both the initial OAuth flow and token refresh.

### OAuth 2.0 Flow

1. **Initiate OAuth Flow**
   - Endpoint: `GET /auth/initiate`
   - Parameters:
     - `redirect_uri`: Callback URL (default: `http://localhost:8000/auth/callback`)
     - `state`: Optional CSRF protection state
     - `open_browser`: Whether to open auth URL in browser (default: `true`)

2. **OAuth Callback**
   - Endpoint: `GET /auth/callback`
   - Handles the OAuth callback with the authorization code
   - Exchanges the code for access and refresh tokens

### Token Management

- Access tokens are valid for 1 hour by default
- Refresh tokens are used to obtain new access tokens
- The server automatically refreshes tokens when they're about to expire

## API Endpoints

### Base URL
```
https://smartdevicemanagement.googleapis.com/v1
```

### Authentication Header
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Available Endpoints

1. **Get Devices**
   - `GET /enterprises/{project_id}/devices`
   - Lists all Nest Protect devices in the account

2. **Get Device**
   - `GET /enterprises/{project_id}/devices/{device_id}`
   - Retrieves details for a specific device

3. **Execute Device Command**
   - `POST /enterprises/{project_id}/devices/{device_id}:executeCommand`
   - Sends commands to Nest Protect devices

## Device Commands

### Available Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| `hush`  | Silence the alarm | - |
| `test`  | Start a manual test | `type`: Test type (smoke, co, full) |
| `locate`| Make the device beep | - |
| `update`| Update device settings | Varies by setting |

## Error Handling

### Common Error Responses

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | INVALID_ARGUMENT | Missing or invalid parameters |
| 401 | UNAUTHENTICATED | Invalid or expired token |
| 403 | PERMISSION_DENIED | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 429 | RESOURCE_EXHAUSTED | Rate limit exceeded |
| 500 | INTERNAL | Internal server error |

### Error Response Format
```json
{
  "error": {
    "code": 401,
    "message": "Request had invalid authentication credentials.",
    "status": "UNAUTHENTICATED"
  }
}
```

## Rate Limiting

- The Nest API enforces rate limits on API calls
- The client implements automatic retry with exponential backoff for rate-limited requests
- Recommended to implement client-side rate limiting if making frequent API calls

## Webhooks

The Nest API supports webhooks for real-time updates. To set up webhooks:

1. Register a webhook URL in the Google Cloud Console
2. Handle the following event types:
   - `sdm.devices.events.*` - Device state changes
   - `sdm.devices.traits.*` - Trait updates

## Best Practices

1. **Token Management**
   - Store refresh tokens securely
   - Implement token refresh before expiration
   - Handle token revocation gracefully

2. **Error Handling**
   - Implement retry logic for transient failures
   - Handle rate limiting with exponential backoff
   - Log errors with sufficient context

3. **Performance**
   - Cache device states when possible
   - Batch requests when making multiple API calls
   - Use webhooks instead of polling when real-time updates are needed

## Example Requests

### Get All Devices
```http
GET /enterprises/project-id/devices
Authorization: Bearer ya29.A0ARrdaM...
```

### Execute Command (Hush Alarm)
```http
POST /enterprises/project-id/devices/device-id:executeCommand
Authorization: Bearer ya29.A0ARrdaM...
Content-Type: application/json

{
  "command": "sdm.devices.commands.SmokeCOAlarm.Hush",
  "params": {}
}
```

## Troubleshooting

### Common Issues

1. **Invalid Credentials**
   - Verify client ID and secret
   - Check token expiration
   - Ensure proper OAuth scopes are requested

2. **Rate Limiting**
   - Implement exponential backoff
   - Reduce request frequency
   - Cache responses when possible

3. **Webhook Delivery Failures**
   - Verify webhook URL is accessible
   - Handle duplicate events
   - Implement proper error handling for webhook responses

## Additional Resources

- [Google Smart Device Management API Documentation](https://developers.google.com/nest/device-access)
- [OAuth 2.0 for Device Authorization](https://developers.google.com/identity/protocols/oauth2/device-code)
- [Nest Device Access Program](https://developers.google.com/nest/device-access/registration)
