# Deploying Terminal Zero Governance on AWS EKS

This guide covers running the governance control plane as a Kubernetes Job on Amazon EKS.

## Prerequisites

- AWS CLI configured with appropriate IAM permissions
- `kubectl` connected to your EKS cluster (`aws eks update-kubeconfig`)
- `helm` v3.x installed
- Docker image pushed to ECR or a registry accessible from the cluster
- A PersistentVolumeClaim (PVC) named `governance-workspace` containing your governed repository

## 1. Build and Push the Image

```bash
# From quant_current_scope/
docker build -t terminal-zero-governance:0.2.0 .

# Tag and push to ECR
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
ECR_REPO=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/terminal-zero-governance

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${ECR_REPO}
docker tag terminal-zero-governance:0.2.0 ${ECR_REPO}:0.2.0
docker push ${ECR_REPO}:0.2.0
```

## 2. Provision the Workspace PVC

Create a PVC that holds your governed repository. Example using EFS CSI driver:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: governance-workspace
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 5Gi
```

Apply with: `kubectl apply -f workspace-pvc.yaml`

Then sync your repository contents into the PVC (e.g. via an init Job or a CI step that
uses `kubectl cp` or an S3 sync).

## 3. Install the Helm Chart

```bash
# From quant_current_scope/
helm install governance ./charts/terminal-zero-governance \
  --set image.repository=${ECR_REPO} \
  --set image.tag=0.2.0 \
  --set workspace.pvcName=governance-workspace
```

## 4. Verify the Job

```bash
kubectl get jobs
kubectl logs job/governance-terminal-zero-governance
```

Expect the final line to include `final_result=READY` or `final_result=NOT_READY` — never a
silent exit without an artifact.

## 5. One-shot healthcheck

```bash
kubectl run governance-health --rm -it --restart=Never \
  --image=${ECR_REPO}:0.2.0 -- sop healthcheck
```

Exit code 0 = installation healthy. Non-zero = preflight failure (check stderr for FATAL envelope).

## Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|-------------|------------|
| `ERROR: Missing script` on every step | PVC mounted at wrong path or too narrow | Confirm PVC contains full repo root at `/workspace` |
| `FATAL failure_class=INSTALL_ERROR` | `sop` entrypoint not on PATH in image | Rebuild image; confirm `PATH=/install/bin:$PATH` in Dockerfile |
| Job restarts immediately | Missing `restartPolicy: Never` | Upgrade chart to latest version |
| `ImagePullBackOff` | ECR auth expired | Re-run `aws ecr get-login-password` and update imagePullSecrets |
