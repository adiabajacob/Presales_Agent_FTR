"""
Confluence search tool for finding documentation related to APN solutions.
"""

import logging
import uuid
import boto3
from strands.tools import tool
from ..mcp_client import create_atlassian_mcp_client


@tool
def search_confluence_for_solutions(
    max_solutions: int = 5,
    catalog: str = "AWS",
    target_solution_name: str = None
) -> str:
    """Search Confluence for documentation related to your APN solutions.
    
    This tool:
    1. Fetches your solutions from Partner Central (unless target_solution_name is provided)
    2. Connects to Confluence via Atlassian MCP
    3. Searches for the solution name(s)
    4. Returns matching Confluence pages
    
    Args:
        max_solutions: Max number of solutions to search for (default: 5)
        catalog: Catalog to use ('AWS' or 'Sandbox', default: 'AWS')
        target_solution_name: If provided, ONLY search for this specific solution name. 
                              Use this to focus the search and avoid irrelevant results.
    """
    lines = []
    lines.append(f"\n{'=' * 80}")
    lines.append(f"🔍 SEARCHING CONFLUENCE FOR APN SOLUTIONS")
    lines.append(f"{'=' * 80}\n")
    
    solutions = []

    # Step 1: Determine what to search for
    if target_solution_name:
         lines.append(f"🎯 Target Solution Specified: '{target_solution_name}'")
         # Create a dummy solution object for the loop below
         solutions = [{"Name": target_solution_name, "Id": "Targeted-Search"}]
    else:
        # Fetch from Partner Central as before
        try:
            pc_client = boto3.client("partnercentral-selling")
            sol_response = pc_client.list_solutions(Catalog=catalog, MaxResults=max_solutions)
            solutions = sol_response.get("SolutionSummaries", [])
            
            if not solutions:
                return "No solutions found in Partner Central."
            
            lines.append(f"📦 Found {len(solutions)} solutions in Partner Central:\n")
            for idx, sol in enumerate(solutions, 1):
                lines.append(f"    [{idx}] {sol.get('Name', 'Unnamed')} ({sol.get('Id', 'N/A')})")
            
        except Exception as e:
            return f"Error fetching solutions from Partner Central: {e}"
    
    # Step 2: Connect to Atlassian MCP
    lines.append(f"\n{'─' * 80}")
    lines.append(f"🔗 Connecting to Atlassian MCP...")
    lines.append(f"{'─' * 80}\n")
    
    try:
        mcp_client = create_atlassian_mcp_client()
        with mcp_client:
            # List available tools
            mcp_tools = mcp_client.list_tools_sync()
            
            # Extract tool names - try multiple ways
            def get_tool_name(t):
                if hasattr(t, 'tool_name'): return t.tool_name
                if hasattr(t, 'name') and isinstance(t.name, str): return t.name
                if hasattr(t, 'tool') and hasattr(t.tool, 'name'): return t.tool.name
                # Try to get from __dict__
                if hasattr(t, '__dict__'):
                    for key in ['tool_name', 'name', '_name']:
                        if key in t.__dict__ and isinstance(t.__dict__[key], str):
                            return t.__dict__[key]
                return str(t)
            
            tool_names = [get_tool_name(t) for t in mcp_tools]
            
            lines.append(f"    ✅ Connected to Atlassian!")
            lines.append(f"    📋 Available tools ({len(mcp_tools)})")
            
            # Step 3: Find the Confluence search tool
            confluence_search = None
            
            for t in mcp_tools:
                t_name = get_tool_name(t).lower()
                if 'search' in t_name and ('confluence' in t_name or 'page' in t_name):
                    confluence_search = get_tool_name(t)
                    break
            
            # Helper to safely get content from result (dict or object)
            def get_content_text(result):
                # Try dict access
                if isinstance(result, dict):
                    content = result.get('content')
                else:
                    # Try object access
                    content = getattr(result, 'content', None)
                
                if not content:
                    return None
                    
                if isinstance(content, list) and len(content) > 0:
                    item = content[0]
                    if isinstance(item, dict):
                        return item.get('text')
                    else:
                        return getattr(item, 'text', None)
                return None

            # Step 3.5: Get Cloud ID (Required for search)
            cloud_id = None
            try:
                # Find resource tool
                resource_tool_name = None
                for t in tool_names:
                    if "getaccessibleatlassianresources" in t.lower():
                        resource_tool_name = t
                        break
                
                if resource_tool_name:
                    lines.append(f"\n    🆔 Fetching Atlassian Resources using {resource_tool_name}...")
                    res_tool_use_id = str(uuid.uuid4())
                    res_result = mcp_client.call_tool_sync(
                        name=resource_tool_name,
                        tool_use_id=res_tool_use_id,
                        arguments={}
                    )
                    
                    text_content = get_content_text(res_result)
                    
                    if text_content:
                        import json
                        resources = json.loads(text_content)
                        if resources and isinstance(resources, list):
                            # Prefer a Confluence resource if possible
                            for res in resources:
                                scopes = res.get('scopes', [])
                                if any('confluence' in s for s in scopes):
                                    cloud_id = res.get('id')
                                    cloud_name = res.get('name')
                                    cloud_url = res.get('url')
                                    lines.append(f"    ✅ Found Confluence Cloud ID: {cloud_id} ({cloud_name})")
                                    break
                            
                            # Fallback to first resource if no specific confluence scope found
                            if not cloud_id and len(resources) > 0:
                                cloud_id = resources[0].get('id')
                                lines.append(f"    ✅ Found Cloud ID (fallback): {cloud_id}")
                    else:
                         lines.append(f"    ⚠ No text content returned from resource tool.")
                                
            except Exception as e:
                lines.append(f"    ⚠ Could not fetch Cloud ID: {e}")

            if not confluence_search:
                # Fallback search tool search
                for t in mcp_tools:
                    t_name = get_tool_name(t).lower()
                    if 'search' in t_name:
                        confluence_search = get_tool_name(t)
                        break
            
            if not confluence_search:
                lines.append(f"\n    ⚠ No search tool found in available tools")
                return "\n".join(lines)

            if not cloud_id:
                lines.append(f"\n    ⚠ No Cloud ID found. Search will likely fail.")

            lines.append(f"\n    🔍 Using search tool: {confluence_search}")
            
            # Step 4: Search for each solution
            lines.append(f"\n{'─' * 80}")
            lines.append(f"📄 CONFLUENCE SEARCH RESULTS:")
            lines.append(f"{'─' * 80}\n")
            
            for sol in solutions:
                sol_name = sol.get("Name", "")
                sol_id = sol.get("Id", "N/A")
                
                if not sol_name:
                    continue
                
                # Dynamic Query Construction
                if target_solution_name:
                    # Strict search for targeted solution
                    # Prioritize exact phrase matches in title or text
                    cql_query = f'title ~ "{sol_name}" OR text ~ "{sol_name}"'
                else:
                    # Broad heuristic search handling
                    search_words = [w for w in sol_name.split() 
                                   if len(w) > 3 and w.lower() not in ['with', 'and', 'the', 'for', 'aws']][:4]
                    search_query = " ".join(search_words)
                    cql_query = f'text ~ "{search_query}"'
                
                lines.append(f"\n📦 Solution: {sol_name[:60]}...")
                lines.append(f"   ID: {sol_id}")
                lines.append(f"   CQL query: {cql_query}")
                
                try:
                    # Call the MCP search tool with required parameters
                    tool_use_id = str(uuid.uuid4())
                    
                    args = {"cql": cql_query}
                    if cloud_id:
                        args["cloudId"] = cloud_id
                        
                    result = mcp_client.call_tool_sync(
                        name=confluence_search,
                        tool_use_id=tool_use_id,
                        arguments=args
                    )
                    
                    # Parse result using helper
                    result_text = get_content_text(result)
                    
                    if result_text:
                        import json
                        try:
                            # Try to parse as JSON to extract links
                            data = json.loads(result_text)
                            results_list = data.get('results', [])
                            
                            if results_list:
                                lines.append(f"   ✅ Found {len(results_list)} results:")
                                for item in results_list:
                                    # Handle simplified or nested structure
                                    content = item.get('content', item) if 'content' in item else item
                                    
                                    title = content.get('title', 'Untitled')
                                    links = content.get('_links', {})
                                    webui = links.get('webui', '')
                                    page_id = content.get('id', '')
                                    
                                    full_link = webui
                                    if webui.startswith('/') and cloud_url:
                                        base = cloud_url.rstrip('/')
                                        # Heuristic: ensure we don't double /wiki if it's already there
                                        if not webui.startswith('/wiki'):
                                            full_link = f"{base}/wiki{webui}"
                                        else:
                                            full_link = f"{base}{webui}"
                                    elif webui.startswith('/') and not cloud_url:
                                         full_link = f"https://atlassian.net{webui} (Base URL missing)"

                                    lines.append(f"      • [{title}]({full_link}) (ID: {page_id})")
                            else:
                                lines.append(f"      (No 'results' list in JSON response)")
                                lines.append(f"      Raw: {result_text[:200]}...")

                        except json.JSONDecodeError:
                            # Fallback if text is not JSON
                            lines.append(f"   ✅ Found results (Text):")
                            if len(result_text) > 500:
                                lines.append(f"      {result_text[:500]}...")
                            else:
                                lines.append(f"      {result_text}")
                    else:
                        # Fallback str conversion if not standard text content
                        res_str = str(result)
                        if "error" in res_str.lower():
                            lines.append(f"   ⚠ Potential error in result: {res_str[:200]}")
                        else:
                            lines.append(f"   ⚠ No text content in results")
                            
                except Exception as e:
                    lines.append(f"   ❌ Search error: {str(e)[:100]}")
            
    except Exception as e:
        lines.append(f"\n    ❌ Could not connect to Atlassian MCP: {e}")
        lines.append(f"    Make sure you have authenticated with Atlassian.")
    
    lines.append(f"\n{'=' * 80}\n")
    return "\n".join(lines)


@tool
def read_confluence_page(page_id: str) -> str:
    """Read the full content of a specific Confluence page by its ID.
    
    Use this tool to verify technical details (e.g., specific configurations, 
    architecture diagrams described in text) that aren't visible in the title alone.
    
    Args:
        page_id: The numeric ID of the page to read (returned by search_confluence_for_solutions).
    """
    lines = []
    lines.append(f"📖 READING PAGE: {page_id}...")
    
    try:
        mcp_client = create_atlassian_mcp_client()
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            
            # Find the get_page tool
            read_tool = None
            for t in tools:
                t_name = getattr(t, 'name', '') or getattr(t, 'tool_name', '')
                if 'get_page' in t_name or ('read' in t_name and 'page' in t_name):
                    read_tool = t_name
                    break
            
            if not read_tool:
                # Try finding a generic resource reader if specific page reader not found
                return "Error: Could not find a 'get_page' tool in the Atlassian MCP."
                
            tool_use_id = str(uuid.uuid4())
            # Most Atlassian MCPs use 'pageId' or 'id' as argument
            try:
                result = mcp_client.call_tool_sync(
                    name=read_tool,
                    tool_use_id=tool_use_id,
                    arguments={"pageId": page_id}
                )
            except Exception:
                # Retry with just 'id' if pageId failed
                 result = mcp_client.call_tool_sync(
                    name=read_tool,
                    tool_use_id=tool_use_id,
                    arguments={"id": page_id}
                )

            # Extract content
            content = None
            if hasattr(result, 'content'):
                content_list = result.content
                if content_list and len(content_list) > 0:
                    item = content_list[0]
                    content = getattr(item, 'text', '')
            
            if not content:
                content = str(result)
                
            # Basic cleanup of XML/Storage format if needed (simple tag stripping)
            # For now, return raw-ish text, relying on LLM to parse
            return f"""
page_id: {page_id}
---
{content[:8000]} 
---
(Content truncated at 8k chars if longer)
"""

    except Exception as e:
        return f"Error reading page {page_id}: {e}"
