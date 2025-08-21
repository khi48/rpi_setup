# Raspberry Pi Remote Health Monitor

A Python script to monitor the health of a remote Raspberry Pi via SSH and collect comprehensive metrics to help diagnose crash causes.

## Features

- **System Metrics**: CPU usage, temperature, frequency, load averages
- **Memory Monitoring**: RAM and swap usage with alerts for high usage
- **Disk Monitoring**: Disk space usage and I/O statistics
- **Network Health**: Interface status, connectivity tests, active connections
- **Process Monitoring**: Top CPU/memory consuming processes, failed services
- **Log Analysis**: Recent kernel and system log errors
- **Data Storage**: JSON format with timestamps for historical analysis
- **Continuous Monitoring**: Configurable intervals with automatic logging

## Requirements

- Python 3.6+
- SSH access to the target Raspberry Pi
- SSH key-based authentication (recommended) or password authentication

## Setup

1. **SSH Key Setup** (recommended for security):
   ```bash
   # Generate SSH key if you don't have one
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/rpi_monitor_key
   
   # Copy public key to target Raspberry Pi
   ssh-copy-id -i ~/.ssh/rpi_monitor_key.pub pi@your-rpi-ip
   ```

2. **Make the script executable**:
   ```bash
   chmod +x rpi_monitor.py
   ```

## Usage

### Single Health Check
```bash
# Basic usage with IP address
./rpi_monitor.py 192.168.1.100 --once

# With custom username and SSH key
./rpi_monitor.py 192.168.1.100 -u myuser -k ~/.ssh/rpi_monitor_key --once

# Using hostname
./rpi_monitor.py myrpi.local --once
```

### Continuous Monitoring
```bash
# Monitor every 5 minutes (300 seconds - default)
./rpi_monitor.py 192.168.1.100

# Monitor every 1 minute
./rpi_monitor.py 192.168.1.100 -i 60

# Background monitoring with nohup
nohup ./rpi_monitor.py 192.168.1.100 > monitor.log 2>&1 &
```

## Output Files

The script creates:
- `./rpi_logs/` directory for all output files
- `health_check_[hostname]_[timestamp].json` - Complete metrics in JSON format
- `rpi_monitor_[hostname]_[date].log` - Human-readable log with alerts

## Key Metrics Collected

### System Health
- Uptime and load averages
- CPU temperature (alerts if >70°C)
- CPU frequency and usage
- Memory usage (alerts if >90%)
- Disk space usage

### Process Information
- Top 10 CPU-consuming processes
- Top 10 memory-consuming processes
- Failed systemd services
- Total process count

### Network Status
- Network interface configuration
- Internet connectivity test (ping to 8.8.8.8)
- Active network connections

### Error Detection
- Recent kernel errors from dmesg
- Recent system log errors from journalctl
- Failed system services

## Troubleshooting

### SSH Connection Issues
```bash
# Test SSH connection manually
ssh -o ConnectTimeout=10 pi@your-rpi-ip

# Check SSH key permissions
chmod 600 ~/.ssh/rpi_monitor_key

# Verify SSH agent
ssh-add ~/.ssh/rpi_monitor_key
```

### Common Problems
- **Permission denied**: Ensure SSH key is properly installed on target Pi
- **Connection timeout**: Check if SSH is enabled on target Pi: `sudo systemctl enable ssh`
- **Command not found**: Some commands may not be available on all Pi distributions

## Analyzing Crash Patterns

Look for these warning signs in the logs:
- High CPU temperatures (>70°C sustained)
- Memory usage consistently >90%
- Increasing swap usage over time
- Kernel errors related to hardware
- Failed critical services
- Network connectivity issues

## Automation

Add to crontab for automatic monitoring:
```bash
# Monitor every hour
0 * * * * /path/to/rpi_monitor.py 192.168.1.100 --once

# Or run as a systemd service for continuous monitoring
```

## Data Analysis

The JSON output can be analyzed with tools like:
- `jq` for command-line JSON processing
- Python pandas for data analysis
- Grafana for visualization (with appropriate data import)

Example jq queries:
```bash
# Extract CPU temperatures from all files
jq '.cpu_metrics.cpu_temperature_c' rpi_logs/*.json

# Find high memory usage instances
jq 'select(.memory_metrics.memory.usage_percent > 90)' rpi_logs/*.json
```