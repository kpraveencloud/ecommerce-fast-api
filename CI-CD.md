# Ecommerce API - CI/CD Pipeline Documentation

## Overview

This document outlines the complete CI/CD pipeline for the Ecommerce API service. The pipeline follows a 3-stage approach:
1. **CI (Build and Test)** — Automated testing and linting on every push/PR
2. **CD-Step1 (Registry Push)** — Build and push Docker image to GCR
3. **CD-Step2 (Deploy)** — Deploy to GKE cluster using Helm

All services run in the **same Kubernetes cluster** and are part of the **same unified architecture**.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│  ecommerce-fast-api (API Service)                               │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │  Build & Test    │ │  Registry Push   │ │  Deploy to Cluster│
    │  (CI Workflow)   │ │  (CD-Step 1)     │ │  (CD-Step 2)     │
    └──────────────────┘ └──────────────────┘ └──────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    Test & Lint Results    Docker Image         GKE Cluster
    (Codecov Upload)       in GCR Registry      ├─ Dev Namespace
                                                └─ Prod Namespace
```

---

## 1. Continuous Integration (Build & Test)

### Workflow File: `.github/workflows/build-and-test.yml`

**Trigger Events:**
- Push to `develop`, `main`, or `feature/*` branches
- Pull requests to `develop` or `main`
- Manual trigger via `workflow_dispatch`

**Steps:**
1. Checkout code
2. Set up Python 3.14
3. Install `uv` package manager
4. Install dependencies with `uv sync`
5. Run linting with `ruff check` and `ruff format --check`
6. Run type checking with `mypy` (non-blocking)
7. Run test suite with `pytest` and generate coverage report
8. Upload coverage to Codecov

**Configuration:**
- Runtime: Ubuntu latest
- Python: 3.14
- No secrets required

**Manual Trigger:**
```bash
# Via GitHub UI: Actions > Build and Test > Run workflow
# Or via CLI:
gh workflow run build-and-test.yml -f branch=develop
```

---

## 2. Docker Registry Push (CD - Step 1)

### Workflow File: `.github/workflows/registry-push.yml`

**Trigger Events:**
- Manual trigger via `workflow_dispatch` (recommended)
- Automatic push on tags matching `v*` (e.g., `v1.0.0`)
- Automatic push on merge to `main` branch

**Inputs (Manual Trigger):**
| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `image_tag` | Docker image tag | `latest` | ✅ Yes |
| `image_name` | Image name (e.g., `ecommerce-api`) | Fallback to secrets | ❌ No |
| `registry_url` | Registry URL (e.g., `gcr.io/project-id`) | Fallback to secrets | ❌ No |

**Steps:**
1. Checkout code
2. Set up Google Cloud SDK
3. Authenticate to GCP using service account key
4. Set up Docker Buildx
5. Configure Docker for GCR
6. Extract metadata (version, registry, image name)
7. Build and push Docker image to registry
8. Output image digest

**Secrets Required:**
- `GCP_PROJECT_ID` — GCP project ID
- `GCP_SA_KEY` — GCP service account JSON key
- `GCP_REGISTRY_URL` — GCR registry URL (e.g., `gcr.io/your-project-id`)
- `DOCKER_IMAGE_NAME` — Docker image name (e.g., `ecommerce-api`)

**How to Configure Secrets:**
1. Go to GitHub repository → Settings → Secrets and Variables → Actions
2. Create/update each secret:
   ```
   GCP_PROJECT_ID = your-gcp-project
   GCP_REGISTRY_URL = gcr.io/your-gcp-project
   DOCKER_IMAGE_NAME = ecommerce-api
   GCP_SA_KEY = {complete JSON from GCP service account key file}
   ```

**Manual Trigger Example:**
```bash
# Using GitHub CLI
gh workflow run registry-push.yml \
  -f image_tag=v1.0.0 \
  -f image_name=ecommerce-api \
  -f registry_url=gcr.io/my-project

# Or via GitHub UI:
# Actions > Push to Registry > Run workflow > Fill inputs
```

**Output:**
- Docker image pushed to: `gcr.io/your-project/ecommerce-api:v1.0.0`
- Also tagged as: `gcr.io/your-project/ecommerce-api:latest`

---

## 3. Deploy to Cluster (CD)

### Workflow File: `.github/workflows/deploy.yml`

**Trigger Events:**
- Manual trigger via `workflow_dispatch` (only way to deploy)

**Inputs (Required):**
| Input | Description | Options | Default |
|-------|-------------|---------|---------|
| `environment` | Target environment | `dev`, `prod` | `dev` |
| `image_tag` | Image tag to deploy | Any string | `latest` |
| `image_name` | Image name | Any string | Fallback to secrets |
| `registry_url` | Registry URL | Any string | Fallback to secrets |

**Deployment Steps:**
1. Checkout code
2. Authenticate to GCP
3. Get GKE cluster credentials
4. Set up Helm CLI
5. Verify deployment target and cluster access
6. Update Helm repositories
7. Lint Helm chart
8. Deploy/update Helm release:
   - **Dev**: `dev` namespace, 5min timeout
   - **Prod**: `prod` namespace, 10min timeout, additional values file
9. Verify deployment rollout
10. Run health checks (HTTP GET to `/health` endpoint)
11. Create deployment annotations (prod only)
12. Notify deployment completion

**Secrets Required:**
- `GCP_PROJECT_ID` — GCP project ID
- `GCP_SA_KEY` — GCP service account JSON key
- `GKE_CLUSTER_NAME` — GKE cluster name (e.g., `ecommerce-cluster`)
- `GKE_ZONE` — GKE cluster zone (e.g., `us-central1-a`)
- `GCP_REGISTRY_URL` — GCR registry URL
- `DOCKER_IMAGE_NAME` — Docker image name

**Manual Deployment Example:**
```bash
# Deploy to dev with specific version
gh workflow run deploy.yml \
  -f environment=dev \
  -f image_tag=v1.0.0

# Deploy to prod
gh workflow run deploy.yml \
  -f environment=prod \
  -f image_tag=v1.0.0

# Via GitHub UI: Actions > Deploy to Cluster > Run workflow
```

**Deployment Locations:**
- **Dev**: Namespace `dev`
- **Prod**: Namespace `prod`

**Environment Differences:**
| Property | Dev | Prod |
|----------|-----|------|
| Replicas | 1 | 3 (with HPA scaling 3-10) |
| Timeout | 5m | 10m |
| Resource Limits | 500m CPU / 512Mi RAM | 1000m CPU / 1Gi RAM |
| Ingress | Disabled | Enabled with TLS |
| Log Level | INFO | WARNING |
| Health Check | `/health` | `/health` + `/ready` |

**Helm Release Name:** `ecommerce-api`

---

## Prerequisites Setup

### 1. GCP Service Account Setup

Create a service account with necessary permissions:

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/container.developer

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.admin

# Create and download JSON key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Copy contents of key.json to GCP_SA_KEY secret in GitHub
```

### 2. GitHub Secrets Configuration

Add these secrets to your GitHub repository:

```
Settings → Secrets and Variables → Actions → New Repository Secret
```

**Required Secrets:**

| Secret Name | Value | Example |
|-------------|-------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | `my-ecommerce-project` |
| `GCP_REGISTRY_URL` | GCR registry URL | `gcr.io/my-ecommerce-project` |
| `GCP_SA_KEY` | Service account JSON key | (entire JSON file content) |
| `DOCKER_IMAGE_NAME` | Docker image name | `ecommerce-api` |
| `GKE_CLUSTER_NAME` | GKE cluster name | `ecommerce-cluster` |
| `GKE_ZONE` | GKE cluster zone | `us-central1-a` |

### 3. Kubernetes Prerequisites

Ensure your GKE cluster has:

```bash
# Namespaces
kubectl create namespace dev
kubectl create namespace prod

# Service accounts (Helm creates these, but you can pre-create)
# These are created automatically by the Helm templates
```

### 4. Helm Chart Validation

Validate Helm chart locally:

```bash
# Lint the chart
helm lint ./helm

# Dry-run deployment
helm install ecommerce-api ./helm \
  --namespace dev \
  --dry-run \
  --debug
```

---

## Workflow Execution Guide

### Complete CI/CD Pipeline (Recommended Flow)

#### 1. Development Flow
```
Feature Branch → Create PR → CI Runs (Build & Test)
                                ↓
                    Review & Approve PR
                                ↓
                    Merge to develop
                                ↓
                    CI runs automatically
                                ↓
            Ready for Registry Push
```

#### 2. Release Flow
```
develop branch → Create Release PR to main
                         ↓
                    CI runs on PR
                         ↓
                  Merge to main
                         ↓
                Tag with v1.x.x
                         ↓
         Registry Push triggered automatically
                         ↓
    Manual: Trigger Deploy workflow to dev
                         ↓
              Test in dev environment
                         ↓
    Manual: Trigger Deploy workflow to prod
                         ↓
            Verify health checks pass
                         ↓
               Production live
```

### Manual Workflow Triggers

#### Trigger CI (Build & Test)
```bash
gh workflow run build-and-test.yml -f branch=develop
```

#### Trigger Registry Push
```bash
# Push with specific tag
gh workflow run registry-push.yml -f image_tag=v1.0.0

# Push latest
gh workflow run registry-push.yml -f image_tag=latest
```

#### Trigger Deployment
```bash
# Deploy to dev
gh workflow run deploy.yml \
  -f environment=dev \
  -f image_tag=v1.0.0

# Deploy to prod
gh workflow run deploy.yml \
  -f environment=prod \
  -f image_tag=v1.0.0
```

---

## Monitoring & Health Checks

### Health Check Endpoints

Your FastAPI app must expose these endpoints:

```python
@app.get("/health")
async def health_check():
    """Liveness probe endpoint"""
    return {"status": "ok"}

@app.get("/ready")
async def readiness_check():
    """Readiness probe endpoint (prod only)"""
    # Check database connectivity, cache, etc.
    return {"status": "ready"}
```

### Deployment Verification

After deployment, verify:

```bash
# Check rollout status
kubectl rollout status deployment/ecommerce-api -n dev

# View pod status
kubectl get pods -n dev -l app.kubernetes.io/name=ecommerce-api

# Check recent events
kubectl describe deployment ecommerce-api -n dev

# View logs
kubectl logs -n dev -l app.kubernetes.io/name=ecommerce-api --tail=50
```

### Health Probe Configuration

**Liveness Probe** (checks if pod is alive):
- Path: `/health`
- Initial delay: 30s
- Period: 10s
- Timeout: 5s
- Failure threshold: 3

**Readiness Probe** (checks if pod can receive traffic):
- Path: `/ready`
- Initial delay: 10s (prod: 30s)
- Period: 5s
- Timeout: 3s
- Failure threshold: 2

---

## Environment Variables

### Available Variables

See `helm/values.yaml` for all environment variables. Key ones:

```yaml
env:
  ENVIRONMENT: "development"        # dev or production
  LOG_LEVEL: "INFO"                 # Log level
  DATABASE_URL: "sqlite:///..."     # Database connection
  PROJECT_NAME: "Ecommerce FastAPI" # Project name
  API_V1_STR: "/api/v1"             # API prefix
  ACCESS_TOKEN_EXPIRE_MINUTES: "11520"
```

### Modifying Environment Variables

1. **Dev environment**: Edit `helm/values.yaml`
2. **Prod environment**: Add/override in `helm/values-prod.yaml`
3. Deploy with: `gh workflow run deploy.yml -f environment=prod -f image_tag=...`

---

## Troubleshooting

### Issue: Build & Test Workflow Fails

**Check:**
1. Python version (must be 3.14+)
2. Dependencies install: `uv sync`
3. Tests pass locally: `pytest tests/`
4. Linting: `ruff check src/`

### Issue: Registry Push Fails

**Check:**
1. GCP secrets are set correctly
2. Service account has Storage Admin role
3. GCR is enabled in GCP project: `gcloud services enable containerregistry.googleapis.com`
4. Docker credentials: `gcloud auth configure-docker gcr.io`

### Issue: Deployment Fails

**Check:**
1. GKE cluster is running: `kubectl cluster-info`
2. Namespaces exist: `kubectl get namespaces`
3. Helm chart is valid: `helm lint ./helm`
4. Image exists in registry: `gcloud container images list --repository=gcr.io/...`
5. Pod can pull image: Check ImagePullBackOff errors

### Issue: Health Checks Failing

**Check:**
1. App is running: `kubectl logs -n dev deployment/ecommerce-api`
2. Health endpoints exist: `curl http://localhost:8000/health`
3. Pod port-forward works: `kubectl port-forward -n dev svc/ecommerce-api 8000:80`

---

## Integration with Backend Services

This API service is part of a unified microservices architecture:

- **Ecommerce Backend** (backend-service): Core business logic
- **Ecommerce API** (this service): API gateway/frontend API
- **Shared Cluster**: Both services in same GKE cluster
- **Shared Namespace**: Services in `dev` and `prod` namespaces

### Service Communication

Services communicate via Kubernetes DNS:
```
http://ecommerce-backend:80/api/v1/...    # Within cluster
```

### Database Considerations

- **Dev**: SQLite file in pod (ephemeral, resets on restart)
- **Prod**: Should use managed database (Cloud SQL)

To enable persistent database:
1. Set `persistence.enabled: true` in values-prod.yaml
2. Configure `persistence.storageClassName` (e.g., `standard` for GKE)

---

## Security Considerations

### Docker Image
- Runs as non-root user (`appuser`, UID 1000)
- Read-only filesystem
- Minimal base image (`python:3.14-slim`)
- No unnecessary packages

### Kubernetes
- Service account with minimal permissions
- Pod security context enforces:
  - Non-root user
  - Read-only root filesystem
  - No privilege escalation
  - Dropped all capabilities

### GCP Secrets
- Service account key never committed to repo
- Stored only in GitHub Secrets
- Rotated regularly recommended

### Image Registry
- Private GCR repository
- Images scanned for vulnerabilities (GCP Container Analysis)

---

## Useful Commands

```bash
# View recent runs
gh run list --repo=your-org/ecommerce-fast-api

# Check specific run
gh run view <RUN_ID> --log

# Re-run workflow
gh run rerun <RUN_ID>

# Cancel running workflow
gh run cancel <RUN_ID>

# View secrets (names only, not values)
gh secret list --repo=your-org/ecommerce-fast-api

# Update secret
gh secret set GCP_PROJECT_ID --body "new-value"

# Kubernetes commands
kubectl get all -n dev                    # View all resources in dev
kubectl logs -n dev deployment/ecommerce-api --tail=100
kubectl exec -it pod/name -n dev bash    # Shell into pod
kubectl delete pod/name -n dev            # Delete pod (triggers restart)

# Helm commands
helm list -n dev                          # List releases
helm history ecommerce-api -n dev        # View deployment history
helm rollback ecommerce-api 1 -n dev     # Rollback to previous release
helm get values ecommerce-api -n dev     # View current values
```

---

## Maintenance & Updates

### Updating Base Image
1. Update `Dockerfile` Python version
2. Run CI workflow to test
3. Trigger registry push to build new image
4. Deploy to dev first to test
5. Deploy to prod after validation

### Updating Helm Chart
1. Modify `helm/Chart.yaml` version
2. Update `helm/values.yaml` or `helm/values-prod.yaml`
3. Run `helm lint ./helm` locally
4. Commit and push
5. Deploy to dev, then prod

### Updating Dependencies
1. Edit `pyproject.toml`
2. Run `uv add <package>` or `uv add --dev <package>`
3. Commit changes
4. CI workflow will test automatically
5. Deploy with new image tag

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Google Cloud GKE](https://cloud.google.com/kubernetes-engine/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Last Updated:** 2026-09-30

For questions or improvements, refer to the project's CLAUDE.md file for architecture guidelines.
