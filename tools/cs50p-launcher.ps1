param(
    [switch]$SelfTest
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

$account = (& $gh api user --jq .login).Trim()
if ($LASTEXITCODE -ne 0 -or -not $account) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

$token = (& $gh auth token).Trim()
if ($LASTEXITCODE -ne 0 -or -not $token) {
    throw "GitHub authentication token is unavailable. Run: gh auth login"
}

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
