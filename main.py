"""
Atlassian and APN Agent - FTR Accelerator

Connects to Atlassian (Confluence/Jira via Rovo MCP) + AWS Partner Central Selling API.
Uses local llama3.2 via Ollama.

This is the main entry point for the application.
"""

import sys
import boto3
from strands import Agent

from src.config import (
    OLLAMA_MODEL, 
    OLLAMA_HOST, 
    SYSTEM_PROMPT, 
    APN_AWS_PROFILE,
    APN_AWS_ACCESS_KEY_ID,
    APN_AWS_SECRET_ACCESS_KEY,
    APN_AWS_SESSION_TOKEN,
    APN_AWS_REGION
)
from src.models import local_model
from src.mcp_client import create_atlassian_mcp_client
from src.tools import (
    get_apn_solutions,
    get_opportunities,
    get_opportunity_details,
    map_opportunities_to_solutions,
    search_confluence_for_solutions,
    read_confluence_page,
    lookup_ftr_control,
    search_ftr_guide,
    generate_ftr_assessment,
)


def get_solutions_interactive():
    """Fetch APN solutions and let the user select one."""
    print("\n🔍 Fetching your APN Solutions...")
    try:
        if APN_AWS_ACCESS_KEY_ID and APN_AWS_SECRET_ACCESS_KEY:
             session = boto3.Session(
                aws_access_key_id=APN_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APN_AWS_SECRET_ACCESS_KEY,
                aws_session_token=APN_AWS_SESSION_TOKEN,
                region_name=APN_AWS_REGION
            )
             pc_client = session.client("partnercentral-selling")
        elif APN_AWS_PROFILE:
            session = boto3.Session(profile_name=APN_AWS_PROFILE)
            pc_client = session.client("partnercentral-selling")
        else:
            pc_client = boto3.client("partnercentral-selling")
        
        sol_response = pc_client.list_solutions(Catalog="AWS", MaxResults=20)
        solutions = sol_response.get("SolutionSummaries", [])

        if not solutions:
            print("❌ No solutions found using AWS Partner Central.")
            return None

        print(f"\n📦 Found {len(solutions)} Registered Solutions:")
        for idx, sol in enumerate(solutions, 1):
            print(f"   [{idx}] {sol.get('Name', 'Unnamed')} (ID: {sol.get('Id')})")

        print("\n   [0] Skip selection (General FTR Chat)")
        
        while True:
            try:
                choice = input("\n👉 Select a solution to focus on (enter number): ").strip()
                if choice == "0":
                    return None
                
                idx = int(choice)
                if 1 <= idx <= len(solutions):
                    return solutions[idx - 1]
                else:
                    print(f"   ⚠ Please enter a number between 0 and {len(solutions)}")
            except ValueError:
                print("   ⚠ Invalid input. Please enter a number.")
                
    except Exception as e:
        print(f"❌ Error fetching solutions: {e}")
        return None


def run_interactive_session():
    """Run the interactive FTR Accelerator Agent session."""
    print("=" * 78)
    print("  AWS Partner FTR Accelerator Agent")
    print("  Connects your APN Solutions ↔ Atlassian Documentation")
    print("=" * 78)
    
    # Step 1: Interactive Solution Selection
    selected_solution = get_solutions_interactive()
    
    # Step 2: Update System Prompt with Context
    current_system_prompt = SYSTEM_PROMPT
    if selected_solution:
        sol_name = selected_solution.get('Name')
        sol_id = selected_solution.get('Id')
        print(f"\n✅ Context Set: FTR assistance for '{sol_name}' ({sol_id})")
        
        current_system_prompt += f"\n\nCURRENT CONTEXT:\nThe user has selected the APN Solution: '{sol_name}' (ID: {sol_id}).\nFocus your FTR analysis, document searches, and recommendations specifically on this solution."
    else:
        print("\nℹ No specific solution selected. Starting general chat.")

    # Step 3: Connect to MCP
    print("\n🔗 Connecting to Atlassian Rovo MCP Server...")
    print("   (Check your browser if an authentication tab opens)")
    
    tools = [
        get_apn_solutions,
        get_opportunities,
        get_opportunity_details,
        map_opportunities_to_solutions,
        search_confluence_for_solutions,
        read_confluence_page,
        lookup_ftr_control,
        search_ftr_guide,
        generate_ftr_assessment,
    ]
    
    mcp_client = None
    try:
        mcp_client = create_atlassian_mcp_client()
        # Initialize context manager manually to keep it open during the loop
        mcp_client.__enter__()
        
        mcp_tools = mcp_client.list_tools_sync()
        tools.extend(mcp_tools)
        print(f"   ✅ Connected! Loaded {len(mcp_tools)} Atlassian tools.")
        
    except Exception as e:
        print(f"   ⚠ Atlassian connection failed: {e}")
        print("   → Continuing with AWS tools only.")

    # Step 4: Start Agent
    print("-" * 78)
    print("🤖 Agent is ready! Ask about FTR requirements, gaps, or documentation.")
    print("   Type 'quit', 'exit' or 'q' to end.")
    print("-" * 78)

    agent = Agent(
        model=local_model,
        system_prompt=current_system_prompt,
        tools=tools,
    )

    # Auto-prompt initialization
    next_input = None
    if selected_solution:
        sol_name = selected_solution.get('Name')
        sol_id = selected_solution.get('Id')
        next_input = (
            f"Generate a preliminary FTR compliance draft for {sol_name} (ID: {sol_id}). "
            "Check against key FTR controls (e.g., SEC-1, REL-1). "
            f"IMPORTANT: Use `search_confluence_for_solutions(target_solution_name='{sol_name}')` to find candidate documents. "
            "THEN, if a document title looks relevant but you need to confirm details (e.g., specific config values), use `read_confluence_page(page_id)` to verify. "
            "List the status of each checked control. "
            "**CRITICAL INSTRUCTIONS:**\n"
            "1. If you cannot find relevant documentation for a control, explicitly state 'No documentation found' and recommend creating it.\n"
            "2. **ALWAYS include the direct source URL** for any evidence found (the search tool provides these links). Format: [Document Title](URL).\n"
            "3. DO NOT hallucinate or guess document names/links."
        )
        print(f"\n🚀 Auto-generating FTR Draft for '{sol_name}'...")

    while True:
        try:
            if next_input:
                user_input = next_input
                # Print it so user sees what's happening, but maybe simpler
                print(f"\n(Auto-Submitted Task): {user_input[:100]}...") 
                next_input = None
            else:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
            
            if user_input.lower() in ("quit", "exit", "q"):
                print("\nGoodbye! 👋")
                break

            print("\nThinking...", end="", flush=True)
            response = agent(user_input)
            
            # Clear "Thinking..." line
            print("\r" + " " * 20 + "\r", end="") 
            print(f"Agent: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

    # Cleanup
    if mcp_client:
        try:
            mcp_client.__exit__(None, None, None)
        except:
            pass


if __name__ == "__main__":
    run_interactive_session()
