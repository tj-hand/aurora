#!/bin/bash
# deploy.sh - Deploy Aurora to Spark Stack
#
# This root script is called by Spark and delegates to:
# - aurora-fe/deploy.sh → Infinity (when DEPLOY_TARGET=infinity or not set)
# - aurora-be/deploy.sh → Matrix (when DEPLOY_TARGET=matrix or not set)
#
# Spark calls this script twice (once per target), so we check DEPLOY_TARGET
# to know which component to deploy.
#
# Usage:
#   ./deploy.sh                    # Deploy both (standalone mode)
#   ./deploy.sh --migrate          # Deploy both + run migrations
#   DEPLOY_TARGET=infinity ./deploy.sh  # Deploy FE only (Spark mode)
#   DEPLOY_TARGET=matrix ./deploy.sh    # Deploy BE only (Spark mode)
#   DEPLOY_MIGRATE=true ./deploy.sh     # Deploy + run migrations (env var)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments and env vars
RUN_MIGRATE="${DEPLOY_MIGRATE:-false}"
for arg in "$@"; do
    case $arg in
        --migrate)
            RUN_MIGRATE=true
            ;;
    esac
done

# Export for child scripts
export DEPLOY_MIGRATE="$RUN_MIGRATE"

# Determine what to deploy based on DEPLOY_TARGET (set by Spark)
DEPLOY_TARGET="${DEPLOY_TARGET:-}"
TARGET_PATH="${DEPLOY_TARGET_PATH:-}"

echo "Deploying Aurora..."

# =============================================================================
# Deploy Frontend to Infinity
# =============================================================================
# Deploy FE if: no target specified OR target is infinity
if [ -z "$DEPLOY_TARGET" ] || [ "$DEPLOY_TARGET" = "infinity" ]; then
    if [ -f "${SCRIPT_DIR}/aurora-fe/deploy.sh" ]; then
        echo ""
        echo "=== Aurora FE → Infinity ==="
        
        # Determine Infinity path
        INFINITY_PATH="$TARGET_PATH"
        if [ -z "$INFINITY_PATH" ] && [ -n "$REPOS_DIR" ]; then
            INFINITY_PATH="${REPOS_DIR}/infinity"
        fi
        if [ -z "$INFINITY_PATH" ]; then
            INFINITY_PATH="${SCRIPT_DIR}/../infinity"
        fi
        
        if [ -d "$INFINITY_PATH" ]; then
            DEPLOY_TARGET_PATH="$INFINITY_PATH" bash "${SCRIPT_DIR}/aurora-fe/deploy.sh"
        else
            echo "  [SKIP] Infinity not found at $INFINITY_PATH"
        fi
    fi
fi

# =============================================================================
# Deploy Backend to Matrix
# =============================================================================
# Deploy BE if: no target specified OR target is matrix
if [ -z "$DEPLOY_TARGET" ] || [ "$DEPLOY_TARGET" = "matrix" ]; then
    if [ -f "${SCRIPT_DIR}/aurora-be/deploy.sh" ]; then
        echo ""
        echo "=== Aurora BE → Matrix ==="
        
        # Determine Matrix path
        MATRIX_PATH="$TARGET_PATH"
        if [ -z "$MATRIX_PATH" ] && [ -n "$REPOS_DIR" ]; then
            MATRIX_PATH="${REPOS_DIR}/matrix"
        fi
        if [ -z "$MATRIX_PATH" ]; then
            MATRIX_PATH="${SCRIPT_DIR}/../matrix"
        fi
        
        if [ -d "$MATRIX_PATH" ]; then
            MIGRATE_FLAG=""
            if [ "$RUN_MIGRATE" = true ]; then
                MIGRATE_FLAG="--migrate"
            fi
            DEPLOY_TARGET_PATH="$MATRIX_PATH" bash "${SCRIPT_DIR}/aurora-be/deploy.sh" $MIGRATE_FLAG
        else
            echo "  [SKIP] Matrix not found at $MATRIX_PATH"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "Aurora deployment complete!"
echo "=========================================="

if [ "$RUN_MIGRATE" = false ] && { [ -z "$DEPLOY_TARGET" ] || [ "$DEPLOY_TARGET" = "matrix" ]; }; then
    echo ""
    echo "To run migrations (inside matrix container):"
    echo "  docker exec -it spark-matrix alembic upgrade head"
fi
