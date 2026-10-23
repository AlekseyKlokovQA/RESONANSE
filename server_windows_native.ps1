# ==============================================================================
# Resonance Club - Native Windows Server (100% Pure PowerShell, Zero Install)
# Does NOT use Add-Type (No compiler, No %TEMP% DLLs, No Antivirus blocks)
# Does NOT use http.sys (No Admin rights, No "Access Denied" errors)
# ==============================================================================

param(
    [int]$Port = 3000
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $ScriptDir) { $ScriptDir = (Get-Location).Path }
Set-Location -LiteralPath $ScriptDir

# Try binding with automatic fallback if port is in use
$candidatePorts = @($Port, 3001, 8080, 5000, 8000)
$listener = $null
$activePort = 0

foreach ($p in $candidatePorts) {
    try {
        $listener = New-Object System.Net.Sockets.TcpListener ([System.Net.IPAddress]::Any, $p)
        $listener.Start()
        $activePort = $p
        break
    } catch {
        try {
            $listener = New-Object System.Net.Sockets.TcpListener ([System.Net.IPAddress]::Loopback, $p)
            $listener.Start()
            $activePort = $p
            break
        } catch {
            $listener = $null
        }
    }
}

if (-not $listener) {
    Write-Host "[ERROR] Could not open ports 3000, 3001, 8080, 5000." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

$LocalIP = "127.0.0.1"
try {
    $foundIP = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
    if ($foundIP) { $LocalIP = $foundIP }
} catch {}

$MimeTypes = @{
    ".html" = "text/html; charset=utf-8"
    ".htm"  = "text/html; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".js"   = "application/javascript; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".svg"  = "image/svg+xml"
    ".png"  = "image/png"
    ".jpg"  = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".mp3"  = "audio/mpeg"
    ".zip"  = "application/zip"
}

$MaxUsers = 5
$ActiveUsers = 0

Write-Host "===================================================================" -ForegroundColor DarkYellow
Write-Host "   RESONANCE CLUB - SERVER IS RUNNING ON PORT $activePort" -ForegroundColor Yellow
Write-Host "===================================================================" -ForegroundColor DarkYellow
Write-Host " 1. Main Page:         http://localhost:$activePort" -ForegroundColor Green
Write-Host " 2. Resident Profile:  http://localhost:$activePort/profile.html" -ForegroundColor Green
Write-Host " 3. LAN / Wi-Fi URL:   http://${LocalIP}:$activePort" -ForegroundColor Cyan
Write-Host "-------------------------------------------------------------------"
Write-Host " STRICT LIMIT: MAXIMUM 5 CONCURRENT USERS ACROSS NETWORK" -ForegroundColor Yellow
Write-Host " To stop server: close this window or press Ctrl + C" -ForegroundColor Red
Write-Host "===================================================================" -ForegroundColor DarkYellow
Write-Host ""
Write-Host "Opening web browser at http://localhost:$activePort ..." -ForegroundColor Gray

# Open browser
try {
    Start-Process "http://localhost:$activePort"
} catch {}

try {
    while ($listener.Server.IsBound) {
        if (-not $listener.Pending()) {
            Start-Sleep -Milliseconds 25
            continue
        }

        $client = $listener.AcceptTcpClient()
        $stream = $client.GetStream()
        $stream.ReadTimeout = 6000
        $stream.WriteTimeout = 20000

        try {
            $buffer = New-Object byte[] 4096
            $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
            if ($bytesRead -le 0) {
                $client.Close()
                continue
            }

            $requestText = [System.Text.Encoding]::ASCII.GetString($buffer, 0, $bytesRead)
            $lines = $requestText -split "`r`n"
            if ($lines.Length -lt 1) {
                $client.Close()
                continue
            }

            $tokens = $lines[0] -split " "
            if ($tokens.Length -lt 2) {
                $client.Close()
                continue
            }

            $method = $tokens[0].ToUpper()
            $rawUrl = $tokens[1]

            $rangeHeader = $null
            foreach ($h in $lines) {
                if ($h -like "Range: bytes=*") {
                    $rangeHeader = $h.Substring(6).Trim()
                    break
                }
            }

            # 5-User limit check
            if ($ActiveUsers -ge $MaxUsers) {
                $limitFile = Join-Path $ScriptDir "temp_server\limit_exceeded.html"
                if (Test-Path -LiteralPath $limitFile) {
                    $bodyBytes = [System.IO.File]::ReadAllBytes($limitFile)
                } else {
                    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes("<h1>503 Server Busy</h1><p>Maximum 5 users limit reached.</p>")
                }
                $hdr = "HTTP/1.1 503 Service Unavailable`r`nContent-Type: text/html; charset=utf-8`r`nContent-Length: $($bodyBytes.Length)`r`nConnection: close`r`n`r`n"
                $hdrBytes = [System.Text.Encoding]::ASCII.GetBytes($hdr)
                $stream.Write($hdrBytes, 0, $hdrBytes.Length)
                $stream.Write($bodyBytes, 0, $bodyBytes.Length)
                $client.Close()
                continue
            }

            $ActiveUsers++

            if ($rawUrl.Contains("?")) {
                $rawUrl = $rawUrl.Substring(0, $rawUrl.IndexOf("?"))
            }
            $rawUrl = $rawUrl.TrimStart('/')
            if ([string]::IsNullOrWhiteSpace($rawUrl)) {
                $rawUrl = "index.html"
            }
            $rawUrl = [System.Uri]::UnescapeDataString($rawUrl)

            $filePath = Join-Path $ScriptDir $rawUrl
            if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
                $msg = "<h1>404 Not Found: $rawUrl</h1>"
                $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($msg)
                $hdr = "HTTP/1.1 404 Not Found`r`nContent-Type: text/html; charset=utf-8`r`nContent-Length: $($bodyBytes.Length)`r`nConnection: close`r`n`r`n"
                $hdrBytes = [System.Text.Encoding]::ASCII.GetBytes($hdr)
                $stream.Write($hdrBytes, 0, $hdrBytes.Length)
                $stream.Write($bodyBytes, 0, $bodyBytes.Length)
                $ActiveUsers = [Math]::Max(0, $ActiveUsers - 1)
                $client.Close()
                continue
            }

            $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
            $mime = "application/octet-stream"
            if ($MimeTypes.ContainsKey($ext)) {
                $mime = $MimeTypes[$ext]
            }

            $fileInfo = New-Object System.IO.FileInfo($filePath)
            $totalSize = $fileInfo.Length

            if ($method -eq "HEAD") {
                $hdr = "HTTP/1.1 200 OK`r`nContent-Type: $mime`r`nContent-Length: $totalSize`r`nAccess-Control-Allow-Origin: *`r`nAccept-Ranges: bytes`r`nConnection: close`r`n`r`n"
                $hdrBytes = [System.Text.Encoding]::ASCII.GetBytes($hdr)
                $stream.Write($hdrBytes, 0, $hdrBytes.Length)
                $ActiveUsers = [Math]::Max(0, $ActiveUsers - 1)
                $client.Close()
                continue
            }

            if ($rangeHeader -and $rangeHeader.StartsWith("bytes=")) {
                $parts = $rangeHeader.Substring(6).Split('-')
                $start = 0
                [int64]::TryParse($parts[0], [ref]$start) | Out-Null
                $end = $totalSize - 1
                if ($parts.Length -gt 1 -and -not [string]::IsNullOrEmpty($parts[1])) {
                    [int64]::TryParse($parts[1], [ref]$end) | Out-Null
                }
                if ($end -ge $totalSize) { $end = $totalSize - 1 }
                $length = $end - $start + 1

                $hdr = "HTTP/1.1 206 Partial Content`r`nContent-Type: $mime`r`nContent-Range: bytes $start-$end/$totalSize`r`nContent-Length: $length`r`nAccess-Control-Allow-Origin: *`r`nAccept-Ranges: bytes`r`nConnection: close`r`n`r`n"
                $hdrBytes = [System.Text.Encoding]::ASCII.GetBytes($hdr)
                $stream.Write($hdrBytes, 0, $hdrBytes.Length)

                $fileStream = [System.IO.File]::OpenRead($filePath)
                try {
                    $fileStream.Seek($start, [System.IO.SeekOrigin]::Begin) | Out-Null
                    $chunk = New-Object byte[] 65536
                    $remaining = $length
                    while ($remaining -gt 0) {
                        $toRead = [Math]::Min($chunk.Length, $remaining)
                        $read = $fileStream.Read($chunk, 0, $toRead)
                        if ($read -le 0) { break }
                        $stream.Write($chunk, 0, $read)
                        $remaining -= $read
                    }
                } finally {
                    $fileStream.Close()
                }
            } else {
                $hdr = "HTTP/1.1 200 OK`r`nContent-Type: $mime`r`nContent-Length: $totalSize`r`nAccess-Control-Allow-Origin: *`r`nAccept-Ranges: bytes`r`nConnection: close`r`n`r`n"
                $hdrBytes = [System.Text.Encoding]::ASCII.GetBytes($hdr)
                $stream.Write($hdrBytes, 0, $hdrBytes.Length)

                $fileStream = [System.IO.File]::OpenRead($filePath)
                try {
                    $fileStream.CopyTo($stream)
                } finally {
                    $fileStream.Close()
                }
            }
        } catch {
        } finally {
            $ActiveUsers = [Math]::Max(0, $ActiveUsers - 1)
            try { $client.Close() } catch {}
        }
    }
} finally {
    if ($listener) {
        try { $listener.Stop() } catch {}
    }
    Write-Host "`nServer stopped." -ForegroundColor Yellow
}
