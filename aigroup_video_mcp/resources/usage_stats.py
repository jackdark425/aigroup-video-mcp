"""
Usage statistics resource.

This resource provides usage statistics and analytics information.
"""

import time
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from .base import MCPResourceBase, ResourceData, format_json_content, format_table_content


@dataclass
class UsageRecord:
    """Usage record for tracking tool and resource usage."""
    
    timestamp: float
    type: str  # 'tool' or 'resource'
    name: str
    success: bool
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class UsageTracker:
    """Thread-safe usage tracker."""
    
    def __init__(self, max_records: int = 1000):
        """
        Initialize usage tracker.
        
        Args:
            max_records: Maximum number of records to keep in memory
        """
        self.max_records = max_records
        self._records = deque(maxlen=max_records)
        self._lock = Lock()
        self._start_time = time.time()
    
    def record_usage(
        self,
        usage_type: str,
        name: str,
        success: bool = True,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a usage event.
        
        Args:
            usage_type: Type of usage ('tool' or 'resource')
            name: Name of tool or resource
            success: Whether the operation was successful
            duration: Duration of operation in seconds
            metadata: Additional metadata
        """
        record = UsageRecord(
            timestamp=time.time(),
            type=usage_type,
            name=name,
            success=success,
            duration=duration,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._records.append(record)
    
    def get_records(self, limit: Optional[int] = None) -> List[UsageRecord]:
        """
        Get usage records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List[UsageRecord]: Usage records
        """
        with self._lock:
            records = list(self._records)
        
        if limit:
            return records[-limit:]
        return records
    
    def get_stats(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Args:
            hours: Number of hours to include in stats (None for all)
            
        Returns:
            Dict[str, Any]: Usage statistics
        """
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600) if hours else 0
        
        with self._lock:
            filtered_records = [
                record for record in self._records
                if record.timestamp >= cutoff_time
            ]
        
        if not filtered_records:
            return self._empty_stats()
        
        # Calculate statistics
        total_requests = len(filtered_records)
        successful_requests = sum(1 for r in filtered_records if r.success)
        failed_requests = total_requests - successful_requests
        
        # Tool statistics
        tool_records = [r for r in filtered_records if r.type == 'tool']
        tool_usage = defaultdict(int)
        tool_success = defaultdict(int)
        tool_durations = defaultdict(list)
        
        for record in tool_records:
            tool_usage[record.name] += 1
            if record.success:
                tool_success[record.name] += 1
            if record.duration is not None:
                tool_durations[record.name].append(record.duration)
        
        # Resource statistics
        resource_records = [r for r in filtered_records if r.type == 'resource']
        resource_usage = defaultdict(int)
        resource_success = defaultdict(int)
        
        for record in resource_records:
            resource_usage[record.name] += 1
            if record.success:
                resource_success[record.name] += 1
        
        # Calculate averages
        avg_durations = {}
        for tool, durations in tool_durations.items():
            if durations:
                avg_durations[tool] = sum(durations) / len(durations)
        
        # Time series data (hourly buckets)
        time_series = self._calculate_time_series(filtered_records, hours or 24)
        
        return {
            "period": {
                "hours": hours,
                "start_time": cutoff_time,
                "end_time": current_time
            },
            "totals": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests) * 100 if total_requests > 0 else 0
            },
            "tools": {
                "usage_count": dict(tool_usage),
                "success_count": dict(tool_success),
                "average_duration": avg_durations,
                "most_used": max(tool_usage.items(), key=lambda x: x[1]) if tool_usage else None
            },
            "resources": {
                "usage_count": dict(resource_usage),
                "success_count": dict(resource_success),
                "most_accessed": max(resource_usage.items(), key=lambda x: x[1]) if resource_usage else None
            },
            "time_series": time_series
        }
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "period": {"hours": None, "start_time": None, "end_time": None},
            "totals": {"total_requests": 0, "successful_requests": 0, "failed_requests": 0, "success_rate": 0},
            "tools": {"usage_count": {}, "success_count": {}, "average_duration": {}, "most_used": None},
            "resources": {"usage_count": {}, "success_count": {}, "most_accessed": None},
            "time_series": []
        }
    
    def _calculate_time_series(self, records: List[UsageRecord], hours: int) -> List[Dict[str, Any]]:
        """Calculate time series data for visualization."""
        if not records:
            return []
        
        # Create hourly buckets
        current_time = time.time()
        start_time = current_time - (hours * 3600)
        
        buckets = []
        for i in range(hours):
            bucket_start = start_time + (i * 3600)
            bucket_end = bucket_start + 3600
            
            bucket_records = [
                r for r in records
                if bucket_start <= r.timestamp < bucket_end
            ]
            
            buckets.append({
                "hour": i,
                "timestamp": bucket_start,
                "total_requests": len(bucket_records),
                "successful_requests": sum(1 for r in bucket_records if r.success),
                "failed_requests": sum(1 for r in bucket_records if not r.success)
            })
        
        return buckets
    
    def clear(self) -> None:
        """Clear all usage records."""
        with self._lock:
            self._records.clear()


# Global usage tracker instance
_usage_tracker = UsageTracker()


def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    return _usage_tracker


def record_tool_usage(tool_name: str, success: bool = True, duration: Optional[float] = None, **metadata) -> None:
    """Record tool usage."""
    _usage_tracker.record_usage("tool", tool_name, success, duration, metadata)


def record_resource_usage(resource_uri: str, success: bool = True, **metadata) -> None:
    """Record resource usage."""
    _usage_tracker.record_usage("resource", resource_uri, success, metadata=metadata)


class UsageStatsResource(MCPResourceBase):
    """Usage statistics resource."""
    
    @property
    def uri(self) -> str:
        """Resource URI."""
        return "stats://usage"
    
    @property
    def name(self) -> str:
        """Resource name."""
        return "Usage Statistics"
    
    @property
    def description(self) -> str:
        """Resource description."""
        return "Usage statistics and analytics for tools and resources"
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "application/json"
    
    async def read(self) -> ResourceData:
        """
        Read usage statistics.
        
        Returns:
            ResourceData: Usage statistics
        """
        try:
            # Get statistics for last 24 hours
            stats_data = _usage_tracker.get_stats(hours=24)
            
            content = format_json_content(stats_data, pretty=True)
            
            return ResourceData(
                content=content,
                metadata={
                    "resource_type": "usage_statistics",
                    "period_hours": 24,
                    "total_requests": stats_data["totals"]["total_requests"],
                    "success_rate": stats_data["totals"]["success_rate"],
                    "generated_at": time.time()
                },
                mime_type=self.mime_type
            )
            
        except Exception as e:
            return ResourceData(
                content=f"Error reading usage statistics: {str(e)}",
                metadata={"error": str(e)},
                mime_type="text/plain"
            )


class UsageReportResource(MCPResourceBase):
    """Usage report resource with different time periods."""
    
    def __init__(self, hours: int = 24):
        """
        Initialize usage report resource.
        
        Args:
            hours: Number of hours to include in report
        """
        super().__init__()
        self.hours = hours
    
    @property
    def uri(self) -> str:
        """Resource URI."""
        return f"stats://usage/report/{self.hours}h"
    
    @property
    def name(self) -> str:
        """Resource name."""
        return f"Usage Report ({self.hours}h)"
    
    @property
    def description(self) -> str:
        """Resource description."""
        return f"Detailed usage report for the last {self.hours} hours"
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "text/plain"
    
    async def read(self) -> ResourceData:
        """
        Read usage report.
        
        Returns:
            ResourceData: Usage report
        """
        try:
            stats_data = _usage_tracker.get_stats(hours=self.hours)
            
            # Format as readable report
            content = self._format_usage_report(stats_data)
            
            return ResourceData(
                content=content,
                metadata={
                    "resource_type": "usage_report",
                    "period_hours": self.hours,
                    "total_requests": stats_data["totals"]["total_requests"],
                    "success_rate": stats_data["totals"]["success_rate"],
                    "generated_at": time.time()
                },
                mime_type=self.mime_type
            )
            
        except Exception as e:
            return ResourceData(
                content=f"Error generating usage report: {str(e)}",
                metadata={"error": str(e)},
                mime_type="text/plain"
            )
    
    def _format_usage_report(self, stats: Dict[str, Any]) -> str:
        """Format statistics as readable report."""
        lines = []
        
        # Header
        lines.append(f"# Usage Report - Last {self.hours} Hours")
        lines.append("=" * 50)
        lines.append("")
        
        # Summary
        totals = stats["totals"]
        lines.append("## Summary")
        lines.append(f"Total Requests: {totals['total_requests']}")
        lines.append(f"Successful: {totals['successful_requests']}")
        lines.append(f"Failed: {totals['failed_requests']}")
        lines.append(f"Success Rate: {totals['success_rate']:.1f}%")
        lines.append("")
        
        # Tool usage
        tools = stats["tools"]
        if tools["usage_count"]:
            lines.append("## Tool Usage")
            
            # Create table data
            tool_data = []
            for tool_name, count in tools["usage_count"].items():
                success_count = tools["success_count"].get(tool_name, 0)
                avg_duration = tools["average_duration"].get(tool_name)
                
                tool_data.append({
                    "Tool": tool_name,
                    "Total": count,
                    "Success": success_count,
                    "Success Rate": f"{(success_count/count)*100:.1f}%" if count > 0 else "0%",
                    "Avg Duration": f"{avg_duration:.2f}s" if avg_duration else "N/A"
                })
            
            # Sort by usage count
            tool_data.sort(key=lambda x: x["Total"], reverse=True)
            
            table = format_table_content(tool_data)
            lines.append(table)
            lines.append("")
            
            if tools["most_used"]:
                lines.append(f"Most Used Tool: {tools['most_used'][0]} ({tools['most_used'][1]} requests)")
                lines.append("")
        
        # Resource usage
        resources = stats["resources"]
        if resources["usage_count"]:
            lines.append("## Resource Access")
            
            resource_data = []
            for resource_name, count in resources["usage_count"].items():
                success_count = resources["success_count"].get(resource_name, 0)
                
                resource_data.append({
                    "Resource": resource_name,
                    "Total": count,
                    "Success": success_count,
                    "Success Rate": f"{(success_count/count)*100:.1f}%" if count > 0 else "0%"
                })
            
            resource_data.sort(key=lambda x: x["Total"], reverse=True)
            
            table = format_table_content(resource_data)
            lines.append(table)
            lines.append("")
            
            if resources["most_accessed"]:
                lines.append(f"Most Accessed Resource: {resources['most_accessed'][0]} ({resources['most_accessed'][1]} accesses)")
                lines.append("")
        
        # Time series summary
        time_series = stats["time_series"]
        if time_series:
            lines.append("## Activity Over Time")
            
            # Find peak hour
            peak_hour = max(time_series, key=lambda x: x["total_requests"])
            lines.append(f"Peak Activity: Hour {peak_hour['hour']} with {peak_hour['total_requests']} requests")
            
            # Recent activity (last 5 hours)
            recent_hours = time_series[-5:] if len(time_series) >= 5 else time_series
            lines.append("\nRecent Activity (last 5 hours):")
            for hour_data in recent_hours:
                lines.append(f"  Hour {hour_data['hour']}: {hour_data['total_requests']} requests "
                           f"({hour_data['successful_requests']} success, {hour_data['failed_requests']} failed)")
        
        lines.append("")
        lines.append(f"Report generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(lines)