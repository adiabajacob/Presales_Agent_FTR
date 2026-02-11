"""
Configuration and constants for the FTR Accelerator Agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# LLM Configuration
# ──────────────────────────────────────────────────────────────────────────────

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# ──────────────────────────────────────────────────────────────────────────────
# AWS Configuration (Dual Account Support)
# ──────────────────────────────────────────────────────────────────────────────
# 1. Profile-based (Recommended for local dev)
APN_AWS_PROFILE = os.getenv("APN_AWS_PROFILE", None)
BEDROCK_AWS_PROFILE = os.getenv("BEDROCK_AWS_PROFILE", None)

# 2. Explicit Key-based (Alternative Setup)
# APN Account
APN_AWS_ACCESS_KEY_ID = os.getenv("APN_AWS_ACCESS_KEY_ID", None)
APN_AWS_SECRET_ACCESS_KEY = os.getenv("APN_AWS_SECRET_ACCESS_KEY", None)
APN_AWS_SESSION_TOKEN = os.getenv("APN_AWS_SESSION_TOKEN", None)
APN_AWS_REGION = os.getenv("APN_AWS_REGION", "us-east-1")

# Bedrock Account
BEDROCK_AWS_ACCESS_KEY_ID = os.getenv("BEDROCK_AWS_ACCESS_KEY_ID", None)
BEDROCK_AWS_SECRET_ACCESS_KEY = os.getenv("BEDROCK_AWS_SECRET_ACCESS_KEY", None)
BEDROCK_AWS_SESSION_TOKEN = os.getenv("BEDROCK_AWS_SESSION_TOKEN", None)
BEDROCK_AWS_REGION = os.getenv("BEDROCK_AWS_REGION", "us-east-1")

# Default Model (Overriding default to Bedrock Sonnet 4 as requested)
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")

# ──────────────────────────────────────────────────────────────────────────────
# Atlassian MCP Configuration
# ──────────────────────────────────────────────────────────────────────────────

ATLASSIAN_MCP_ENDPOINT = "https://mcp.atlassian.com/v1/mcp"
MCP_REMOTE_COMMAND = "npx"
MCP_REMOTE_ARGS = ["-y", "mcp-remote", ATLASSIAN_MCP_ENDPOINT]
MCP_STARTUP_TIMEOUT = 300

# ──────────────────────────────────────────────────────────────────────────────
# System Prompt
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an FTR Acceleration Assistant for AWS Partners.

Your goal is to help the partner prepare for their Foundational Technical Review (FTR).

You have access to:
1. "get_apn_solutions": To fetch registered solutions from AWS Partner Central.
2. "search_confluence_for_solutions": To find internal documentation.
3. "get_opportunities": To see co-selling opportunities.
4. "map_opportunities_to_solutions": To link opportunities to solutions.
5. "lookup_ftr_control" / "search_ftr_guide": To fetch authoritative requirements from the FTR Guide.

CORE BEHAVIOR:
- **PRIORITY 1**: When the user asks about a specific control ID (e.g., "SEC-001", "DEF-001", "OPS-002"), you MUST use `lookup_ftr_control` FIRST. Do NOT assume these are Jira tickets.
- **PRIORITY 2**: When asked about FTR topics (e.g., "Backups", "SLA"), use `search_ftr_guide` to find the relevant controls.
- **PRIORITY 3**: Only after understanding the *official* FTR requirements, search Confluence for *evidence* (architectural diagrams, runbooks) that proves compliance.

Be precise: Quote the FTR Guide text exactly when explaining requirements.

If the user hasn't selected a solution, ask them which one they want to work on.
"""
