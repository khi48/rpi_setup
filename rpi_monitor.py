#!/usr/bin/env python3
"""
Raspberry Pi Remote Health Monitor

Connects to a remote Raspberry Pi via SSH and collects comprehensive
health metrics to diagnose potential crash causes.
"""

import subprocess
import json
import datetime
import time
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class RPiMonitor:
    def __init__(self, hostname: str, username: str = 'pi', key_path: Optional[str] = None):
        self.hostname = hostname
        self.username = username
        self.key_path = key_path
        self.log_dir = Path('./rpi_logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        log_file = self.log_dir / f'rpi_monitor_{hostname}_{datetime.datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _run_remote_command(self, command: str) -> Optional[str]:
        """Execute a command on the remote Raspberry Pi via SSH"""
        try:
            ssh_cmd = ['ssh', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=no']
            
            if self.key_path:
                ssh_cmd.extend(['-i', self.key_path])
            
            ssh_cmd.append(f'{self.username}@{self.hostname}')
            ssh_cmd.append(command)
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self.logger.error(f"Command failed: {command}, Error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {command}")
            return None
        except Exception as e:
            self.logger.error(f"SSH connection failed: {e}")
            return None

    def get_system_info(self) -> Dict[str, Any]:
        """Collect basic system information"""
        info = {}
        
        # System uptime
        uptime = self._run_remote_command("uptime")
        if uptime:
            info['uptime'] = uptime
            
        # Kernel version
        kernel = self._run_remote_command("uname -r")
        if kernel:
            info['kernel_version'] = kernel
            
        # OS version
        os_version = self._run_remote_command("cat /etc/os-release | grep PRETTY_NAME")
        if os_version:
            info['os_version'] = os_version.split('=')[1].strip('"')
            
        return info

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU-related metrics"""
        metrics = {}
        
        # CPU usage
        cpu_usage = self._run_remote_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
        if cpu_usage:
            try:
                metrics['cpu_usage_percent'] = float(cpu_usage)
            except ValueError:
                pass
                
        # Load average
        load_avg = self._run_remote_command("cat /proc/loadavg")
        if load_avg:
            loads = load_avg.split()[:3]
            metrics['load_average'] = {
                '1min': float(loads[0]),
                '5min': float(loads[1]),
                '15min': float(loads[2])
            }
            
        # CPU temperature
        temp = self._run_remote_command("vcgencmd measure_temp")
        if temp:
            try:
                temp_val = temp.replace("temp=", "").replace("'C", "")
                metrics['cpu_temperature_c'] = float(temp_val)
            except ValueError:
                pass
                
        # CPU frequency
        freq = self._run_remote_command("vcgencmd measure_clock arm")
        if freq:
            try:
                freq_val = freq.split('=')[1]
                metrics['cpu_frequency_hz'] = int(freq_val)
            except (ValueError, IndexError):
                pass
                
        return metrics

    def get_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory usage metrics"""
        metrics = {}
        
        # Memory usage
        mem_info = self._run_remote_command("free -m")
        if mem_info:
            lines = mem_info.split('\n')
            if len(lines) >= 2:
                mem_line = lines[1].split()
                metrics['memory'] = {
                    'total_mb': int(mem_line[1]),
                    'used_mb': int(mem_line[2]),
                    'free_mb': int(mem_line[3]),
                    'available_mb': int(mem_line[6]) if len(mem_line) > 6 else int(mem_line[3])
                }
                metrics['memory']['usage_percent'] = (metrics['memory']['used_mb'] / metrics['memory']['total_mb']) * 100
                
        # Swap usage
        swap_info = self._run_remote_command("swapon --show --noheadings")
        if swap_info:
            swap_lines = swap_info.strip().split('\n')
            if swap_lines and swap_lines[0]:
                swap_parts = swap_lines[0].split()
                if len(swap_parts) >= 4:
                    metrics['swap'] = {
                        'size': swap_parts[1],
                        'used': swap_parts[2],
                        'usage_percent': float(swap_parts[4].rstrip('%'))
                    }
        
        return metrics

    def get_disk_metrics(self) -> Dict[str, Any]:
        """Collect disk usage and I/O metrics"""
        metrics = {}
        
        # Disk usage
        disk_usage = self._run_remote_command("df -h")
        if disk_usage:
            lines = disk_usage.split('\n')[1:]  # Skip header
            disks = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 6 and parts[0].startswith('/dev/'):
                    disks.append({
                        'device': parts[0],
                        'size': parts[1],
                        'used': parts[2],
                        'available': parts[3],
                        'usage_percent': parts[4].rstrip('%'),
                        'mount_point': parts[5]
                    })
            metrics['disk_usage'] = disks
            
        # I/O statistics
        iostat = self._run_remote_command("iostat -d 1 2 | tail -n +4")
        if iostat:
            metrics['disk_io'] = iostat
            
        return metrics

    def get_network_metrics(self) -> Dict[str, Any]:
        """Collect network-related metrics"""
        metrics = {}
        
        # Network interfaces
        interfaces = self._run_remote_command("ip addr show")
        if interfaces:
            metrics['network_interfaces'] = interfaces
            
        # Network connectivity test
        ping_test = self._run_remote_command("ping -c 3 8.8.8.8")
        if ping_test:
            metrics['internet_connectivity'] = 'ping successful' in ping_test or '3 received' in ping_test
        else:
            metrics['internet_connectivity'] = False
            
        # Active connections
        connections = self._run_remote_command("ss -tuln")
        if connections:
            metrics['active_connections'] = len(connections.split('\n')) - 1
            
        return metrics

    def get_process_metrics(self) -> Dict[str, Any]:
        """Collect process and service information"""
        metrics = {}
        
        # Top processes by CPU
        top_cpu = self._run_remote_command("ps aux --sort=-%cpu | head -10")
        if top_cpu:
            metrics['top_cpu_processes'] = top_cpu
            
        # Top processes by memory
        top_mem = self._run_remote_command("ps aux --sort=-%mem | head -10")
        if top_mem:
            metrics['top_memory_processes'] = top_mem
            
        # Process count
        proc_count = self._run_remote_command("ps aux | wc -l")
        if proc_count:
            try:
                metrics['total_processes'] = int(proc_count) - 1  # Subtract header
            except ValueError:
                pass
                
        # Failed services
        failed_services = self._run_remote_command("systemctl --failed --no-legend")
        if failed_services:
            metrics['failed_services'] = failed_services.split('\n') if failed_services.strip() else []
            
        return metrics

    def get_log_errors(self) -> Dict[str, Any]:
        """Check for recent errors in system logs"""
        metrics = {}
        
        # Recent kernel errors
        kernel_errors = self._run_remote_command("dmesg | grep -i error | tail -10")
        if kernel_errors:
            metrics['recent_kernel_errors'] = kernel_errors.split('\n')
            
        # Recent syslog errors
        syslog_errors = self._run_remote_command("journalctl --since='1 hour ago' -p err --no-pager | tail -20")
        if syslog_errors:
            metrics['recent_syslog_errors'] = syslog_errors.split('\n')
            
        return metrics

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        timestamp = datetime.datetime.now().isoformat()
        
        self.logger.info(f"Starting health check for {self.hostname}")
        
        metrics = {
            'timestamp': timestamp,
            'hostname': self.hostname,
            'system_info': self.get_system_info(),
            'cpu_metrics': self.get_cpu_metrics(),
            'memory_metrics': self.get_memory_metrics(),
            'disk_metrics': self.get_disk_metrics(),
            'network_metrics': self.get_network_metrics(),
            'process_metrics': self.get_process_metrics(),
            'log_errors': self.get_log_errors()
        }
        
        return metrics

    def save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save metrics to JSON file"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.log_dir / f'health_check_{self.hostname}_{timestamp}.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(metrics, f, indent=2)
            self.logger.info(f"Metrics saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    def monitor_once(self) -> bool:
        """Perform a single monitoring cycle"""
        try:
            metrics = self.collect_all_metrics()
            self.save_metrics(metrics)
            
            # Log key health indicators
            cpu_metrics = metrics.get('cpu_metrics', {})
            mem_metrics = metrics.get('memory_metrics', {})
            
            if 'cpu_temperature_c' in cpu_metrics:
                temp = cpu_metrics['cpu_temperature_c']
                if temp > 70:
                    self.logger.warning(f"High CPU temperature: {temp}°C")
                    
            if 'memory' in mem_metrics:
                mem_usage = mem_metrics['memory'].get('usage_percent', 0)
                if mem_usage > 90:
                    self.logger.warning(f"High memory usage: {mem_usage:.1f}%")
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Monitoring cycle failed: {e}")
            return False

    def monitor_continuous(self, interval: int = 300) -> None:
        """Run continuous monitoring with specified interval (seconds)"""
        self.logger.info(f"Starting continuous monitoring every {interval} seconds")
        
        while True:
            try:
                success = self.monitor_once()
                if not success:
                    self.logger.error("Monitoring cycle failed, will retry next interval")
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='Monitor Raspberry Pi health remotely')
    parser.add_argument('hostname', help='Hostname or IP address of the target Raspberry Pi')
    parser.add_argument('-u', '--username', default='pi', help='SSH username (default: pi)')
    parser.add_argument('-k', '--key', help='Path to SSH private key file')
    parser.add_argument('-i', '--interval', type=int, default=300, 
                       help='Monitoring interval in seconds (default: 300)')
    parser.add_argument('--once', action='store_true', 
                       help='Run once instead of continuous monitoring')
    
    args = parser.parse_args()
    
    monitor = RPiMonitor(args.hostname, args.username, args.key)
    
    if args.once:
        monitor.monitor_once()
    else:
        monitor.monitor_continuous(args.interval)


if __name__ == '__main__':
    main()