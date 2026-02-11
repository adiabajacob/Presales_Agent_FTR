
import json
import logging
import os
import re
import pandas as pd
import pypdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Output file
OUTPUT_PATH = "src/data/ftr_controls.json"

def find_files():
    excel_file = None
    pdf_file = None
    files = os.listdir('.')
    for f in files:
        if f.endswith('.xlsx') and not f.startswith('~$'):
            excel_file = f
        if f.endswith('.pdf'):
            pdf_file = f
    return excel_file, pdf_file

def clean_text(text):
    if isinstance(text, str):
        return re.sub(r'\s+', ' ', text).strip()
    return ""

def process_excel(file_path):
    logger.info(f"Processing Excel: {file_path}")
    controls = {}
    
    try:
        # Based on inspection: Sheet "FTR Requirements", Header on row 1 (0-indexed)
        df = pd.read_excel(file_path, sheet_name="FTR Requirements", header=1)
        
        # Rename columns based on inspection output
        # Found: 'ID', 'Requirement Description', 'Met?', 'Partner Response'
        # The inspection showed standard names in row 1
        
        # Standardize column names
        df.columns = [str(c).strip() for c in df.columns]
        
        if 'ID' not in df.columns:
            logger.error(f"Column 'ID' not found. Available: {df.columns}")
            return {}

        for _, row in df.iterrows():
            cid = str(row.get('ID', '')).strip()
            if not cid or cid.lower() == 'nan' or 'example' in cid.lower():
                continue
                
            controls[cid] = {
                "id": cid,
                "description": clean_text(row.get('Requirement Description', '')),
                "source": "Foundational Technical Review for Service Offering Self-Assessment",
                "calibration_guide": "" # Will be filled from PDF
            }
            logger.info(f"Loaded Control: {cid}")
            
    except Exception as e:
        logger.error(f"Error processing Excel: {e}")
        
    return controls

def process_pdf(file_path, controls_dict):
    logger.info(f"Processing PDF: {file_path}")
    try:
        reader = pypdf.PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
            
        # Try to split by Control ID
        # Pattern: looks for something like "DEF-001 - " or just "DEF-001" followed by text
        # We will iterate through our known controls and try to find their section
        
        control_ids = list(controls_dict.keys())
        
        for cid in control_ids:
            # Simple extraction: Find start of this control and end at start of next
            # This is heuristic and might need tuning
            start_idx = full_text.find(cid)
            if start_idx == -1:
                # Try finding with space, e.g. "DEF - 001"
                parts = cid.split('-')
                if len(parts) == 2:
                    alt_cid = f"{parts[0]} - {parts[1]}"
                    start_idx = full_text.find(alt_cid)
            
            if start_idx != -1:
                # Find the next control's start to define the chunk
                # Ideally we sort controls by their appearance, but PDF text might not be linear
                # We'll just grab a chunk of text (e.g., 2000 chars) or look for keywords
                
                # Extract a generous chunk
                chunk = full_text[start_idx:start_idx+3000]
                
                # Truncate at next control (heuristic)
                for other_cid in control_ids:
                    if other_cid != cid and other_cid in chunk[50:]: # Skip self
                        idx = chunk.find(other_cid)
                        if idx != -1:
                            chunk = chunk[:idx]
                            break
                            
                controls_dict[cid]['calibration_guide'] = clean_text(chunk)
                logger.info(f"Enriched Control {cid} with {len(chunk)} chars from PDF")
            else:
                logger.warning(f"Could not find PDF section for {cid}")
                
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")

    return controls_dict

def main():
    excel_path, pdf_path = find_files()
    
    if not excel_path or not pdf_path:
        logger.error("Missing Excel or PDF file.")
        return

    # 1. Parse Excel (The Source of Truth for IDs)
    controls = process_excel(excel_path)
    
    if not controls:
        logger.error("No controls extracted from Excel.")
        return

    # 2. Enrich with PDF content
    controls = process_pdf(pdf_path, controls)
    
    # 3. Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(controls, f, indent=2)
        
    logger.info(f"✅ Successfully exported {len(controls)} controls to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
