"""
APN Solutions tool for retrieving Partner Solutions from AWS Partner Central.
"""

import textwrap
import logging
import boto3
from strands.tools import tool
from src.config import (
    APN_AWS_PROFILE, 
    APN_AWS_ACCESS_KEY_ID, 
    APN_AWS_SECRET_ACCESS_KEY, 
    APN_AWS_SESSION_TOKEN,
    APN_AWS_REGION
) # Ensure import is updated

@tool
def get_apn_solutions(
    max_results: int = 10,
    catalog: str = "AWS",
    categories: list = None,
    statuses: list = None,
    keywords: str = "",
    pillar: str = "",
    show_all_fields: bool = True
) -> str:
    """Retrieve your organization's registered AWS Partner Solutions from Partner Central.
    
    Args:
        max_results: Max number of results (default: 10)
        catalog: 'AWS' or 'Sandbox'
        categories: List of category filters
        statuses: List of status filters
        keywords: Search keywords
        pillar: Well-Architected pillar to filter by
        show_all_fields: If True, display all available fields from the API response
    """
    try:
        # Priority 1: Explicit Keys
        if APN_AWS_ACCESS_KEY_ID and APN_AWS_SECRET_ACCESS_KEY:
            session = boto3.Session(
                aws_access_key_id=APN_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APN_AWS_SECRET_ACCESS_KEY,
                aws_session_token=APN_AWS_SESSION_TOKEN,
                region_name=APN_AWS_REGION
            )
            client = session.client("partnercentral-selling")
        
        # Priority 2: Named Profile
        elif APN_AWS_PROFILE:
            session = boto3.Session(profile_name=APN_AWS_PROFILE)
            client = session.client("partnercentral-selling")
            
        # Priority 3: Default Chain
        else:
            client = boto3.client("partnercentral-selling")

        if pillar and not categories:
            pillar = pillar.lower().strip()
            pillar_to_categories = {
                "security": ["Security", "Identity & Access Management", "Encryption"],
                "reliability": ["Resilience", "Disaster Recovery", "Compute", "Storage"],
                "operational excellence": ["Management & Governance", "Monitoring", "Automation"],
                "performance efficiency": ["Compute", "Database", "Networking"],
                "cost optimization": ["Cost Management", "FinOps"],
                "sustainability": ["Sustainability"],
            }
            categories = pillar_to_categories.get(pillar, [])

        params = {
            "Catalog": catalog,
            "MaxResults": min(100, max_results * 2),
        }
        if categories:
            params["Category"] = categories
        if statuses:
            params["Status"] = statuses

        solutions = []
        next_token = None

        while True:
            if next_token:
                params["NextToken"] = next_token

            response = client.list_solutions(**params)
            new_solutions = response.get("SolutionSummaries", [])
            solutions.extend(new_solutions)

            next_token = response.get("NextToken")
            if not next_token or len(solutions) >= max_results * 3:
                break

        if keywords:
            keywords = keywords.lower().split()
            filtered = []
            for sol in solutions:
                text = " ".join([
                    (sol.get("Name") or "").lower(),
                    (sol.get("ShortDescription") or "").lower(),
                    " ".join(sol.get("Categories", [])).lower()
                ])
                if all(k in text for k in keywords):
                    filtered.append(sol)
            solutions = filtered

        solutions = solutions[:max_results]

        if not solutions:
            msg = "No matching Partner Solutions found."
            if categories or statuses or keywords or pillar:
                msg += " Try broadening filters."
            return msg

        # If show_all_fields is True and we have solutions, show what's available
        if show_all_fields and solutions:
            lines = ["📊 AVAILABLE FIELDS IN SOLUTION RESPONSE:\n"]
            first_sol = solutions[0]
            lines.append(f"Fields: {', '.join(first_sol.keys())}\n")
            lines.append("=" * 80 + "\n")
        else:
            lines = []
        
        for idx, sol in enumerate(solutions, 1):
            name = sol.get("Name", "Unnamed")
            sol_id = sol.get("Id", "N/A")
            status = sol.get("Status", "Unknown")
            # Handle both Category (string) and Categories (list) formats
            category = sol.get("Category", "N/A")
            if isinstance(category, list):
                cats = ", ".join(category) or "N/A"
            else:
                cats = category or "N/A"
            short_desc = (sol.get("ShortDescription") or "").strip()
            catalog_val = sol.get("Catalog", "")
            created_date = sol.get("CreatedDate", "")
            
            # Format solution header
            lines.append(f"\n{'=' * 80}")
            lines.append(f"[{idx}] {name}")
            lines.append(f"{'=' * 80}")
            lines.append(f"Status: {status} | Catalog: {catalog_val}")
            lines.append(f"ID: {sol_id}")
            lines.append(f"Category: {cats}")
            
            if created_date:
                lines.append(f"Created: {created_date}")
            
            # Display available fields if requested
            if show_all_fields:
                lines.append(f"\n📋 All available fields:")
                for key, value in sol.items():
                    if key not in ["Name", "Status", "Category", "Catalog", "Id", "CreatedDate"]:
                        if isinstance(value, list):
                            lines.append(f"  • {key}: {', '.join(map(str, value[:3]))}" + 
                                       (f" (+{len(value)-3} more)" if len(value) > 3 else ""))
                        elif isinstance(value, str):
                            if len(value) > 100:
                                lines.append(f"  • {key}: {value[:97]}...")
                            else:
                                lines.append(f"  • {key}: {value}")
                        else:
                            lines.append(f"  • {key}: {value}")
            else:
                # Normal display - show short description if available
                if short_desc:
                    if len(short_desc) > 200:
                        short_desc = short_desc[:197] + "..."
                    wrapped = textwrap.fill(
                        short_desc, width=76,
                        initial_indent="Description: ",
                        subsequent_indent="  "
                    )
                    lines.append(f"\n{wrapped}")
        
        lines.append(f"\n{'=' * 80}\n")
        return "\n".join(lines)

    except Exception as e:
        return f"Error fetching Partner Solutions: {str(e)}\n(Check IAM: partnercentral-selling:ListSolutions)"
