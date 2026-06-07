#!/usr/bin/env bash
# ============================================================
#  azure/deploy.sh
#  Deploy Bhagavad Gita RAG ChatBot to Azure Web Apps
#  Prerequisites: az CLI logged in, Docker running
# ============================================================
set -e

# ── Config — edit these ──────────────────────────────────────
RESOURCE_GROUP="bhagavad-gita-rg"
LOCATION="eastus"
ACR_NAME="bhagavadgitaacr"          # must be globally unique, lowercase, 5-50 chars
APP_SERVICE_PLAN="gita-plan"
BACKEND_APP="bhagavad-gita-api"     # must be globally unique
FRONTEND_APP="bhagavad-gita-ui"     # must be globally unique
SKU="B2"                            # B1/B2/B3 for basic; P1v3 for production
# ─────────────────────────────────────────────────────────────

if [ -z "$OPENAI_API_KEY" ]; then
  echo "ERROR: OPENAI_API_KEY environment variable is not set."
  exit 1
fi

echo "==> Creating Resource Group: $RESOURCE_GROUP"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "==> Creating Azure Container Registry: $ACR_NAME"
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true

echo "==> Creating App Service Plan: $APP_SERVICE_PLAN"
az appservice plan create \
  --name "$APP_SERVICE_PLAN" \
  --resource-group "$RESOURCE_GROUP" \
  --sku "$SKU" \
  --is-linux

# ── Backend ─────────────────────────────────────────────────
echo "==> Building & pushing backend image"
az acr build \
  --registry "$ACR_NAME" \
  --image gita-backend:latest \
  ./backend

echo "==> Creating backend Web App"
az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$BACKEND_APP" \
  --deployment-container-image-name "$ACR_NAME.azurecr.io/gita-backend:latest"

echo "==> Configuring backend environment"
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$BACKEND_APP" \
  --settings \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    WEBSITES_PORT=8000

# ── Frontend ─────────────────────────────────────────────────
echo "==> Building & pushing frontend image"
az acr build \
  --registry "$ACR_NAME" \
  --image gita-frontend:latest \
  ./frontend

echo "==> Creating frontend Web App"
az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$FRONTEND_APP" \
  --deployment-container-image-name "$ACR_NAME.azurecr.io/gita-frontend:latest"

# ── Done ─────────────────────────────────────────────────────
BACKEND_URL="https://${BACKEND_APP}.azurewebsites.net"
FRONTEND_URL="https://${FRONTEND_APP}.azurewebsites.net"

echo ""
echo "=============================================="
echo " Deployment complete!"
echo " Backend  : $BACKEND_URL"
echo " Frontend : $FRONTEND_URL"
echo " API Docs : ${BACKEND_URL}/api/docs"
echo "=============================================="
echo ""
echo "NOTE: Update the CORS origins in backend/app/main.py"
echo "      to include $FRONTEND_URL before deploying to production."
