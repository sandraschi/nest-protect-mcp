<#
.SYNOPSIS
    Builds a DXT package with all dependencies included.
.DESCRIPTION
    This script:
    1. Validates the package using 'dxt validate'
    2. Installs dependencies to a local directory
    3. Creates a DXT package with all dependencies included
#>

# Create necessary directories
$distDir = "dist"
$packageDir = "$distDir/package"
$libDir = "$packageDir/lib"

# Clean up from previous builds
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
New-Item -ItemType Directory -Path $libDir -Force | Out-Null

# Function to run a command and return exit code and output
function Invoke-CommandWithOutput {
    param (
        [string]$Command,
        [string[]]$Arguments,
        [string]$WorkingDir = "."
    )
    
    $process = Start-Process -FilePath $Command -ArgumentList $Arguments -NoNewWindow -PassThru -Wait -WorkingDirectory $WorkingDir
    return @{
        ExitCode = $process.ExitCode
    }
}

# Step 1: Validate the package
Write-Host "🔍 Validating package with 'dxt validate'..." -ForegroundColor Cyan
$validateResult = Invoke-CommandWithOutput -Command "dxt" -Arguments @("validate", ".")

if ($validateResult.ExitCode -ne 0) {
    Write-Host "❌ Validation failed. Please fix the reported issues before packaging." -ForegroundColor Red
    exit $validateResult.ExitCode
}

Write-Host "✅ Validation successful!" -ForegroundColor Green

# Step 2: Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
$requirements = @(
    "fastmcp>=2.11.3",
    "pydantic>=1.10.0",
    "aiohttp>=3.8.0",
    "python-dotenv>=0.19.0",
    "toml>=0.10.2",
    "requests>=2.28.0"
)

# Create requirements.txt
$requirements | Out-File -FilePath "$distDir/requirements.txt" -Encoding UTF8

# Install dependencies to lib directory
$pipResult = Invoke-CommandWithOutput -Command "pip" -Arguments @(
    "install", 
    "-r", "$distDir/requirements.txt", 
    "--target", "$libDir",
    "--no-compile"
)

if ($pipResult.ExitCode -ne 0) {
    Write-Host "❌ Failed to install dependencies." -ForegroundColor Red
    exit $pipResult.ExitCode
}

# Step 3: Copy package files
Write-Host "📂 Copying package files..." -ForegroundColor Cyan
Copy-Item -Path "src/nest_protect_mcp" -Destination $packageDir -Recurse -Force

# Step 4: Create a simple setup.py that includes the lib directory
$setupPyContent = @'
import sys
import os
from setuptools import setup, find_packages

# Add lib directory to Python path
sys.path.insert(0, os.path.abspath('lib'))

setup(
    name="nest-protect-mcp",
    version="0.1.0",
    packages=find_packages(where='.'),
    package_dir={'': '.'},
    install_requires=open('requirements.txt').read().splitlines(),
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.json", "*.md"],
    }
)
'@

$setupPyContent | Out-File -FilePath "$packageDir/setup.py" -Encoding UTF8

# Copy requirements.txt to package directory
Copy-Item -Path "$distDir/requirements.txt" -Destination $packageDir -Force

# Step 5: Create the DXT package
Write-Host "📦 Creating DXT package..." -ForegroundColor Cyan
$outputFile = "$distDir/nest-protect-mcp.dxt"

# Create a zip of the package directory
Add-Type -Assembly System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $packageDir, 
    $outputFile, 
    [System.IO.Compression.CompressionLevel]::Optimal, 
    $false
)

# Check the result
if (Test-Path $outputFile) {
    $fileInfo = Get-Item $outputFile
    Write-Host "✅ DXT package created successfully!" -ForegroundColor Green
    Write-Host "   File: $($fileInfo.FullName)"
    Write-Host "   Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB"
    Write-Host "   Created: $($fileInfo.CreationTime)"
} else {
    Write-Host "❌ Failed to create DXT package." -ForegroundColor Red
    exit 1
}
