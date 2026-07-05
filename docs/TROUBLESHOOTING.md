# Troubleshooting Guide

[← Back to Main README](../README.md)

Common issues and their solutions for the Image Processing API.

## Port 8000 Already in Use

**Error**: `Address already in use` or `port is already allocated`

**Solution**: 
- Change the port using the [Port Configuration](INSTALLATION.md#port-configuration) instructions in the Installation Guide
- Or stop the process using port 8000:
  ```bash
  # Find the process using port 8000
  # On Linux/Mac:
  lsof -i :8000
  # On Windows:
  netstat -ano | findstr :8000
  
  # Kill the process (replace PID with actual process ID)
  kill -9 <PID>  # Linux/Mac
  taskkill /PID <PID> /F  # Windows
  ```

## Model Download Failures

**Error**: Model fails to download from Hugging Face

**Solutions**:
- Check your internet connection
- Verify access to Hugging Face (https://huggingface.co)
- Clear Hugging Face cache and retry:
  ```bash
  # Linux/Mac
  rm -rf ~/.cache/huggingface/
  # Windows
  rmdir /s C:\Users\<username>\.cache\huggingface\
  ```
- Check firewall/proxy settings if behind a corporate network
- The model will retry on the next detection request

## Permission Errors

**Error**: `Permission denied` when accessing files or directories

**Solutions**:
- Ensure the application has read/write permissions to:
  - `app/static/uploaded/`
  - `app/static/edited/`
  - `app/static/detected/`
  - `logs/`
- On Linux/Mac, you may need to adjust permissions:
  ```bash
  chmod -R 755 app/static/
  chmod -R 755 logs/
  ```
- For Docker, check volume mount permissions

## Memory Errors During Model Loading

**Error**: `Out of memory` or `CUDA out of memory`

**Solutions**:
- Ensure you have at least 8GB RAM available
- Close other memory-intensive applications
- For Docker, increase memory allocation in Docker settings
- Consider using a machine with more RAM for production deployments
- The model loads into RAM on first use and stays loaded

## Docker Build Failures

**Error**: Docker build fails or tests fail during build

**Solutions**:
- Ensure Docker has enough disk space (at least 10GB free)
- Check Docker logs: `docker-compose logs`
- Verify all files are present (requirements.txt, Dockerfile, etc.)
- Try rebuilding without cache: `docker-compose build --no-cache`
- Ensure tests pass locally before building Docker image

## Test Failures

**Error**: Tests fail with coverage below 80%

**Solutions**:
- Run tests locally to see detailed error messages: `pytest -v`
- Check test coverage report: `pytest --cov=app --cov-report=html`
- Review `htmlcov/index.html` to see which code is not covered
- Ensure all test dependencies are installed: `pip install -r requirements.txt`
- Check that test files are in the correct location (`tests/` directory)

## Logs Not Appearing

**Issue**: No log output or log file not found

**Solutions**:
- Check that `logs/` directory exists and is writable
- Verify `LOG_LEVEL` environment variable is set correctly
- Check log file location: `logs/app.log`
- For Docker, check container logs: `docker-compose logs -f`
- Ensure the application has write permissions to the logs directory

## First Detection Request is Slow

**Issue**: First object detection request takes a long time

**Explanation**: This is expected behavior. The DETR model needs to be downloaded and loaded into memory on the first request. Subsequent requests will be faster.

**Solutions**:
- Wait for the first request to complete (typically 1-3 minutes)
- The model is cached after first download
- Consider pre-warming the model in production deployments

## Image Upload Failures

**Error**: Image upload fails or returns validation errors

**Solutions**:
- Verify image format is supported (JPEG, PNG)
- Check file size is under 5MB limit
- Ensure image file is not corrupted
- Verify file extension matches actual image format
- Check that the `app/static/uploaded/` directory exists and is writable

## API Not Responding

**Issue**: API doesn't respond or returns timeouts

**Solutions**:
- Check if the server is running: `curl http://localhost:8000/health`
- Check server logs for errors
- Verify port 8000 is not blocked by firewall
- For Docker, check container status: `docker-compose ps`
- Review resource usage (CPU, memory) - may need to scale up

## Rate Limit Errors

**Error**: `429 Too Many Requests`

**Solutions**:
- Wait for the rate limit window to reset
- Reduce request frequency
- Review rate limits in [API Documentation](API.md)
- Consider implementing request queuing for batch operations

## Performance Optimization Tips

### General Performance

- Use Docker for consistent performance across environments
- Ensure adequate RAM (8GB+ recommended for ML operations)
- Use SSD storage for faster file I/O
- Monitor resource usage during peak times

### Docker Performance

- Allocate sufficient memory to Docker (8GB+ recommended)
- Use Docker volumes for persistent data
- Monitor container resource usage: `docker stats`
- Consider using Docker Compose profiles for different environments

### Model Performance

- First detection request is slow (model download) - this is expected
- Subsequent requests use cached model
- Consider GPU support for faster inference
- Pre-warm the model in production deployments

### API Performance

- Use async endpoints for concurrent requests
- Monitor rate limits to avoid throttling
- Cache frequently accessed images if possible
- Use appropriate image sizes (don't upload unnecessarily large images)

## FAQ

### Q: Can I use a different port?

A: Yes, see [Port Configuration](INSTALLATION.md#port-configuration) in the Installation Guide.

### Q: How do I change the log level?

A: Set the `LOG_LEVEL` environment variable in your `.env` file. See [Environment Variables](INSTALLATION.md#environment-variables) in the Installation Guide.

### Q: Can I use GPU for faster detection?

A: Yes, if you have a CUDA-compatible GPU, PyTorch will automatically use it. Ensure CUDA drivers are installed.

### Q: How do I clear all uploaded images?

A: Use `DELETE /images?folder=uploaded` or manually delete files from `app/static/uploaded/`.

### Q: Can I change the rate limits?

A: Rate limits are configured in the code. See the rate limiting configuration in `app/core/rate_limiting.py`.

### Q: How do I run tests?

A: See the [Development Guide](DEVELOPMENT.md) for detailed testing instructions.

### Q: The model download is very slow. Can I pre-download it?

A: The model is automatically cached after first download. You can manually download it by making a detection request, or pre-download using Hugging Face CLI.

## Getting More Help

If you're still experiencing issues:

1. Check the [Installation Guide](INSTALLATION.md) for setup problems
2. Review the [API Documentation](API.md) for endpoint-specific issues
3. Check server logs in `logs/app.log` for detailed error messages
4. Review Docker logs if using Docker: `docker-compose logs -f`
5. Ensure all prerequisites are met (Python version, dependencies, etc.)

---

[← Back to Main README](../README.md) | [Documentation Index](README.md)

