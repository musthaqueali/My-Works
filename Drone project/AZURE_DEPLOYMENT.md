# Deploying PUCDesk Cloud to Microsoft Azure

This guide explains how to deploy this PUC Centre Management System to **Microsoft Azure** using **Azure App Service (Linux Web App)** or **Azure Container Apps**.

---

## Option 1: Azure App Service (Quickest & Free/Low Cost Tier)

### Step 1: Install Azure CLI & Login
```bash
az login
```

### Step 2: Create a Resource Group
```bash
az group create --name PUCDesk-RG --location centralindia
```

### Step 3: Create an App Service Plan (Linux)
Choose either Free (`F1`) for testing or Basic (`B1`) for production:
```bash
az appservice plan create \
  --name PUCDesk-Plan \
  --resource-group PUCDesk-RG \
  --is-linux \
  --sku B1
```

### Step 4: Create the Web App with Python 3.12 Runtime
```bash
az webapp create \
  --resource-group PUCDesk-RG \
  --plan PUCDesk-Plan \
  --name pucdesk-app \
  --runtime "PYTHON:3.12"
```

### Step 5: Configure Application Settings (Environment Variables)
In the Azure Portal or via CLI, configure the startup command and Cashfree credentials:
```bash
az webapp config set \
  --resource-group PUCDesk-RG \
  --name pucdesk-app \
  --startup-file "uvicorn main:app --host 0.0.0.0 --port 8000"

az webapp config appsettings set \
  --resource-group PUCDesk-RG \
  --name pucdesk-app \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    CASHFREE_ENV="TEST" \
    CASHFREE_APP_ID="YOUR_CASHFREE_APP_ID" \
    CASHFREE_SECRET_KEY="YOUR_CASHFREE_SECRET_KEY" \
    SMS_SENDER_ID="AIRPOL-KL"
```

### Step 6: Deploy Code
You can deploy using GitHub Actions or direct zip deployment:
```bash
# Direct deployment from local project root
az webapp up --resource-group PUCDesk-RG --name pucdesk-app
```

Your app will be live at: `https://pucdesk-app.azurewebsites.net`

---

## Option 2: Azure Container Apps (Dockerized)

If you prefer deploying the provided `Dockerfile`:
```bash
# 1. Build and push to Azure Container Registry (ACR)
az acr create --resource-group PUCDesk-RG --name pucdeskacr --sku Basic --admin-enabled true
az acr build --registry pucdeskacr --image pucdesk:v1 .

# 2. Deploy to Azure Container App
az containerapp up \
  --name pucdesk-app \
  --resource-group PUCDesk-RG \
  --location centralindia \
  --environment 'pucdesk-env' \
  --image pucdeskacr.azurecr.io/pucdesk:v1 \
  --target-port 8000 \
  --ingress external
```

---

## Setting up Cashfree Payment Webhooks in Production

1. Log into [Cashfree Merchant Dashboard](https://merchant.cashfree.com/).
2. Navigate to **Payment Gateway > Developers > Webhooks**.
3. Add your webhook URL:
   ```
   https://pucdesk-app.azurewebsites.net/api/payments/webhook
   ```
4. Select event: `ORDER.PAID` or `PAYMENT.SUCCESS_WEBHOOK`.
5. Enter your Webhook Secret in Azure App Settings (`CASHFREE_SECRET_KEY`).
