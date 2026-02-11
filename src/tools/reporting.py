
import os
import shutil
import openpyxl
from datetime import datetime
from strands.tools import tool

TEMPLATE_PATH = "_Foundational Technical Review for Service Offering Self-Assessment.xlsx"
OUTPUT_DIR = "ftr_assessments"

@tool
def generate_ftr_assessment(
    solution_name: str,
    assessments: list[dict]
) -> str:
    """Generate an FTR Self-Assessment Excel file with the agent's findings.
    
    Args:
        solution_name: Name of the APN solution.
        assessments: A list of findings. Each item must be a dict with:
                     - "control_id": e.g., "SEC-001"
                     - "status": "Met" or "Not Met"
                     - "evidence": URL or description of evidence
                     - "comments": Agent's analysis or summary
    """
    if not os.path.exists(TEMPLATE_PATH):
        return f"Error: Template file '{TEMPLATE_PATH}' not found."

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in solution_name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
    output_filename = f"FTR_Assessment_{safe_name}_{timestamp}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    try:
        shutil.copy(TEMPLATE_PATH, output_path)
        workbook = openpyxl.load_workbook(output_path)
        
        # Assume "FTR Requirements" sheet based on project knowledge
        if "FTR Requirements" not in workbook.sheetnames:
             return f"Error: Template missing 'FTR Requirements' sheet."
             
        sheet = workbook["FTR Requirements"]
        
        # Map Control IDs to content
        # We need to find which rows correspond to each control ID.
        # Heuristic: Iterate rows, check column A (or B?) for ID.
        # Based on structure_ftr_data.py, ID is likely in a specific column.
        # Let's inspect rows 1-200.
        
        control_map = {a['control_id'].upper().strip(): a for a in assessments}
        
        # Find column indices (assuming header is row 2, 1-indexed)
        header_row = 2
        col_map = {}
        for cell in sheet[header_row]:
            if cell.value:
                col_map[str(cell.value).strip()] = cell.column
        
        # Fallbacks if headers aren't exact
        idx_id = col_map.get('ID', 2) # Default B
        idx_status = col_map.get('Met?', 5) # Default E
        idx_evidence = col_map.get('Partner Response', 6) # Default F
        
        updated_count = 0
        
        for row in sheet.iter_rows(min_row=header_row+1, max_row=500):
            cell_id = row[idx_id-1] # 0-indexed access for row tuple
            if not cell_id.value:
                continue
                
            cid = str(cell_id.value).strip().upper()
            
            if cid in control_map:
                assessment = control_map[cid]
                
                # Update Status
                sheet.cell(row=cell_id.row, column=idx_status).value = assessment.get('status', 'Not Met')
                
                # Update Evidence/Comments
                evidence = assessment.get('evidence', '')
                comments = assessment.get('comments', '')
                full_text = f"{comments}\n\nEvidence: {evidence}".strip()
                
                sheet.cell(row=cell_id.row, column=idx_evidence).value = full_text
                updated_count += 1
        
        workbook.save(output_path)
        return f"✅ Successfully generated FTR Assessment: {output_path} ({updated_count} controls updated)"

    except Exception as e:
        return f"Error generating Excel: {e}"
