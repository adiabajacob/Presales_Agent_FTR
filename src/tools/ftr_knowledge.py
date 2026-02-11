
import json
import logging
import os
from strands.tools import tool

# Path to the structured knowledge base
KNOWLEDGE_PATH = "src/data/ftr_controls.json"

@tool
def lookup_ftr_control(control_id: str) -> str:
    """Get the OFFICIAL requirements and calibration guidance for an FTR Control (e.g., SEC-001).
    
    CRITICAL: Use this tool whenever the user mentions a code like 'SEC-001', 'DEF-001', 'OPS-001', 'RISK-001'.
    These are NOT Jira tickets; they are FTR Controls.
    
    Args:
        control_id: The FTR Control ID (e.g. "SEC-001")
    """
    try:
        if not os.path.exists(KNOWLEDGE_PATH):
            return "Error: FTR Knowledge Base not found. Please run ingestion script."
            
        with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            controls = json.load(f)
            
        # Normalize ID lookup
        cid = control_id.strip().upper()
        if cid in controls:
            c_data = controls[cid]
            return f"""
📚 **FTR Control: {cid}**
────────────────────────────────────────
**Requirement:**
{c_data.get('description', 'N/A')}

**Calibration Guide & Best Practices:**
{c_data.get('calibration_guide', 'No detailed guidance found in PDF.')[:2000]}
────────────────────────────────────────
"""
        else:
            return f"Control ID '{cid}' not found in knowledge base."
            
    except Exception as e:
        return f"Error reading knowledge base: {e}"

@tool
def search_ftr_guide(query: str) -> str:
    """Search the FTR Guide for topics or keywords.
    
    Use this tool to find relevant controls when you don't know the ID (e.g., "backup", "disaster recovery").
    
    Args:
        query: Keywords to search for
    """
    try:
        if not os.path.exists(KNOWLEDGE_PATH):
            return "Error: FTR Knowledge Base not found."
            
        with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            controls = json.load(f)
            
        matches = []
        query_lower = query.lower()
        
        for cid, data in controls.items():
            content = (data.get('description', '') + " " + data.get('calibration_guide', '')).lower()
            if query_lower in content or query_lower in cid.lower():
                matches.append(f"• {cid}: {data.get('description', '')[:100]}...")
                
        if not matches:
            return f"No matches found for '{query}' in FTR Guide."
            
        return f"""
🔍 **FTR Guide Search Results for '{query}'**
Found {len(matches)} relevant controls:

{chr(10).join(matches[:10])}

(Use `lookup_ftr_control` with an ID to see full details)
"""
    except Exception as e:
        return f"Error searching knowledge base: {e}"
