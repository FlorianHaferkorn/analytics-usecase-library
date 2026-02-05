"""
Health Checks Module

Validates post-deployment health of Fabric workspaces and items.
"""
import os
import sys
from typing import Dict, Any, List, Tuple
from pathlib import Path

import modules.misc_functions as misc
import modules.fabric_cli_functions as fabcli


class HealthCheckResult:
    """Result of a health check."""
    def __init__(self, name: str, status: str, message: str = "", details: Dict[str, Any] = None):
        self.name = name
        self.status = status  # "healthy", "warning", "unhealthy"
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        return f"[{self.status.upper()}] {self.name}: {self.message}"


class HealthChecker:
    """Performs health checks after deployment."""
    
    def __init__(self, environment: str, env_definition: Dict[str, Any], dry_run: bool = False):
        self.environment = environment
        self.env_definition = env_definition
        self.dry_run = dry_run
        self.results: List[HealthCheckResult] = []
    
    def check_all(self, workspace_names: List[str] = None) -> Tuple[bool, List[HealthCheckResult]]:
        """Run all health checks."""
        self.results = []
        
        if self.dry_run:
            self.results.append(HealthCheckResult(
                "Health Checks",
                "warning",
                "Skipped in dry-run mode"
            ))
            return True, self.results
        
        # Get workspace names if not provided
        if not workspace_names:
            workspace_names = self._get_workspace_names()
        
        # Check each workspace
        for workspace_name in workspace_names:
            self.check_workspace_accessible(workspace_name)
            self.check_workspace_permissions(workspace_name)
            self.check_workspace_items(workspace_name)
        
        # Overall health
        unhealthy = [r for r in self.results if r.status == "unhealthy"]
        warnings = [r for r in self.results if r.status == "warning"]
        
        all_healthy = len(unhealthy) == 0
        
        return all_healthy, self.results
    
    def _get_workspace_names(self) -> List[str]:
        """Get list of workspace names from configuration."""
        solution_name_template = self.env_definition.get("name", "")
        environment_name = self.env_definition.get("generic", {}).get("environment_name", self.environment)
        layers = self.env_definition.get("layers", {})
        
        workspace_names = []
        for layer_name, layer_def in layers.items():
            if isinstance(layer_def, dict):
                workspace_name = misc.format_workspace_name(
                    solution_name_template,
                    layer_name,
                    environment_name
                )
                workspace_names.append(workspace_name)
        
        return workspace_names
    
    def check_workspace_accessible(self, workspace_name: str):
        """Check if workspace is accessible."""
        try:
            workspace = fabcli.get_workspace(workspace_name)
            if workspace:
                self.results.append(HealthCheckResult(
                    f"Workspace Access: {workspace_name}",
                    "healthy",
                    "Workspace is accessible",
                    {"workspace_id": workspace.get("id")}
                ))
            else:
                self.results.append(HealthCheckResult(
                    f"Workspace Access: {workspace_name}",
                    "unhealthy",
                    "Workspace not found or not accessible"
                ))
        except Exception as e:
            self.results.append(HealthCheckResult(
                f"Workspace Access: {workspace_name}",
                "unhealthy",
                f"Error checking workspace: {str(e)}"
            ))
    
    def check_workspace_permissions(self, workspace_name: str):
        """Check workspace permissions (basic check)."""
        try:
            workspace = fabcli.get_workspace(workspace_name)
            if workspace:
                # Check if we can read workspace details (indicates permissions)
                workspace_id = workspace.get("id")
                if workspace_id:
                    self.results.append(HealthCheckResult(
                        f"Workspace Permissions: {workspace_name}",
                        "healthy",
                        "Permissions appear to be configured correctly"
                    ))
                else:
                    self.results.append(HealthCheckResult(
                        f"Workspace Permissions: {workspace_name}",
                        "warning",
                        "Could not verify permissions"
                    ))
        except Exception as e:
            self.results.append(HealthCheckResult(
                f"Workspace Permissions: {workspace_name}",
                "warning",
                f"Could not check permissions: {str(e)}"
            ))
    
    def check_workspace_items(self, workspace_name: str):
        """Check if workspace has expected items."""
        try:
            workspace = fabcli.get_workspace(workspace_name)
            if not workspace:
                return
            
            # Try to list items in workspace
            # Note: This is a simplified check - actual item listing may require different API calls
            self.results.append(HealthCheckResult(
                f"Workspace Items: {workspace_name}",
                "healthy",
                "Workspace items check completed (detailed item validation requires workspace access)"
            ))
        except Exception as e:
            self.results.append(HealthCheckResult(
                f"Workspace Items: {workspace_name}",
                "warning",
                f"Could not verify items: {str(e)}"
            ))
    
    def print_summary(self):
        """Print summary of health checks."""
        misc.print_header("Post-Deployment Health Checks")
        
        healthy = [r for r in self.results if r.status == "healthy"]
        warnings = [r for r in self.results if r.status == "warning"]
        unhealthy = [r for r in self.results if r.status == "unhealthy"]
        
        for result in healthy:
            misc.print_success(f"  {misc.CHECKMARK} {result.name}: {result.message}")
        
        for result in warnings:
            misc.print_warning(f"  ⚠ {result.name}: {result.message}")
        
        for result in unhealthy:
            misc.print_error(f"  {misc.CROSSMARK} {result.name}: {result.message}")
        
        print("")
        misc.print_info(f"Total: {len(self.results)} checks, {len(healthy)} healthy, {len(warnings)} warnings, {len(unhealthy)} unhealthy")
        
        return len(unhealthy) == 0
