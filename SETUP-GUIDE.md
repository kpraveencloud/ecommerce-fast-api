# Ecommerce API - CI/CD Setup Complete ✅

## What Was Created

### 1. GitHub Actions Workflows (`.github/workflows/`)
- **`build-and-test.yml`** — CI pipeline (build, lint, test)
- **`registry-push.yml`** — Docker image build & push to GCR
- **`deploy.yml`** — Kubernetes deployment via Helm

### 2. Docker Configuration
- **`Dockerfile`** — Multi-stage build for FastAPI app
  - Builder stage: Install dependencies
  - Runtime stage: Minimal production image
  - Health checks included
  - Runs as non-root user

### 3. Helm Chart (`helm/`)
- **`Chart.yaml`** — Chart metadata
- **`values.yaml`** — Development defaults
- **`values-prod.yaml`** — Production overrides
- **Templates:**
  - `deployment.yaml` — Kubernetes Deployment
  - `service.yaml` — ClusterIP Service
  - `serviceaccount.yaml` — ServiceAccount
  - `hpa.yaml` — Horizontal Pod Autoscaler
  - `ingress.yaml` — Ingress for prod TLS
  - `_helpers.tpl` — Helper templates

### 4. Documentation
- **`CI-CD.md`** — Complete CI/CD documentation (⭐ READ THIS FIRST)
- **`helm/README.md`** — Helm chart deployment guide
- **`SETUP-GUIDE.md`** — This file

---

## 🚀 Quick Start Setup (15 minutes)

### Step 1: Configure GitHub Secrets

Go to your GitHub repository: **Settings → Secrets and Variables → Actions**

Create these secrets:

```
GCP_PROJECT_ID = your-gcp-project-id
GCP_REGISTRY_URL = gcr.io/your-gcp-project-id
DOCKER_IMAGE_NAME = ecommerce-api
GKE_CLUSTER_NAME = your-cluster-name
GKE_ZONE = us-central1-a (or your zone)
GCP_SA_KEY = (entire JSON key file - see instructions below)
```

### Step 2: Create GCP Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account"

# Grant container access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/container.developer

# Grant storage access (for GCR)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.admin

# Create JSON key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Copy the entire contents of key.json to GCP_SA_KEY secret
```

### Step 3: Create Kubernetes Namespaces

```bash
# Authenticate to your GKE cluster
gcloud container clusters get-credentials YOUR_CLUSTER_NAME --zone YOUR_ZONE

# Create namespaces
kubectl create namespace dev
kubectl create namespace prod

# Verify
kubectl get namespaces
```

### Step 4: Add Health Check Endpoints

Ensure your FastAPI app has these endpoints:

```python
# In your main.py or appropriate route file
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Liveness probe - simple health status"""
    return {"status": "ok"}

@router.get("/ready")
async def readiness_check():
    """Readiness probe - checks dependencies"""
    # Optionally check database connection, cache, etc.
    return {"status": "ready"}

# Add to app
app.include_router(router)
```

### Step 5: Commit & Push

```bash
cd ecommerce-fast-api
git add .github/ Dockerfile helm/ CI-CD.md SETUP-GUIDE.md
git commit -m "feat: Add complete CI/CD pipeline with GitHub Actions and Helm

- GitHub Actions workflows for CI (build/test), CD (registry/deploy)
- Docker build configuration with health checks
- Helm chart for Kubernetes deployments (dev & prod)
- Comprehensive documentation for CI/CD setup

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
git push origin develop
```

---

## 📋 Complete Workflow (After Setup)

### 1. Development (On Feature Branch)

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, test locally
pytest tests/
ruff check src/

# Push to GitHub
git push origin feature/my-feature

# Create PR → CI runs automatically ✅
```

### 2. Code Review & Merge

```
✅ CI passes (lint, type check, tests)
👥 Team reviews PR
✅ Merge to develop
✅ CI runs on develop branch
```

### 3. Release to Dev

Via GitHub UI or CLI:

```bash
# Trigger registry push (builds Docker image)
gh workflow run registry-push.yml \
  -f image_tag=dev-2026-09-30

# Trigger deployment to dev
gh workflow run deploy.yml \
  -f environment=dev \
  -f image_tag=dev-2026-09-30
```

Verify in dev:
```bash
kubectl get pods -n dev -w
kubectl logs -n dev deployment/ecommerce-api
```

### 4. Release to Production

```bash
# Trigger registry push with version tag
gh workflow run registry-push.yml \
  -f image_tag=v1.0.0

# Trigger deployment to prod
gh workflow run deploy.yml \
  -f environment=prod \
  -f image_tag=v1.0.0
```

---

## 🔄 Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│        GitHub Repository (ecommerce-fast-api)          │
└────────────────────────────────────────────────────────┘
            ↓ (Push to develop/main or PR)
        ┌───────────────────────┐
        │  ✅ Build & Test (CI)  │
        │  - Lint (ruff)         │
        │  - Type check (mypy)   │
        │  - Run tests (pytest)  │
        │  - Upload coverage     │
        └───────────────────────┘
            ↓ (Manual trigger or tag push)
        ┌───────────────────────┐
        │  📦 Registry Push      │
        │  - Build Docker image  │
        │  - Push to GCR         │
        └───────────────────────┘
                 ↓ GCR: gcr.io/project/ecommerce-api:tag
            ┌───────────────────────┐
            │  🚀 Deploy to GKE      │
            │  - Dev Namespace       │
            │  - OR Prod Namespace   │
            │  - Helm deployment     │
            │  - Health checks       │
            └───────────────────────┘
                     ↓
        ┌───────────────────────────────────┐
        │  Kubernetes Cluster (Same as      │
        │  ecommerce-backend)               │
        │  ├─ dev namespace                 │
        │  │  └─ ecommerce-api pod(s)       │
        │  └─ prod namespace                │
        │     └─ ecommerce-api pod(s)       │
        └───────────────────────────────────┘
```

---

## 🔗 Service Integration

### Same Cluster Architecture

```
┌─────────────────── GKE Cluster ────────────────────┐
│                                                    │
│  ┌─────────────────┐      ┌──────────────────┐   │
│  │  ecommerce-api  │      │ ecommerce-backend│   │
│  │  (This service) │◄────►│  (Core service)  │   │
│  │  Dev & Prod     │      │  Dev & Prod      │   │
│  └─────────────────┘      └──────────────────┘   │
│         ↑                           ↑             │
│         │ Share data via            │             │
│         │ Kubernetes DNS            │             │
│         └───────────────────────────┘             │
│                                                    │
│  Service communication:                            │
│  http://ecommerce-backend:80/api/v1/...           │
│  http://ecommerce-api:80/api/v1/...               │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Both services:**
- Run in the same namespace (dev or prod)
- Share Kubernetes networking
- Can communicate via DNS names
- Deploy via same CI/CD pipeline
- Use same cluster resources

---

## 📖 Documentation Reference

### Read These First
1. **`CI-CD.md`** — Complete guide to all workflows, secrets, and troubleshooting
2. **`helm/README.md`** — Helm deployment options and customization

### For Specific Tasks
- **Deploying to dev**: See "Deploy to Cluster (CD)" in CI-CD.md
- **Deploying to prod**: Same steps, use `environment=prod`
- **Updating image tag**: See "Registry Push" section
- **Helm customization**: See "Configuration" in helm/README.md
- **Troubleshooting**: See "Troubleshooting" section in CI-CD.md

---

## ✅ Verification Checklist

After setup is complete:

- [ ] GitHub secrets configured (all 6 secrets)
- [ ] GCP service account created with correct roles
- [ ] Kubernetes namespaces created (dev, prod)
- [ ] Health check endpoints added to FastAPI app
- [ ] Code committed to repository
- [ ] CI workflow runs successfully on first push
- [ ] Can manually trigger registry-push workflow
- [ ] Can manually trigger deploy workflow
- [ ] Deployment appears in dev namespace
- [ ] Pod is running and healthy
- [ ] Health check endpoints respond (curl /health)

---

## 🆘 Common Issues & Fixes

### Issue: "Workflow file not found"
**Solution:** Make sure files are in correct path:
```
.github/workflows/build-and-test.yml ✅
.github/workflows/registry-push.yml  ✅
.github/workflows/deploy.yml         ✅
```

### Issue: "Secret 'GCP_SA_KEY' not found"
**Solution:** Create all 6 secrets in GitHub:
```
Settings → Secrets and Variables → Actions → New Repository Secret
```

### Issue: "Pod stuck in ImagePullBackOff"
**Solution:** Check image exists in GCR:
```bash
gcloud container images list --repository=gcr.io/YOUR_PROJECT
gcloud container images list-tags gcr.io/YOUR_PROJECT/ecommerce-api
```

### Issue: "Health check failed"
**Solution:** Ensure endpoints exist and respond:
```bash
kubectl port-forward -n dev svc/ecommerce-api 8000:80
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

---

## 📞 Next Steps

1. ✅ **Setup (15 min)**: Follow "Quick Start Setup" above
2. ✅ **Commit**: Push files to repository
3. ✅ **Test CI**: Make a small change and push to trigger CI
4. ✅ **Test Registry Push**: Manually trigger registry-push workflow
5. ✅ **Test Deploy to Dev**: Deploy to dev environment
6. ✅ **Test Deploy to Prod**: Deploy to prod environment
7. 📖 **Documentation**: Share CI-CD.md link with team
8. 🔧 **Customize**: Update values in helm/ for your needs

---

## 📚 File Structure Reference

```
ecommerce-fast-api/
├── .github/
│   └── workflows/
│       ├── build-and-test.yml      ← CI: Build, lint, test
│       ├── registry-push.yml        ← CD Step 1: Docker push to GCR
│       └── deploy.yml              ← CD Step 2: Deploy to GKE
├── helm/
│   ├── Chart.yaml                  ← Chart metadata
│   ├── values.yaml                 ← Dev defaults
│   ├── values-prod.yaml            ← Prod overrides
│   ├── README.md                   ← Helm documentation
│   └── templates/
│       ├── deployment.yaml         ← Deployment template
│       ├── service.yaml            ← Service template
│       ├── serviceaccount.yaml     ← ServiceAccount template
│       ├── hpa.yaml                ← Autoscaler template
│       ├── ingress.yaml            ← Ingress template
│       └── _helpers.tpl            ← Helper functions
├── Dockerfile                      ← Docker build file
├── CI-CD.md                        ← Complete CI/CD guide ⭐
├── SETUP-GUIDE.md                  ← This file
├── src/                            ← Your FastAPI code
└── tests/                          ← Test files
```

---

## 🎯 Success Criteria

Your CI/CD setup is complete when:

✅ You can push code and CI workflow runs automatically
✅ You can trigger registry-push and Docker image builds
✅ You can trigger deploy workflow and pods appear in GKE
✅ Health checks pass and service is accessible
✅ Both dev and prod environments work
✅ Team understands the pipeline via documentation

---

**Questions?** Refer to:
- `CI-CD.md` for detailed documentation
- `helm/README.md` for deployment options
- Workflow files themselves (well-commented)

**Ready to deploy?** Start with:
```bash
gh workflow run build-and-test.yml
# Then check Actions tab in GitHub UI
```

---

**Created:** 2026-09-30  
**Setup Duration:** ~15 minutes + testing  
**Part of:** Unified ecommerce microservices architecture
