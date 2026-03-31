# Deploying Terminal Zero Governance on Azure AKS

This guide covers running the governance control plane as a Kubernetes Job on Azure AKS.

## Prerequisites

- Azure CLI (`az`) configured and logged in
- `kubectl` connected to your AKS cluster (`az aks get-credentials`)
- `helm` v3.x installed
- Docker image pushed to Azure Container Registry (ACR)
- A PersistentVolumeClaim (PVC) named `governance-workspace` containing your governed repository

## 1. Use Published Image (recommended)

```bash
# Pull official image from GHCR
docker pull ghcr.io/<org>/terminal-zero-governance:latest

# Optional: mirror into ACR
ACR_NAME=myacr  # replace with your ACR name
az acr login --name $ACR_NAME
docker tag ghcr.io/<org>/terminal-zero-governance:latest ${ACR_NAME}.azurecr.io/terminal-zero-governance:0.2.0
docker push ${ACR_NAME}.azurecr.io/terminal-zero-governance:0.2.0
```

## 2. Attach ACR to AKS

```bash
az aks update \
  --name my-aks-cluster \
  --resource-group my-resource-group \
  --attach-acr $ACR_NAME
```

## 3. Provision the Workspace PVC

Create a PVC backed by Azure Files (supports ReadWriteMany):

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: governance-workspace
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: azurefile
  resources:
    requests:
      storage: 5Gi
```

Apply with: `kubectl apply -f workspace-pvc.yaml`

Sync your repository contents into the PVC via a CI step or init container.

## 4. Install the Helm Chart

```bash
# From quant_current_scope/
helm install governance ./charts/terminal-zero-governance \
  --set image.repository=${ACR_NAME}.azurecr.io/terminal-zero-governance \
  --set image.tag=0.2.0 \
  --set workspace.pvcName=governance-workspace
```

## 5. Verify the Job

```bash
kubectl get jobs
kubectl logs job/governance-terminal-zero-governance
```

## 6. One-shot healthcheck

```bash
kubectl run governance-health --rm -it --restart=Never \
  --image=${ACR_NAME}.azurecr.io/terminal-zero-governance:0.2.0 -- sop healthcheck
```

Exit code 0 = installation healthy.

## Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|-------------|------------|
| `ERROR: Missing script` on every step | PVC too narrow or wrong mountPath | Confirm full repo root is at `/workspace` |
| `FATAL failure_class=INSTALL_ERROR` | Package not on PATH | Rebuild image with correct ENV PATH |
| `ImagePullBackOff` | ACR not attached to AKS | Run `az aks update --attach-acr` |
| Azure Files mount timeout | Storage account firewall | Allow AKS node subnet in storage account network rules |
