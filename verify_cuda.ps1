Write-Host "=== CUDA INSTALLATION VERIFICATION ==="
Write-Host ""

# Check CUDA environment variables
Write-Host "1. Environment Variables:"
Write-Host "   CUDA_PATH: $env:CUDA_PATH"
Write-Host "   PATH contains CUDA: " -NoNewline
if ($env:PATH -like "*CUDA*") { Write-Host "✅ YES" } else { Write-Host "❌ NO" }
Write-Host ""

# Check nvcc compiler
Write-Host "2. NVCC Compiler:"
try {
    $nvccVersion = nvcc --version 2>$null
    if ($nvccVersion) {
        Write-Host "   ✅ nvcc found"
        nvcc --version | Select-String "release"
    } else {
        Write-Host "   ❌ nvcc not found"
    }
} catch {
    Write-Host "   ❌ nvcc not accessible"
}
Write-Host ""

# Check installation directory
Write-Host "3. Installation Directory:"
$cudaInstallPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2"
if (Test-Path $cudaInstallPath) {
    Write-Host "   ✅ CUDA 12.2 directory exists"
    $size = (Get-ChildItem $cudaInstallPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "   Installation size: $([math]::Round($size,2)) GB"
} else {
    Write-Host "   ❌ CUDA 12.2 directory not found"
}
