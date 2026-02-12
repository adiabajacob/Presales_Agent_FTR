
import json
import logging
import os
from strands import Agent
from ..models import local_model

# Path to the structured knowledge base
# Assuming runs from project root
KNOWLEDGE_PATH = os.path.join("src", "data", "ftr_controls.json")

def _load_control_data(control_id: str) -> dict:
    """Load control details from the knowledge base."""
    try:
        if not os.path.exists(KNOWLEDGE_PATH):
            logging.warning(f"Knowledge base not found at {KNOWLEDGE_PATH}")
            return {}
            
        with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            controls = json.load(f)
            
        return controls.get(control_id.strip().upper(), {})
    except Exception as e:
        logging.error(f"Error loading control data: {e}")
        return {}

def generate_remediation_plan(
    control_id: str, 
    solution_name: str, 
    status: str, 
    evidence: str, 
    comments: str
) -> str:
    """
    Generate specific remediation steps for a failed FTR control.
    
    Returns:
        String containing the recommendations, or empty string if Met/Error.
    """
    # Only generate for Not Met controls
    if status.strip().lower() == "met":
        return ""
        
    control_data = _load_control_data(control_id)
    if not control_data:
        return "" # Can't generate without context
        
    description = control_data.get('description', 'N/A')
    calibration = control_data.get('calibration_guide', 'N/A')
    
    prompt = f"""
    You are an expert AWS FTR (Foundational Technical Review) auditor.
    
    CONTEXT:
    - Solution Name: "{solution_name}"
    - Control ID: {control_id}
    - Requirement: {description}
    - Calibration Guide (What usually satisfies this): {calibration[:2000]}
    
    CURRENT ASSESSMENT:
    - Status: {status}
    - Findings/Comments: {comments}
    - Existing Evidence: {evidence}
    
    TASK:
    Generate a specific, actionable REMEDIATION PLAN to help the partner meet this control.
    
    GUIDELINES:
    1. Be prescriptive. Don't just say "Review the guide". Say "Create a page..." or "Update the diagram...".
    2. Suggest specific artifacts to create (e.g. "Confluence page: 'Backup Strategy'", "Architecture Diagram").
    3. Assume the user needs to modify their documentation or configuration.
    4. Keep it concise (3-5 bullet points max).
    
    OUTPUT FORMAT:
    🎯 FTR REMEDIATION PLAN:
    1. [Actionable Step 1]
    2. [Actionable Step 2]
    ...
    """
    
    try:
        # Use a lightweight agent for generation
        advisor = Agent(model=local_model)
        response = advisor.chat(prompt)
        
        # Cleanup
        text = str(response).strip()
        # Remove markdown code blocks if present
        text = text.replace('```markdown', '').replace('```', '')
        return text
            
    except Exception as e:
        logging.error(f"Error generating remediation plan: {e}")
        return "Error generating recommendations."
