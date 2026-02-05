#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parameter File Builder

Generates parameter.yml files from environment JSON configuration and workspace/item metadata.
Reduces manual maintenance of parameter files.

Usage:
    python utils_build_parameter_file.py --environments dev,tst,prd
"""
import os
import sys
import io
import argparse
import yaml
from pathlib import Path

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

# Default values
DEFAULT_ENVIRONMENTS = "dev,tst,prd"


def load_environment_configs(environments: list):
    """Load configuration for multiple environments."""
    script_dir = Path(__file__).parent
    base_json_path = script_dir.parent / "resources" / "environments" / "infrastructure.json"
    
    base_json = misc.load_json(str(base_json_path))
    if not base_json:
        return None
    
    configs = {}
    for env in environments:
        env_json_path = script_dir.parent / "resources" / "environments" / f"infrastructure.{env}.json"
        env_json = misc.load_json(str(env_json_path))
        if env_json:
            configs[env] = misc.merge_json(base_json, env_json)
    
    return configs


def generate_parameter_file(configs: dict, output_path: str = None):
    """
    Generate parameter.yml from environment configurations.
    
    This is a simplified version - in practice, you would:
    1. Query Fabric workspaces to get actual item IDs
    2. Map dev IDs to tst/prd IDs based on naming patterns
    3. Generate find_replace, key_value_replace, etc. entries
    """
    parameter_data = {
        "find_replace": [],
        "key_value_replace": [],
        "spark_pool": [],
        "semantic_model_binding": []
    }
    
    # Example: Generate find_replace entries for connections
    # In practice, you would query Fabric to get actual connection IDs
    
    # Example: Generate semantic_model_binding entries
    base_config = configs.get("dev", {})
    layers = base_config.get("layers", {})
    
    dm_layer = layers.get("DM", {})
    items = dm_layer.get("items", {})
    semantic_models = items.get("SemanticModel", [])
    
    for model in semantic_models:
        model_name = model.get("item_name")
        if model_name:
            # In practice, get connection_id from config or Fabric
            parameter_data["semantic_model_binding"].append({
                "connection_id": "connection-id-placeholder",
                "semantic_model_name": model_name
            })
    
    # Write YAML file
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(parameter_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        misc.print_success(f"Parameter file written to: {output_path}")
    else:
        print(yaml.dump(parameter_data, default_flow_style=False, sort_keys=False, allow_unicode=True))
    
    return parameter_data


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Build parameter.yml files from environment configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--environments",
        required=False,
        default=DEFAULT_ENVIRONMENTS,
        help=f"Comma-separated list of environments (default: {DEFAULT_ENVIRONMENTS})"
    )
    
    parser.add_argument(
        "--output",
        required=False,
        help="Output file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    environments = [env.strip() for env in args.environments.split(",")]
    
    misc.print_header("Building Parameter Files")
    
    configs = load_environment_configs(environments)
    if not configs:
        misc.print_error("Failed to load environment configurations")
        sys.exit(1)
    
    misc.print_info(f"Loaded configurations for: {', '.join(configs.keys())}")
    
    parameter_data = generate_parameter_file(configs, args.output)
    
    misc.print_success("Parameter file generation complete")
    misc.print_info("Note: This is a template generator. Review and update with actual IDs from Fabric.")


if __name__ == "__main__":
    main()
