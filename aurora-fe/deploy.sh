#!/bin/bash
# aurora-fe/deploy.sh - Deploy Aurora Frontend to Infinity
#
# Deploys:
# - Components → infinity/src/aurora/components/
# - Stores → infinity/src/stores/
# - Composables → infinity/src/composables/
# - Views → infinity/src/aurora/views/
# - Routes → infinity/src/routes/aurora.js
# - Navigation → infinity/src/navigation/aurora.js
#
# Usage:
#   DEPLOY_TARGET_PATH=/path/to/infinity ./deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${DEPLOY_TARGET_PATH:-../infinity}"

echo "Deploying Aurora FE to $TARGET..."

# =============================================================================
# Create target directories
# =============================================================================
mkdir -p "$TARGET/src/aurora/components"
mkdir -p "$TARGET/src/aurora/views"
mkdir -p "$TARGET/src/stores"
mkdir -p "$TARGET/src/composables"
mkdir -p "$TARGET/src/routes"
mkdir -p "$TARGET/src/navigation"

# =============================================================================
# Deploy components
# =============================================================================
echo "  → Deploying components..."

if [ -d "${SCRIPT_DIR}/components" ]; then
    find "${SCRIPT_DIR}/components" -name '*.vue' -exec cp {} "$TARGET/src/aurora/components/" \; 2>/dev/null || true
fi

# =============================================================================
# Deploy views
# =============================================================================
echo "  → Deploying views..."

if [ -d "${SCRIPT_DIR}/views" ]; then
    find "${SCRIPT_DIR}/views" -name '*.vue' -exec cp {} "$TARGET/src/aurora/views/" \; 2>/dev/null || true
fi

# =============================================================================
# Deploy stores
# =============================================================================
echo "  → Deploying stores..."

if [ -d "${SCRIPT_DIR}/stores" ]; then
    for store_file in "${SCRIPT_DIR}/stores/"*.js "${SCRIPT_DIR}/stores/"*.ts; do
        if [ -f "$store_file" ]; then
            cp "$store_file" "$TARGET/src/stores/"
        fi
    done
fi

# =============================================================================
# Deploy composables
# =============================================================================
echo "  → Deploying composables..."

if [ -d "${SCRIPT_DIR}/composables" ]; then
    for composable_file in "${SCRIPT_DIR}/composables/"*.js "${SCRIPT_DIR}/composables/"*.ts; do
        if [ -f "$composable_file" ]; then
            cp "$composable_file" "$TARGET/src/composables/"
        fi
    done
fi

# =============================================================================
# Deploy routes
# =============================================================================
echo "  → Deploying routes..."

if [ -f "${SCRIPT_DIR}/routes.js" ]; then
    cp "${SCRIPT_DIR}/routes.js" "$TARGET/src/routes/aurora.js"
fi

# =============================================================================
# Deploy navigation
# =============================================================================
echo "  → Deploying navigation..."

if [ -f "${SCRIPT_DIR}/navigation.js" ]; then
    cp "${SCRIPT_DIR}/navigation.js" "$TARGET/src/navigation/aurora.js"
fi

echo "  ✓ Aurora FE deployed to $TARGET"
