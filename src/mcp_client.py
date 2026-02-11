"""
Atlassian MCP client setup for the FTR Accelerator Agent.
"""

from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient
from .config import (
    MCP_REMOTE_COMMAND,
    MCP_REMOTE_ARGS,
    MCP_STARTUP_TIMEOUT,
)


def create_atlassian_mcp_client() -> MCPClient:
    """
    Create and return an Atlassian MCP client.
    
    Returns:
        MCPClient: Configured MCP client for Atlassian integration
    """
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command=MCP_REMOTE_COMMAND,
                args=MCP_REMOTE_ARGS,
            )
        ),
        startup_timeout=MCP_STARTUP_TIMEOUT,
    )
