# =============================================================================
# PowerShell Script to Scaffold Subfolders for the Wikimedia Trends Engine
# =============================================================================
#
# This script will:
# 1. Create the subdirectory structure (terraform, src, etc.) in the
#    CURRENT directory.
# 2. Create all the necessary empty files (.tf, .py, .sh, .md, .txt)
#    ready for you to populate with code.
#
# Usage:
# 1. CD into your "wikimedia-trends-engine-cloud" project folder.
# 2. Save this file inside it as "Create-Project-Subfolders.ps1".
# 3. Open a PowerShell terminal in that folder.
# 4. Run the script: .\Create-Project-Subfolders.ps1
#
# =============================================================================

Write-Host "🚀 Scaffolding project structure in the current directory..." -ForegroundColor Green

# --- Create Main Directories ---
New-Item -ItemType Directory -Path ".\terraform" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path ".\src" -ErrorAction SilentlyContinue

# --- Create Source Subdirectories ---
Write-Host "  -> Creating src subdirectories..."
New-Item -ItemType Directory -Path ".\src\streaming" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path ".\src\batch" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path ".\src\producer" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path ".\src\dags" -ErrorAction SilentlyContinue

# --- Create Empty Terraform Files ---
Write-Host "  -> Creating empty Terraform files..."
$terraformFiles = @(
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "networking.tf",
    "storage.tf",
    "catalog.tf",
    "security.tf",
    "compute.tf",
    "userdata.sh"
)
foreach ($file in $terraformFiles) {
    New-Item -ItemType File -Path ".\terraform\$file" -Force
}

# --- Create Empty Application Code Files ---
Write-Host "  -> Creating empty application files..."
New-Item -ItemType File -Path ".\src\streaming\streaming_job.py" -Force
New-Item -ItemType File -Path ".\src\batch\batch_job.py" -Force
New-Item -ItemType File -Path ".\src\producer\producer.py" -Force
New-Item -ItemType File -Path ".\src\dags\wikimedia_batch_dag.py" -Force

# --- Create Root Project Files ---
Write-Host "  -> Creating root project files..."
New-Item -ItemType File -Path ".\README.md" -Force
New-Item -ItemType File -Path ".\requirements.txt" -Force

Write-Host "✅ Project structure created successfully in the current directory." -ForegroundColor Green
Write-Host "You can now start populating the files with code."