param(
    [switch]$SelfTest,
    [switch]$RefreshCredentials
)

$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

function Find-GitHubCli {
    $candidates = @(
        (Join-Path $env:ProgramFiles "GitHub CLI\gh.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\GitHub CLI\gh.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    throw "GitHub CLI was not found. Install it with: winget install GitHub.cli"
}

function Read-CachedGitHubAuth {
    $cachePath = Join-Path $env:LOCALAPPDATA "CS50P-Submissions\github-auth.dat"
    if (-not (Test-Path -LiteralPath $cachePath)) {
        return $null
    }

    try {
        Add-Type -AssemblyName System.Security
        $encryptedBytes = [System.IO.File]::ReadAllBytes($cachePath)
        $plainBytes = [System.Security.Cryptography.ProtectedData]::Unprotect(
            $encryptedBytes,
            $null,
            [System.Security.Cryptography.DataProtectionScope]::CurrentUser
        )
        $json = [System.Text.Encoding]::UTF8.GetString($plainBytes)
        $auth = $json | ConvertFrom-Json
        if ($auth.username -and $auth.token) {
            return $auth
        }
    }
    catch {
        return $null
    }

    return $null
}

function Save-CachedGitHubAuth {
    param(
        [Parameter(Mandatory)][string]$Username,
        [Parameter(Mandatory)][string]$Token
    )

    Add-Type -AssemblyName System.Security
    $cacheDirectory = Join-Path $env:LOCALAPPDATA "CS50P-Submissions"
    New-Item -ItemType Directory -Path $cacheDirectory -Force | Out-Null

    $payload = @{ username = $Username; token = $Token } | ConvertTo-Json -Compress
    $plainBytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
    $encryptedBytes = [System.Security.Cryptography.ProtectedData]::Protect(
        $plainBytes,
        $null,
        [System.Security.Cryptography.DataProtectionScope]::CurrentUser
    )
    [System.IO.File]::WriteAllBytes(
        (Join-Path $cacheDirectory "github-auth.dat"),
        $encryptedBytes
    )
}

function Get-GitHubAuth {
    param(
        [Parameter(Mandatory)][string]$GitHubCli,
        [switch]$ForceRefresh
    )

    if (-not $ForceRefresh) {
        $cached = Read-CachedGitHubAuth
        if ($cached) {
            return $cached
        }
    }

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $accountOutput = & $GitHubCli api user --jq .login 2>$null
        $tokenOutput = & $GitHubCli auth token 2>$null
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }

    if ($LASTEXITCODE -ne 0 -or -not $accountOutput -or -not $tokenOutput) {
        throw @"
GitHub authentication is not available.

Open PowerShell and run:
  gh auth login

Then double-click the CS50P desktop shortcut again.
"@
    }

    $auth = @{
        username = ([string]$accountOutput).Trim()
        token = ([string]$tokenOutput).Trim()
    }

    Save-CachedGitHubAuth -Username $auth.username -Token $auth.token
    return [pscustomobject]$auth
}

function ConvertTo-WslPath {
    param([Parameter(Mandatory)][string]$WindowsPath)

    $fullPath = [System.IO.Path]::GetFullPath($WindowsPath)
    $drive = $fullPath.Substring(0, 1).ToLowerInvariant()
    $remainder = $fullPath.Substring(2).Replace("\", "/")
    return "/mnt/$drive$remainder"
}

function Find-WorkingGitHubIp {
    $knownCandidates = @(
        "20.27.177.113",
        "20.200.245.247",
        "4.237.22.38",
        "20.201.28.151"
    )

    $dynamicCandidates = @()
    try {
        $metadata = Invoke-RestMethod `
            -Uri "https://api.github.com/meta" `
            -Headers @{ "User-Agent" = "CS50P-Launcher" } `
            -TimeoutSec 10
        $dynamicCandidates = $metadata.web |
            Where-Object { $_ -match '/32$' } |
            ForEach-Object { ($_ -split "/")[0] }
    }
    catch {
        # The known candidates still provide a reliable fallback.
    }

    $candidates = @($knownCandidates + $dynamicCandidates | Select-Object -Unique)
    foreach ($ip in $candidates) {
        $status = & curl.exe -sS -o NUL -w "%{http_code}" `
            --connect-timeout 4 --max-time 6 `
            --resolve "github.com:443:$ip" `
            "https://github.com/login/device" 2>$null
        if ($LASTEXITCODE -eq 0 -and $status -in @("200", "301", "302")) {
            return $ip
        }
    }

    throw "No reachable GitHub web node was found from this network."
}

$repoWindows = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$repoWsl = ConvertTo-WslPath $repoWindows
$gh = Find-GitHubCli

$auth = Get-GitHubAuth -GitHubCli $gh -ForceRefresh:$RefreshCredentials
$account = $auth.username
$token = $auth.token

$oldUser = $env:CS50_GH_USER
$oldToken = $env:CS50_TOKEN
$oldWslEnv = $env:WSLENV

try {
    $env:CS50_GH_USER = $account
    $env:CS50_TOKEN = $token
    $env:WSLENV = (@($oldWslEnv, "CS50_GH_USER/u", "CS50_TOKEN/u") |
        Where-Object { $_ }) -join ":"

    Write-Host "Checking GitHub connection..." -ForegroundColor DarkGray
    $githubIp = Find-WorkingGitHubIp
    & wsl.exe -d Ubuntu --user root -- bash `
        "$repoWsl/tools/fix-wsl-github-route.sh" $githubIp
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to update the GitHub route inside WSL."
    }

    $menuPath = "$repoWsl/tools/cs50p_menu.py"
    $wslArgs = @(
        "-d", "Ubuntu",
        "--user", "cs50p",
        "--cd", $repoWsl,
        "--", "/opt/cs50p-venv/bin/python", $menuPath
    )

    if ($SelfTest) {
        $wslArgs += "--self-test"
    }

    & wsl.exe @wslArgs
    exit $LASTEXITCODE
}
finally {
    $env:CS50_GH_USER = $oldUser
    $env:CS50_TOKEN = $oldToken
    $env:WSLENV = $oldWslEnv
}
