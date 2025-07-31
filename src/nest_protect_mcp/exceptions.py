"""
Custom exceptions for the Nest Protect MCP server.
"""

class NestProtectError(Exception):
    """Base exception for all Nest Protect MCP errors."""
    pass

class NestAuthError(NestProtectError):
    """Raised when there's an authentication or authorization error with the Nest API."""
    pass

class NestConnectionError(NestProtectError):
    """Raised when there's a connection error with the Nest API or devices."""
    pass

class NestDeviceNotFoundError(NestProtectError):
    """Raised when a requested device is not found."""
    pass

class NestDeviceOfflineError(NestProtectError):
    """Raised when trying to communicate with an offline device."""
    pass

class NestInvalidCommandError(NestProtectError):
    """Raised when an invalid command is sent to a device."""
    pass

class NestRateLimitExceededError(NestProtectError):
    """Raised when the rate limit for the Nest API is exceeded."""
    pass

class NestConfigError(NestProtectError):
    """Raised when there's an error in the configuration."""
    pass

class NestMQTTError(NestProtectError):
    """Raised when there's an error with MQTT communication."""
    pass

class NestUpdateError(NestProtectError):
    """Raised when there's an error updating device state."""
    pass

class NestTestError(NestProtectError):
    """Raised when there's an error during a device test."""
    pass

class NestHushError(NestProtectError):
    """Raised when there's an error hushing an alarm."""
    pass
