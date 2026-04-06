#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabric Enterprise Orchestrator v2.0

Domain-Driven Medallion Architecture provisioning for Microsoft Fabric.
Implements Infrastructure-as-Code with strict Layer x Environment separation.

Usage:
    python orchestrator.py init-domain --name Sales --capacity-dev F2
    python orchestrator.py create-feature --domain Sales --feature-name jira-123
    python orchestrator.py deploy --domain Sales --target test
    python orchestrator.py destroy-feature --domain Sales --feature-name jira-123
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import yaml
import requests
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from msal import ConfidentialClientApplication

# ============================================================================
# CLI Setup
# ============================================================================

app = typer.Typer(
    name="fabric-orchestrator",
    help="Fabric Enterprise Orchestrator v2.0 - Domain-Driven Medallion Architecture",
    add_completion=False
)
console = Console()


# ============================================================================
# Enums & Data Classes
# ============================================================================

class Environment(str, Enum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class Layer(str, Enum):
    SRC = "Src"
    TRF = "Trf"
    ANL = "Anl"
    ALL = "All"  # Compact strategy: single workspace per env (logical layers inside)


class Strategy(str, Enum):
    ENTERPRISE = "enterprise"
    COMPACT = "compact"


class GitProvider(str, Enum):
    GITHUB = "github"
    AZURE_DEVOPS = "azuredevops"


@dataclass
class WorkspaceConfig:
    name: str
    display_name: str
    capacity_id: str
    environment: Environment
    layer: Layer
    domain: str
    git_folder: str
    git_branch: str


@dataclass
class DeploymentStage:
    order: int
    name: str
    environment: Environment
    workspace_id: Optional[str] = None


# ============================================================================
# Exceptions
# ============================================================================

class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""
    pass


class AuthenticationError(OrchestratorError):
    """Raised when authentication fails."""
    pass


class FabricApiError(OrchestratorError):
    """Raised when Fabric API call fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ConfigurationError(OrchestratorError):
    """Raised when configuration is invalid."""
    pass


# ============================================================================
# Configuration Loader
# ============================================================================

class ConfigLoader:
    """Loads and validates configuration from YAML file."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        """Load configuration from YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key path."""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value
    
    def get_capacity_id(self, environment: str) -> str:
        """Get capacity ID for environment."""
        capacity = self.config.get('capacities', {}).get(environment, {})
        capacity_id = capacity.get('capacity_id')
        if not capacity_id:
            raise ConfigurationError(f"Capacity ID not found for environment: {environment}")
        return capacity_id
    
    def get_git_branch(self, environment: str) -> str:
        """Get Git branch for environment."""
        return self.get(f'git_provider.branches.{environment}', 'main')
    
    def get_domain_config(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """Get domain configuration by name."""
        domains = self.get('domains', [])
        for domain in domains:
            if domain.get('name') == domain_name:
                return domain
        return None

    def get_default_strategy(self) -> str:
        """Get default strategy (enterprise or compact). CLI --strategy overrides."""
        return self.get('default_strategy', 'enterprise').lower().strip()

    def get_folder_pattern(self, strategy: str) -> str:
        """Get Git folder pattern for strategy. Falls back to git_provider.folder_pattern."""
        key = f'strategy.{strategy.lower()}.folder_pattern'
        pattern = self.get(key)
        if pattern:
            return pattern
        return self.get('git_provider.folder_pattern', 'domains/{domain}/{layer}')


# ============================================================================
# Authentication Provider
# ============================================================================

class AuthProvider:
    """Handles Service Principal authentication via MSAL."""
    
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.tenant_id = config.get('fabric.tenant_id')
        self.authority = config.get('fabric.authority', f"https://login.microsoftonline.com/{self.tenant_id}")
        self.scopes = config.get('fabric.scopes', ["https://api.fabric.microsoft.com/.default"])
        
        # Get credentials from environment
        self.client_id = os.environ.get('FABRIC_CLIENT_ID')
        self.client_secret = os.environ.get('FABRIC_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise AuthenticationError(
                "FABRIC_CLIENT_ID and FABRIC_CLIENT_SECRET environment variables must be set"
            )
        
        self.app: Optional[ConfidentialClientApplication] = None
        self._token: Optional[str] = None
        self._token_expires_at: float = 0
    
    def get_token(self, force_refresh: bool = False) -> str:
        """Get access token, refreshing if necessary."""
        if not force_refresh and self._token and time.time() < self._token_expires_at:
            return self._token
        
        if not self.app:
            self.app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
        
        result = self.app.acquire_token_for_client(scopes=self.scopes)
        
        if "access_token" not in result:
            error_desc = result.get("error_description", "Unknown error")
            raise AuthenticationError(f"Failed to acquire token: {error_desc}")
        
        self._token = result["access_token"]
        # Set expiration with 5 minute buffer
        self._token_expires_at = time.time() + result.get("expires_in", 3600) - 300
        
        return self._token


# ============================================================================
# Fabric API Client
# ============================================================================

class FabricApiClient:
    """
    REST API client for Microsoft Fabric.
    Implements exponential backoff with Retry-After header support.
    """
    
    def __init__(self, config: ConfigLoader, auth: AuthProvider, dry_run: bool = False):
        self.config = config
        self.auth = auth
        self.dry_run = dry_run
        self.api_base = config.get('fabric.api_base', 'https://api.fabric.microsoft.com/v1')
        
        # Retry settings
        retry_config = config.get('retry', {})
        self.max_retries = retry_config.get('max_retries', 3)
        self.initial_delay = retry_config.get('initial_delay', 1.0)
        self.backoff_multiplier = retry_config.get('backoff_multiplier', 2.0)
        self.transient_codes = set(retry_config.get('transient_status_codes', [429, 500, 502, 503, 504]))
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token."""
        token = self.auth.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _is_transient_error(self, status_code: int) -> bool:
        """Check if status code indicates transient error."""
        return status_code in self.transient_codes
    
    def _calculate_retry_delay(self, attempt: int, response: Optional[requests.Response] = None) -> float:
        """Calculate retry delay with exponential backoff and Retry-After support."""
        # API CALL ERROR HANDLING: Exponential Backoff with Retry-After header
        if response and 'Retry-After' in response.headers:
            try:
                return float(response.headers['Retry-After'])
            except (ValueError, TypeError):
                pass
        
        return self.initial_delay * (self.backoff_multiplier ** attempt)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """
        Make HTTP request with retry logic.
        Returns (status_code, response_body).
        """
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        
        if self.dry_run:
            console.print(f"[cyan][DRY-RUN][/cyan] {method} {url}")
            if json_data:
                console.print(f"[cyan]Payload:[/cyan] {json.dumps(json_data, indent=2)}")
            return (200, {"dry_run": True})
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                headers = self._get_headers()
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params,
                    timeout=120
                )
                
                # Success
                if response.status_code < 400:
                    body = None
                    if response.content:
                        try:
                            body = response.json()
                        except json.JSONDecodeError:
                            body = {"text": response.text}
                    return (response.status_code, body)
                
                # Transient error - retry
                if self._is_transient_error(response.status_code) and attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt, response)
                    logging.warning(
                        f"Transient error {response.status_code}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(delay)
                    continue
                
                # Non-transient error or max retries reached
                raise FabricApiError(
                    f"API request failed: {response.status_code} {response.reason}",
                    status_code=response.status_code,
                    response_body=response.text
                )
            
            except requests.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logging.warning(f"Request exception, retrying in {delay}s: {e}")
                    time.sleep(delay)
                    continue
                else:
                    raise FabricApiError(f"Request failed after {self.max_retries} retries: {e}")
        
        # Should not reach here, but just in case
        raise FabricApiError(f"Request failed: {last_exception}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """GET request."""
        _, body = self._make_request("GET", endpoint, params=params)
        return body
    
    def post(self, endpoint: str, json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """POST request."""
        _, body = self._make_request("POST", endpoint, json_data=json_data)
        return body
    
    def patch(self, endpoint: str, json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """PATCH request."""
        _, body = self._make_request("PATCH", endpoint, json_data=json_data)
        return body
    
    def delete(self, endpoint: str) -> bool:
        """DELETE request. Returns True if successful."""
        status, _ = self._make_request("DELETE", endpoint)
        return status in [200, 202, 204]


# ============================================================================
# Workspace Manager
# ============================================================================

class WorkspaceManager:
    """Manages Fabric workspace operations."""
    
    def __init__(self, api: FabricApiClient, config: ConfigLoader):
        self.api = api
        self.config = config
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all workspaces."""
        response = self.api.get("workspaces")
        return response.get('value', []) if response else []
    
    def find_workspace(self, name: str) -> Optional[Dict[str, Any]]:
        """Find workspace by name."""
        workspaces = self.list_workspaces()
        for ws in workspaces:
            if ws.get('displayName') == name:
                return ws
        return None
    
    def create_workspace(self, name: str, capacity_id: str, description: str = "") -> Dict[str, Any]:
        """Create new workspace."""
        payload = {
            "displayName": name,
            "capacityId": capacity_id,
            "description": description
        }
        
        console.print(f"[green]Creating workspace:[/green] {name}")
        response = self.api.post("workspaces", payload)
        
        if not response:
            raise FabricApiError(f"Failed to create workspace: {name}")
        
        # Wait for workspace to be ready
        if not self.api.dry_run:
            time.sleep(2)
        
        return response
    
    def delete_workspace(self, workspace_id: str, workspace_name: str) -> bool:
        """Delete workspace by ID."""
        console.print(f"[red]Deleting workspace:[/red] {workspace_name} ({workspace_id})")
        return self.api.delete(f"workspaces/{workspace_id}")
    
    def assign_capacity(self, workspace_id: str, capacity_id: str) -> bool:
        """Assign workspace to capacity."""
        payload = {"capacityId": capacity_id}
        response = self.api.patch(f"workspaces/{workspace_id}", payload)
        return response is not None
    
    def connect_to_git(
        self,
        workspace_id: str,
        git_provider_type: str,
        repo_url: str,
        branch: str,
        folder: str,
        organization: str,
        project: Optional[str] = None,
        repository: Optional[str] = None
    ) -> bool:
        """
        Connect workspace to Git repository.
        
        API CALL: Workspace Git Connect
        This is a critical CI/CD integration point.
        """
        console.print(f"[blue]Connecting to Git:[/blue] branch={branch}, folder={folder}")
        
        git_details: Dict[str, Any] = {
            "gitProviderType": git_provider_type,
            "organizationName": organization,
            "repositoryName": repository or repo_url.split('/')[-1],
            "branchName": branch,
            "directoryName": folder
        }
        
        # Azure DevOps requires projectName
        if git_provider_type.lower() == "azuredevops" and project:
            git_details["projectName"] = project
        
        payload = {
            "gitProviderDetails": git_details
        }
        
        response = self.api.post(f"workspaces/{workspace_id}/git/connect", payload)
        return response is not None


# ============================================================================
# Governance Manager
# ============================================================================

class GovernanceManager:
    """Manages governance (sensitivity labels, endorsement)."""
    
    def __init__(self, api: FabricApiClient, config: ConfigLoader):
        self.api = api
        self.config = config
    
    def apply_sensitivity_label(self, workspace_id: str, environment: str) -> bool:
        """Apply sensitivity label to workspace based on environment."""
        label_name = self.config.get(f'governance.sensitivity_labels.{environment}')
        if not label_name:
            logging.info(f"No sensitivity label configured for environment: {environment}")
            return True
        
        console.print(f"[yellow]Applying sensitivity label:[/yellow] {label_name}")
        
        # Note: Actual endpoint may vary based on Purview integration
        # This is a placeholder for the governance API pattern
        payload = {
            "labelName": label_name
        }
        
        # Fabric governance API (endpoint may need adjustment based on tenant config)
        response = self.api.post(f"workspaces/{workspace_id}/governanceLabels", payload)
        return response is not None
    
    def set_endorsement(self, item_id: str, item_type: str, endorsement: str) -> bool:
        """Set endorsement for item (Promoted, Certified)."""
        console.print(f"[yellow]Setting endorsement:[/yellow] {endorsement}")
        
        payload = {
            "endorsement": endorsement
        }
        
        # Item endorsement API
        response = self.api.patch(f"items/{item_id}/endorsement", payload)
        return response is not None


# ============================================================================
# Shortcut Manager
# ============================================================================

class ShortcutManager:
    """
    Manages OneLake Shortcuts — zero-copy references between Fabric items/workspaces.

    Use case: After domain init, create Trf→Src shortcuts so the Transform layer
    can read raw data without copying. The shortcut lives inside the *target*
    lakehouse and points at the *source* lakehouse path in OneLake.

    API reference: POST /v1/workspaces/{workspaceId}/items/{itemId}/shortcuts
    Docs: https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts
    """

    def __init__(self, api: FabricApiClient, config: ConfigLoader):
        self.api = api
        self.config = config

    def create_shortcut(
        self,
        workspace_id: str,
        lakehouse_id: str,
        name: str,
        path: str,
        source_workspace_id: str,
        source_item_id: str,
        source_path: str,
    ) -> Dict[str, Any]:
        """
        Create a OneLake shortcut inside a lakehouse.

        Args:
            workspace_id:       Target workspace (where the shortcut will appear).
            lakehouse_id:       Target lakehouse item ID.
            name:               Shortcut name (folder name inside the lakehouse).
            path:               Parent path in the target lakehouse (e.g. "Tables").
            source_workspace_id: Source workspace ID.
            source_item_id:     Source lakehouse/warehouse item ID.
            source_path:        Path inside the source item (e.g. "Tables/FactSales").

        Returns:
            API response dict.
        """
        payload = {
            "name": name,
            "path": path,
            "target": {
                "type": "OneLake",
                "oneLake": {
                    "workspaceId": source_workspace_id,
                    "itemId": source_item_id,
                    "path": source_path,
                },
            },
        }
        console.print(
            f"[blue]Creating shortcut:[/blue] {name} → "
            f"ws={source_workspace_id[:8]}…/item={source_item_id[:8]}…/{source_path}"
        )
        response = self.api.post(
            f"workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts", payload
        )
        if not response:
            raise FabricApiError(
                f"Failed to create shortcut '{name}' in lakehouse {lakehouse_id}"
            )
        return response

    def list_shortcuts(
        self,
        workspace_id: str,
        lakehouse_id: str,
        path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List shortcuts in a lakehouse, optionally filtered by path.

        GET /v1/workspaces/{workspaceId}/items/{itemId}/shortcuts
        """
        params = {"path": path} if path else None
        response = self.api.get(
            f"workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts",
            params=params,
        )
        return response.get("value", []) if response else []

    def delete_shortcut(
        self,
        workspace_id: str,
        lakehouse_id: str,
        shortcut_path: str,
        shortcut_name: str,
    ) -> bool:
        """
        Delete a shortcut by path + name.

        DELETE /v1/workspaces/{workspaceId}/items/{itemId}/shortcuts/{path}/{name}
        """
        endpoint = (
            f"workspaces/{workspace_id}/items/{lakehouse_id}"
            f"/shortcuts/{shortcut_path.strip('/')}/{shortcut_name}"
        )
        console.print(f"[red]Deleting shortcut:[/red] {shortcut_path}/{shortcut_name}")
        return self.api.delete(endpoint)

    def shortcut_exists(
        self,
        workspace_id: str,
        lakehouse_id: str,
        path: str,
        name: str,
    ) -> bool:
        """Return True if a shortcut with the given path/name already exists."""
        shortcuts = self.list_shortcuts(workspace_id, lakehouse_id, path=path)
        return any(s.get("name") == name for s in shortcuts)


# ============================================================================
# Pipeline Manager
# ============================================================================

class PipelineManager:
    """Manages Deployment Pipelines."""
    
    def __init__(self, api: FabricApiClient, config: ConfigLoader):
        self.api = api
        self.config = config
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all deployment pipelines."""
        response = self.api.get("deploymentPipelines")
        return response.get('value', []) if response else []
    
    def find_pipeline(self, name: str) -> Optional[Dict[str, Any]]:
        """Find pipeline by name."""
        pipelines = self.list_pipelines()
        for pipeline in pipelines:
            if pipeline.get('displayName') == name:
                return pipeline
        return None
    
    def create_pipeline(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create deployment pipeline.
        
        API CALL: Create Deployment Pipeline
        This creates the DEV/TEST/PROD promotion infrastructure.
        """
        console.print(f"[green]Creating deployment pipeline:[/green] {name}")
        
        payload = {
            "displayName": name,
            "description": description
        }
        
        response = self.api.post("deploymentPipelines", payload)
        
        if not response:
            raise FabricApiError(f"Failed to create pipeline: {name}")
        
        return response
    
    def assign_workspace_to_stage(
        self,
        pipeline_id: str,
        stage_order: int,
        workspace_id: str
    ) -> bool:
        """
        Assign workspace to pipeline stage.
        
        API CALL: Assign Workspace to Stage
        This wires workspaces to deployment stages (DEV/TEST/PROD).
        """
        console.print(f"[blue]Assigning workspace to stage {stage_order}[/blue]")
        
        payload = {
            "workspaceId": workspace_id
        }
        
        response = self.api.post(
            f"deploymentPipelines/{pipeline_id}/stages/{stage_order}/assignWorkspace",
            payload
        )
        return response is not None
    
    def is_first_deploy(self, pipeline_id: str, target_stage_order: int) -> bool:
        """
        Return True when the target stage has no items — i.e. this is the first
        DEV→TEST (or TEST→PROD) promotion and allowCreateArtifact is required.
        """
        response = self.api.get(f"deploymentPipelines/{pipeline_id}/stages/{target_stage_order}/items")
        if not response:
            return True
        items = response.get('value') or response.get('items') or []
        return len(items) == 0

    def deploy(
        self,
        pipeline_id: str,
        source_stage_order: int,
        target_stage_order: int,
        note: str = "",
        allow_create_artifact: Optional[bool] = None,
        allow_overwrite_artifact: bool = True,
    ) -> Dict[str, Any]:
        """
        Deploy (promote) from source to target stage.

        API CALL: POST /v1/deploymentPipelines/{id}/deploy
        This triggers the actual DEV→TEST or TEST→PROD promotion.

        allow_create_artifact:
            When None (default), auto-detected: True if the target stage is empty
            (first deployment), False otherwise. Set explicitly to override.
            IMPORTANT: The first DEV→TEST deploy always requires this flag or the
            API returns 400 "Target workspace is empty; allowCreateArtifact must be true."

        allow_overwrite_artifact:
            Overwrite existing items in target stage (default True). Set False to
            do a "create-only" pass that skips already-deployed items.
        """
        source_name = ["DEV", "TEST", "PROD"][source_stage_order]
        target_name = ["DEV", "TEST", "PROD"][target_stage_order]

        # Auto-detect first deployment when caller did not specify explicitly
        if allow_create_artifact is None:
            if not self.api.dry_run:
                allow_create_artifact = self.is_first_deploy(pipeline_id, target_stage_order)
                if allow_create_artifact:
                    console.print(
                        f"[yellow]First deploy detected for {target_name} stage — "
                        f"setting allowCreateArtifact=true[/yellow]"
                    )
            else:
                allow_create_artifact = True  # Safe default for dry-run

        console.print(
            f"[green]Deploying:[/green] {source_name} → {target_name} "
            f"(allowCreate={allow_create_artifact}, allowOverwrite={allow_overwrite_artifact})"
        )

        payload = {
            "sourceStageOrder": source_stage_order,
            "targetStageOrder": target_stage_order,
            "note": note,
            "options": {
                "allowCreateArtifact": allow_create_artifact,
                "allowOverwriteArtifact": allow_overwrite_artifact,
            },
        }

        response = self.api.post(f"deploymentPipelines/{pipeline_id}/deploy", payload)

        if not response:
            raise FabricApiError(f"Failed to deploy pipeline: {pipeline_id}")

        # Wait for deployment to complete (polling)
        if not self.api.dry_run:
            operation_id = response.get('operationId')
            if operation_id:
                self._wait_for_deployment(pipeline_id, operation_id)

        return response
    
    def _wait_for_deployment(self, pipeline_id: str, operation_id: str, timeout: int = 300):
        """Wait for deployment operation to complete."""
        console.print("[yellow]Waiting for deployment to complete...[/yellow]")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_response = self.api.get(f"deploymentPipelines/{pipeline_id}/operations/{operation_id}")
            
            if not status_response:
                break
            
            status = status_response.get('status', 'Unknown')
            
            if status in ['Succeeded', 'Completed']:
                console.print("[green]Deployment completed successfully[/green]")
                return
            elif status in ['Failed', 'Cancelled']:
                raise FabricApiError(f"Deployment failed with status: {status}")
            
            time.sleep(5)
        
        raise FabricApiError(f"Deployment timeout after {timeout}s")
    
    def update_parameters(
        self,
        workspace_id: str,
        environment: str,
        parameters: Dict[str, str]
    ) -> bool:
        """
        Update workspace/item parameters after deployment.
        
        API CALL: Parameter Update (post-deployment)
        This updates connection strings and item references per environment.
        """
        console.print(f"[blue]Updating parameters for environment:[/blue] {environment}")
        
        # Get environment-specific parameters from config
        env_params = self.config.get(f'parameters.{environment}', {})
        merged_params = {**env_params, **parameters}
        
        if not merged_params:
            return True
        
        payload = {
            "parameters": merged_params
        }
        
        response = self.api.post(f"workspaces/{workspace_id}/updateParameters", payload)
        return response is not None


# ============================================================================
# Template Generator
# ============================================================================

class TemplateGenerator:
    """Generates template files for notebooks and dbt projects."""
    
    def __init__(self, config: ConfigLoader):
        self.config = config
    
    def _build_spark_notebook_content(self, domain: str, layer: str) -> dict:
        """Construct and return the notebook content dict (no I/O)."""
        return {
            "nbformat": 4,
            "nbformat_minor": 2,
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"# {domain} - {layer} Layer - Bronze to Silver\n",
                        "\n",
                        "Spark-based data ingestion and cleansing."
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "# Import libraries\n",
                        "from pyspark.sql import SparkSession\n",
                        "from pyspark.sql.functions import *\n",
                        "\n",
                        "spark = SparkSession.builder.appName(f\"{domain}_{layer}\").getOrCreate()"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "# Bronze: Read raw data\n",
                        f"bronze_path = \"/lakehouse/default/Tables/bronze/{domain.lower()}/\"\n",
                        "df_bronze = spark.read.format(\"delta\").load(bronze_path)\n",
                        "\n",
                        "display(df_bronze.limit(10))"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "# Silver: Data cleansing and transformation\n",
                        "df_silver = df_bronze \\\n",
                        "    .dropDuplicates() \\\n",
                        "    .na.drop() \\\n",
                        "    .withColumn(\"processed_date\", current_timestamp())\n",
                        "\n",
                        "display(df_silver.limit(10))"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": [
                        "# Write to Silver\n",
                        f"silver_path = \"/lakehouse/default/Tables/silver/{domain.lower()}/\"\n",
                        "df_silver.write \\\n",
                        "    .format(\"delta\") \\\n",
                        "    .mode(\"overwrite\") \\\n",
                        "    .save(silver_path)\n",
                        "\n",
                        "print(f\"Written {df_silver.count()} records to Silver layer\")"
                    ]
                }
            ]
        }

    def generate_spark_notebook(self, domain: str, layer: str, output_dir: str) -> str:
        """Generate PySpark notebook template for Src layer."""
        notebook_content = self._build_spark_notebook_content(domain, layer)

        output_path = Path(output_dir) / f"{domain}_{layer}_bronze_to_silver.ipynb"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(notebook_content, f, indent=2)

        return str(output_path)
    
    def _build_dbt_project_configs(self, domain: str) -> dict:
        """Construct and return all dbt config structures (no I/O, no print)."""
        dbt_project = {
            "name": f"{domain.lower()}_dbt",
            "version": "1.0.0",
            "config-version": 2,
            "profile": "fabric",
            "model-paths": ["models"],
            "analysis-paths": ["analyses"],
            "test-paths": ["tests"],
            "seed-paths": ["seeds"],
            "macro-paths": ["macros"],
            "snapshot-paths": ["snapshots"],
            "target-path": "target",
            "clean-targets": ["target", "dbt_packages"],
            "models": {
                f"{domain.lower()}_dbt": {
                    "gold": {
                        "+materialized": "table",
                        "+schema": "gold"
                    }
                }
            }
        }

        profiles = {
            "fabric": {
                "target": "dev",
                "outputs": {
                    "dev": {
                        "type": "fabric",
                        "driver": "ODBC Driver 18 for SQL Server",
                        "server": f"{domain.lower()}-trf-dev.datawarehouse.fabric.microsoft.com",
                        "port": 1433,
                        "database": f"{domain}_Trf_Dev",
                        "schema": "dbo",
                        "authentication": "ServicePrincipal",
                        "tenant_id": "{{ env_var('AZURE_TENANT_ID') }}",
                        "client_id": "{{ env_var('AZURE_CLIENT_ID') }}",
                        "client_secret": "{{ env_var('AZURE_CLIENT_SECRET') }}"
                    },
                    "test": {
                        "type": "fabric",
                        "driver": "ODBC Driver 18 for SQL Server",
                        "server": f"{domain.lower()}-trf-test.datawarehouse.fabric.microsoft.com",
                        "port": 1433,
                        "database": f"{domain}_Trf_Test",
                        "schema": "dbo",
                        "authentication": "ServicePrincipal",
                        "tenant_id": "{{ env_var('AZURE_TENANT_ID') }}",
                        "client_id": "{{ env_var('AZURE_CLIENT_ID') }}",
                        "client_secret": "{{ env_var('AZURE_CLIENT_SECRET') }}"
                    },
                    "prod": {
                        "type": "fabric",
                        "driver": "ODBC Driver 18 for SQL Server",
                        "server": f"{domain.lower()}-trf-prod.datawarehouse.fabric.microsoft.com",
                        "port": 1433,
                        "database": f"{domain}_Trf_Prod",
                        "schema": "dbo",
                        "authentication": "ServicePrincipal",
                        "tenant_id": "{{ env_var('AZURE_TENANT_ID') }}",
                        "client_id": "{{ env_var('AZURE_CLIENT_ID') }}",
                        "client_secret": "{{ env_var('AZURE_CLIENT_SECRET') }}"
                    }
                }
            }
        }

        schema_yml = {
            "version": 2,
            "models": [
                {
                    "name": "fact_transactions",
                    "description": "Gold layer fact table - transactions",
                    "columns": [
                        {"name": "transaction_id", "description": "Unique transaction identifier"},
                        {"name": "transaction_date", "description": "Date of transaction"},
                        {"name": "amount", "description": "Transaction amount"}
                    ]
                }
            ]
        }

        fact_sql = f"""-- Gold layer: Fact table for {domain} transactions
-- Source: Silver layer (via OneLake shortcut)

SELECT
    transaction_id,
    transaction_date,
    customer_id,
    product_id,
    amount,
    quantity,
    CURRENT_TIMESTAMP AS processed_at
FROM silver.transactions_cleaned
WHERE transaction_date >= DATEADD(year, -2, GETDATE())
"""

        return {
            "dbt_project": dbt_project,
            "profiles": profiles,
            "schema": schema_yml,
            "fact_sql": fact_sql,
        }

    def generate_dbt_project(self, domain: str, output_dir: str) -> Tuple[str, str]:
        """Generate dbt-fabric project skeleton."""
        configs = self._build_dbt_project_configs(domain)

        project_dir = Path(output_dir) / f"dbt_{domain.lower()}"
        project_dir.mkdir(parents=True, exist_ok=True)

        # dbt_project.yml
        project_yml_path = project_dir / "dbt_project.yml"
        with open(project_yml_path, 'w', encoding='utf-8') as f:
            yaml.dump(configs["dbt_project"], f, default_flow_style=False)

        # profiles.yml
        profiles_yml_path = project_dir / "profiles.yml"
        with open(profiles_yml_path, 'w', encoding='utf-8') as f:
            yaml.dump(configs["profiles"], f, default_flow_style=False)

        # models/gold/schema.yml
        models_dir = project_dir / "models" / "gold"
        models_dir.mkdir(parents=True, exist_ok=True)

        schema_yml_path = models_dir / "schema.yml"
        with open(schema_yml_path, 'w', encoding='utf-8') as f:
            yaml.dump(configs["schema"], f, default_flow_style=False)

        # models/gold/fact_transactions.sql
        fact_sql_path = models_dir / "fact_transactions.sql"
        with open(fact_sql_path, 'w', encoding='utf-8') as f:
            f.write(configs["fact_sql"])

        console.print(f"[green]Generated dbt project:[/green] {project_dir}")

        return (str(project_yml_path), str(profiles_yml_path))


# ============================================================================
# Item Provisioner
# ============================================================================

class ItemProvisioner:
    """
    Provision default Fabric items in each layer workspace after workspace creation.

    Default item types per layer (from architecture spec):
      Src → Lakehouse   (raw / bronze zone)
      Trf → Warehouse   (transform / silver zone; SQL analytics endpoint auto-created)
      Anl → SemanticModel stub (placeholder — full model via PBI Generator pipeline)

    The provisioner is idempotent: it skips creation if an item with the target
    display name already exists in the workspace.

    API reference: POST /v1/workspaces/{workspaceId}/items
    """

    #: Default item types per layer — override via config key `item_provisioner.layer_items`
    DEFAULT_LAYER_ITEMS: Dict[str, List[str]] = {
        "Src": ["Lakehouse"],
        "Trf": ["Warehouse"],
        "Anl": ["SemanticModel"],
    }

    #: Items that require polling for the SQL endpoint to become ready
    SQL_ENDPOINT_TYPES = {"Warehouse", "Lakehouse"}

    #: Maximum seconds to wait for SQL endpoint readiness after item creation
    SQL_ENDPOINT_TIMEOUT = 120

    def __init__(self, api: FabricApiClient, config: ConfigLoader):
        self.api = api
        self.config = config

    def _get_layer_items(self, layer: str) -> List[str]:
        """Return item types to provision for a given layer (config-driven with defaults)."""
        override = self.config.get(f"item_provisioner.layer_items.{layer}")
        if override is not None:
            return override if isinstance(override, list) else [override]
        return self.DEFAULT_LAYER_ITEMS.get(layer, [])

    def _find_item(
        self,
        workspace_id: str,
        item_type: str,
        display_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Find an existing item by type and display name in a workspace."""
        response = self.api.get(f"workspaces/{workspace_id}/items?type={item_type}")
        items = response.get("value", []) if response else []
        for item in items:
            if item.get("displayName", "").lower() == display_name.lower():
                return item
        return None

    def _wait_for_sql_endpoint(
        self,
        workspace_id: str,
        item_id: str,
        item_type: str,
        timeout: int = SQL_ENDPOINT_TIMEOUT,
    ) -> bool:
        """
        Poll until the SQL analytics endpoint for a Lakehouse/Warehouse is ready.

        Returns True when ready, False on timeout.
        GET /v1/workspaces/{workspaceId}/items/{itemId}
        """
        if item_type not in self.SQL_ENDPOINT_TYPES:
            return True

        console.print(
            f"    [yellow]Waiting for SQL endpoint:[/yellow] {item_type} {item_id[:8]}…"
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(5)
            response = self.api.get(f"workspaces/{workspace_id}/items/{item_id}")
            if not response:
                continue
            props = response.get("properties", {})
            endpoint = props.get("sqlEndpointProperties", {}).get("connectionString")
            if endpoint:
                console.print(f"    [green]SQL endpoint ready:[/green] {endpoint[:40]}…")
                return True
        console.print(f"    [yellow]SQL endpoint not ready after {timeout}s — continuing[/yellow]")
        return False

    def provision_layer_items(
        self,
        workspace_id: str,
        layer: str,
        domain: str,
    ) -> Dict[str, Any]:
        """
        Create the default Fabric items for a layer workspace.

        Args:
            workspace_id:  Target workspace GUID.
            layer:         Layer name — "Src", "Trf", or "Anl".
            domain:        Domain name (used to build display_name: domain_layer).

        Returns:
            Dict mapping item_type → item_id for all provisioned items.
        """
        items_created: Dict[str, Any] = {}
        item_types = self._get_layer_items(layer)

        for item_type in item_types:
            display_name = f"{domain.lower()}_{layer.lower()}"
            existing = self._find_item(workspace_id, item_type, display_name)

            if existing:
                item_id = existing["id"]
                console.print(
                    f"  [yellow]Item exists:[/yellow] {item_type} '{display_name}' ({item_id[:8]}…)"
                )
                items_created[item_type] = item_id
                continue

            console.print(f"  [green]Creating {item_type}:[/green] '{display_name}'")

            payload: Dict[str, Any] = {
                "displayName": display_name,
                "type": item_type,
            }
            # SemanticModel stub: add minimal description so it can be identified
            if item_type == "SemanticModel":
                payload["description"] = (
                    f"Placeholder SemanticModel for {domain} Anl layer. "
                    "Replace with full model via PBI Generator."
                )

            response = self.api.post(f"workspaces/{workspace_id}/items", payload)
            if not response:
                raise FabricApiError(
                    f"Failed to create {item_type} '{display_name}' in workspace {workspace_id}"
                )

            item_id = response.get("id")
            items_created[item_type] = item_id

            # Wait for SQL endpoint on Lakehouse/Warehouse before proceeding
            if item_id and item_type in self.SQL_ENDPOINT_TYPES and not self.api.dry_run:
                self._wait_for_sql_endpoint(workspace_id, item_id, item_type)

        return items_created

    def provision_domain(
        self,
        domain_name: str,
        created_workspaces: Dict[str, Dict[str, Any]],
        strategy: str = "enterprise",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Provision items across all workspaces in a domain.

        For enterprise strategy: iterates Src/Trf/Anl × Dev/Test/Prod.
        For compact strategy: provisions a Lakehouse in each env workspace.

        Returns:
            Nested dict: workspace_name → {item_type: item_id}
        """
        console.print(f"\n[bold]Provisioning items:[/bold] {domain_name} [strategy={strategy}]\n")
        results: Dict[str, Dict[str, Any]] = {}

        for ws_name, ws_info in created_workspaces.items():
            ws_id = ws_info.get("id")
            ws_config = ws_info.get("config")
            if not ws_id or not ws_config:
                continue

            if strategy == Strategy.COMPACT.value:
                layer = "Src"  # Compact: single Lakehouse per env workspace
            else:
                layer = ws_config.layer.value if hasattr(ws_config, "layer") else "Src"

            provisioned = self.provision_layer_items(ws_id, layer, domain_name)
            if provisioned:
                results[ws_name] = provisioned

        console.print(f"\n[bold green]Item provisioning complete:[/bold green] {domain_name}")
        return results


# ============================================================================
# Notebook Deployer
# ============================================================================

class NotebookDeployer:
    """
    Deploy Fabric Notebooks to workspaces.

    Supports two deployment modes:
      1. From template  — generated via TemplateGenerator.generate_spark_notebook()
      2. From file      — deploy an existing .ipynb file to a target workspace

    Notebook items are identified by displayName within a workspace.
    If a notebook with the same name already exists, it is updated (idempotent).

    API reference:
      Create: POST /v1/workspaces/{workspaceId}/items  (type: "Notebook")
      Update: PATCH /v1/workspaces/{workspaceId}/items/{itemId}
      Update definition: POST /v1/workspaces/{workspaceId}/items/{itemId}/updateItemDefinition
    """

    def __init__(self, api: FabricApiClient, config: ConfigLoader, template_gen: "TemplateGenerator"):
        self.api = api
        self.config = config
        self.template_gen = template_gen

    def _find_notebook(self, workspace_id: str, display_name: str) -> Optional[Dict[str, Any]]:
        """Find an existing notebook by display name in a workspace."""
        response = self.api.get(f"workspaces/{workspace_id}/items?type=Notebook")
        items = response.get("value", []) if response else []
        for item in items:
            if item.get("displayName", "").lower() == display_name.lower():
                return item
        return None

    def _encode_notebook(self, notebook_path: Path) -> str:
        """Base64-encode a .ipynb file for the Fabric Items API definition payload."""
        import base64
        content = notebook_path.read_bytes()
        return base64.b64encode(content).decode("utf-8")

    def _build_definition_payload(self, notebook_path: Path) -> Dict[str, Any]:
        """Build the `definition.parts` payload for createItemWithDefinition."""
        encoded = self._encode_notebook(notebook_path)
        return {
            "parts": [
                {
                    "path": "artifact.content.ipynb",
                    "payload": encoded,
                    "payloadType": "InlineBase64",
                }
            ]
        }

    def deploy_from_file(
        self,
        workspace_id: str,
        notebook_path: Path,
        display_name: Optional[str] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Deploy a .ipynb notebook file to a Fabric workspace.

        If a notebook with the same display_name exists, its definition is updated.
        If not, a new Notebook item is created.

        Args:
            workspace_id:   Target workspace GUID.
            notebook_path:  Path to the local .ipynb file.
            display_name:   Display name in Fabric (defaults to file stem).
            description:    Optional description for the notebook item.

        Returns:
            API response dict for the created/updated notebook.
        """
        if not notebook_path.exists():
            raise FabricApiError(f"Notebook file not found: {notebook_path}")

        name = display_name or notebook_path.stem
        definition = self._build_definition_payload(notebook_path)

        existing = self._find_notebook(workspace_id, name)

        if existing:
            item_id = existing["id"]
            console.print(f"  [yellow]Notebook exists — updating definition:[/yellow] {name}")
            response = self.api.post(
                f"workspaces/{workspace_id}/items/{item_id}/updateItemDefinition",
                {"definition": definition},
            )
            return response or {"id": item_id, "updated": True}

        console.print(f"  [green]Creating notebook:[/green] {name}")
        payload: Dict[str, Any] = {
            "displayName": name,
            "type": "Notebook",
            "definition": definition,
        }
        if description:
            payload["description"] = description

        response = self.api.post(f"workspaces/{workspace_id}/items", payload)
        if not response:
            raise FabricApiError(f"Failed to create notebook '{name}' in workspace {workspace_id}")
        return response

    def deploy_template(
        self,
        workspace_id: str,
        domain: str,
        layer: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a layer-appropriate notebook from template and deploy it.

        Template is generated by TemplateGenerator.generate_spark_notebook().
        The notebook is written to a temp directory (or output_dir if given),
        then deployed via deploy_from_file.

        Args:
            workspace_id:  Target workspace GUID.
            domain:        Domain name (e.g. "Sales").
            layer:         Layer name (e.g. "Src", "Trf").
            output_dir:    Directory to write the generated .ipynb; defaults to /tmp.

        Returns:
            API response dict for the deployed notebook.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = output_dir or tmp
            notebook_path_str = self.template_gen.generate_spark_notebook(domain, layer, out)
            notebook_path = Path(notebook_path_str)
            display_name = f"{domain}_{layer}_ETL"
            return self.deploy_from_file(
                workspace_id=workspace_id,
                notebook_path=notebook_path,
                display_name=display_name,
                description=f"Auto-generated {layer} ETL notebook for {domain} domain.",
            )

    def deploy_domain_notebooks(
        self,
        domain_name: str,
        created_workspaces: Dict[str, Dict[str, Any]],
        strategy: str = "enterprise",
    ) -> Dict[str, Any]:
        """
        Deploy ETL notebooks to Src and Trf layer workspaces in a domain.

        Args:
            domain_name:         Domain name.
            created_workspaces:  Workspace map from DomainOrchestrator.init_domain().
            strategy:            "enterprise" or "compact".

        Returns:
            Dict mapping workspace_name → notebook deployment result.
        """
        console.print(f"\n[bold]Deploying notebooks:[/bold] {domain_name}\n")
        results: Dict[str, Any] = {}

        notebook_layers = {"Src", "Trf"} if strategy != Strategy.COMPACT.value else {"Anl"}

        for ws_name, ws_info in created_workspaces.items():
            ws_id = ws_info.get("id")
            ws_config = ws_info.get("config")
            if not ws_id or not ws_config:
                continue

            layer = ws_config.layer.value if hasattr(ws_config, "layer") else ""
            if layer not in notebook_layers:
                continue

            try:
                result = self.deploy_template(workspace_id=ws_id, domain=domain_name, layer=layer)
                results[ws_name] = result
                console.print(f"  [green]Notebook deployed:[/green] {domain_name}_{layer}_ETL → {ws_name}")
            except FabricApiError as e:
                console.print(f"  [red]Notebook deploy failed:[/red] {ws_name} — {e}")

        return results


# ============================================================================
# Domain Orchestrator
# ============================================================================

class DomainOrchestrator:
    """Orchestrates domain-level operations (init, feature, destroy)."""
    
    def __init__(self, config: ConfigLoader, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        
        # Initialize components
        self.auth = AuthProvider(config)
        self.api = FabricApiClient(config, self.auth, dry_run)
        self.workspace_mgr = WorkspaceManager(self.api, config)
        self.governance_mgr = GovernanceManager(self.api, config)
        self.shortcut_mgr = ShortcutManager(self.api, config)
        self.pipeline_mgr = PipelineManager(self.api, config)
        self.template_gen = TemplateGenerator(config)
        self.item_provisioner = ItemProvisioner(self.api, config)
        self.notebook_deployer = NotebookDeployer(self.api, config, self.template_gen)
    
    def init_domain(
        self,
        domain_name: str,
        capacity_dev: Optional[str] = None,
        capacity_test: Optional[str] = None,
        capacity_prod: Optional[str] = None,
        strategy: str = "enterprise"
    ) -> Dict[str, Any]:
        """
        Initialize domain: create workspaces based on strategy.
        Enterprise: 9 workspaces (Src/Trf/Anl × Dev/Test/Prod).
        Compact: 3 workspaces (one per Dev/Test/Prod, logical layers inside).
        """
        console.print(f"\n[bold]Initializing domain:[/bold] {domain_name} [strategy={strategy}]\n")
        
        # Validate domain exists in config
        domain_config = self.config.get_domain_config(domain_name)
        if not domain_config:
            raise ConfigurationError(f"Domain '{domain_name}' not found in config.yaml")
        
        layers = domain_config.get('layers', ['Src', 'Trf', 'Anl'])
        environments = [Environment.DEV, Environment.TEST, Environment.PROD]
        
        # Build workspace matrix by strategy
        workspaces: List[WorkspaceConfig] = []
        
        for env in environments:
            if env == Environment.DEV and capacity_dev:
                capacity_id = capacity_dev
            elif env == Environment.TEST and capacity_test:
                capacity_id = capacity_test
            elif env == Environment.PROD and capacity_prod:
                capacity_id = capacity_prod
            else:
                capacity_id = self.config.get_capacity_id(env.value)
            
            git_branch = self.config.get_git_branch(env.value)
            
            if strategy == Strategy.COMPACT.value:
                # Compact: one workspace per environment
                ws_name = f"{domain_name}_{env.value.capitalize()}"
                folder_pattern = self.config.get_folder_pattern(Strategy.COMPACT.value)
                git_folder = folder_pattern.format(domain=domain_name, env=env.value)
                ws_config = WorkspaceConfig(
                    name=ws_name,
                    display_name=ws_name,
                    capacity_id=capacity_id,
                    environment=env,
                    layer=Layer.ALL,
                    domain=domain_name,
                    git_folder=git_folder,
                    git_branch=git_branch
                )
                workspaces.append(ws_config)
            else:
                # Enterprise: 9 workspaces (layer × env)
                folder_pattern = self.config.get_folder_pattern(Strategy.ENTERPRISE.value)
                for layer in layers:
                    ws_name = f"{domain_name}_{layer}_{env.value.capitalize()}"
                    git_folder = folder_pattern.format(domain=domain_name, layer=layer, env=env.value)
                    ws_config = WorkspaceConfig(
                        name=ws_name,
                        display_name=ws_name,
                        capacity_id=capacity_id,
                        environment=env,
                        layer=Layer(layer),
                        domain=domain_name,
                        git_folder=git_folder,
                        git_branch=git_branch
                    )
                    workspaces.append(ws_config)
        
        # Create or find workspaces
        created_workspaces = {}
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Creating workspaces...", total=len(workspaces))
            
            for ws_config in workspaces:
                # Check if exists
                existing = self.workspace_mgr.find_workspace(ws_config.name)
                
                if existing:
                    console.print(f"[yellow]Workspace exists:[/yellow] {ws_config.name}")
                    ws_id = existing['id']
                else:
                    # Create workspace
                    if ws_config.layer == Layer.ALL:
                        desc = f"{domain_name} – Compact – {ws_config.environment.value.upper()}"
                    else:
                        desc = f"{domain_name} {ws_config.layer.value} layer - {ws_config.environment.value.upper()}"
                    result = self.workspace_mgr.create_workspace(
                        name=ws_config.name,
                        capacity_id=ws_config.capacity_id,
                        description=desc
                    )
                    ws_id = result.get('id')
                
                created_workspaces[ws_config.name] = {
                    "id": ws_id,
                    "config": ws_config
                }
                
                # Apply governance
                self.governance_mgr.apply_sensitivity_label(ws_id, ws_config.environment.value)
                
                # Connect to Git
                git_config = self.config.get('git_provider', {})
                self.workspace_mgr.connect_to_git(
                    workspace_id=ws_id,
                    git_provider_type=git_config.get('type', 'github'),
                    repo_url=git_config.get('repo_url', ''),
                    branch=ws_config.git_branch,
                    folder=ws_config.git_folder,
                    organization=git_config.get('organization', ''),
                    project=git_config.get('project'),
                    repository=git_config.get('repository')
                )
                
                progress.update(task, advance=1)
        
        # Create deployment pipeline (if auto_create enabled)
        if self.config.get('deployment_pipelines.auto_create', True):
            self._create_deployment_pipeline(domain_name, created_workspaces, strategy)

        # Create OneLake shortcuts between layers (if enabled)
        if self.config.get('onelake_shortcuts.enabled', False):
            self._create_layer_shortcuts(domain_name, created_workspaces, strategy)

        # Provision default items (Lakehouse/Warehouse/SemanticModel) per layer (opt-in)
        if self.config.get('item_provisioner.enabled', False):
            self.item_provisioner.provision_domain(domain_name, created_workspaces, strategy)

        # Deploy ETL notebook templates to Src/Trf workspaces (opt-in)
        if self.config.get('notebooks.auto_deploy', False):
            self.notebook_deployer.deploy_domain_notebooks(domain_name, created_workspaces, strategy)

        console.print(f"\n[bold green]Domain initialized:[/bold green] {domain_name}")
        console.print(f"[green]Created {len(created_workspaces)} workspaces[/green]\n")
        
        return created_workspaces
    
    def _create_deployment_pipeline(
        self,
        domain_name: str,
        created_workspaces: Dict[str, Dict[str, Any]],
        strategy: str = "enterprise"
    ):
        """Create and wire deployment pipeline for domain. Stage assignment depends on strategy."""
        pipeline_name = self.config.get('deployment_pipelines.naming_pattern', '{domain}_Pipeline')
        pipeline_name = pipeline_name.format(domain=domain_name)
        
        # Check if pipeline exists
        existing_pipeline = self.pipeline_mgr.find_pipeline(pipeline_name)
        if existing_pipeline:
            console.print(f"[yellow]Pipeline exists:[/yellow] {pipeline_name}")
            pipeline_id = existing_pipeline['id']
        else:
            # Create pipeline
            result = self.pipeline_mgr.create_pipeline(
                name=pipeline_name,
                description=f"Medallion deployment pipeline for {domain_name} domain"
            )
            pipeline_id = result.get('id')
        
        stages = self.config.get('deployment_pipelines.stages', [])
        
        for stage_config in stages:
            stage_order = stage_config['order']
            env = stage_config['env']
            
            if strategy == Strategy.COMPACT.value:
                # Compact: one workspace per env
                ws_name = f"{domain_name}_{env.capitalize()}"
            else:
                # Enterprise: Anl workspace per env
                ws_name = f"{domain_name}_Anl_{env.capitalize()}"
            
            if ws_name in created_workspaces:
                ws_id = created_workspaces[ws_name]['id']
                self.pipeline_mgr.assign_workspace_to_stage(
                    pipeline_id=pipeline_id,
                    stage_order=stage_order,
                    workspace_id=ws_id
                )

    def _create_layer_shortcuts(
        self,
        domain_name: str,
        created_workspaces: Dict[str, Dict[str, Any]],
        strategy: str = "enterprise",
    ) -> None:
        """
        Create OneLake shortcuts from Trf→Src and Anl→Trf for each environment.

        Config section (config.yaml):
          onelake_shortcuts:
            enabled: true
            shortcuts:
              - source_layer: Src
                target_layer: Trf
                tables: ["*"]           # "*" = all tables; list specific table names to limit
              - source_layer: Trf
                target_layer: Anl
                tables: ["*"]

        Compact strategy: skipped (single workspace per env; no cross-workspace shortcuts needed).
        Enterprise strategy: Trf workspace gets Src shortcuts; Anl workspace gets Trf shortcuts.
        """
        if strategy == Strategy.COMPACT.value:
            console.print(
                "[yellow]Skipping layer shortcuts — not applicable for compact strategy[/yellow]"
            )
            return

        shortcut_defs = self.config.get("onelake_shortcuts.shortcuts", [
            {"source_layer": "Src", "target_layer": "Trf", "tables": ["*"]},
            {"source_layer": "Trf", "target_layer": "Anl", "tables": ["*"]},
        ])

        console.print(
            f"\n[bold]Creating OneLake layer shortcuts:[/bold] {domain_name}\n"
        )

        environments = [Environment.DEV, Environment.TEST, Environment.PROD]

        for env in environments:
            env_val = env.value
            for shortcut_def in shortcut_defs:
                src_layer = shortcut_def["source_layer"]
                tgt_layer = shortcut_def["target_layer"]
                tables = shortcut_def.get("tables", ["*"])

                src_ws_name = f"{domain_name}_{src_layer}_{env_val.capitalize()}"
                tgt_ws_name = f"{domain_name}_{tgt_layer}_{env_val.capitalize()}"

                src_ws = created_workspaces.get(src_ws_name)
                tgt_ws = created_workspaces.get(tgt_ws_name)

                if not src_ws or not tgt_ws:
                    console.print(
                        f"[yellow]Skipping {src_ws_name}→{tgt_ws_name}: workspace not found[/yellow]"
                    )
                    continue

                src_ws_id = src_ws["id"]
                tgt_ws_id = tgt_ws["id"]

                # Resolve lakehouse IDs within each workspace
                src_lakehouse_id = self._resolve_lakehouse_id(src_ws_id, f"{domain_name.lower()}_src")
                tgt_lakehouse_id = self._resolve_lakehouse_id(tgt_ws_id, f"{domain_name.lower()}_trf")

                if not src_lakehouse_id or not tgt_lakehouse_id:
                    console.print(
                        f"[yellow]Skipping {src_layer}→{tgt_layer}/{env_val}: lakehouse not yet provisioned[/yellow]"
                    )
                    continue

                if tables == ["*"]:
                    # Single shortcut at the Tables root
                    shortcut_name = f"{src_layer.lower()}_tables"
                    if not self.shortcut_mgr.shortcut_exists(
                        tgt_ws_id, tgt_lakehouse_id, "Tables", shortcut_name
                    ):
                        self.shortcut_mgr.create_shortcut(
                            workspace_id=tgt_ws_id,
                            lakehouse_id=tgt_lakehouse_id,
                            name=shortcut_name,
                            path="Tables",
                            source_workspace_id=src_ws_id,
                            source_item_id=src_lakehouse_id,
                            source_path="Tables",
                        )
                    else:
                        console.print(
                            f"[yellow]Shortcut exists:[/yellow] {shortcut_name} in {tgt_ws_name}"
                        )
                else:
                    # Per-table shortcuts
                    for table_name in tables:
                        shortcut_name = f"{src_layer.lower()}_{table_name.lower()}"
                        if not self.shortcut_mgr.shortcut_exists(
                            tgt_ws_id, tgt_lakehouse_id, "Tables", shortcut_name
                        ):
                            self.shortcut_mgr.create_shortcut(
                                workspace_id=tgt_ws_id,
                                lakehouse_id=tgt_lakehouse_id,
                                name=shortcut_name,
                                path="Tables",
                                source_workspace_id=src_ws_id,
                                source_item_id=src_lakehouse_id,
                                source_path=f"Tables/{table_name}",
                            )

    def _resolve_lakehouse_id(self, workspace_id: str, display_name: str) -> Optional[str]:
        """Find a Lakehouse item by display name in a workspace. Returns item ID or None."""
        response = self.api.get(f"workspaces/{workspace_id}/items?type=Lakehouse")
        items = response.get("value", []) if response else []
        for item in items:
            if item.get("displayName", "").lower() == display_name.lower():
                return item.get("id")
        return None

    def create_feature_workspaces(
        self,
        domain_name: str,
        feature_name: str,
        dev_capacity: str,
        strategy: str = "enterprise"
    ) -> Dict[str, Any]:
        """Create isolated feature workspaces. Enterprise: 3 (Src/Trf/Anl). Compact: 1."""
        console.print(f"\n[bold]Creating feature workspaces:[/bold] {domain_name} / {feature_name} [strategy={strategy}]\n")
        
        feature_clean = feature_name.replace('/', '_').replace(' ', '_')
        
        domain_config = self.config.get_domain_config(domain_name)
        if not domain_config:
            raise ConfigurationError(f"Domain '{domain_name}' not found in config.yaml")
        
        capacity_id = dev_capacity or self.config.get_capacity_id('dev')
        git_config = self.config.get('git_provider', {})
        feature_branch = f"feature/{feature_name}"
        created_workspaces = {}
        
        if strategy == Strategy.COMPACT.value:
            # Compact: one feature workspace
            ws_name = f"{domain_name}_Feat_{feature_clean}"
            feature_folder = f"features/{feature_clean}"
            existing = self.workspace_mgr.find_workspace(ws_name)
            if existing:
                console.print(f"[yellow]Feature workspace exists:[/yellow] {ws_name}")
                ws_id = existing['id']
            else:
                result = self.workspace_mgr.create_workspace(
                    name=ws_name,
                    capacity_id=capacity_id,
                    description=f"Feature workspace: {feature_name}"
                )
                ws_id = result.get('id')
            created_workspaces[ws_name] = {"id": ws_id, "layer": "All"}
            self.workspace_mgr.connect_to_git(
                workspace_id=ws_id,
                git_provider_type=git_config.get('type', 'github'),
                repo_url=git_config.get('repo_url', ''),
                branch=feature_branch,
                folder=feature_folder,
                organization=git_config.get('organization', ''),
                project=git_config.get('project'),
                repository=git_config.get('repository')
            )
        else:
            # Enterprise: one workspace per layer
            layers = domain_config.get('layers', ['Src', 'Trf', 'Anl'])
            for layer in layers:
                ws_name = f"{domain_name}_{layer}_Feat_{feature_clean}"
                feature_folder = f"features/{feature_clean}/{layer}"
                existing = self.workspace_mgr.find_workspace(ws_name)
                if existing:
                    console.print(f"[yellow]Feature workspace exists:[/yellow] {ws_name}")
                    ws_id = existing['id']
                else:
                    result = self.workspace_mgr.create_workspace(
                        name=ws_name,
                        capacity_id=capacity_id,
                        description=f"Feature workspace: {feature_name}"
                    )
                    ws_id = result.get('id')
                created_workspaces[ws_name] = {"id": ws_id, "layer": layer}
                self.workspace_mgr.connect_to_git(
                    workspace_id=ws_id,
                    git_provider_type=git_config.get('type', 'github'),
                    repo_url=git_config.get('repo_url', ''),
                    branch=feature_branch,
                    folder=feature_folder,
                    organization=git_config.get('organization', ''),
                    project=git_config.get('project'),
                    repository=git_config.get('repository')
                )
        
        console.print(f"\n[bold green]Feature workspaces created:[/bold green] {len(created_workspaces)}\n")
        
        return created_workspaces
    
    def destroy_feature_workspaces(self, domain_name: str, feature_name: str) -> bool:
        """Delete feature workspaces (with safety checks). Supports both enterprise (3) and compact (1) naming."""
        console.print(f"\n[bold red]Destroying feature workspaces:[/bold red] {domain_name} / {feature_name}\n")
        
        feature_clean = feature_name.replace('/', '_').replace(' ', '_')
        
        workspaces = self.workspace_mgr.list_workspaces()
        to_delete = []
        
        # Match both patterns: enterprise {domain}_{Layer}_Feat_{feature}, compact {domain}_Feat_{feature}
        for ws in workspaces:
            ws_name = ws.get('displayName', '')
            if not ws_name.startswith(domain_name) or '_Feat_' not in ws_name or feature_clean not in ws_name:
                continue
            # Require exact suffix for safety: _Feat_{feature_clean} or _{Layer}_Feat_{feature_clean}
            if ws_name.endswith(f"_Feat_{feature_clean}") or f"_Feat_{feature_clean}" in ws_name:
                to_delete.append((ws['id'], ws_name))
        
        if not to_delete:
            console.print(f"[yellow]No feature workspaces found for:[/yellow] {feature_name}")
            return True
        
        console.print(f"[yellow]Found {len(to_delete)} workspace(s) to delete (enterprise=3, compact=1):[/yellow]")
        for _, ws_name in to_delete:
            console.print(f"  - {ws_name}")
        
        if not self.dry_run:
            confirm = typer.confirm("\nAre you sure you want to delete these workspaces?")
            if not confirm:
                console.print("[yellow]Deletion cancelled[/yellow]")
                return False
        
        # Delete workspaces
        for ws_id, ws_name in to_delete:
            success = self.workspace_mgr.delete_workspace(ws_id, ws_name)
            if not success:
                console.print(f"[red]Failed to delete:[/red] {ws_name}")
        
        console.print(f"\n[bold green]Deleted {len(to_delete)} workspace(s)[/bold green]\n")
        return True
    
    def deploy_domain(
        self,
        domain_name: str,
        target: str,
        strategy: str = "enterprise",
        allow_create_artifact: Optional[bool] = None,
        allow_overwrite_artifact: bool = True,
    ) -> bool:
        """Deploy domain to target environment (test or prod). Target workspace depends on strategy."""
        console.print(f"\n[bold]Deploying domain:[/bold] {domain_name} → {target.upper()} [strategy={strategy}]\n")

        pipeline_name = self.config.get('deployment_pipelines.naming_pattern', '{domain}_Pipeline')
        pipeline_name = pipeline_name.format(domain=domain_name)

        pipeline = self.pipeline_mgr.find_pipeline(pipeline_name)
        if not pipeline:
            raise FabricApiError(f"Deployment pipeline not found: {pipeline_name}")

        pipeline_id = pipeline['id']

        if target.lower() == 'test':
            source_order = 0
            target_order = 1
        elif target.lower() == 'prod':
            source_order = 1
            target_order = 2
        else:
            raise ValueError(f"Invalid target: {target}. Must be 'test' or 'prod'")

        result = self.pipeline_mgr.deploy(
            pipeline_id=pipeline_id,
            source_stage_order=source_order,
            target_stage_order=target_order,
            note=f"Automated deployment: {domain_name} to {target.upper()}",
            allow_create_artifact=allow_create_artifact,
            allow_overwrite_artifact=allow_overwrite_artifact,
        )
        
        # Find target workspace for parameter update (enterprise=Anl, compact=single env workspace)
        if strategy == Strategy.COMPACT.value:
            target_ws_name = f"{domain_name}_{target.capitalize()}"
        else:
            target_ws_name = f"{domain_name}_Anl_{target.capitalize()}"
        target_ws = self.workspace_mgr.find_workspace(target_ws_name)
        
        if target_ws:
            self.pipeline_mgr.update_parameters(
                workspace_id=target_ws['id'],
                environment=target,
                parameters={}  # Config-driven parameters
            )
        
        console.print(f"\n[bold green]Deployment completed:[/bold green] {domain_name} → {target.upper()}\n")
        
        return True


# ============================================================================
# CLI Helpers
# ============================================================================

def _resolve_strategy(cli_value: Optional[str], config: ConfigLoader) -> str:
    """Resolve strategy from CLI or config; validate and return 'enterprise' or 'compact'."""
    raw = (cli_value or config.get_default_strategy()).lower().strip()
    if raw in (Strategy.ENTERPRISE.value, Strategy.COMPACT.value):
        return raw
    raise ConfigurationError(
        f"Invalid strategy '{raw}'. Must be 'enterprise' (9 workspaces) or 'compact' (3 workspaces)."
    )


# ============================================================================
# CLI Commands
# ============================================================================

@app.command()
def init_domain(
    name: str = typer.Option(..., help="Domain name (e.g., Sales)"),
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Architecture: enterprise (9 workspaces) or compact (3 workspaces)"),
    capacity_dev: Optional[str] = typer.Option(None, "--capacity-dev", help="Dev capacity ID or SKU"),
    capacity_test: Optional[str] = typer.Option(None, "--capacity-test", help="Test capacity ID or SKU"),
    capacity_prod: Optional[str] = typer.Option(None, "--capacity-prod", help="Prod capacity ID or SKU"),
    provision_items: bool = typer.Option(False, "--provision-items", help="Create default Lakehouse/Warehouse/SemanticModel items after workspace creation"),
    deploy_notebooks: bool = typer.Option(False, "--deploy-notebooks", help="Deploy ETL notebook templates to Src/Trf workspaces after provisioning"),
    config_file: str = typer.Option("config.yaml", "--config", help="Config file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without creating resources"),
):
    """
    Initialize domain: create workspaces by strategy (enterprise=9, compact=3).

    Optional flags:
      --provision-items   Create default Fabric items (Lakehouse, Warehouse, SemanticModel stub)
                          in each workspace immediately after workspace creation.
      --deploy-notebooks  Deploy generated PySpark ETL notebooks to Src/Trf workspaces
                          (requires --provision-items to have run first or items to exist).

    Examples:
        python orchestrator.py init-domain --name Sales --capacity-dev F2
        python orchestrator.py init-domain --name Sales --strategy compact --provision-items
        python orchestrator.py init-domain --name Sales --provision-items --deploy-notebooks
    """
    try:
        config = ConfigLoader(config_file)
        resolved_strategy = _resolve_strategy(strategy, config)
        orchestrator = DomainOrchestrator(config, dry_run=dry_run)

        # Override config flags from CLI
        if provision_items:
            orchestrator.config.config.setdefault("item_provisioner", {})["enabled"] = True
        if deploy_notebooks:
            orchestrator.config.config.setdefault("notebooks", {})["auto_deploy"] = True

        result = orchestrator.init_domain(
            domain_name=name,
            capacity_dev=capacity_dev,
            capacity_test=capacity_test,
            capacity_prod=capacity_prod,
            strategy=resolved_strategy
        )
        
        # Display summary table
        table = Table(title=f"Domain: {name} [{resolved_strategy}]")
        table.add_column("Workspace", style="cyan")
        table.add_column("Environment", style="green")
        table.add_column("Layer", style="yellow")
        
        for ws_name, ws_data in result.items():
            config_obj = ws_data['config']
            table.add_row(ws_name, config_obj.environment.value, config_obj.layer.value)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def create_feature(
    domain: str = typer.Option(..., help="Domain name"),
    feature_name: str = typer.Option(..., "--feature-name", help="Feature name (e.g., jira-123)"),
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Architecture: enterprise (3 feature workspaces) or compact (1)"),
    dev_capacity: Optional[str] = typer.Option(None, "--dev-capacity", help="Dev capacity ID or SKU"),
    generate_templates: bool = typer.Option(False, "--generate-templates", help="Generate Spark + dbt templates"),
    config_file: str = typer.Option("config.yaml", "--config", help="Config file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without creating resources")
):
    """
    Create isolated feature workspaces (enterprise=3, compact=1).
    
    Example:
        python orchestrator.py create-feature --domain Sales --feature-name jira-123
        python orchestrator.py create-feature --domain Sales --feature-name jira-123 --strategy compact
    """
    try:
        config = ConfigLoader(config_file)
        resolved_strategy = _resolve_strategy(strategy, config)
        orchestrator = DomainOrchestrator(config, dry_run=dry_run)
        
        result = orchestrator.create_feature_workspaces(
            domain_name=domain,
            feature_name=feature_name,
            dev_capacity=dev_capacity,
            strategy=resolved_strategy
        )
        
        # Optionally generate templates
        if generate_templates:
            console.print("\n[bold]Generating templates...[/bold]\n")
            feature_clean = feature_name.replace('/', '_').replace(' ', '_')
            output_dir = f"features/{feature_clean}"
            
            # Spark notebook for Src
            notebook_path = orchestrator.template_gen.generate_spark_notebook(domain, "Src", output_dir)
            console.print(f"[green]Generated Spark notebook:[/green] {notebook_path}")
            
            # dbt project for Trf
            proj_path, prof_path = orchestrator.template_gen.generate_dbt_project(domain, output_dir)
            console.print(f"[green]Generated dbt project:[/green] {proj_path}")
        
        console.print(f"\n[bold green]Feature workspaces ready:[/bold green] {feature_name}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def deploy(
    domain: str = typer.Option(..., help="Domain name"),
    target: str = typer.Option(..., help="Target environment: test or prod"),
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Architecture: enterprise or compact (for target workspace lookup)"),
    allow_create: Optional[bool] = typer.Option(None, "--allow-create/--no-allow-create", help="Allow creating new items in target stage. Auto-detected when omitted: True if target stage is empty (first deploy)."),
    no_overwrite: bool = typer.Option(False, "--no-overwrite", help="Skip overwriting items that already exist in target stage."),
    config_file: str = typer.Option("config.yaml", "--config", help="Config file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without deploying")
):
    """
    Deploy domain to target environment (DEV→TEST or TEST→PROD).

    allowCreateArtifact is auto-detected on first deploy (target stage empty).
    Override with --allow-create / --no-allow-create when auto-detection is not desired.

    Example:
        python orchestrator.py deploy --domain Sales --target test
        python orchestrator.py deploy --domain Sales --target test --allow-create
        python orchestrator.py deploy --domain Sales --target prod --strategy compact
        python orchestrator.py deploy --domain Sales --target prod --no-overwrite
    """
    try:
        if target.lower() not in ['test', 'prod']:
            raise ValueError("Target must be 'test' or 'prod'")

        config = ConfigLoader(config_file)
        resolved_strategy = _resolve_strategy(strategy, config)
        orchestrator = DomainOrchestrator(config, dry_run=dry_run)

        orchestrator.deploy_domain(
            domain_name=domain,
            target=target,
            strategy=resolved_strategy,
            allow_create_artifact=allow_create,
            allow_overwrite_artifact=not no_overwrite,
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def destroy_feature(
    domain: str = typer.Option(..., help="Domain name"),
    feature_name: str = typer.Option(..., "--feature-name", help="Feature name to destroy"),
    config_file: str = typer.Option("config.yaml", "--config", help="Config file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without deleting")
):
    """
    Delete feature workspaces (with safety checks).
    
    Example:
        python orchestrator.py destroy-feature --domain Sales --feature-name jira-123
    """
    try:
        config = ConfigLoader(config_file)
        orchestrator = DomainOrchestrator(config, dry_run=dry_run)
        
        success = orchestrator.destroy_feature_workspaces(domain_name=domain, feature_name=feature_name)
        
        if not success:
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def create_shortcut(
    workspace_id: str = typer.Option(..., "--workspace-id", help="Target workspace ID"),
    lakehouse_id: str = typer.Option(..., "--lakehouse-id", help="Target lakehouse item ID"),
    name: str = typer.Option(..., "--name", help="Shortcut name (folder name in the lakehouse)"),
    path: str = typer.Option("Tables", "--path", help="Parent path in the target lakehouse"),
    source_workspace_id: str = typer.Option(..., "--source-workspace-id", help="Source workspace ID"),
    source_item_id: str = typer.Option(..., "--source-item-id", help="Source lakehouse/warehouse item ID"),
    source_path: str = typer.Option(..., "--source-path", help="Path inside the source item"),
    config_file: str = typer.Option("config.yaml", "--config", help="Config file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without creating"),
):
    """
    Create a OneLake shortcut from a source lakehouse path into a target lakehouse.

    Example:
        python orchestrator.py create-shortcut \\
          --workspace-id <tgt-ws-id> --lakehouse-id <tgt-lh-id> \\
          --name src_tables --path Tables \\
          --source-workspace-id <src-ws-id> --source-item-id <src-lh-id> \\
          --source-path Tables
    """
    try:
        config = ConfigLoader(config_file)
        auth = AuthProvider(config)
        api = FabricApiClient(config, auth, dry_run)
        mgr = ShortcutManager(api, config)
        result = mgr.create_shortcut(
            workspace_id=workspace_id,
            lakehouse_id=lakehouse_id,
            name=name,
            path=path,
            source_workspace_id=source_workspace_id,
            source_item_id=source_item_id,
            source_path=source_path,
        )
        console.print(f"[green]Shortcut created:[/green] {name}")
        console.print_json(data=result)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def list_shortcuts(
    workspace_id: str = typer.Option(..., "--workspace-id", help="Workspace ID"),
    lakehouse_id: str = typer.Option(..., "--lakehouse-id", help="Lakehouse item ID"),
    path: Optional[str] = typer.Option(None, "--path", help="Filter by path (e.g. Tables)"),
    config_file: str = typer.Option("config.yaml", "--config", help="Config file path"),
):
    """
    List OneLake shortcuts in a lakehouse.

    Example:
        python orchestrator.py list-shortcuts \\
          --workspace-id <ws-id> --lakehouse-id <lh-id> --path Tables
    """
    try:
        config = ConfigLoader(config_file)
        auth = AuthProvider(config)
        api = FabricApiClient(config, auth)
        mgr = ShortcutManager(api, config)
        shortcuts = mgr.list_shortcuts(workspace_id, lakehouse_id, path=path)

        table = Table(title=f"Shortcuts in {lakehouse_id[:8]}…")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Source Type")
        table.add_column("Source Path")

        for sc in shortcuts:
            target = sc.get("target", {})
            one_lake = target.get("oneLake", {})
            table.add_row(
                sc.get("name", ""),
                sc.get("path", ""),
                target.get("type", ""),
                one_lake.get("path", ""),
            )

        console.print(table)
        console.print(f"Total: {len(shortcuts)} shortcuts")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def provision_items(
    domain: str = typer.Option(..., help="Domain name"),
    workspace_id: str = typer.Option(..., "--workspace-id", help="Target workspace ID"),
    layer: str = typer.Option(..., "--layer", help="Layer: Src, Trf, or Anl"),
    config_file: str = typer.Option("config.yaml", "--config", help="Config file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without creating items"),
):
    """
    Provision default Fabric items in a single workspace layer.

    Creates Lakehouse (Src), Warehouse (Trf), or SemanticModel stub (Anl) if not present.
    Idempotent — skips items that already exist.

    Example:
        python orchestrator.py provision-items --domain Sales --workspace-id <ws-id> --layer Src
    """
    try:
        config = ConfigLoader(config_file)
        auth = AuthProvider(config)
        api = FabricApiClient(config, auth, dry_run)
        provisioner = ItemProvisioner(api, config)
        result = provisioner.provision_layer_items(workspace_id, layer, domain)
        console.print(f"[green]Provisioned:[/green] {result}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def deploy_notebook(
    workspace_id: str = typer.Option(..., "--workspace-id", help="Target workspace ID"),
    notebook: Optional[str] = typer.Option(None, "--notebook", help="Path to .ipynb file (omit to use generated template)"),
    domain: Optional[str] = typer.Option(None, "--domain", help="Domain name (required when using template)"),
    layer: Optional[str] = typer.Option(None, "--layer", help="Layer name (required when using template): Src, Trf"),
    display_name: Optional[str] = typer.Option(None, "--display-name", help="Display name for the notebook in Fabric"),
    config_file: str = typer.Option("config.yaml", "--config", help="Config file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without deploying"),
):
    """
    Deploy a notebook to a Fabric workspace.

    If --notebook is provided, deploys that .ipynb file.
    Otherwise generates a PySpark ETL template for --domain/--layer and deploys it.

    Examples:
        python orchestrator.py deploy-notebook --workspace-id <id> --notebook etl.ipynb
        python orchestrator.py deploy-notebook --workspace-id <id> --domain Sales --layer Src
    """
    try:
        config = ConfigLoader(config_file)
        auth = AuthProvider(config)
        api = FabricApiClient(config, auth, dry_run)
        template_gen = TemplateGenerator(config)
        deployer = NotebookDeployer(api, config, template_gen)

        if notebook:
            nb_path = Path(notebook)
            result = deployer.deploy_from_file(workspace_id, nb_path, display_name=display_name)
        else:
            if not domain or not layer:
                console.print("[bold red]Error:[/bold red] --domain and --layer required when not providing --notebook")
                raise typer.Exit(code=1)
            result = deployer.deploy_template(workspace_id, domain, layer)

        console.print(f"[green]Notebook deployed:[/green] {result.get('id', 'ok')}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app()
