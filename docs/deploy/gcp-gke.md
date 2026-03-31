# Deploying Terminal Zero Governance on GCP GKE

This guide covers running the governance control plane as a Kubernetes Job on Google Kubernetes Engine.

## Prerequisites

- `gcloud` CLI configured and authenticated
- `kubectl` connected to your GKE cluster (`gcloud container clusters get-credentials`)
- `helm` v3.x installed
- Docker image pushed to Artifact Registry
- A PersistentVolumeClaim (PVC) named `governance-workspace` containing your governed repository

## 1. Use Published Image (recommended)

```bash
# Pull official image from GHCR
docker pull ghcr.io/<org>/terminal-zero-governance:latest

# Optional: mirror into Artifact Registry
REGION=us-central1
PROJECT_ID=$(gcloud config get-value project)
REPO=terminal-zero

gcloud auth configure-docker ${REGION}-docker.pkg.dev
docker tag ghcr.io/<org>/terminal-zero-governance:latest \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/terminal-zero-governance:0.2.0
docker push \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/terminal-zero-governance:0.2.0
```

## 2. Provision the Workspace PVC

Create a PVC backed by Filestore (NFS, supports ReadWriteMany) or a regional persistent disk:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: governance-workspace
spec:
  accessModes:
    - ReadWriteOnce  # use ReadWriteMany with Filestore for multi-node
  storageClassName: standard-rwo
  resources:
    requests:
      storage: 10Gi
```

Apply with: `kubectl apply -f workspace-pvc.yaml`

Sync your repository into the PVC via a CI init step.

## 3. Install the Helm Chart

```bash
# From quant_current_scope/
helm install governance ./charts/terminal-zero-governance \
  --set image.repository=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/terminal-zero-governance \
  --set image.tag=0.2.0 \
  --set workspace.pvcName=governance-workspace
```

## 4. Verify the Job

```bash
kubectl get jobs
kubectl logs job/governance-terminal-zero-governance
```

## 5. One-shot healthcheck

```bash
kubectl run governance-health --rm -it --restart=Never \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/terminal-zero-governance:0.2.0 \
  -- sop healthcheck
```

Exit code 0 = installation healthy.

## 6. Workload Identity (recommended)

If your governance scripts access GCP APIs, attach a Kubernetes Service Account to a
GCP Service Account via Workload Identity rather than mounting key files:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  governance-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[default/governance]"
```

## Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|-------------|------------|
| `ERROR: Missing script` on every step | PVC too narrow | Confirm full repo root at `/workspace` |
| `FATAL failure_class=INSTALL_ERROR` | `sop` not on PATH in image | Rebuild image; check `ENV PATH=/install/bin:$PATH` |
| `ImagePullBackOff` | Artifact Registry auth | Run `gcloud auth configure-docker ${REGION}-docker.pkg.dev` and confirm image path/repo permissions |
