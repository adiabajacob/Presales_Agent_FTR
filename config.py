lis"""
Configuration settings for the FTR Draft Generator Agent.
"""

import os
from dotenv import load_dotenv


load_dotenv()



# ==============================================================================
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", None)


BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID", 
    "amazon.nova-pro-v1:0"
)


# ==============================================================================
# Atlassian MCP Server Configuration
# ==============================================================================
# Atlassian Rovo MCP Server endpoint (cloud-based)
ATLASSIAN_MCP_ENDPOINT = "https://mcp.atlassian.com/v1/mcp"

# For local development, we use mcp-remote as a proxy to handle OAuth
# This requires Node.js v18+ installed
MCP_REMOTE_COMMAND = "npx"
MCP_REMOTE_ARGS = [
    "-y",
    "mcp-remote",
    ATLASSIAN_MCP_ENDPOINT
]


# ==============================================================================
# FTR Competency Configuration
# ==============================================================================
SUPPORTED_COMPETENCIES = [
    "lambda",      # AWS Lambda - Serverless Delivery
    "eks",         # Amazon EKS - Containers Delivery
    "rds",         # Amazon RDS - Database Delivery
    "ec2",         # Amazon EC2/Windows - Compute Delivery
    "config",      # AWS Config - Governance
    "control-tower"  # AWS Control Tower - Multi-Account
]

# Requirement ID prefixes per competency
COMPETENCY_REQUIREMENT_PREFIX = {
    "lambda": "LAM",
    "eks": "EKS",
    "rds": "RDS",
    "ec2": "EC2",
    "config": "CFG",
    "control-tower": "CT"
}

# Common requirement prefixes (shared across all competencies)
COMMON_REQUIREMENT_PREFIXES = [
    "DOC",      # Documentation requirements
    "ACCT",     # Account governance
    "OPE",      # Operations
    "NETSEC",   # Network security
    "REL",      # Reliability
    "COST"      # Cost optimization
]


# ==============================================================================
# Agent System Prompts
# ==============================================================================
FTR_AGENT_SYSTEM_PROMPT = """You are an AWS FTR (Foundational Technical Review) documentation assistant.

Your role is to help generate draft responses for AWS Partner Network FTR requirements.

CRITICAL RULES:
1. NEVER invent requirements or answers - all responses must be grounded in retrieved documents
2. Always cite the source document when providing information
3. Use official AWS FTR calibration guidance to shape answer quality
4. Reference AmaliTech internal documentation as evidence where applicable

You have access to Atlassian Confluence for retrieving internal documentation and evidence.

When asked about FTR requirements:
1. Search for relevant internal documentation
2. Cross-reference with the requirement criteria
3. Generate a structured response with evidence citations
"""
