# FTR Draft Generator Agent

An AI-powered agent for automating AWS Partner Network (APN) Foundational Technical Review (FTR) documentation.

Built with **AWS Strands Agent SDK** and connected to **Atlassian MCP Server** for retrieving internal documentation from Confluence.

## Overview

This agent helps:

- Search Confluence for internal technical documentation
- Retrieve evidence for FTR requirements
- Generate structured draft responses
- Cross-reference requirements with existing documentation

## Prerequisites

### 1. Python 3.10+

```bash
python --version  # Should be 3.10 or higher
```

### 2. Node.js v18+

Required for `mcp-remote` proxy which handles Atlassian OAuth authentication.

```bash
node --version  # Should be v18 or higher
```

### 3. AWS Credentials

Configure AWS credentials for Bedrock access:

```bash
aws configure
```

Or set environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

### 4. Atlassian Cloud Account

You need access to an Atlassian Cloud site with Jira and/or Confluence. No API keys required - the agent uses OAuth 2.1 authentication (a browser window opens on first run).

## Installation

1. **Clone and navigate to the project**

   ```bash
   cd FTR
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Usage

### Interactive Session

Run the agent in interactive mode:

```bash
python agent.py
```

On first run:

1. A browser window will open for Atlassian login
2. Authorize the MCP connection
3. Return to the terminal and start chatting

### Example Prompts

```
You: List all Confluence spaces I have access to

You: Search Confluence for AWS Lambda architecture documentation

You: Find evidence for FTR requirement DOC-001 (Architecture Diagram)

You: What internal documentation do we have about EKS deployments?
```

### Programmatic Usage

```python
from agent import search_confluence, list_confluence_spaces, get_ftr_evidence

# Search Confluence
results = search_confluence("AWS Lambda best practices")
print(results)

# List spaces
spaces = list_confluence_spaces()
print(spaces)

# Get FTR evidence
evidence = get_ftr_evidence("lambda", "DOC-001")
print(evidence)
```

## Available Atlassian MCP Tools

Once connected, the agent has access to these tools:

### Confluence Tools

| Tool                        | Description                         |
| --------------------------- | ----------------------------------- |
| `getConfluencePage`         | Get a page by ID with Markdown body |
| `getConfluenceSpaces`       | List accessible spaces              |
| `getPagesInConfluenceSpace` | List pages in a space               |
| `searchConfluenceUsingCql`  | Search using CQL query              |
| `createConfluencePage`      | Create new pages                    |
| `updateConfluencePage`      | Update existing pages               |

### Jira Tools

| Tool                       | Description            |
| -------------------------- | ---------------------- |
| `getJiraIssue`             | Get issue by ID or key |
| `searchJiraIssuesUsingJql` | Search using JQL       |
| `createJiraIssue`          | Create new issues      |
| `editJiraIssue`            | Update issue fields    |

### Rovo Search

| Tool     | Description                                      |
| -------- | ------------------------------------------------ |
| `search` | Natural language search across Jira & Confluence |
| `fetch`  | Fetch content by Atlassian Resource Identifier   |

## Project Structure

```
FTR/
├── agent.py           # Main agent implementation
├── config.py          # Configuration settings
├── requirements.txt   # Python dependencies
├── .env.example       # Example environment variables
└── README.md          # This file
```

## Supported FTR Competencies

| AWS Service       | Competency Type     | Requirement Prefix |
| ----------------- | ------------------- | ------------------ |
| AWS Lambda        | Serverless Delivery | LAM-xxx            |
| Amazon EKS        | Containers Delivery | EKS-xxx            |
| Amazon RDS        | Database Delivery   | RDS-xxx            |
| Amazon EC2        | Compute Delivery    | EC2-xxx            |
| AWS Config        | Governance          | CFG-xxx            |
| AWS Control Tower | Multi-Account       | CT-xxx             |

Common requirements (shared across all): `DOC-xxx`, `ACCT-xxx`, `OPE-xxx`, `NETSEC-xxx`, `REL-xxx`, `COST-xxx`

## Troubleshooting

### "mcp-remote: command not found"

Ensure Node.js v18+ is installed and npx is available:

```bash
npm install -g npx
```

### OAuth Browser Doesn't Open

If running in a headless environment, you may need to:

1. Run locally first to cache credentials
2. Or use a GUI-enabled terminal

### AWS Bedrock Access Denied

Ensure your AWS credentials have access to Amazon Bedrock and the Claude model:

```bash
aws bedrock list-foundation-models --region us-east-1
```

### Connection Timeout

Check network connectivity to:

- `https://mcp.atlassian.com`
- AWS Bedrock endpoint

## Security Notes

- OAuth tokens are session-based and scoped to your permissions
- MCP actions respect your Atlassian access controls
- Never commit `.env` files with credentials
- Review Atlassian audit logs for MCP activity

## Next Steps

1. **Add SharePoint RAG** - Connect to SharePoint for official FTR/calibration documents
2. **Output Generation** - Add Word/Excel document generation
3. **Web UI** - Build a Streamlit or FastAPI frontend
4. **Batch Processing** - Process multiple requirements at once

## References

- [AWS Strands Agent SDK](https://strandsagents.com/)
- [Atlassian MCP Server](https://support.atlassian.com/atlassian-rovo-mcp-server/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [AWS FTR Program](https://aws.amazon.com/partners/foundational-technical-review/)
# Presales_Agent_FTR
