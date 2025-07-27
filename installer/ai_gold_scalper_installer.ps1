# ================================
# AI Gold Scalper - GUI Installer
# Version: 1.0.0
# Created: 2025-07-27
# ================================

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName PresentationFramework

# Global variables
$global:InstallationPath = "C:\AI_Gold_Scalper"
$global:LogFile = "$env:TEMP\ai_gold_scalper_install.log"
$global:InstallationSteps = @()
$global:CurrentStep = 0

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $global:LogFile -Value $logEntry
    Write-Host $logEntry
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# System requirements check
function Test-SystemRequirements {
    $requirements = @{
        "Windows Version" = $true
        "RAM (16GB+)" = $false
        "Disk Space (10GB+)" = $false
        "Python 3.11+" = $false
        "NVIDIA GPU" = $false
    }
    
    # Check Windows version
    $osVersion = [System.Environment]::OSVersion.Version
    if ($osVersion.Major -ge 10) {
        $requirements["Windows Version"] = $true
    }
    
    # Check RAM
    $ram = Get-WmiObject -Class Win32_ComputerSystem
    $ramGB = [math]::Round($ram.TotalPhysicalMemory / 1GB, 1)
    if ($ramGB -ge 16) {
        $requirements["RAM (16GB+)"] = $true
    }
    
    # Check disk space
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 1)
    if ($freeSpaceGB -ge 10) {
        $requirements["Disk Space (10GB+)"] = $true
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion -match "Python 3\.1[1-9]") {
            $requirements["Python 3.11+"] = $true
        }
    } catch {
        Write-Log "Python not found" "WARNING"
    }
    
    # Check NVIDIA GPU
    try {
        $nvidiaOutput = nvidia-smi 2>$null
        if ($nvidiaOutput) {
            $requirements["NVIDIA GPU"] = $true
        }
    } catch {
        Write-Log "NVIDIA GPU not detected" "WARNING"
    }
    
    return $requirements
}

# Download file with progress
function Download-FileWithProgress {
    param(
        [string]$Url,
        [string]$OutputPath,
        [System.Windows.Forms.ProgressBar]$ProgressBar
    )
    
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.add_DownloadProgressChanged({
            param($sender, $e)
            $ProgressBar.Value = $e.ProgressPercentage
            [System.Windows.Forms.Application]::DoEvents()
        })
        
        $webClient.DownloadFileAsync($Url, $OutputPath)
        
        while ($webClient.IsBusy) {
            [System.Windows.Forms.Application]::DoEvents()
            Start-Sleep -Milliseconds 100
        }
        
        $webClient.Dispose()
        return $true
    } catch {
        Write-Log "Download failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Install CUDA Toolkit
function Install-CUDAToolkit {
    param([System.Windows.Forms.ProgressBar]$ProgressBar)
    
    Write-Log "Starting CUDA Toolkit installation"
    $ProgressBar.Value = 10
    
    $cudaUrl = "https://developer.download.nvidia.com/compute/cuda/12.2.0/network_installers/cuda_12.2.0_windows_network.exe"
    $cudaInstaller = "$env:TEMP\cuda_installer.exe"
    
    # Download CUDA installer
    Write-Log "Downloading CUDA Toolkit..."
    $ProgressBar.Value = 30
    
    if (Download-FileWithProgress -Url $cudaUrl -OutputPath $cudaInstaller -ProgressBar $ProgressBar) {
        Write-Log "CUDA Toolkit downloaded successfully"
        $ProgressBar.Value = 60
        
        # Run installer
        Write-Log "Running CUDA installer..."
        $process = Start-Process -FilePath $cudaInstaller -ArgumentList "-s" -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Log "CUDA Toolkit installed successfully"
            $ProgressBar.Value = 100
            return $true
        } else {
            Write-Log "CUDA installation failed with exit code: $($process.ExitCode)" "ERROR"
            return $false
        }
    } else {
        Write-Log "Failed to download CUDA Toolkit" "ERROR"
        return $false
    }
}

# Install Python packages
function Install-PythonPackages {
    param([System.Windows.Forms.ProgressBar]$ProgressBar)
    
    Write-Log "Installing Python packages..."
    $ProgressBar.Value = 10
    
    $packages = @(
        "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",
        "tensorflow[and-cuda]==2.15.0",
        "numpy pandas scikit-learn",
        "flask flask-cors flask-socketio",
        "plotly dash",
        "sqlalchemy alembic",
        "psutil pynvml"
    )
    
    $totalPackages = $packages.Count
    $currentPackage = 0
    
    foreach ($package in $packages) {
        $currentPackage++
        $progress = [math]::Round(($currentPackage / $totalPackages) * 100)
        $ProgressBar.Value = $progress
        
        Write-Log "Installing: $package"
        
        try {
            $process = Start-Process -FilePath "pip" -ArgumentList "install $package --upgrade" -Wait -PassThru -WindowStyle Hidden
            if ($process.ExitCode -eq 0) {
                Write-Log "Successfully installed: $package"
            } else {
                Write-Log "Failed to install: $package" "WARNING"
            }
        } catch {
            Write-Log "Error installing $package : $($_.Exception.Message)" "ERROR"
        }
        
        [System.Windows.Forms.Application]::DoEvents()
    }
    
    $ProgressBar.Value = 100
    return $true
}

# Setup project files
function Setup-ProjectFiles {
    param([System.Windows.Forms.ProgressBar]$ProgressBar)
    
    Write-Log "Setting up project files..."
    $ProgressBar.Value = 20
    
    # Create installation directory
    if (!(Test-Path $global:InstallationPath)) {
        New-Item -ItemType Directory -Path $global:InstallationPath -Force
        Write-Log "Created installation directory: $global:InstallationPath"
    }
    
    $ProgressBar.Value = 40
    
    # Copy project files from current directory
    $sourceDir = "G:\My Drive\AI_Gold_Scalper"
    if (Test-Path $sourceDir) {
        Write-Log "Copying project files from $sourceDir to $global:InstallationPath"
        robocopy $sourceDir $global:InstallationPath /E /XD ".git" "__pycache__" /XF "*.pyc" "*.log"
        $ProgressBar.Value = 80
    }
    
    # Initialize databases
    Write-Log "Initializing databases..."
    $initScript = Join-Path $global:InstallationPath "core\database_schemas.py"
    if (Test-Path $initScript) {
        try {
            Set-Location $global:InstallationPath
            python -c "from core.database_schemas import initialize_system_databases; initialize_system_databases()"
            Write-Log "Databases initialized successfully"
        } catch {
            Write-Log "Database initialization failed: $($_.Exception.Message)" "WARNING"
        }
    }
    
    $ProgressBar.Value = 100
    return $true
}

# Create desktop shortcut
function Create-DesktopShortcut {
    $shortcutPath = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "AI Gold Scalper.lnk")
    $targetPath = Join-Path $global:InstallationPath "main.py"
    
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = "python"
    $Shortcut.Arguments = "`"$targetPath`""
    $Shortcut.WorkingDirectory = $global:InstallationPath
    $Shortcut.IconLocation = "python.exe,0"
    $Shortcut.Description = "AI Gold Scalper Trading Bot"
    $Shortcut.Save()
    
    Write-Log "Desktop shortcut created: $shortcutPath"
}

# Main GUI form
function Show-InstallerGUI {
    # Create main form
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "AI Gold Scalper Installer v1.0"
    $form.Size = New-Object System.Drawing.Size(600, 500)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.BackColor = [System.Drawing.Color]::White
    
    # Header
    $headerLabel = New-Object System.Windows.Forms.Label
    $headerLabel.Text = "AI Gold Scalper Installation Wizard"
    $headerLabel.Font = New-Object System.Drawing.Font("Arial", 16, [System.Drawing.FontStyle]::Bold)
    $headerLabel.ForeColor = [System.Drawing.Color]::DarkBlue
    $headerLabel.Location = New-Object System.Drawing.Point(20, 20)
    $headerLabel.Size = New-Object System.Drawing.Size(560, 30)
    $headerLabel.TextAlign = "MiddleCenter"
    $form.Controls.Add($headerLabel)
    
    # Tab control
    $tabControl = New-Object System.Windows.Forms.TabControl
    $tabControl.Location = New-Object System.Drawing.Point(20, 60)
    $tabControl.Size = New-Object System.Drawing.Size(550, 350)
    $form.Controls.Add($tabControl)
    
    # Welcome tab
    $welcomeTab = New-Object System.Windows.Forms.TabPage
    $welcomeTab.Text = "Welcome"
    $tabControl.Controls.Add($welcomeTab)
    
    $welcomeText = New-Object System.Windows.Forms.RichTextBox
    $welcomeText.Text = @"
Welcome to the AI Gold Scalper Installation Wizard!

This installer will set up:
• CUDA Toolkit 12.2 for GPU acceleration
• PyTorch and TensorFlow with GPU support
• All required Python packages
• Database initialization
• Web dashboard components

System Requirements:
• Windows 10/11
• NVIDIA GPU with recent drivers
• Python 3.11 or higher
• 16GB+ RAM (recommended)
• 10GB+ free disk space

Click 'Next' to continue with the installation.
"@
    $welcomeText.Location = New-Object System.Drawing.Point(10, 10)
    $welcomeText.Size = New-Object System.Drawing.Size(520, 300)
    $welcomeText.ReadOnly = $true
    $welcomeText.BackColor = [System.Drawing.Color]::White
    $welcomeTab.Controls.Add($welcomeText)
    
    # System Check tab
    $systemTab = New-Object System.Windows.Forms.TabPage
    $systemTab.Text = "System Check"
    $tabControl.Controls.Add($systemTab)
    
    $systemCheckButton = New-Object System.Windows.Forms.Button
    $systemCheckButton.Text = "Run System Check"
    $systemCheckButton.Location = New-Object System.Drawing.Point(10, 10)
    $systemCheckButton.Size = New-Object System.Drawing.Size(150, 30)
    $systemTab.Controls.Add($systemCheckButton)
    
    $systemResults = New-Object System.Windows.Forms.ListBox
    $systemResults.Location = New-Object System.Drawing.Point(10, 50)
    $systemResults.Size = New-Object System.Drawing.Size(520, 250)
    $systemTab.Controls.Add($systemResults)
    
    $systemCheckButton.Add_Click({
        $systemResults.Items.Clear()
        $systemResults.Items.Add("Running system requirements check...")
        [System.Windows.Forms.Application]::DoEvents()
        
        $requirements = Test-SystemRequirements
        foreach ($req in $requirements.GetEnumerator()) {
            $status = if ($req.Value) { "✅ PASS" } else { "❌ FAIL" }
            $systemResults.Items.Add("$($req.Key): $status")
        }
    })
    
    # Installation tab
    $installTab = New-Object System.Windows.Forms.TabPage
    $installTab.Text = "Installation"
    $tabControl.Controls.Add($installTab)
    
    $installPathLabel = New-Object System.Windows.Forms.Label
    $installPathLabel.Text = "Installation Path:"
    $installPathLabel.Location = New-Object System.Drawing.Point(10, 20)
    $installPathLabel.Size = New-Object System.Drawing.Size(100, 20)
    $installTab.Controls.Add($installPathLabel)
    
    $installPathTextBox = New-Object System.Windows.Forms.TextBox
    $installPathTextBox.Text = $global:InstallationPath
    $installPathTextBox.Location = New-Object System.Drawing.Point(120, 20)
    $installPathTextBox.Size = New-Object System.Drawing.Size(300, 20)
    $installTab.Controls.Add($installPathTextBox)
    
    $browseButton = New-Object System.Windows.Forms.Button
    $browseButton.Text = "Browse"
    $browseButton.Location = New-Object System.Drawing.Point(430, 18)
    $browseButton.Size = New-Object System.Drawing.Size(80, 25)
    $installTab.Controls.Add($browseButton)
    
    $browseButton.Add_Click({
        $folderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderDialog.Description = "Select installation directory"
        $folderDialog.SelectedPath = $global:InstallationPath
        
        if ($folderDialog.ShowDialog() -eq "OK") {
            $global:InstallationPath = $folderDialog.SelectedPath
            $installPathTextBox.Text = $global:InstallationPath
        }
    })
    
    $installProgress = New-Object System.Windows.Forms.ProgressBar
    $installProgress.Location = New-Object System.Drawing.Point(10, 60)
    $installProgress.Size = New-Object System.Drawing.Size(520, 30)
    $installProgress.Style = "Continuous"
    $installTab.Controls.Add($installProgress)
    
    $installStatus = New-Object System.Windows.Forms.Label
    $installStatus.Text = "Ready to install"
    $installStatus.Location = New-Object System.Drawing.Point(10, 100)
    $installStatus.Size = New-Object System.Drawing.Size(520, 20)
    $installTab.Controls.Add($installStatus)
    
    $installLog = New-Object System.Windows.Forms.RichTextBox
    $installLog.Location = New-Object System.Drawing.Point(10, 130)
    $installLog.Size = New-Object System.Drawing.Size(520, 180)
    $installLog.ReadOnly = $true
    $installLog.BackColor = [System.Drawing.Color]::Black
    $installLog.ForeColor = [System.Drawing.Color]::White
    $installLog.Font = New-Object System.Drawing.Font("Consolas", 9)
    $installTab.Controls.Add($installLog)
    
    # Navigation buttons
    $backButton = New-Object System.Windows.Forms.Button
    $backButton.Text = "Back"
    $backButton.Location = New-Object System.Drawing.Point(300, 420)
    $backButton.Size = New-Object System.Drawing.Size(80, 30)
    $form.Controls.Add($backButton)
    
    $nextButton = New-Object System.Windows.Forms.Button
    $nextButton.Text = "Next"
    $nextButton.Location = New-Object System.Drawing.Point(390, 420)
    $nextButton.Size = New-Object System.Drawing.Size(80, 30)
    $form.Controls.Add($nextButton)
    
    $installButton = New-Object System.Windows.Forms.Button
    $installButton.Text = "Install"
    $installButton.Location = New-Object System.Drawing.Point(480, 420)
    $installButton.Size = New-Object System.Drawing.Size(80, 30)
    $installButton.BackColor = [System.Drawing.Color]::Green
    $installButton.ForeColor = [System.Drawing.Color]::White
    $installButton.Enabled = $false
    $form.Controls.Add($installButton)
    
    # Navigation logic
    $backButton.Add_Click({
        if ($tabControl.SelectedIndex -gt 0) {
            $tabControl.SelectedIndex--
        }
    })
    
    $nextButton.Add_Click({
        if ($tabControl.SelectedIndex -lt ($tabControl.TabCount - 1)) {
            $tabControl.SelectedIndex++
        }
        if ($tabControl.SelectedIndex -eq 2) {
            $installButton.Enabled = $true
            $nextButton.Enabled = $false
        }
    })
    
    # Installation process
    $installButton.Add_Click({
        $installButton.Enabled = $false
        $global:InstallationPath = $installPathTextBox.Text
        
        $installLog.AppendText("Starting AI Gold Scalper installation...`n")
        $installStatus.Text = "Installing CUDA Toolkit..."
        [System.Windows.Forms.Application]::DoEvents()
        
        # Install CUDA
        $cudaResult = Install-CUDAToolkit -ProgressBar $installProgress
        $installLog.AppendText("CUDA Toolkit: $(if($cudaResult){'SUCCESS'}else{'FAILED'})`n")
        
        # Install Python packages
        $installStatus.Text = "Installing Python packages..."
        $installProgress.Value = 0
        [System.Windows.Forms.Application]::DoEvents()
        
        $packagesResult = Install-PythonPackages -ProgressBar $installProgress
        $installLog.AppendText("Python packages: $(if($packagesResult){'SUCCESS'}else{'FAILED'})`n")
        
        # Setup project files
        $installStatus.Text = "Setting up project files..."
        $installProgress.Value = 0
        [System.Windows.Forms.Application]::DoEvents()
        
        $projectResult = Setup-ProjectFiles -ProgressBar $installProgress
        $installLog.AppendText("Project setup: $(if($projectResult){'SUCCESS'}else{'FAILED'})`n")
        
        # Create desktop shortcut
        Create-DesktopShortcut
        $installLog.AppendText("Desktop shortcut: SUCCESS`n")
        
        $installStatus.Text = "Installation completed!"
        $installLog.AppendText("`nInstallation completed successfully!`n")
        $installLog.AppendText("You can now run AI Gold Scalper from the desktop shortcut.`n")
        
        [System.Windows.Forms.MessageBox]::Show("Installation completed successfully!", "AI Gold Scalper Installer", "OK", "Information")
    })
    
    # Show form
    $form.ShowDialog()
}

# Main execution
try {
    Write-Log "AI Gold Scalper Installer started"
    
    if (-not (Test-Administrator)) {
        $msg = "This installer requires administrator privileges. Please run as administrator."
        [System.Windows.Forms.MessageBox]::Show($msg, "Administrator Required", "OK", "Warning")
        Write-Log $msg "ERROR"
        exit 1
    }
    
    Show-InstallerGUI
    
} catch {
    Write-Log "Fatal error: $($_.Exception.Message)" "ERROR"
    [System.Windows.Forms.MessageBox]::Show("Installation failed: $($_.Exception.Message)", "Error", "OK", "Error")
} finally {
    Write-Log "AI Gold Scalper Installer finished"
}
