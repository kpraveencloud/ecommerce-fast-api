# Ecommerce API - Helm Chart

This Helm chart deploys the Ecommerce API FastAPI application to Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- GCP service account (for image pull if using private GCR)

## Chart Structure

```
helm/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default values (dev environment)
├── values-prod.yaml        # Production overrides
├── README.md               # This file
└── templates/
    ├── deployment.yaml     # Kubernetes Deployment
    ├── service.yaml        # Kubernetes Service
    ├── serviceaccount.yaml # ServiceAccount
    ├── hpa.yaml            # Horizontal Pod Autoscaler
    ├── ingress.yaml        # Ingress (for prod)
    └── _helpers.tpl        # Template helpers
```

## Quick Start

### Development Deployment

```bash
# Install
helm install ecommerce-api ./helm \
  --namespace dev \
  --create-namespace \
  --values helm/values.yaml \
  --set image.tag=latest

# Verify
kubectl get deployment -n dev
kubectl get pods -n dev
kubectl port-forward -n dev svc/ecommerce-api 8000:80

# Access: http://localhost:8000/api/v1/docs
```

### Production Deployment

```bash
# Install with production values
helm install ecommerce-api ./helm \
  --namespace prod \
  --create-namespace \
  --values helm/values.yaml \
  --values helm/values-prod.yaml \
  --set image.tag=v1.0.0

# Verify
kubectl get all -n prod
kubectl describe deployment/ecommerce-api -n prod
```

## Configuration

### Key Parameters

| Parameter | Description | Default | Dev | Prod |
|-----------|-------------|---------|-----|------|
| `replicaCount` | Number of replicas | 1 | 1 | 3 |
| `image.repository` | Image repository | `gcr.io/your-project-id/ecommerce-api` | - | - |
| `image.tag` | Image tag | `latest` | `latest` | Version tag |
| `service.port` | Service port | 80 | 80 | 80 |
| `service.targetPort` | Container port | 8000 | 8000 | 8000 |
| `resources.limits.cpu` | CPU limit | - | 500m | 1000m |
| `resources.limits.memory` | Memory limit | - | 512Mi | 1Gi |
| `autoscaling.enabled` | Enable HPA | false | false | true |
| `autoscaling.minReplicas` | Min replicas for HPA | 1 | - | 3 |
| `autoscaling.maxReplicas` | Max replicas for HPA | 3 | - | 10 |
| `ingress.enabled` | Enable Ingress | false | false | true |

### Environment Variables

Set via `env` section in values:

```yaml
env:
  ENVIRONMENT: "development"
  LOG_LEVEL: "INFO"
  DATABASE_URL: "sqlite:///./ecommerce.db"
  PROJECT_NAME: "Ecommerce FastAPI"
  API_V1_STR: "/api/v1"
  ACCESS_TOKEN_EXPIRE_MINUTES: "11520"
```

### Resource Customization

#### Development (values.yaml)
```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

#### Production (values-prod.yaml)
```yaml
resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi
```

### Scaling

Enable Horizontal Pod Autoscaler (HPA) for production:

```bash
helm upgrade ecommerce-api ./helm \
  --namespace prod \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=3 \
  --set autoscaling.maxReplicas=10 \
  --set autoscaling.targetCPUUtilizationPercentage=70
```

### Ingress Configuration

For production with TLS:

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ecommerce-api-tls
      hosts:
        - api.example.com
```

Deploy with:
```bash
helm install ecommerce-api ./helm \
  --namespace prod \
  --values helm/values.yaml \
  --values helm/values-prod.yaml \
  --values helm/ingress-prod.yaml
```

## Health Checks

### Liveness Probe
- Path: `/health`
- Initial delay: 30s (dev), 60s (prod)
- Period: 10s
- Timeout: 5s
- Failure threshold: 3

### Readiness Probe
- Path: `/ready`
- Initial delay: 10s (dev), 30s (prod)
- Period: 5s
- Timeout: 3s
- Failure threshold: 2

Ensure your FastAPI app implements these endpoints.

## Upgrade & Rollback

### Upgrade to New Version

```bash
# Update image tag
helm upgrade ecommerce-api ./helm \
  --namespace prod \
  --values helm/values.yaml \
  --values helm/values-prod.yaml \
  --set image.tag=v1.1.0

# Wait for rollout
kubectl rollout status deployment/ecommerce-api -n prod
```

### Rollback to Previous Release

```bash
# View release history
helm history ecommerce-api -n prod

# Rollback
helm rollback ecommerce-api 1 -n prod
```

## Debugging

### View Chart Values

```bash
# Current values
helm get values ecommerce-api -n prod

# Full manifest
helm get values ecommerce-api -n prod
```

### Dry Run

```bash
# Test deployment without applying
helm install ecommerce-api ./helm \
  --namespace prod \
  --dry-run \
  --debug \
  --values helm/values.yaml \
  --values helm/values-prod.yaml
```

### Lint Chart

```bash
# Validate chart syntax
helm lint ./helm
```

### View Rendered Templates

```bash
# See what will be deployed
helm template ecommerce-api ./helm \
  --namespace prod \
  --values helm/values.yaml \
  --values helm/values-prod.yaml \
  --set image.tag=v1.0.0
```

## Uninstall

```bash
# Remove deployment (dev)
helm uninstall ecommerce-api -n dev

# Remove deployment (prod)
helm uninstall ecommerce-api -n prod

# Remove namespace
kubectl delete namespace dev
kubectl delete namespace prod
```

## Persistence

For persistent storage (prod):

```yaml
persistence:
  enabled: true
  storageClassName: "standard"  # GKE default
  size: 10Gi
  mountPath: /app/data
```

## Security

The chart enforces:
- Non-root container user (`appuser`, UID 1000)
- Read-only root filesystem
- No privilege escalation
- Dropped all Linux capabilities
- Pod security context with fsGroup

## Monitoring

### Prometheus Metrics

To enable Prometheus scraping, add annotations:

```yaml
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

Then add `/metrics` endpoint to your FastAPI app:

```python
from prometheus_client import Counter, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

REQUESTS = Counter('requests_total', 'Total requests', ['method', 'endpoint'])

@app.middleware("http")
async def track_requests(request, call_next):
    response = await call_next(request)
    REQUESTS.labels(method=request.method, endpoint=request.url.path).inc()
    return response
```

## Examples

### Deploy with Custom Values

```bash
helm install ecommerce-api ./helm \
  --namespace prod \
  --create-namespace \
  --values helm/values.yaml \
  --values helm/values-prod.yaml \
  --set image.repository=gcr.io/my-project/ecommerce-api \
  --set image.tag=v1.0.0 \
  --set service.port=8080 \
  --set autoscaling.enabled=true \
  --set autoscaling.maxReplicas=15
```

### Deploy with External Configuration

Create custom-values.yaml:

```yaml
replicaCount: 5
resources:
  limits:
    cpu: 2000m
    memory: 2Gi
env:
  LOG_LEVEL: "DEBUG"
  DATABASE_URL: "postgresql://host:5432/db"
```

Deploy with:

```bash
helm install ecommerce-api ./helm \
  --namespace prod \
  --values helm/values.yaml \
  --values helm/values-prod.yaml \
  --values custom-values.yaml
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n prod

# View logs
kubectl logs <pod-name> -n prod

# Check image pull
kubectl get events -n prod --sort-by='.lastTimestamp'
```

### Service Not Accessible

```bash
# Verify service exists
kubectl get svc -n prod

# Check endpoints
kubectl get endpoints -n prod

# Test port-forward
kubectl port-forward -n prod svc/ecommerce-api 8000:80
```

### Deployment Stuck

```bash
# Check rollout status
kubectl rollout status deployment/ecommerce-api -n prod

# View recent events
kubectl describe deployment ecommerce-api -n prod

# Force restart
kubectl rollout restart deployment/ecommerce-api -n prod
```

## Contributing

To make changes to the Helm chart:

1. Update `Chart.yaml` version
2. Modify templates or values
3. Run `helm lint ./helm`
4. Test with `helm install --dry-run --debug`
5. Deploy to dev first, then prod

## References

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GKE Deployment Guide](https://cloud.google.com/kubernetes-engine/docs/deploy-app)
