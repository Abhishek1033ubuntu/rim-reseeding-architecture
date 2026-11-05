#!/usr/bin/env bash
# ==============================================================================
# RIM Handset Re-Inception Repository Initializer & Push Automation Script
# ==============================================================================
# File: publish_repo.sh
# License: Apache-2.0
# Description:
#   Automates local git initialization, branch configuration, .gitignore generation,
#   file staging, commit creation, and pushing to the target GitHub repository.
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status

REPO_NAME="rim-reseeding-architecture"
GITHUB_USER="Abhishek1033ubuntu"
REMOTE_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
DEFAULT_BRANCH="main"

echo "======================================================================"
echo "      RIM RE-SEEDING ARCHITECTURE: GITHUB PUBLISHING AUTOMATION      "
echo "======================================================================"

# 1. Check for Git CLI
if ! command -v git &> /dev/null; then
    echo "[-] Error: Git CLI is not installed. Please install git and retry."
    exit 1
fi

# 2. Initialize Git Repository
if [ ! -d ".git" ]; then
    echo "[*] Initializing local Git repository..."
    git init -b "${DEFAULT_BRANCH}"
else
    echo "[*] Git repository already initialized."
fi

# 3. Create Production .gitignore
if [ ! -f ".gitignore" ]; then
    echo "[*] Generating production .gitignore..."
    cat << 'EOF' > .gitignore
# Python Bytecode & Virtual Environments
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/
*.json
!models/sim_results.json
!models/financial_summary.json

# C Build Artifacts & Kernel Module Logs
*.o
*.ko
*.mod
*.mod.c
*.symvers
*.order
.tmp_versions/

# IDE & OS Metadata
.DS_Store
Thumbs.db
.vscode/
.idea/

# CAD Lock & Backup Files
*.bak
*.dwl
*.dwl2
EOF
    echo "[+] .gitignore created successfully."
fi

# 4. Configure Remote Origin URL
if git remote | grep -q "^origin$"; then
    echo "[*] Updating existing Git remote 'origin' to ${REMOTE_URL}..."
    git remote set-url origin "${REMOTE_URL}"
else
    echo "[*] Adding Git remote 'origin' pointing to ${REMOTE_URL}..."
    git remote add origin "${REMOTE_URL}"
fi

# 5. Audit Core Repository Files Before Staging
echo "[*] Auditing core architecture file inventory..."
REQUIRED_FILES=(
    "LICENSE-HARDWARE"
    "LICENSE-SOFTWARE"
    "README.md"
    "docs/rim_executive_master_deck.pdf"
    "docs/qms-dpmo-protocol-spec.md"
    "docs/software-persona-overlays.md"
    "docs/chips-act-grant-proposal.md"
    "docs/agentic-ai-enterprise-restructuring.md"
    "models/monte_carlo_launch_sim.py"
    "models/2_chassis_bom_financial_engine.py"
    "hardware/r_sce_asic_12nm_block_diagram.svg"
    "firmware/r_sce_dma_crypto_driver.c"
    "firmware/pcv_enclave_provisioner.py"
    "firmware/rim-r-sce.dts"
)

MISSING_COUNT=0
for FILE in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        echo "  [!] Warning: File missing locally: $FILE"
        MISSING_COUNT=$((MISSING_COUNT+1))
    fi
done

if [ $MISSING_COUNT -eq 0 ]; then
    echo "[+] All required core architecture files verified."
else
    echo "[!] Proceeding with $MISSING_COUNT missing optional/un-staged files."
fi

# 6. Stage All Local Files
echo "[*] Staging files for commit..."
git add .

# 7. Create Formatted Release Commit
COMMIT_MSG="feat(core): Publish RIM Handset Re-Inception Architectural Framework

- Dual-Licensing topology: CERN-OHL-S-2.0 (Hardware) & Apache-2.0 (Software)
- Master Executive PDF Deck, QMS Spec (<35 DPMO), and Software Personas
- Vectorized Monte Carlo launch engine & 2-Chassis BOM financial model
- Low-level 12nm R-SCE Companion ASIC C driver, DTS node, and PCV provisioner
- US CHIPS Act Title IV grant proposal ($14.50M matching request)
- Agentic AI Enterprise Restructuring Strategy ($15.20M/yr OpEx savings)"

echo "[*] Committing files..."
git commit -m "$COMMIT_MSG" || echo "[*] Working tree clean, nothing new to commit."

# 8. Push to GitHub Remote
echo "[*] Pushing repository to GitHub remote (${DEFAULT_BRANCH} branch)..."
git push -u origin "${DEFAULT_BRANCH}"

echo "======================================================================"
echo "[+] SUCCESS: Repository published to ${REMOTE_URL}"
echo "======================================================================"
