#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Validation Script

Validates environment JSON files and simulates setup/release operations
without requiring Fabric capacity or authentication.

Usage:
    python validate_config.py --environment dev
    python validate_config.py --all
"""
import os
import sys
import io
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

import modules.misc_functions as misc


def validate_json_structure(config: Dict[str, Any], env_name: str) -> List[str]:
    """Validate JSON structure and return list of errors."""
    errors = []
    
    # Check required top-level keys
    required_keys = ["name", "generic", "layers"]
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")
    
    # Validate generic section
    if "generic" in config:
        generic = config["generic"]
        if "capacity_name" not in generic:
            errors.append("generic.capacity_name is required")
        if "permissions" not in generic:
            errors.append("generic.permissions is required")
        else:
            valid_roles = ["Admin", "Member", "Contributor", "Viewer"]
            for role in generic["permissions"]:
                if role not in valid_roles:
                    errors.append(f"Invalid permission role: {role} (must be one of {valid_roles})")
    
    # Validate layers
    if "layers" in config:
        layers = config["layers"]
        expected_layers = ["DE", "DM", "BI", "Shared"]
        for layer_name, layer_def in layers.items():
            if layer_name not in expected_layers:
                errors.append(f"Unexpected layer: {layer_name} (expected: {expected_layers})")
            
            if isinstance(layer_def, dict):
                if "git_directoryName" in layer_def and not layer_def["git_directoryName"]:
                    errors.append(f"Layer {layer_name}: git_directoryName is empty")
    
    return errors


def simulate_workspace_creation(config: Dict[str, Any], env_name: str) -> Dict[str, Any]:
    """Simulate workspace creation and return what would be created."""
    solution_name_template = config.get("name", "")
    layers = config.get("layers", {})
    capacity_name = config.get("generic", {}).get("capacity_name", "MyCapacity")
    
    workspaces = {}
    
    for layer_name, layer_def in layers.items():
        if not isinstance(layer_def, dict):
            continue
        
        workspace_name = misc.format_workspace_name(
            solution_name_template,
            layer_name,
            env_name
        )
        
        workspaces[layer_name] = {
            "workspace_name": workspace_name,
            "capacity": capacity_name,
            "layer": layer_name,
            "environment": env_name,
            "git_directory": layer_def.get("git_directoryName", ""),
            "items": layer_def.get("items", {})
        }
    
    return workspaces


def simulate_connections(config: Dict[str, Any], env_name: str) -> List[Dict[str, Any]]:
    """Simulate connection creation."""
    generic = config.get("generic", {})
    fabric_connections = generic.get("fabric_connections", [])
    git_settings = generic.get("git_settings")
    
    connections = []
    
    # Fabric connections
    for conn in fabric_connections:
        conn_name = misc.replace_template_variables(
            conn.get("name", ""),
            {"environment": env_name}
        )
        connections.append({
            "name": conn_name,
            "type": conn.get("type"),
            "category": "Fabric"
        })
    
    # Git connection
    if git_settings:
        git_creds = git_settings.get("myGitCredentials", {})
        conn_name_template = git_creds.get("connection_name", "")
        conn_name = misc.replace_template_variables(
            conn_name_template,
            {"environment": env_name}
        )
        
        git_provider = git_settings.get("gitProviderDetails", {})
        connections.append({
            "name": conn_name,
            "type": git_provider.get("gitProviderType", ""),
            "category": "Git",
            "repository": git_provider.get("repositoryName", ""),
            "branch": git_provider.get("branchName", "")
        })
    
    return connections


def simulate_permissions(config: Dict[str, Any], env_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """Simulate permission assignments."""
    generic = config.get("generic", {})
    permissions = generic.get("permissions", {})
    
    return permissions


def print_simulation_summary(config: Dict[str, Any], env_name: str):
    """Print simulation summary of what would be created."""
    misc.print_header(f"Simulation Summary for {env_name.upper()} Environment")
    
    # Workspaces
    workspaces = simulate_workspace_creation(config, env_name)
    misc.print_subheader("Workspaces to be Created")
    for layer, ws_info in workspaces.items():
        print(f"  {misc.BULLET} {ws_info['workspace_name']}")
        print(f"    - Capacity: {ws_info['capacity']}")
        print(f"    - Git Directory: {ws_info['git_directory']}")
        if ws_info['items']:
            print(f"    - Items: {list(ws_info['items'].keys())}")
    
    # Connections
    connections = simulate_connections(config, env_name)
    if connections:
        misc.print_subheader("Connections to be Created")
        for conn in connections:
            print(f"  {misc.BULLET} {conn['name']} ({conn['type']})")
            if conn.get('repository'):
                print(f"    - Repository: {conn['repository']}")
                print(f"    - Branch: {conn['branch']}")
    
    # Permissions
    permissions = simulate_permissions(config, env_name)
    if permissions:
        misc.print_subheader("Permission Assignments")
        for role, principals in permissions.items():
            if principals:
                print(f"  {misc.BULLET} {role}: {len(principals)} principal(s)")
                for principal in principals:
                    print(f"    - {principal.get('type')}: {principal.get('id')[:8]}...")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Validate and simulate Fabric setup configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--environment",
        required=False,
        choices=["dev", "tst", "prd"],
        help="Environment to validate (or use --all)"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all environments"
    )
    
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Show simulation of what would be created"
    )
    
    args = parser.parse_args()
    
    if not args.environment and not args.all:
        misc.print_error("Error: Specify --environment or --all")
        sys.exit(1)
    
    script_dir = Path(__file__).parent
    base_json_path = script_dir.parent / "resources" / "environments" / "infrastructure.json"
    
    base_json = misc.load_json(str(base_json_path))
    if not base_json:
        misc.print_error("Failed to load base configuration")
        sys.exit(1)
    
    environments_to_check = []
    if args.all:
        environments_to_check = ["dev", "tst", "prd"]
    else:
        environments_to_check = [args.environment]
    
    all_valid = True
    
    for env_name in environments_to_check:
        misc.print_header(f"Validating {env_name.upper()} Environment")
        
        env_json_path = script_dir.parent / "resources" / "environments" / f"infrastructure.{env_name}.json"
        env_json = misc.load_json(str(env_json_path))
        
        if not env_json:
            misc.print_error(f"Failed to load {env_name} configuration")
            all_valid = False
            continue
        
        # Merge configs
        merged_config = misc.merge_json(base_json, env_json)
        
        # Validate structure
        errors = validate_json_structure(merged_config, env_name)
        
        if errors:
            misc.print_error(f"Validation errors for {env_name}:")
            for error in errors:
                print(f"  {misc.CROSSMARK} {error}")
            all_valid = False
        else:
            misc.print_success(f"{misc.CHECKMARK} {env_name.upper()} configuration is valid")
        
        # Simulate if requested
        if args.simulate:
            print_simulation_summary(merged_config, env_name)
    
    if all_valid:
        misc.print_header("Validation Complete")
        misc.print_success(f"{misc.CHECKMARK} All configurations are valid!")
        sys.exit(0)
    else:
        misc.print_header("Validation Complete")
        misc.print_error("Some configurations have errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
