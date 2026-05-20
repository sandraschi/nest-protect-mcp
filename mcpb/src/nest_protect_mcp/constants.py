"""Fleet and Google Nest Device Access (SDM) API constants.

The SDM OAuth scope is often labeled *Home automation* or *Smart Device Management*
on the Google consent screen. It is not a separate scope from ``sdm.service``.
See: https://developers.google.com/nest/device-access/api/authorization
"""

# Smart Device Management API — required for Nest Device Access (Partner Connections)
NEST_SDM_OAUTH_SCOPE: str = "https://www.googleapis.com/auth/sdm.service"

# Google OAuth 2.0 token endpoint (preferred over legacy .../oauth2/v4/token)
GOOGLE_OAUTH_TOKEN_URL: str = "https://oauth2.googleapis.com/token"

# Partner Connections Manager (PCM) — must be used instead of accounts.google.com
# for the SDM authorization step. {device_access_project_id} is the Device Access
# program project id (UUID), same as NEST_PROJECT_ID / enterprise in API paths.
def partner_connections_auth_base(device_access_project_id: str) -> str:
    """Base URL for PCM (trailing /auth is added with query parameters)."""
    pid = device_access_project_id.strip()
    return f"https://nestservices.google.com/partnerconnections/{pid}/auth"
