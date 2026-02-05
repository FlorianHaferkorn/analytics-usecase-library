"""
Fabric CLI wrapper functions for workspace and connection management.
Provides high-level functions that abstract Fabric CLI commands.
"""
import subprocess
import json
import time
import uuid
from typing import Optional, Dict, Any, List

from . import retry_logic

EXIT_ON_ERROR = False

# Retry settings for Fabric CLI commands (transient failures)
DEFAULT_RETRY_MAX = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_RETRY_BACKOFF = 2.0


def _run_command_impl(command: str) -> str:
    """Internal: run Fabric CLI command and return stdout. Raises CalledProcessError on failure."""
    result = subprocess.run(
        ["fab", "-c", command],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    output = result.stdout.strip()
    filtered_lines = [
        line for line in output.splitlines()
        if not line.strip().startswith("!") and not line.strip().startswith("'")
    ]
    return "\n".join(filtered_lines)


@retry_logic.retry(
    max_retries=DEFAULT_RETRY_MAX,
    initial_delay=DEFAULT_RETRY_DELAY,
    backoff_multiplier=DEFAULT_RETRY_BACKOFF,
    retryable_exceptions=(subprocess.CalledProcessError, TimeoutError, ConnectionError, OSError),
    retry_condition=lambda e, _: retry_logic.is_transient_failure(
        e, getattr(e, "stderr", "") or getattr(e, "output", "") or str(e)
    ),
)
def _run_command_with_retry(command: str) -> str:
    """Run Fabric CLI command with retry on transient failures."""
    return _run_command_impl(command)


def is_guid(value: str) -> bool:
    """Check if string is a valid GUID."""
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj) == value.lower()
    except (ValueError, AttributeError, TypeError):
        return False


def run_command(command: str, use_retry: bool = True) -> str:
    """
    Run Fabric CLI command.

    Uses retry logic for transient failures when use_retry=True (default).

    Args:
        command: Fabric CLI command (without 'fab -c' prefix)
        use_retry: If True, retry on transient failures (default True)

    Returns:
        Command output (stdout) or error message (stderr)
    """
    try:
        if use_retry:
            return _run_command_with_retry(command)
        return _run_command_impl(command)
    except subprocess.CalledProcessError as e:
        err_msg = (e.stderr or e.stdout or str(e)).strip()
        print(f"Error running Fabric CLI command: {command}")
        print(f"Error message: {err_msg}")
        if EXIT_ON_ERROR:
            raise
        return err_msg
    except (TimeoutError, ConnectionError, OSError) as e:
        print(f"Error running Fabric CLI command: {command}")
        print(f"Error message: {e}")
        if EXIT_ON_ERROR:
            raise
        return str(e)


def get_item(item_path: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Get Fabric item by path.
    
    Args:
        item_path: Item path (e.g., 'MyWorkspace.Workspace')
        retry_count: Number of retries on failure
    
    Returns:
        Item JSON or None if not found
    """
    for attempt in range(retry_count + 1):
        try:
            result = run_command(f"get {item_path} -q .")
            return json.loads(result)
        except Exception as e:
            if attempt < retry_count:
                time.sleep(2)
            else:
                return None
    return None


def item_exists(item_path: str) -> bool:
    """Check if Fabric item exists."""
    result = run_command(f"exists {item_path}")
    return result.replace("*", "").strip().lower() == "true"


def get_workspace(workspace_name: str) -> Optional[Dict[str, Any]]:
    """
    Get workspace by name.
    
    Args:
        workspace_name: Workspace display name
    
    Returns:
        Workspace JSON or None if not found
    """
    workspace_path = f"{workspace_name}.Workspace"
    return get_item(workspace_path)


def workspace_exists(workspace_name: str) -> bool:
    """Check if workspace exists."""
    workspace_path = f"{workspace_name}.Workspace"
    return item_exists(workspace_path)


def delete_workspace(workspace_id: str) -> bool:
    """
    Delete a Fabric workspace by ID (for rollback).
    Requires admin role on the workspace.
    """
    try:
        response = run_command(f"api -X delete workspaces/{workspace_id}", use_retry=False)
        result = json.loads(response)
        return result.get("status_code", 0) in [200, 204]
    except Exception as e:
        print(f"Error deleting workspace {workspace_id}: {e}")
        return False


def delete_connection(connection_id: str) -> bool:
    """
    Delete a Fabric connection by ID (for rollback).
    """
    try:
        response = run_command(f"api -X delete connections/{connection_id}", use_retry=False)
        result = json.loads(response)
        return result.get("status_code", 0) in [200, 204]
    except Exception as e:
        print(f"Error deleting connection {connection_id}: {e}")
        return False


def create_workspace(workspace_name: str, capacity_name: str) -> Optional[Dict[str, Any]]:
    """
    Create Fabric workspace.
    
    Args:
        workspace_name: Workspace display name
        capacity_name: Fabric capacity name
    
    Returns:
        Created workspace JSON or None on failure
    """
    try:
        command = f"create {workspace_name}.Workspace -c {capacity_name}"
        result = run_command(command)
        # Wait a moment for workspace to be ready
        time.sleep(2)
        return get_workspace(workspace_name)
    except Exception as e:
        print(f"Error creating workspace {workspace_name}: {e}")
        return None


def get_connection(connection_identifier: str) -> Optional[Dict[str, Any]]:
    """
    Get Fabric connection by name or ID.
    
    Args:
        connection_identifier: Connection name or GUID
    
    Returns:
        Connection JSON or None if not found
    """
    if is_guid(connection_identifier):
        connection_url = f"connections/{connection_identifier}"
        response = run_command(f"api -X get {connection_url}")
        try:
            result = json.loads(response)
            if result.get("status_code", 404) == 200:
                return result.get("text")
            return None
        except:
            return None
    else:
        connection_path = f".connections/{connection_identifier}.Connection"
        try:
            return get_item(connection_path)
        except:
            return None


def connection_exists(connection_identifier: str) -> bool:
    """Check if Fabric connection exists."""
    if is_guid(connection_identifier):
        connection_url = f"connections/{connection_identifier}"
        response = run_command(f"api -X get {connection_url}")
        try:
            result = json.loads(response)
            return result.get("status_code", 404) == 200
        except:
            return False
    else:
        connection_path = f".connections/{connection_identifier}.Connection"
        return item_exists(connection_path)


def create_fabric_connection(
    connection_name: str,
    connection_type: str,
    tenant_id: str,
    client_id: str,
    client_secret: str
) -> Optional[Dict[str, Any]]:
    """
    Create Fabric connection.
    
    Args:
        connection_name: Connection display name
        connection_type: Connection type (e.g., 'FabricDataPipelines', 'FabricSql')
        tenant_id: Azure tenant ID
        client_id: Service principal client ID
        client_secret: Service principal client secret
    
    Returns:
        Created connection JSON or None on failure
    """
    try:
        connection_payload = {
            "name": connection_name,
            "type": connection_type,
            "authentication": {
                "type": "ServicePrincipal",
                "tenantId": tenant_id,
                "clientId": client_id,
                "clientSecret": client_secret
            }
        }
        
        response = run_command(f"api -X post connections -i {json.dumps(connection_payload)}")
        result = json.loads(response)
        
        if result.get("status_code") == 200 or result.get("status_code") == 201:
            return result.get("text")
        else:
            print(f"Failed to create connection: {result}")
            return None
    except Exception as e:
        print(f"Error creating connection {connection_name}: {e}")
        return None


def create_github_connection(
    connection_name: str,
    repo_url: str,
    github_pat: str
) -> Optional[Dict[str, Any]]:
    """
    Create GitHub Git connection.
    
    Args:
        connection_name: Connection display name
        repo_url: GitHub repository URL
        github_pat: GitHub Personal Access Token
    
    Returns:
        Created connection JSON or None on failure
    """
    try:
        connection_payload = {
            "name": connection_name,
            "type": "GitHub",
            "properties": {
                "repositoryUrl": repo_url,
                "personalAccessToken": github_pat
            }
        }
        
        response = run_command(f"api -X post connections -i {json.dumps(connection_payload)}")
        result = json.loads(response)
        
        if result.get("status_code") == 200 or result.get("status_code") == 201:
            return result.get("text")
        else:
            print(f"Failed to create GitHub connection: {result}")
            return None
    except Exception as e:
        print(f"Error creating GitHub connection {connection_name}: {e}")
        return None


def create_azuredevops_connection(
    connection_name: str,
    repo_url: str,
    tenant_id: str,
    client_id: str,
    client_secret: str
) -> Optional[Dict[str, Any]]:
    """
    Create Azure DevOps Git connection.
    
    Args:
        connection_name: Connection display name
        repo_url: Azure DevOps repository URL
        tenant_id: Azure tenant ID
        client_id: Service principal client ID
        client_secret: Service principal client secret
    
    Returns:
        Created connection JSON or None on failure
    """
    try:
        connection_payload = {
            "name": connection_name,
            "type": "AzureRepos",
            "properties": {
                "repositoryUrl": repo_url
            },
            "authentication": {
                "type": "ServicePrincipal",
                "tenantId": tenant_id,
                "clientId": client_id,
                "clientSecret": client_secret
            }
        }
        
        response = run_command(f"api -X post connections -i {json.dumps(connection_payload)}")
        result = json.loads(response)
        
        if result.get("status_code") == 200 or result.get("status_code") == 201:
            return result.get("text")
        else:
            print(f"Failed to create Azure DevOps connection: {result}")
            return None
    except Exception as e:
        print(f"Error creating Azure DevOps connection {connection_name}: {e}")
        return None


def add_connection_roleassignment(
    connection_id: str,
    principal_id: str,
    principal_type: str,
    role: str
) -> bool:
    """
    Assign role to connection.
    
    Args:
        connection_id: Connection ID (GUID)
        principal_id: Principal ID (user/group/service principal GUID)
        principal_type: Principal type ('User', 'Group', 'ServicePrincipal')
        role: Role ('Owner' or 'User')
    
    Returns:
        True if successful, False otherwise
    """
    try:
        assignment_payload = {
            "principalId": principal_id,
            "principalType": principal_type,
            "role": role
        }
        
        response = run_command(
            f"api -X post connections/{connection_id}/roleAssignments -i {json.dumps(assignment_payload)}"
        )
        result = json.loads(response)
        return result.get("status_code", 0) in [200, 201]
    except Exception as e:
        print(f"Error assigning connection role: {e}")
        return False


def add_workspace_roleassignment(
    workspace_id: str,
    principal_id: str,
    principal_type: str,
    role: str
) -> bool:
    """
    Assign role to workspace.
    
    Args:
        workspace_id: Workspace ID (GUID)
        principal_id: Principal ID (user/group/service principal GUID)
        principal_type: Principal type ('User', 'Group', 'ServicePrincipal')
        role: Role ('Admin', 'Member', 'Contributor', 'Viewer')
    
    Returns:
        True if successful, False otherwise
    """
    try:
        assignment_payload = {
            "principalId": principal_id,
            "principalType": principal_type,
            "role": role
        }
        
        response = run_command(
            f"api -X post workspaces/{workspace_id}/roleAssignments -i {json.dumps(assignment_payload)}"
        )
        result = json.loads(response)
        return result.get("status_code", 0) in [200, 201]
    except Exception as e:
        print(f"Error assigning workspace role: {e}")
        return False


def get_git_connection(workspace_id: str, max_retries: int = 5) -> Optional[Dict[str, Any]]:
    """
    Get Git connection status for workspace.
    
    Args:
        workspace_id: Workspace ID (GUID)
        max_retries: Maximum retry attempts
    
    Returns:
        Git connection state JSON or None if not connected
    """
    git_url = f"workspaces/{workspace_id}/git/connection"
    
    retry_count = 0
    while retry_count < max_retries:
        response = run_command(f"api -X get {git_url}")
        try:
            result = json.loads(response)
            git_connection_state = result.get("text", {}).get("gitConnectionState", "Unknown")
            
            if git_connection_state == "NotConnected":
                time.sleep(2)
                retry_count += 1
            else:
                return result.get("text")
        except:
            time.sleep(2)
            retry_count += 1
    
    return None


def connect_workspace_to_git(workspace_id: str, git_settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Connect workspace to Git repository.
    
    Args:
        workspace_id: Workspace ID (GUID)
        git_settings: Git settings dictionary (from infrastructure JSON)
    
    Returns:
        Git connection JSON or None on failure
    """
    connect_url = f"workspaces/{workspace_id}/git/connect"
    
    try:
        response = run_command(f"api -X post {connect_url} -i {json.dumps(git_settings)}")
        result = json.loads(response)
        
        if result.get("status_code") in [200, 201]:
            # Wait for connection to be ready
            time.sleep(3)
            return get_git_connection(workspace_id)
        else:
            print(f"Failed to connect workspace to Git: {result}")
            return None
    except Exception as e:
        print(f"Error connecting workspace to Git: {e}")
        return None
