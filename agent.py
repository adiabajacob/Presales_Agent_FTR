"""
FTR Draft Generator Agent

An AI agent built with AWS Strands Agent SDK that connects to Atlassian MCP Server
to retrieve internal documentation for AWS FTR (Foundational Technical Review) generation.
"""

from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

from config import (
    MCP_REMOTE_COMMAND,
    MCP_REMOTE_ARGS,
    FTR_AGENT_SYSTEM_PROMPT,
    BEDROCK_MODEL_ID,
)


# Timeout for MCP client initialization (seconds)
# Increased to 120s to allow time for browser-based OAuth flow
MCP_STARTUP_TIMEOUT = 120


def create_atlassian_mcp_client() -> MCPClient:
    """
    Create an MCP client that connects to Atlassian Rovo MCP Server.
    
    Uses mcp-remote as a proxy to handle OAuth 2.1 authentication.
    On first run, a browser window will open for Atlassian login.
    
    Prerequisites:
        - Node.js v18+ installed
        - Atlassian Cloud account with Jira/Confluence access
    
    Returns:
        MCPClient configured for Atlassian MCP Server
    """
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command=MCP_REMOTE_COMMAND,
                args=MCP_REMOTE_ARGS,
            )
        ),
        # Increase timeout to allow for OAuth browser authentication
        startup_timeout=MCP_STARTUP_TIMEOUT,
    )


def create_ftr_agent(mcp_client: MCPClient | None = None) -> Agent:
    """
    Create the FTR Draft Generator Agent.
    
    Args:
        mcp_client: Optional MCP client for Atlassian. If None, creates one.
    
    Returns:
        Configured Strands Agent with Atlassian MCP tools
    """
    if mcp_client is None:
        mcp_client = create_atlassian_mcp_client()
    
    # Create agent with MCP client - lifecycle managed automatically
    agent = Agent(
        model=BEDROCK_MODEL_ID,
        system_prompt=FTR_AGENT_SYSTEM_PROMPT,
        tools=[mcp_client],
    )
    
    return agent


def run_interactive_session():
    """
    Run an interactive chat session with the FTR agent.
    
    The agent can:
    - Search Confluence for internal documentation
    - Query Jira for project context
    - Help draft FTR requirement responses
    """
    print("=" * 60)
    print("FTR Draft Generator Agent")
    print("=" * 60)
    print("\nConnecting to Atlassian MCP Server...")
    print("(A browser window will open for authentication)")
    print(f"(You have {MCP_STARTUP_TIMEOUT} seconds to complete login)\n")
    
    mcp_client = create_atlassian_mcp_client()
    
    # Use context manager for proper lifecycle management
    with mcp_client:
        # List available tools from Atlassian MCP
        tools = mcp_client.list_tools_sync()
        
        print(f"Connected! Available Atlassian tools: {len(tools)}")
        print("-" * 60)
        for tool in tools:
            # MCPAgentTool uses tool_name and tool_spec properties
            name = tool.tool_name
            desc = tool.tool_spec.get("description", "No description")[:60]
            print(f"  - {name}: {desc}...")
        print("-" * 60)
        print("\nYou can now ask questions about your Atlassian content.")
        print("Type 'quit' or 'exit' to end the session.\n")
        
        # Create agent with the tools
        agent = Agent(
            model=BEDROCK_MODEL_ID,
            system_prompt=FTR_AGENT_SYSTEM_PROMPT,
            tools=tools,
        )
        
        # Interactive loop
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ("quit", "exit", "q"):
                    print("\nGoodbye!")
                    break
                
                # Send to agent and get response
                response = agent(user_input)
                print(f"\nAgent: {response}")
                
            except KeyboardInterrupt:
                print("\n\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Please try again or type 'quit' to exit.")


def search_confluence(query: str) -> str:
    """
    Search Confluence for documentation matching the query.
    
    This is a convenience function that creates a temporary agent session
    to perform a single search.
    
    Args:
        query: Natural language search query
    
    Returns:
        Search results as a string
    """
    mcp_client = create_atlassian_mcp_client()
    
    with mcp_client:
        agent = Agent(
            model=BEDROCK_MODEL_ID,
            system_prompt="You are a search assistant. Search Confluence and return relevant results.",
            tools=mcp_client.list_tools_sync(),
        )
        
        response = agent(f"Search Confluence for: {query}")
        return str(response)


def list_confluence_spaces() -> str:
    """
    List all accessible Confluence spaces.
    
    Returns:
        List of Confluence spaces the user has access to
    """
    mcp_client = create_atlassian_mcp_client()
    
    with mcp_client:
        agent = Agent(
            model=BEDROCK_MODEL_ID,
            system_prompt="You are a helper assistant. List Confluence spaces.",
            tools=mcp_client.list_tools_sync(),
        )
        
        response = agent("List all Confluence spaces I have access to")
        return str(response)


# ==============================================================================
# Example usage patterns for FTR generation
# ==============================================================================

def get_ftr_evidence(competency: str, requirement_id: str) -> str:
    """
    Search for evidence related to a specific FTR requirement.
    
    Args:
        competency: AWS competency (e.g., 'lambda', 'eks')
        requirement_id: Requirement ID (e.g., 'DOC-001', 'LAM-001')
    
    Returns:
        Evidence documentation found in Confluence
    """
    mcp_client = create_atlassian_mcp_client()
    
    with mcp_client:
        agent = Agent(
            model=BEDROCK_MODEL_ID,
            system_prompt=FTR_AGENT_SYSTEM_PROMPT,
            tools=mcp_client.list_tools_sync(),
        )
        
        prompt = f"""
        Search for internal documentation that provides evidence for FTR requirement {requirement_id}
        for the {competency.upper()} competency.
        
        Look for:
        - Architecture diagrams
        - Technical documentation
        - Implementation details
        - Best practices followed
        
        Summarize what you find and cite the specific Confluence pages.
        """
        
        response = agent(prompt)
        return str(response)


# ==============================================================================
# Main entry point
# ==============================================================================

if __name__ == "__main__":
    run_interactive_session()
