# Jaguar Re-ID Docker Compose Startup Script
# Automatically finds an available port for the frontend

function Test-PortAvailable {
    param([int]$Port)
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        return $null -eq $connection
    } catch {
        return $true
    }
}

function Find-AvailablePort {
    param([int]$StartPort = 3000, [int]$MaxAttempts = 10)
    
    for ($i = 0; $i -lt $MaxAttempts; $i++) {
        $port = $StartPort + $i
        if (Test-PortAvailable -Port $port) {
            return $port
        }
        Write-Host "Port $port is in use, trying next..." -ForegroundColor Yellow
    }
    
    Write-Host "ERROR: Could not find an available port after $MaxAttempts attempts" -ForegroundColor Red
    exit 1
}

# Find available port
$frontendPort = Find-AvailablePort -StartPort 3000
Write-Host "✓ Found available port: $frontendPort" -ForegroundColor Green

# Set environment variable for docker-compose
$env:FRONTEND_PORT = $frontendPort

# Run docker-compose
Write-Host "`nStarting services..." -ForegroundColor Cyan
Write-Host "Frontend will be available at: http://localhost:$frontendPort" -ForegroundColor Green
Write-Host "Backend will be available at: http://localhost:8000`n" -ForegroundColor Green

docker compose up $args
