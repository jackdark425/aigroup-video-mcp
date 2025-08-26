"""
Status resource.

This resource provides system status and health information.
"""

import time
import psutil
import platform
from typing import Dict, Any
from .base import MCPResourceBase, ResourceData, format_json_content


class StatusResource(MCPResourceBase):
    """System status resource."""
    
    @property
    def uri(self) -> str:
        """Resource URI."""
        return "status://system"
    
    @property
    def name(self) -> str:
        """Resource name."""
        return "System Status"
    
    @property
    def description(self) -> str:
        """Resource description."""
        return "Real-time system status and health information"
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "application/json"
    
    async def read(self) -> ResourceData:
        """
        Read system status.
        
        Returns:
            ResourceData: System status information
        """
        try:
            status_data = self._get_system_status()
            
            content = format_json_content(status_data, pretty=True)
            
            return ResourceData(
                content=content,
                metadata={
                    "resource_type": "system_status",
                    "status": status_data.get("overall_status", "unknown"),
                    "generated_at": time.time()
                },
                mime_type=self.mime_type
            )
            
        except Exception as e:
            return ResourceData(
                content=f"Error reading system status: {str(e)}",
                metadata={"error": str(e)},
                mime_type="text/plain"
            )
    
    def _get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dict[str, Any]: System status information
        """
        try:
            # Get current time
            current_time = time.time()
            
            # System information
            system_info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_release": platform.release(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percentage": memory.percent,
                "formatted": {
                    "total": self._format_bytes(memory.total),
                    "available": self._format_bytes(memory.available),
                    "used": self._format_bytes(memory.used)
                }
            }
            
            # CPU information
            cpu_info = {
                "count": psutil.cpu_count(),
                "count_physical": psutil.cpu_count(logical=False),
                "usage_percent": psutil.cpu_percent(interval=1),
                "load_average": getattr(psutil, 'getloadavg', lambda: [0, 0, 0])()
            }
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percentage": (disk.used / disk.total) * 100,
                "formatted": {
                    "total": self._format_bytes(disk.total),
                    "used": self._format_bytes(disk.used),
                    "free": self._format_bytes(disk.free)
                }
            }
            
            # Process information
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "memory_info": process.memory_info()._asdict(),
                "cpu_percent": process.cpu_percent(),
                "create_time": process.create_time(),
                "status": process.status(),
                "num_threads": process.num_threads()
            }
            
            # Service status
            service_status = self._get_service_status()
            
            # Overall health assessment
            overall_status = self._assess_overall_health(memory_info, cpu_info, disk_info, service_status)
            
            return {
                "timestamp": current_time,
                "overall_status": overall_status,
                "uptime": current_time - psutil.boot_time(),
                "system": system_info,
                "memory": memory_info,
                "cpu": cpu_info,
                "disk": disk_info,
                "process": process_info,
                "service": service_status,
                "configuration": {
                    "environment": self.settings.environment,
                    "debug_mode": self.settings.debug,
                    "max_concurrent_requests": self.settings.mcp.max_concurrent_requests,
                    "max_file_size": self.settings.video.max_file_size,
                    "supported_formats": len(self.settings.video.supported_formats)
                }
            }
            
        except Exception as e:
            return {
                "timestamp": time.time(),
                "overall_status": "error",
                "error": str(e),
                "basic_info": {
                    "environment": getattr(self.settings, 'environment', 'unknown'),
                    "debug_mode": getattr(self.settings, 'debug', False)
                }
            }
    
    def _get_service_status(self) -> Dict[str, Any]:
        """
        Get service-specific status information.
        
        Returns:
            Dict[str, Any]: Service status
        """
        try:
            # Check DashScope configuration
            dashscope_status = "configured" if self.settings.dashscope.api_key else "not_configured"
            
            # Check video settings
            video_settings_valid = (
                self.settings.video.max_file_size > 0 and
                len(self.settings.video.supported_formats) > 0
            )
            
            return {
                "mcp_server": "running",
                "dashscope_api": dashscope_status,
                "video_processor": "available" if video_settings_valid else "misconfigured",
                "config_status": "loaded",
                "api_endpoints": {
                    "analyze_video": "available",
                    "summarize_video": "available", 
                    "analyze_scenes": "available",
                    "analyze_custom": "available",
                    "validate_source": "available"
                }
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _assess_overall_health(
        self, 
        memory_info: Dict[str, Any], 
        cpu_info: Dict[str, Any], 
        disk_info: Dict[str, Any],
        service_status: Dict[str, Any]
    ) -> str:
        """
        Assess overall system health.
        
        Args:
            memory_info: Memory usage information
            cpu_info: CPU usage information
            disk_info: Disk usage information
            service_status: Service status information
            
        Returns:
            str: Overall health status
        """
        try:
            issues = []
            warnings = []
            
            # Check memory usage
            if memory_info["percentage"] > 90:
                issues.append("high_memory_usage")
            elif memory_info["percentage"] > 75:
                warnings.append("moderate_memory_usage")
            
            # Check CPU usage
            if cpu_info["usage_percent"] > 90:
                issues.append("high_cpu_usage")
            elif cpu_info["usage_percent"] > 75:
                warnings.append("moderate_cpu_usage")
            
            # Check disk usage
            if disk_info["percentage"] > 95:
                issues.append("high_disk_usage")
            elif disk_info["percentage"] > 85:
                warnings.append("moderate_disk_usage")
            
            # Check service status
            if service_status.get("dashscope_api") == "not_configured":
                issues.append("dashscope_not_configured")
            
            if service_status.get("video_processor") == "misconfigured":
                issues.append("video_processor_misconfigured")
            
            # Determine overall status
            if issues:
                return "unhealthy"
            elif warnings:
                return "warning"
            else:
                return "healthy"
                
        except Exception:
            return "unknown"
    
    def _format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes in human readable format.
        
        Args:
            bytes_value: Bytes to format
            
        Returns:
            str: Formatted string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"


class ServiceHealthResource(MCPResourceBase):
    """Service health resource for specific service checks."""
    
    @property
    def uri(self) -> str:
        """Resource URI."""
        return "status://service/health"
    
    @property
    def name(self) -> str:
        """Resource name."""
        return "Service Health Check"
    
    @property
    def description(self) -> str:
        """Resource description."""
        return "Detailed health check for video analysis service components"
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "application/json"
    
    async def read(self) -> ResourceData:
        """
        Read service health information.
        
        Returns:
            ResourceData: Service health information
        """
        try:
            health_data = await self._perform_health_checks()
            
            content = format_json_content(health_data, pretty=True)
            
            return ResourceData(
                content=content,
                metadata={
                    "resource_type": "service_health",
                    "overall_health": health_data.get("overall_status", "unknown"),
                    "checks_passed": health_data.get("checks_passed", 0),
                    "checks_total": health_data.get("checks_total", 0),
                    "generated_at": time.time()
                },
                mime_type=self.mime_type
            )
            
        except Exception as e:
            return ResourceData(
                content=f"Error performing health checks: {str(e)}",
                metadata={"error": str(e)},
                mime_type="text/plain"
            )
    
    async def _perform_health_checks(self) -> Dict[str, Any]:
        """
        Perform comprehensive health checks.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        checks = []
        passed = 0
        
        # Configuration checks
        config_check = self._check_configuration()
        checks.append(config_check)
        if config_check["status"] == "pass":
            passed += 1
        
        # DashScope API check
        api_check = self._check_dashscope_config()
        checks.append(api_check)
        if api_check["status"] == "pass":
            passed += 1
        
        # Video processing check
        video_check = self._check_video_processing()
        checks.append(video_check)
        if video_check["status"] == "pass":
            passed += 1
        
        # System resources check
        resources_check = self._check_system_resources()
        checks.append(resources_check)
        if resources_check["status"] == "pass":
            passed += 1
        
        total_checks = len(checks)
        overall_status = "healthy" if passed == total_checks else "unhealthy" if passed < total_checks / 2 else "warning"
        
        return {
            "timestamp": time.time(),
            "overall_status": overall_status,
            "checks_passed": passed,
            "checks_total": total_checks,
            "health_score": (passed / total_checks) * 100 if total_checks > 0 else 0,
            "checks": checks
        }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity."""
        try:
            # Basic configuration validation
            if not self.settings:
                return {"name": "configuration", "status": "fail", "message": "Settings not loaded"}
            
            return {"name": "configuration", "status": "pass", "message": "Configuration loaded successfully"}
        except Exception as e:
            return {"name": "configuration", "status": "fail", "message": f"Configuration error: {str(e)}"}
    
    def _check_dashscope_config(self) -> Dict[str, Any]:
        """Check DashScope configuration."""
        try:
            if not self.settings.dashscope.api_key:
                return {"name": "dashscope_api", "status": "fail", "message": "DashScope API key not configured"}
            
            if len(self.settings.dashscope.api_key) < 10:
                return {"name": "dashscope_api", "status": "fail", "message": "DashScope API key appears invalid"}
            
            return {"name": "dashscope_api", "status": "pass", "message": "DashScope API configured"}
        except Exception as e:
            return {"name": "dashscope_api", "status": "fail", "message": f"DashScope config error: {str(e)}"}
    
    def _check_video_processing(self) -> Dict[str, Any]:
        """Check video processing configuration."""
        try:
            if not self.settings.video.supported_formats:
                return {"name": "video_processing", "status": "fail", "message": "No supported video formats configured"}
            
            if self.settings.video.max_file_size <= 0:
                return {"name": "video_processing", "status": "fail", "message": "Invalid max file size configuration"}
            
            return {"name": "video_processing", "status": "pass", "message": "Video processing configured"}
        except Exception as e:
            return {"name": "video_processing", "status": "fail", "message": f"Video config error: {str(e)}"}
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources availability."""
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 95:
                return {"name": "system_resources", "status": "fail", "message": "Critical memory usage"}
            
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 95:
                return {"name": "system_resources", "status": "fail", "message": "Critical CPU usage"}
            
            return {"name": "system_resources", "status": "pass", "message": "System resources available"}
        except Exception as e:
            return {"name": "system_resources", "status": "fail", "message": f"Resource check error: {str(e)}"}