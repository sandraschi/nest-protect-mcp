# Per-repo fleet start config for nest-protect-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'nest-protect-mcp'
    BackendPort  = 10753
    FrontendPort = 10752
    HealthPath   = '/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'main:app'
        WorkDir       = 'webapp\backend'
        PythonPath    = 'webapp\backend;src'
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
