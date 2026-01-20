#!/bin/bash
# aurora-be/deploy.sh - Deploy Aurora Backend to Matrix
#
# Deploys:
# - Models → matrix/src/models/
# - Schemas → matrix/src/schemas/
# - Services → matrix/src/services/
# - Routers → matrix/src/modules/aurora/
# - Migrations → matrix/alembic/versions/
#
# Usage:
#   DEPLOY_TARGET_PATH=/path/to/matrix ./deploy.sh
#   DEPLOY_TARGET_PATH=/path/to/matrix ./deploy.sh --migrate

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${DEPLOY_TARGET_PATH:-../matrix}"

echo "Deploying Aurora BE to $TARGET..."

# =============================================================================
# Create target directories
# =============================================================================
mkdir -p "$TARGET/src/modules/aurora/routers"
mkdir -p "$TARGET/src/models"
mkdir -p "$TARGET/src/schemas"
mkdir -p "$TARGET/src/services"
mkdir -p "$TARGET/alembic/versions"

# =============================================================================
# Deploy module package
# =============================================================================
echo "  → Deploying module package..."

# Copy main module files
cp "${SCRIPT_DIR}/__init__.py" "$TARGET/src/modules/aurora/"
cp "${SCRIPT_DIR}/router.py" "$TARGET/src/modules/aurora/"
cp "${SCRIPT_DIR}/config.py" "$TARGET/src/modules/aurora/"

# =============================================================================
# Deploy routers
# =============================================================================
echo "  → Deploying routers..."

if [ -d "${SCRIPT_DIR}/routers" ]; then
    cp -r "${SCRIPT_DIR}/routers/"*.py "$TARGET/src/modules/aurora/routers/" 2>/dev/null || true
    
    # Create routers __init__.py if not exists
    if [ ! -f "$TARGET/src/modules/aurora/routers/__init__.py" ]; then
        echo '"""Aurora Routers"""' > "$TARGET/src/modules/aurora/routers/__init__.py"
    fi
fi

# =============================================================================
# Deploy models
# =============================================================================
echo "  → Deploying models..."

if [ -d "${SCRIPT_DIR}/models" ]; then
    for model_file in "${SCRIPT_DIR}/models/"*.py; do
        if [ -f "$model_file" ] && [ "$(basename "$model_file")" != "__init__.py" ]; then
            cp "$model_file" "$TARGET/src/models/"
        fi
    done
fi

# =============================================================================
# Deploy schemas
# =============================================================================
echo "  → Deploying schemas..."

if [ -d "${SCRIPT_DIR}/schemas" ]; then
    for schema_file in "${SCRIPT_DIR}/schemas/"*.py; do
        if [ -f "$schema_file" ] && [ "$(basename "$schema_file")" != "__init__.py" ]; then
            cp "$schema_file" "$TARGET/src/schemas/"
        fi
    done
fi

# =============================================================================
# Deploy services
# =============================================================================
echo "  → Deploying services..."

if [ -d "${SCRIPT_DIR}/services" ]; then
    for service_file in "${SCRIPT_DIR}/services/"*.py; do
        if [ -f "$service_file" ] && [ "$(basename "$service_file")" != "__init__.py" ]; then
            cp "$service_file" "$TARGET/src/services/"
        fi
    done
fi

# =============================================================================
# Deploy migrations
# =============================================================================
echo "  → Deploying migrations..."

if [ -d "${SCRIPT_DIR}/migrations" ]; then
    find "${SCRIPT_DIR}/migrations" -name '*.py' -exec cp {} "$TARGET/alembic/versions/" \; 2>/dev/null || true
fi

echo "  ✓ Aurora BE deployed to $TARGET"

# =============================================================================
# Run migrations if requested
# =============================================================================
if [ "${DEPLOY_MIGRATE}" = "true" ] || [[ "$*" == *"--migrate"* ]]; then
    echo ""
    echo "  → Running migrations..."
    cd "$TARGET" && alembic upgrade head
    echo "  ✓ Migrations complete"
fi
