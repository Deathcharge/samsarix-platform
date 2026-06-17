# Helix Platform Deployment Guide

Complete guide to deploying Helix Platform to production environments.

---

## Deployment Options

| Option | Best For | Complexity | Cost |
|--------|----------|-----------|------|
| **Docker** | Local development, single machine | Low | Free |
| **Docker Compose** | Multi-container local setup | Low | Free |
| **Kubernetes** | Production, scalability | High | Medium |
| **AWS ECS** | AWS ecosystem | Medium | Variable |
| **Google Cloud Run** | Serverless, auto-scaling | Medium | Pay-per-use |
| **Azure Container Instances** | Azure ecosystem | Medium | Variable |

---

## Docker Deployment

### Prerequisites

- Docker installed (version 20.10+)
- Docker Hub account (optional, for image registry)
- 2GB RAM minimum

### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HELIX_LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "helix_platform.server"]
```

### Build and Run

```bash
# Build image
docker build -t helix-platform:latest .

# Run container
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_key \
  -e HELIX_LOG_LEVEL=INFO \
  helix-platform:latest

# Run with volume mount (for persistence)
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OPENROUTER_API_KEY=your_key \
  helix-platform:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  helix-platform:
    build: .
    ports:
      - "8000:8000"
    environment:
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      HELIX_LOG_LEVEL: INFO
      HELIX_WORKERS: 4
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Optional: PostgreSQL for persistence
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: helix
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: helix_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

Run with Docker Compose:

```bash
# Create .env file
cat > .env << EOF
OPENROUTER_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
POSTGRES_PASSWORD=secure_password
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f helix-platform

# Stop services
docker-compose down
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Container registry access (Docker Hub, ECR, GCR)

### Push Image to Registry

```bash
# Tag image
docker tag helix-platform:latest your-registry/helix-platform:latest

# Push to registry
docker push your-registry/helix-platform:latest
```

### Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helix-platform
  namespace: default
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: helix-platform
  template:
    metadata:
      labels:
        app: helix-platform
    spec:
      containers:
      - name: helix-platform
        image: your-registry/helix-platform:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: helix-secrets
              key: openrouter-api-key
        - name: HELIX_LOG_LEVEL
          value: "INFO"
        - name: HELIX_WORKERS
          value: "4"
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
```

Create `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: helix-platform
  namespace: default
spec:
  type: LoadBalancer
  selector:
    app: helix-platform
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
    name: http
```

Create `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: helix-config
  namespace: default
data:
  config.yaml: |
    orchestration:
      max_agents: 100
      agent_timeout: 300
    intelligence:
      default_provider: openrouter
    coordination:
      consensus_strategy: supermajority
    monitoring:
      metrics_enabled: true
```

Create `k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: helix-secrets
  namespace: default
type: Opaque
stringData:
  openrouter-api-key: your_key_here
  anthropic-api-key: your_key_here
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace helix

# Create secrets
kubectl apply -f k8s/secrets.yaml -n helix

# Create configmap
kubectl apply -f k8s/configmap.yaml -n helix

# Deploy application
kubectl apply -f k8s/deployment.yaml -n helix
kubectl apply -f k8s/service.yaml -n helix

# Check deployment status
kubectl get pods -n helix
kubectl get svc -n helix

# View logs
kubectl logs -f deployment/helix-platform -n helix

# Scale deployment
kubectl scale deployment helix-platform --replicas=5 -n helix
```

---

## Cloud Platform Deployment

### AWS ECS

```bash
# Create ECR repository
aws ecr create-repository --repository-name helix-platform

# Push image
docker tag helix-platform:latest your-account.dkr.ecr.us-east-1.amazonaws.com/helix-platform:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/helix-platform:latest

# Create ECS task definition (task-definition.json)
# Deploy with AWS CLI
aws ecs create-service \
  --cluster helix-cluster \
  --service-name helix-platform \
  --task-definition helix-platform:1 \
  --desired-count 3 \
  --launch-type FARGATE
```

### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/your-project/helix-platform

# Deploy to Cloud Run
gcloud run deploy helix-platform \
  --image gcr.io/your-project/helix-platform \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars OPENROUTER_API_KEY=your_key
```

### Azure Container Instances

```bash
# Push to ACR
az acr build --registry your-registry --image helix-platform:latest .

# Deploy container
az container create \
  --resource-group helix-rg \
  --name helix-platform \
  --image your-registry.azurecr.io/helix-platform:latest \
  --cpu 2 \
  --memory 2 \
  --environment-variables OPENROUTER_API_KEY=your_key
```

---

## Configuration for Production

### Environment Variables

```bash
# LLM Configuration
OPENROUTER_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GROQ_API_KEY=your_key

# System Configuration
HELIX_LOG_LEVEL=INFO
HELIX_WORKERS=4
HELIX_PORT=8000

# Persistence
HELIX_PERSISTENCE_ENABLED=true
HELIX_PERSISTENCE_PATH=/data

# Monitoring
HELIX_METRICS_ENABLED=true
HELIX_METRICS_INTERVAL=10

# Security
HELIX_ENABLE_HTTPS=true
HELIX_SSL_CERT_PATH=/etc/ssl/certs/cert.pem
HELIX_SSL_KEY_PATH=/etc/ssl/private/key.pem
```

### Database Configuration

```yaml
# For PostgreSQL persistence
database:
  type: postgresql
  host: postgres.example.com
  port: 5432
  user: helix
  password: ${DB_PASSWORD}
  database: helix_platform
  pool_size: 20
  max_overflow: 40

# For Redis caching
cache:
  type: redis
  host: redis.example.com
  port: 6379
  db: 0
  password: ${REDIS_PASSWORD}
```

---

## Monitoring and Logging

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'helix-platform'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# logstash.conf
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  if [type] == "helix" {
    mutate {
      add_field => { "[@metadata][index_name]" => "helix-%{+YYYY.MM.dd}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index_name]}"
  }
}
```

---

## Health Checks and Monitoring

### Health Check Endpoints

```python
# GET /health
# Returns: 200 OK if service is healthy
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}

# GET /ready
# Returns: 200 OK if ready to accept traffic
{
  "ready": true,
  "dependencies": {
    "database": "connected",
    "cache": "connected",
    "llm": "available"
  }
}

# GET /metrics
# Returns Prometheus metrics
```

---

## Scaling Strategies

### Horizontal Scaling

```bash
# Kubernetes
kubectl scale deployment helix-platform --replicas=10

# Docker Swarm
docker service scale helix-platform=10

# AWS Auto Scaling
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name helix-asg \
  --desired-capacity 10
```

### Vertical Scaling

Increase resources per instance:

```yaml
# Kubernetes
resources:
  requests:
    cpu: 2000m
    memory: 4Gi
  limits:
    cpu: 4000m
    memory: 8Gi
```

---

## Security Best Practices

### API Key Management

```bash
# Use secrets management
# AWS Secrets Manager
aws secretsmanager create-secret --name helix/openrouter-key

# Kubernetes Secrets
kubectl create secret generic helix-secrets \
  --from-literal=openrouter-api-key=your_key

# Azure Key Vault
az keyvault secret set --vault-name helix-kv --name openrouter-key
```

### Network Security

```yaml
# Network Policy for Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: helix-network-policy
spec:
  podSelector:
    matchLabels:
      app: helix-platform
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 8000
```

### SSL/TLS Configuration

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Or use Let's Encrypt with Certbot
certbot certonly --standalone -d helix-platform.example.com
```

---

## Troubleshooting

### Common Issues

**Issue**: Container exits immediately

```bash
# Check logs
docker logs helix-platform

# Run with debug logging
docker run -e HELIX_LOG_LEVEL=DEBUG helix-platform:latest
```

**Issue**: High memory usage

```bash
# Limit memory
docker run -m 2g helix-platform:latest

# Monitor memory
docker stats helix-platform
```

**Issue**: API key not found

```bash
# Verify environment variable
docker exec helix-platform env | grep OPENROUTER

# Set variable
docker run -e OPENROUTER_API_KEY=your_key helix-platform:latest
```

---

## Performance Tuning

### Worker Configuration

```python
# Adjust worker count based on CPU cores
HELIX_WORKERS = CPU_COUNT * 2 + 1
```

### Connection Pooling

```yaml
database:
  pool_size: 20
  max_overflow: 40
  pool_recycle: 3600
  pool_pre_ping: true
```

### Caching Strategy

```python
# Enable Redis caching
cache:
  type: redis
  ttl: 3600
  compression: true
```

---

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -U helix -h postgres.example.com helix_platform > backup.sql

# Restore
psql -U helix -h postgres.example.com helix_platform < backup.sql
```

### Volume Backup

```bash
# Kubernetes PVC backup
kubectl get pvc
kubectl exec pod-name -- tar czf /backup/data.tar.gz /data
```

---

## Rollback Procedures

### Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment/helix-platform

# Rollback to previous version
kubectl rollout undo deployment/helix-platform

# Rollback to specific revision
kubectl rollout undo deployment/helix-platform --to-revision=2
```

### Docker Rollback

```bash
# Use image tags for versioning
docker run helix-platform:v1.0.0

# Keep multiple versions available
docker tag helix-platform:latest helix-platform:v1.1.0
```

---

## Support and Resources

- **Documentation**: https://docs.helix-platform.ai
- **GitHub Issues**: https://github.com/Deathcharge/helix-platform/issues
- **Community**: https://discord.gg/helix-platform

---

**Happy deploying! 🚀**
