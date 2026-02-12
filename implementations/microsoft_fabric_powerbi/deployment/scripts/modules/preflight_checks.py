"""
Pre-flight Checks Module

Validates prerequisites before deployment operations:
- Workspace existence and accessibility
- Capacity availability
- Permissions
- Git connectivity
- Configuration consistency
"""
import os
import sys
from typing import Dict, Any, List, Tuple
from pathlib import Path

import modules.misc_functions as misc
import modules.fabric_cli_functions as fabcli

try:
    import modules.framework_validator as fw_validator
except ImportError:
    fw_validator = None


class PreflightCheckResult:
    """Result of a pre-flight check."""
    def __init__(self, name: str, passed: bool, message: str = "", details: Dict[str, Any] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


class PreflightChecker:
    """Performs pre-flight checks before deployment operations."""
    
    def __init__(
        self,
        environment: str,
        env_definition: Dict[str, Any],
        dry_run: bool = False,
        skip_framework_validation: bool = False,
        include_stage1: bool = True,
        include_fabric: bool = True,
    ):
        self.environment = environment
        self.env_definition = env_definition
        self.dry_run = dry_run
        self.skip_framework_validation = skip_framework_validation
        self.include_stage1 = include_stage1
        self.include_fabric = include_fabric
        self.results: List[PreflightCheckResult] = []

    def check_all(self) -> Tuple[bool, List[PreflightCheckResult]]:
        """Run all pre-flight checks."""
        self.results = []

        # Configuration checks
        self.check_configuration_structure()
        self.check_required_fields()
        self.check_workspace_names()

        # Framework validation (Stage 1 + Fabric checks)
        if not self.dry_run and not self.skip_framework_validation and fw_validator:
            self.check_framework_validation()

        # Environment checks (skip in dry-run)
        if not self.dry_run:
            self.check_authentication()
            self.check_capacity_access()
            self.check_workspaces_exist()
            self.check_permissions()

        # Git checks
        self.check_git_configuration()

        # Path checks
        self.check_repository_paths()

        # Summary
        all_passed = all(r.passed for r in self.results)
        return all_passed, self.results

    def check_framework_validation(self):
        """Run Stage 1 and Fabric checks (requires repo root and PowerShell)."""
        if not fw_validator:
            self.results.append(PreflightCheckResult(
                "Framework Validation",
                True,
                "Framework validator module not available (skipped)"
            ))
            return
        success, message, details = fw_validator.run_framework_validation(
            include_stage1=self.include_stage1,
            include_fabric=self.include_fabric,
            dry_run=False,
        )
        self.results.append(PreflightCheckResult(
            "Framework Validation",
            success,
            message,
            details
        ))
    
    def check_configuration_structure(self):
        """Validate JSON configuration structure."""
        try:
            required_keys = ["name", "generic", "layers"]
            missing_keys = [key for key in required_keys if key not in self.env_definition]
            
            if missing_keys:
                self.results.append(PreflightCheckResult(
                    "Configuration Structure",
                    False,
                    f"Missing required keys: {', '.join(missing_keys)}"
                ))
            else:
                self.results.append(PreflightCheckResult(
                    "Configuration Structure",
                    True,
                    "All required keys present"
                ))
        except Exception as e:
            self.results.append(PreflightCheckResult(
                "Configuration Structure",
                False,
                f"Error validating structure: {str(e)}"
            ))
    
    def check_required_fields(self):
        """Check that required fields have values."""
        errors = []
        
        generic = self.env_definition.get("generic", {})
        if not generic.get("capacity_name"):
            errors.append("generic.capacity_name is missing or empty")
        
        if not generic.get("permissions"):
            errors.append("generic.permissions is missing")
        
        layers = self.env_definition.get("layers", {})
        for layer_name, layer_def in layers.items():
            if isinstance(layer_def, dict):
                if "git_directoryName" in layer_def and not layer_def.get("git_directoryName"):
                    errors.append(f"Layer {layer_name}: git_directoryName is empty")
        
        if errors:
            self.results.append(PreflightCheckResult(
                "Required Fields",
                False,
                "; ".join(errors)
            ))
        else:
            self.results.append(PreflightCheckResult(
                "Required Fields",
                True,
                "All required fields have values"
            ))
    
    def check_workspace_names(self):
        """Validate workspace name formatting."""
        solution_name_template = self.env_definition.get("name", "")
        environment_name = self.env_definition.get("generic", {}).get("environment_name", self.environment)
        layers = self.env_definition.get("layers", {})
        
        errors = []
        workspace_names = []
        
        for layer_name, layer_def in layers.items():
            if isinstance(layer_def, dict):
                workspace_name = misc.format_workspace_name(
                    solution_name_template,
                    layer_name,
                    environment_name
                )
                
                # Check for template variables that weren't replaced
                if "{" in workspace_name or "}" in workspace_name:
                    errors.append(f"Layer {layer_name}: Workspace name contains unreplaced template variables")
                
                # Check length (Fabric limit is typically 100 characters)
                if len(workspace_name) > 100:
                    errors.append(f"Layer {layer_name}: Workspace name exceeds 100 characters")
                
                workspace_names.append(workspace_name)
        
        if errors:
            self.results.append(PreflightCheckResult(
                "Workspace Names",
                False,
                "; ".join(errors),
                {"workspace_names": workspace_names}
            ))
        else:
            self.results.append(PreflightCheckResult(
                "Workspace Names",
                True,
                f"All {len(workspace_names)} workspace names are valid",
                {"workspace_names": workspace_names}
            ))
    
    def check_authentication(self):
        """Check if authentication is configured."""
        # Check if Fabric CLI is authenticated
        try:
            result = fabcli.run_command("auth show")
            if "error" in result.lower() or "not authenticated" in result.lower():
                self.results.append(PreflightCheckResult(
                    "Authentication",
                    False,
                    "Not authenticated with Fabric CLI. Run 'fabric auth login' first."
                ))
            else:
                self.results.append(PreflightCheckResult(
                    "Authentication",
                    True,
                    "Authenticated with Fabric CLI"
                ))
        except Exception as e:
            self.results.append(PreflightCheckResult(
                "Authentication",
                False,
                f"Error checking authentication: {str(e)}"
            ))
    
    def check_capacity_access(self):
        """Check if capacity is accessible."""
        capacity_name = self.env_definition.get("generic", {}).get("capacity_name", "")
        
        if not capacity_name:
            self.results.append(PreflightCheckResult(
                "Capacity Access",
                False,
                "Capacity name not specified"
            ))
            return
        
        try:
            # Try to list capacities or check access
            result = fabcli.run_command(f"capacity show --name {capacity_name}")
            if "error" in result.lower() or "not found" in result.lower():
                self.results.append(PreflightCheckResult(
                    "Capacity Access",
                    False,
                    f"Capacity '{capacity_name}' not accessible or not found"
                ))
            else:
                self.results.append(PreflightCheckResult(
                    "Capacity Access",
                    True,
                    f"Capacity '{capacity_name}' is accessible"
                ))
        except Exception as e:
            self.results.append(PreflightCheckResult(
                "Capacity Access",
                False,
                f"Error checking capacity access: {str(e)}"
            ))
    
    def check_workspaces_exist(self):
        """Check if workspaces already exist (for update scenarios)."""
        solution_name_template = self.env_definition.get("name", "")
        environment_name = self.env_definition.get("generic", {}).get("environment_name", self.environment)
        layers = self.env_definition.get("layers", {})
        
        existing_workspaces = []
        missing_workspaces = []
        
        for layer_name, layer_def in layers.items():
            if isinstance(layer_def, dict):
                workspace_name = misc.format_workspace_name(
                    solution_name_template,
                    layer_name,
                    environment_name
                )
                
                if fabcli.workspace_exists(workspace_name):
                    existing_workspaces.append(workspace_name)
                else:
                    missing_workspaces.append(workspace_name)
        
        if existing_workspaces and missing_workspaces:
            self.results.append(PreflightCheckResult(
                "Workspace Existence",
                True,  # Not a failure, just informational
                f"{len(existing_workspaces)} exist, {len(missing_workspaces)} will be created",
                {"existing": existing_workspaces, "missing": missing_workspaces}
            ))
        elif existing_workspaces:
            self.results.append(PreflightCheckResult(
                "Workspace Existence",
                True,
                f"All {len(existing_workspaces)} workspaces already exist (update mode)",
                {"existing": existing_workspaces}
            ))
        else:
            self.results.append(PreflightCheckResult(
                "Workspace Existence",
                True,
                f"All {len(missing_workspaces)} workspaces will be created (create mode)",
                {"missing": missing_workspaces}
            ))
    
    def check_permissions(self):
        """Validate permission configuration."""
        generic = self.env_definition.get("generic", {})
        permissions = generic.get("permissions", {})
        
        valid_roles = ["Admin", "Member", "Contributor", "Viewer"]
        invalid_roles = [role for role in permissions.keys() if role not in valid_roles]
        
        if invalid_roles:
            self.results.append(PreflightCheckResult(
                "Permissions",
                False,
                f"Invalid permission roles: {', '.join(invalid_roles)}"
            ))
        else:
            total_principals = sum(len(principals) for principals in permissions.values())
            self.results.append(PreflightCheckResult(
                "Permissions",
                True,
                f"Permissions configured for {total_principals} principal(s) across {len(permissions)} role(s)"
            ))
    
    def check_git_configuration(self):
        """Validate Git configuration."""
        generic = self.env_definition.get("generic", {})
        git_settings = generic.get("git_settings", {})
        
        if not git_settings:
            self.results.append(PreflightCheckResult(
                "Git Configuration",
                True,  # Git is optional
                "Git integration not configured (optional)"
            ))
            return
        
        git_provider = git_settings.get("gitProviderDetails", {})
        required_git_fields = ["gitProviderType", "organizationName", "projectName", "repositoryName", "branchName"]
        missing_fields = [field for field in required_git_fields if not git_provider.get(field)]
        
        if missing_fields:
            self.results.append(PreflightCheckResult(
                "Git Configuration",
                False,
                f"Missing Git provider fields: {', '.join(missing_fields)}"
            ))
        else:
            provider_type = git_provider.get("gitProviderType", "Unknown")
            self.results.append(PreflightCheckResult(
                "Git Configuration",
                True,
                f"Git configured for {provider_type} repository"
            ))
    
    def check_repository_paths(self, repo_base_path: str = "./solution"):
        """Check if repository paths exist."""
        layers = self.env_definition.get("layers", {})
        
        missing_paths = []
        existing_paths = []
        
        for layer_name, layer_def in layers.items():
            if isinstance(layer_def, dict):
                git_directory = layer_def.get("git_directoryName", f"solution/{layer_name.lower()}")
                # Remove 'solution/' prefix if present
                relative_path = git_directory.replace("solution/", "")
                full_path = os.path.join(repo_base_path, relative_path)
                
                if os.path.exists(full_path):
                    existing_paths.append(full_path)
                else:
                    missing_paths.append(full_path)
        
        if missing_paths and existing_paths:
            self.results.append(PreflightCheckResult(
                "Repository Paths",
                True,  # Warning only - paths may not exist during initial setup
                f"{len(existing_paths)} paths exist, {len(missing_paths)} missing (will be created during Git sync)",
                {"existing": existing_paths, "missing": missing_paths}
            ))
        elif missing_paths:
            self.results.append(PreflightCheckResult(
                "Repository Paths",
                True,  # Not a failure - paths will be created when Git is connected
                f"All {len(missing_paths)} repository paths are missing (expected for initial setup - will be created during Git sync)",
                {"missing": missing_paths}
            ))
        else:
            self.results.append(PreflightCheckResult(
                "Repository Paths",
                True,
                f"All {len(existing_paths)} repository paths exist",
                {"existing": existing_paths}
            ))
    
    def print_summary(self):
        """Print summary of all checks."""
        misc.print_header("Pre-flight Checks Summary")
        
        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]
        
        for result in passed:
            misc.print_success(f"  {misc.CHECKMARK} {result.name}: {result.message}")
        
        for result in failed:
            misc.print_error(f"  {misc.CROSSMARK} {result.name}: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"      {key}: {', '.join(str(v) for v in value[:5])}{'...' if len(value) > 5 else ''}")
        
        print("")
        misc.print_info(f"Total: {len(self.results)} checks, {len(passed)} passed, {len(failed)} failed")
        
        return len(failed) == 0
