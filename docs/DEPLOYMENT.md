# Deployment Guide

[← Back to Main README](../README.md)

Production deployment best practices and configuration for the Image Processing API.

## Production Deployment Overview

This guide covers deploying the Image Processing API to production environments using Docker. The production configuration is optimized for performance, reliability, and monitoring.

## Production Environment

### Docker Production Deployment

Run the API in production mode:

```bash
docker-compose -f docker-compose.yml up --build -d
```

**Production Features:**
- Optimized image size (build dependencies removed after installation)
- Health checks configured (uses `/health/ready` endpoint)
- Automatic restart on failure
- Production logging (LOG_LEVEL=INFO)
- Persistent data volumes for images and logs
- Runs in detached mode (`-d` flag)

### Production Configuration

#### Environment Variables

For production, configure your environment variables:

**Production `.env` file:**
```env
LOG_LEVEL=INFO
```

**Key Settings:**
- `LOG_LEVEL=INFO`: Production-appropriate logging level

#### View Production Logs

```bash
docker-compose -f docker-compose.yml logs -f
```

#### Stop Production Container

```bash
docker-compose -f docker-compose.yml down
```

#### Stop and Remove Volumes (⚠️ deletes all data)

```bash
docker-compose -f docker-compose.yml down -v
```

## Production Best Practices

### Security

1. **Environment Variables**: Never commit `.env` files to version control
2. **Logging**: Use `LOG_LEVEL=INFO` or higher in production
3. **Ports**: Only expose necessary ports (8000 for API)
4. **Authentication**: Not implemented — add API keys or OAuth before exposing publicly
5. **Upload limits**: Tune `MAX_UPLOAD_SIZE_MB` and keep rate limits enabled

### Performance

1. **Resource Allocation**: Ensure adequate RAM (8GB+ recommended)
2. **Disk Space**: Monitor disk usage for image storage
3. **Model Caching**: First detection request will be slow (model download)
4. **Rate Limiting**: Configure appropriate rate limits for your use case
5. **Monitoring**: Set up health check monitoring

### Monitoring

#### Health Checks

The API includes a health check endpoint:

```bash
curl http://localhost:8000/health/ready
```

**Docker Health Check:**
- Configured in `docker-compose.yml`
- Uses the `/health/ready` endpoint
- Automatically restarts unhealthy containers

#### Logging

- **Log Location**: `logs/app.log`
- **Log Level**: Set via `LOG_LEVEL` environment variable
- **Log Rotation**: Consider implementing log rotation for production
- **Monitoring**: Integrate with logging services (e.g., ELK, CloudWatch)

### Data Persistence

#### Docker Volumes

The production Docker setup uses named volumes for data persistence:

- **Uploaded Images**: Stored in Docker volume
- **Edited Images**: Stored in Docker volume
- **Detection Outputs**: Stored in Docker volume
- **Logs**: Stored in Docker volume

**Backup Strategy:**
- Regularly backup Docker volumes
- Consider cloud storage for images
- Implement log rotation and archival

### Scaling Considerations

#### Horizontal Scaling

- Run multiple container instances behind a load balancer
- Ensure shared storage for images (consider cloud storage)
- Configure session/state management if needed
- Monitor resource usage per instance

#### Vertical Scaling

- Increase container memory allocation for ML operations
- Use GPU-enabled instances for faster detection
- Monitor CPU and memory usage
- Optimize image processing operations

#### Model Performance

- First request per instance downloads model (1-3 minutes)
- Model stays in memory after first use
- Consider pre-warming model on container startup
- GPU support significantly improves detection speed

### Production Features

#### Automatic Testing

- Tests run during Docker image build
- Build fails if tests fail or coverage < 80%
- Ensures only tested code reaches production

#### Health Checks

- Docker healthcheck configured using `/health/ready` endpoint
- Automatic restart on failure
- Monitor container health status

#### Optimized Images

- Build dependencies removed after installation
- Minimizes image size
- Faster container startup

#### Data Persistence

- Named volumes for uploaded images, edited images, detected outputs, and logs
- Data survives container restarts
- Easy backup and migration

#### Environment Configuration

- Separate configurations for development and production
- Tunable settings via environment variables (see `.env.example`)
- Rate limits and some operational defaults remain code-configured for this portfolio scope

## Deployment Checklist

Before deploying to production:

- [ ] Configure `LOG_LEVEL=INFO` or appropriate level
- [ ] Verify health check endpoint is accessible
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy for data volumes
- [ ] Test container restart and recovery
- [ ] Verify rate limits are appropriate
- [ ] Check disk space allocation
- [ ] Ensure adequate RAM (8GB+ recommended)
- [ ] Test model download and caching
- [ ] Verify all endpoints are working
- [ ] Review security settings
- [ ] Set up log rotation
- [ ] Configure firewall rules
- [ ] Document deployment process

## Cloud Deployment

### AWS

- Use ECS or EKS for container orchestration
- Use S3 for image storage (requires code changes)
- Use CloudWatch for monitoring and logging
- Configure ALB for load balancing

### Azure

- Use Azure Container Instances or AKS
- Use Azure Blob Storage for images (requires code changes)
- Use Azure Monitor for monitoring
- Configure Application Gateway for load balancing

### Google Cloud

- Use Cloud Run or GKE
- Use Cloud Storage for images (requires code changes)
- Use Cloud Monitoring for observability
- Configure Load Balancer for traffic distribution

## Troubleshooting Production Issues

### Container Won't Start

- Check Docker logs: `docker-compose logs`
- Verify environment variables are set correctly
- Check disk space and memory availability
- Review health check configuration

### High Memory Usage

- Monitor container memory: `docker stats`
- Consider increasing memory allocation
- Review image processing operations
- Check for memory leaks

### Slow Performance

- Check resource allocation (CPU, memory)
- Monitor disk I/O
- Review rate limiting configuration
- Consider GPU support for detection
- Check network latency

### Data Loss

- Verify volume mounts are configured correctly
- Check backup strategy
- Review container restart policies
- Ensure volumes are not removed accidentally

For more troubleshooting help, see the [Troubleshooting Guide](TROUBLESHOOTING.md).

## Additional Resources

- [Installation Guide](INSTALLATION.md) - Setup instructions
- [Architecture Overview](ARCHITECTURE.md) - System design
- [API Documentation](API.md) - API reference
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues

---

[← Back to Main README](../README.md) | [Documentation Index](README.md)

