# Per-repo fleet start config for nest-protect-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'nest-protect-mcp'
    BackendPort  = 10753
    FrontendPort = 10752
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\nest-protect-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'nest_protect_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10753' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
