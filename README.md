# Atlassian and APN Agent

A simple AI agent that connects to Atlassian Confluence and Jira via the MCP protocol, and fetches AWS Partner Network solutions to help with FTR (First Time Right) by finding equivalent documents.

Built with **AWS Strands Agent SDK**, **Atlassian Rovo MCP Server**, and **AWS Partner Central API**.

## Prerequisites

- Python 3.10+
- Node.js v18+ (for `mcp-remote` OAuth proxy)
- AWS credentials configured (for Bedrock and Partner Central)
- Atlassian Cloud account

## Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

## Usage

```bash
python main.py
```

On first run, a browser window opens for Atlassian login. After authentication, you can chat with the agent.

**Example prompts:**

- "List all Confluence spaces"
- "Search for documentation about X"
- "Find Jira issues assigned to me"
- "Get the content of page Y"
- "Fetch APN solutions and find related Confluence docs for FTR"

## Configuration

Edit `.env` or the constants in `src/config.py`:

| Setting               | Default                | Description             |
| --------------------- | ---------------------- | ----------------------- |
| `OLLAMA_HOST`         | `http://localhost:11434` | Ollama API endpoint   |
| `OLLAMA_MODEL`        | `llama3.2:latest`      | Ollama model to use     |
| `MCP_STARTUP_TIMEOUT` | `120`                  | OAuth timeout (seconds) |

## Project Structure

```
FTR/
├── main.py                 # Application entry point
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration constants
│   ├── models.py           # LLM model setup (Ollama)
│   ├── mcp_client.py       # Atlassian MCP client
│   └── tools/
│       ├── __init__.py
│       ├── apn_solutions.py    # get_apn_solutions tool
│       ├── opportunities.py    # Opportunity-related tools
│       └── confluence.py       # Confluence search tool
├── agent.py                # Legacy monolithic version (backup)
├── requirements.txt
└── .env.example
```

## Tools

| Tool | Description |
|------|-------------|
| `get_apn_solutions` | Retrieve Partner Solutions from AWS Partner Central |
| `get_opportunities` | List co-selling opportunities |
| `get_opportunity_details` | Get detailed info for a specific opportunity |
| `map_opportunities_to_solutions` | Map opportunities to linked solutions |
| `search_confluence_for_solutions` | Search Confluence for solution docs |

