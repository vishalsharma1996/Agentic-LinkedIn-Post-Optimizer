```bash
Azure Login:

az login
az account show

Create Resource Group:

az group create --name rg-agentic-linkedin --location eastus

Create Azure Container Registry (ACR):

az provider register --namespace Microsoft.ContainerRegistry
az acr create \
  --resource-group rg-agentic-linkedin \
  --name agenticacr001 \
  --sku Basic \
  --admin-enabled true

Push Docker Image to ACR:

az acr login --name agenticacr001
docker tag agentic-linkedin-post-optimizer \
  agenticacr001.azurecr.io/agentic-linkedin-post-optimizer:v1
docker push agenticacr001.azurecr.io/agentic-linkedin-post-optimizer:v1

Register Azure Providers (One-Time):

az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.KeyVault


Create Azure Key Vault (RBAC Enabled)

az keyvault create \
  --name agentic-kv-001 \
  --resource-group rg-agentic-linkedin \
  --location eastus \
  --enable-rbac-authorization true

Store Secrets in Key Vault

az keyvault secret set --vault-name agentic-kv-001 --name OPENAI-API-KEY --value sk-xxxx
az keyvault secret set --vault-name agentic-kv-001 --name LANGCHAIN-API-KEY --value ls-xxxx
az keyvault secret set --vault-name agentic-kv-001 --name LANGCHAIN-TRACING-V2 --value true
az keyvault secret set --vault-name agentic-kv-001 --name LANGCHAIN-PROJECT --value agentic-linkedin-post-optimizer

Key Vault secret names use hyphens (-), not underscores.

Create Container Apps Environment:

az containerapp env create \
  --name agentic-env \
  --resource-group rg-agentic-linkedin \
  --location eastus

Deploy Container App:

az containerapp create \
  --name agentic-linkedin-app \
  --resource-group rg-agentic-linkedin \
  --environment agentic-env \
  --image agenticacr001.azurecr.io/agentic-linkedin-post-optimizer:v1 \
  --registry-server agenticacr001.azurecr.io \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1

Get Public URL:

az containerapp show \
  --name agentic-linkedin-app \
  --resource-group rg-agentic-linkedin \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv


Set Environment Variables (Azure Runtime): # Use this only for demos

az containerapp update \
  --name agentic-linkedin-app \
  --resource-group rg-agentic-linkedin \
  --set-env-vars \
    OPENAI_API_KEY=sk-xxxx \
    LANGCHAIN_API_KEY=ls-xxxx \
    LANGCHAIN_TRACING_V2=true \
    LANGCHAIN_PROJECT=agentic-linkedin-post-optimizer

Enable Managed Identity for Container Apps

az containerapp identity assign \
  --name agentic-linkedin-app \
  --resource-group rg-agentic-linkedin \
  --system-assigned

Grant Container App Access to Key Vault

az role assignment create \
  --assignee-object-id <CONTAINER_APP_PRINCIPAL_ID> \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-agentic-linkedin/providers/Microsoft.KeyVault/vaults/agentic-kv-001

Materialize Key Vault Secrets into Container App Secrets

Azure Container Apps cannot reference Key Vault secrets directly.
Secrets must first be snapshotted into Container App secrets per revision.

az containerapp secret set \
  --name agentic-linkedin-app \
  --resource-group rg-agentic-linkedin \
  --secrets \
    openai-api-key=keyvaultref:https://agentic-kv-001.vault.azure.net/secrets/OPENAI-API-KEY,identityref:system \
    langchain-api-key=keyvaultref:https://agentic-kv-001.vault.azure.net/secrets/LANGCHAIN-API-KEY,identityref:system \
    langchain-tracing-v2=keyvaultref:https://agentic-kv-001.vault.azure.net/secrets/LANGCHAIN-TRACING-V2,identityref:system \
    langchain-project=keyvaultref:https://agentic-kv-001.vault.azure.net/secrets/LANGCHAIN-PROJECT,identityref:system

Bind Environment Variables to Container App Secrets

az containerapp update \
  --name agentic-linkedin-app \
  --resource-group rg-agentic-linkedin \
  --set-env-vars \
    OPENAI_API_KEY=secretref:openai-api-key \
    LANGCHAIN_API_KEY=secretref:langchain-api-key \
    LANGCHAIN_TRACING_V2=secretref:langchain-tracing-v2 \
    LANGCHAIN_PROJECT=secretref:langchain-project

Important: Secret Rotation Model

1) Updating a Key Vault secret does NOT update the running app automatically

2) A new Container App revision is required

3) Re-running az containerapp secret set or any update command triggers a new revision

4) This design ensures deterministic, rollback-safe deployments.


Stop Application (No Compute Cost):

az containerapp ingress disable \
  --name agentic-linkedin-app \
  --resource-group rg-agentic-linkedin

Restart Application:

az containerapp ingress enable \
  --name agentic-linkedin-app \
  --resource-group rg-agentic-linkedin \
  --type external \
  --target-port 8000

Notes

1) Secrets are injected at runtime via Azure Container Apps.

2) No secrets are stored in the image or repository.

3) Scale-to-zero ensures minimal cost when idle.

4) Any code change requires rebuilding and pushing a new Docker image.

```