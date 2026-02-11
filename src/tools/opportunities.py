"""
Opportunities tools for retrieving co-selling opportunities from AWS Partner Central.
"""

import textwrap
import json
import logging
from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import ClientError
from strands.tools import tool
from src.config import (
    APN_AWS_PROFILE, 
    APN_AWS_ACCESS_KEY_ID, 
    APN_AWS_SECRET_ACCESS_KEY, 
    APN_AWS_SESSION_TOKEN,
    APN_AWS_REGION
)


@tool
def get_opportunities(
    max_results: int = 10,
    catalog: str = "AWS",
    status: str = None,
    keywords: str = "",
    days_back: int = 120,
    sort_by: str = "LastModifiedDate",
    sort_order: str = "DESCENDING",
    debug: bool = False
) -> str:
    """Retrieve your organization's co-selling opportunities from AWS Partner Central.
    
    Args:
        max_results: Max number of results to return (default: 10)
        catalog: Catalog to search ('AWS' or 'Sandbox', default: 'AWS')
        status: Filter by opportunity status (e.g., "ACTIVE", "WON", "LOST", "CLOSED", "Approved")
        keywords: Search keywords to filter by opportunity name or details
        days_back: Fetch opportunities modified within this many days (default: 120)
        sort_by: Field to sort by ('LastModifiedDate' or 'CreatedDate', default: 'LastModifiedDate')
        sort_order: Sort order ('ASCENDING' or 'DESCENDING', default: 'DESCENDING')
        debug: If True, show raw API response and available fields
    """
    try:
        if APN_AWS_ACCESS_KEY_ID and APN_AWS_SECRET_ACCESS_KEY:
            session = boto3.Session(
                aws_access_key_id=APN_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APN_AWS_SECRET_ACCESS_KEY,
                aws_session_token=APN_AWS_SESSION_TOKEN,
                region_name=APN_AWS_REGION
            )
            client = session.client("partnercentral-selling")
        elif APN_AWS_PROFILE:
            session = boto3.Session(profile_name=APN_AWS_PROFILE)
            client = session.client("partnercentral-selling")
        else:
            client = boto3.client("partnercentral-selling")
        
        # Calculate cutoff date for filtering
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff_iso = cutoff.isoformat(timespec="seconds").replace("+00:00", "Z")
        
        logging.info(f"Fetching up to {max_results} opportunities modified after {cutoff_iso}")
        
        params = {
            "Catalog": catalog,
            "MaxResults": min(100, max_results * 2),
            "LastModifiedDate": {"AfterLastModifiedDate": cutoff_iso},
            "Sort": {"SortBy": sort_by, "SortOrder": sort_order}
        }
        
        if status:
            params["Filters"] = {
                "Status": [status]
            }
        
        # Fetch opportunities
        opportunities = []
        next_token = None
        
        while True:
            if next_token:
                params["NextToken"] = next_token
            
            response = client.list_opportunities(**params)
            
            # Debug mode: show raw response structure
            if debug and not opportunities:  # Only show once
                lines = ["\n📋 DEBUG: API Response Structure\n"]
                lines.append(f"Response keys: {list(response.keys())}\n")
                
                if "Opportunities" in response:
                    if response["Opportunities"]:
                        lines.append(f"First opportunity keys: {list(response['Opportunities'][0].keys())}\n")
                        lines.append(f"Sample opportunity:\n{json.dumps(response['Opportunities'][0], indent=2, default=str)}\n")
                    else:
                        lines.append("Opportunities list is empty\n")
                
                if "OpportunitySummaries" in response:
                    if response["OpportunitySummaries"]:
                        lines.append(f"First summary keys: {list(response['OpportunitySummaries'][0].keys())}\n")
                        lines.append(f"Sample summary:\n{json.dumps(response['OpportunitySummaries'][0], indent=2, default=str)}\n")
                    else:
                        lines.append("OpportunitySummaries list is empty\n")
                
                return "\n".join(lines)
            
            # Try both possible response keys
            new_opps = response.get("Opportunities", response.get("OpportunitySummaries", []))
            opportunities.extend(new_opps)
            
            next_token = response.get("NextToken")
            if not next_token or len(opportunities) >= max_results * 3:
                break
        
        # Filter by keywords if provided
        if keywords:
            keywords_list = keywords.lower().split()
            filtered = []
            for opp in opportunities:
                project = opp.get("Project", {}) or {}
                customer_obj = opp.get("Customer", {}) or {}
                lifecycle = opp.get("LifeCycle", {}) or {}
                text = " ".join([
                    (project.get("Title") or project.get("Name") or "").lower(),
                    (project.get("DeliveryModels", [""])[0] if project.get("DeliveryModels") else "").lower(),
                    (lifecycle.get("Stage") or "").lower(),
                    (customer_obj.get("CompanyName") or "").lower(),
                    (opp.get("OpportunityType") or "").lower(),
                ])
                if all(k in text for k in keywords_list):
                    filtered.append(opp)
            opportunities = filtered
        
        opportunities = opportunities[:max_results]
        
        if not opportunities:
            msg = "No opportunities found."
            if status or keywords:
                msg += " Try adjusting filters."
            return msg
        
        lines = []
        lines.append(f"\n{'=' * 80}")
        lines.append(f"📊 Your Co-Selling Opportunities ({len(opportunities)} results)")
        lines.append(f"{'=' * 80}\n")
        
        # Show available fields from first opportunity for debugging
        if opportunities:
            first_opp = opportunities[0]
            lines.append(f"📋 Available fields: {', '.join(first_opp.keys())}\n")
        
        for idx, opp in enumerate(opportunities, 1):
            opp_id = opp.get("Id", "N/A")
            # Project is a nested object containing Title
            project = opp.get("Project", {}) or {}
            opp_name = project.get("Title") or project.get("Name") or f"Opportunity {opp_id}"
            # LifeCycle is a nested object containing Stage
            lifecycle = opp.get("LifeCycle", {}) or {}
            opp_status = lifecycle.get("Stage") or lifecycle.get("Status") or "Unknown"
            # Customer is a nested object
            customer_obj = opp.get("Customer", {}) or {}
            customer = customer_obj.get("CompanyName") or customer_obj.get("Account", {}).get("CompanyName") or "N/A"
            
            opp_type = opp.get("OpportunityType", "N/A")
            stage = lifecycle.get("Stage", "")
            created_date = opp.get("CreatedDate", "")
            last_modified = opp.get("LastModifiedDate", "")
            
            lines.append(f"[{idx}] {opp_name}")
            lines.append(f"    ID: {opp_id}")
            lines.append(f"    Status: {opp_status}")
            lines.append(f"    Customer: {customer}")
            if opp_type and opp_type != "N/A":
                lines.append(f"    Type: {opp_type}")
            
            if created_date:
                lines.append(f"    Created: {created_date}")
            if last_modified:
                lines.append(f"    Modified: {last_modified}")
            
            lines.append("")
        
        lines.append(f"{'=' * 80}\n")
        logging.info(f"Returned {len(opportunities)} opportunities")
        return "\n".join(lines)
    
    except ClientError as e:
        error = e.response.get("Error", {})
        logging.error(f"AWS error: {error.get('Message')}")
        return f"AWS Error: {error.get('Message')}\n(Check IAM: partnercentral-selling:ListOpportunities)"
    except Exception as e:
        logging.exception("Unexpected error fetching opportunities")
        return f"Error fetching opportunities: {str(e)}\n(Check IAM: partnercentral-selling:ListOpportunities)"


@tool
def get_opportunity_details(
    opportunity_id: str,
    catalog: str = "AWS"
) -> str:
    """Get detailed information about a specific co-selling opportunity.
    
    Args:
        opportunity_id: The ID of the opportunity (e.g., "O10841795")
        catalog: Catalog to use ('AWS' or 'Sandbox', default: 'AWS')
    """
    try:
        if APN_AWS_ACCESS_KEY_ID and APN_AWS_SECRET_ACCESS_KEY:
            session = boto3.Session(
                aws_access_key_id=APN_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APN_AWS_SECRET_ACCESS_KEY,
                aws_session_token=APN_AWS_SESSION_TOKEN,
                region_name=APN_AWS_REGION
            )
            client = session.client("partnercentral-selling")
        elif APN_AWS_PROFILE:
            session = boto3.Session(profile_name=APN_AWS_PROFILE)
            client = session.client("partnercentral-selling")
        else:
            client = boto3.client("partnercentral-selling")
        
        response = client.get_opportunity(
            Catalog=catalog,
            Identifier=opportunity_id
        )
        
        lines = []
        lines.append(f"\n{'=' * 80}")
        lines.append(f"📋 Opportunity Details: {opportunity_id}")
        lines.append(f"{'=' * 80}\n")
        
        # Basic info
        lines.append(f"ID: {response.get('Id', 'N/A')}")
        lines.append(f"ARN: {response.get('Arn', 'N/A')}")
        lines.append(f"Catalog: {response.get('Catalog', 'N/A')}")
        lines.append(f"Type: {response.get('OpportunityType', 'N/A')}")
        lines.append(f"Partner Opportunity ID: {response.get('PartnerOpportunityIdentifier', 'N/A')}")
        lines.append(f"National Security: {response.get('NationalSecurity', 'N/A')}")
        lines.append(f"Created: {response.get('CreatedDate', 'N/A')}")
        lines.append(f"Modified: {response.get('LastModifiedDate', 'N/A')}")
        
        # Primary Needs from AWS
        primary_needs = response.get('PrimaryNeedsFromAws', [])
        if primary_needs:
            lines.append(f"\n🎯 Primary Needs from AWS:")
            for need in primary_needs:
                lines.append(f"    • {need}")
        
        # LifeCycle
        lifecycle = response.get('LifeCycle', {}) or {}
        if lifecycle:
            lines.append(f"\n📊 Lifecycle:")
            lines.append(f"    Stage: {lifecycle.get('Stage', 'N/A')}")
            lines.append(f"    Target Close Date: {lifecycle.get('TargetCloseDate', 'N/A')}")
            lines.append(f"    Review Status: {lifecycle.get('ReviewStatus', 'N/A')}")
            if lifecycle.get('ReviewStatusReason'):
                lines.append(f"    Review Status Reason: {lifecycle.get('ReviewStatusReason')}")
            if lifecycle.get('ReviewComments'):
                lines.append(f"    Review Comments: {lifecycle.get('ReviewComments')}")
            if lifecycle.get('ClosedLostReason'):
                lines.append(f"    Closed Lost Reason: {lifecycle.get('ClosedLostReason')}")
            if lifecycle.get('NextSteps'):
                lines.append(f"    Next Steps: {lifecycle.get('NextSteps')}")
            # Next Steps History
            next_steps_history = lifecycle.get('NextStepsHistory', [])
            if next_steps_history:
                lines.append(f"    Next Steps History:")
                for step in next_steps_history[-3:]:  # Show last 3
                    lines.append(f"      - {step.get('Time', 'N/A')}: {step.get('Value', '')[:100]}")
        
        # Customer
        customer = response.get('Customer', {}) or {}
        if customer:
            lines.append(f"\n👤 Customer:")
            account = customer.get('Account', {}) or {}
            if account:
                lines.append(f"    Company: {account.get('CompanyName', 'N/A')}")
                lines.append(f"    Industry: {account.get('Industry', 'N/A')}")
                if account.get('OtherIndustry'):
                    lines.append(f"    Other Industry: {account.get('OtherIndustry')}")
                lines.append(f"    Website: {account.get('WebsiteUrl', 'N/A')}")
                if account.get('AwsAccountId'):
                    lines.append(f"    AWS Account ID: {account.get('AwsAccountId')}")
                if account.get('Duns'):
                    lines.append(f"    DUNS: {account.get('Duns')}")
                address = account.get('Address', {}) or {}
                if address:
                    addr_parts = [p for p in [address.get('StreetAddress'), address.get('City'), 
                                              address.get('StateOrRegion'), address.get('PostalCode'),
                                              address.get('CountryCode')] if p]
                    if addr_parts:
                        lines.append(f"    Address: {', '.join(addr_parts)}")
            
            # Customer Contacts
            contacts = customer.get('Contacts', [])
            if contacts:
                lines.append(f"    Contacts:")
                for contact in contacts:
                    name = f"{contact.get('FirstName', '')} {contact.get('LastName', '')}".strip() or "N/A"
                    title = contact.get('BusinessTitle', '')
                    email = contact.get('Email', '')
                    phone = contact.get('Phone', '')
                    lines.append(f"      • {name}" + (f" ({title})" if title else ""))
                    if email:
                        lines.append(f"        Email: {email}")
                    if phone:
                        lines.append(f"        Phone: {phone}")
        
        # Project
        project = response.get('Project', {}) or {}
        if project:
            lines.append(f"\n📁 Project:")
            lines.append(f"    Title: {project.get('Title', 'N/A')}")
            if project.get('CustomerUseCase'):
                lines.append(f"    Use Case: {project.get('CustomerUseCase')}")
            if project.get('CustomerBusinessProblem'):
                problem = project.get('CustomerBusinessProblem')
                if len(problem) > 300:
                    problem = problem[:297] + "..."
                lines.append(f"    Business Problem: {problem}")
            
            delivery_models = project.get('DeliveryModels', [])
            if delivery_models:
                lines.append(f"    Delivery Models: {', '.join(delivery_models)}")
            
            # Expected Customer Spend (list)
            expected_spend = project.get('ExpectedCustomerSpend', [])
            if expected_spend:
                lines.append(f"    Expected Customer Spend:")
                for spend in expected_spend:
                    amount = spend.get('Amount', 'N/A')
                    currency = spend.get('CurrencyCode', '')
                    freq = spend.get('Frequency', '')
                    target = spend.get('TargetCompany', '')
                    lines.append(f"      • {amount} {currency}" + (f" ({freq})" if freq else "") + (f" - {target}" if target else ""))
                    if spend.get('EstimationUrl'):
                        lines.append(f"        Estimation URL: {spend.get('EstimationUrl')}")
            
            # Sales Activities
            sales_activities = project.get('SalesActivities', [])
            if sales_activities:
                lines.append(f"    Sales Activities: {', '.join(sales_activities)}")
            
            # APN Programs
            apn_programs = project.get('ApnPrograms', [])
            if apn_programs:
                lines.append(f"    APN Programs: {', '.join(apn_programs)}")
            
            # Competition
            if project.get('CompetitorName'):
                lines.append(f"    Competitor: {project.get('CompetitorName')}")
            if project.get('OtherCompetitorNames'):
                lines.append(f"    Other Competitors: {project.get('OtherCompetitorNames')}")
            
            if project.get('RelatedOpportunityIdentifier'):
                lines.append(f"    Related Opportunity: {project.get('RelatedOpportunityIdentifier')}")
            if project.get('AdditionalComments'):
                lines.append(f"    Additional Comments: {project.get('AdditionalComments')[:200]}")
            if project.get('OtherSolutionDescription'):
                lines.append(f"    Other Solution: {project.get('OtherSolutionDescription')[:200]}")
        
        # Marketing
        marketing = response.get('Marketing', {}) or {}
        if marketing:
            lines.append(f"\n📣 Marketing:")
            lines.append(f"    AWS Funding Used: {marketing.get('AwsFundingUsed', 'N/A')}")
            if marketing.get('CampaignName'):
                lines.append(f"    Campaign Name: {marketing.get('CampaignName')}")
            lines.append(f"    Source: {marketing.get('Source', 'N/A')}")
            use_cases = marketing.get('UseCases', [])
            if use_cases:
                lines.append(f"    Use Cases: {', '.join(use_cases)}")
            channels = marketing.get('Channels', [])
            if channels:
                lines.append(f"    Channels: {', '.join(channels)}")
        
        # Software Revenue
        software_revenue = response.get('SoftwareRevenue', {}) or {}
        if software_revenue:
            lines.append(f"\n💰 Software Revenue:")
            lines.append(f"    Delivery Model: {software_revenue.get('DeliveryModel', 'N/A')}")
            value = software_revenue.get('Value', {}) or {}
            if value:
                lines.append(f"    Amount: {value.get('Amount', 'N/A')} {value.get('CurrencyCode', '')}")
            if software_revenue.get('EffectiveDate'):
                lines.append(f"    Effective Date: {software_revenue.get('EffectiveDate')}")
            if software_revenue.get('ExpirationDate'):
                lines.append(f"    Expiration Date: {software_revenue.get('ExpirationDate')}")
        
        # Related Entity Identifiers
        related = response.get('RelatedEntityIdentifiers', {}) or {}
        if related:
            lines.append(f"\n🔗 Related Entities:")
            solutions = related.get('Solutions', [])
            if solutions:
                lines.append(f"    Solutions: {', '.join(solutions)}")
            aws_products = related.get('AwsProducts', [])
            if aws_products:
                lines.append(f"    AWS Products: {', '.join(aws_products)}")
            marketplace_offers = related.get('AwsMarketplaceOffers', [])
            if marketplace_offers:
                lines.append(f"    Marketplace Offers: {', '.join(marketplace_offers)}")
            offer_sets = related.get('AwsMarketplaceOfferSets', [])
            if offer_sets:
                lines.append(f"    Marketplace Offer Sets: {', '.join(offer_sets)}")
        
        # Opportunity Team
        opp_team = response.get('OpportunityTeam', [])
        if opp_team:
            lines.append(f"\n👥 Opportunity Team:")
            for member in opp_team:
                name = f"{member.get('FirstName', '')} {member.get('LastName', '')}".strip() or "N/A"
                title = member.get('BusinessTitle', '')
                email = member.get('Email', '')
                phone = member.get('Phone', '')
                lines.append(f"    • {name}" + (f" ({title})" if title else ""))
                if email:
                    lines.append(f"      Email: {email}")
                if phone:
                    lines.append(f"      Phone: {phone}")
        
        lines.append(f"\n{'=' * 80}\n")
        return "\n".join(lines)
    
    except ClientError as e:
        error = e.response.get("Error", {})
        logging.error(f"AWS error: {error.get('Message')}")
        return f"AWS Error: {error.get('Message')}\n(Check IAM: partnercentral-selling:GetOpportunity)"
    except Exception as e:
        logging.exception("Unexpected error fetching opportunity details")
        return f"Error fetching opportunity details: {str(e)}"


@tool
def map_opportunities_to_solutions(
    max_results: int = 20,
    catalog: str = "AWS",
    days_back: int = 120,
    include_solution_details: bool = True
) -> str:
    """Map co-selling opportunities to their linked AWS Partner Solutions.
    
    This tool fetches opportunities and shows which solutions are linked to each.
    Only opportunities with linked solutions are included in the output.
    
    Args:
        max_results: Max number of opportunities to check (default: 20)
        catalog: Catalog to use ('AWS' or 'Sandbox', default: 'AWS')
        days_back: Fetch opportunities modified within this many days (default: 120)
        include_solution_details: If True, fetch and display solution names (default: True)
    """
    try:
        if APN_AWS_ACCESS_KEY_ID and APN_AWS_SECRET_ACCESS_KEY:
            session = boto3.Session(
                aws_access_key_id=APN_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APN_AWS_SECRET_ACCESS_KEY,
                aws_session_token=APN_AWS_SESSION_TOKEN,
                region_name=APN_AWS_REGION
            )
            client = session.client("partnercentral-selling")
        elif APN_AWS_PROFILE:
            session = boto3.Session(profile_name=APN_AWS_PROFILE)
            client = session.client("partnercentral-selling")
        else:
            client = boto3.client("partnercentral-selling")
        
        # Calculate cutoff date
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff_iso = cutoff.isoformat(timespec="seconds").replace("+00:00", "Z")
        
        # First, build a solution cache from list_solutions (this API we know works)
        solution_cache = {}
        if include_solution_details:
            try:
                sol_params = {"Catalog": catalog, "MaxResults": 100}
                sol_next_token = None
                while True:
                    if sol_next_token:
                        sol_params["NextToken"] = sol_next_token
                    sol_response = client.list_solutions(**sol_params)
                    for sol in sol_response.get("SolutionSummaries", []):
                        sol_id = sol.get("Id", "")
                        if sol_id:
                            solution_cache[sol_id] = {
                                "name": sol.get("Name", f"Solution {sol_id}"),
                                "status": sol.get("Status", "Unknown"),
                                "category": sol.get("Category", "N/A")
                            }
                    sol_next_token = sol_response.get("NextToken")
                    if not sol_next_token:
                        break
            except Exception as e:
                logging.warning(f"Could not fetch solutions list: {e}")
        
        # Get the list of opportunities
        params = {
            "Catalog": catalog,
            "MaxResults": min(100, max_results),
            "LastModifiedDate": {"AfterLastModifiedDate": cutoff_iso},
            "Sort": {"SortBy": "LastModifiedDate", "SortOrder": "DESCENDING"}
        }
        
        opportunities = []
        next_token = None
        
        while len(opportunities) < max_results:
            if next_token:
                params["NextToken"] = next_token
            
            response = client.list_opportunities(**params)
            new_opps = response.get("OpportunitySummaries", [])
            opportunities.extend(new_opps)
            
            next_token = response.get("NextToken")
            if not next_token:
                break
        
        opportunities = opportunities[:max_results]
        
        if not opportunities:
            return "No opportunities found."
        
        # For each opportunity, get full details to find linked solutions
        mappings = []
        
        for opp in opportunities:
            opp_id = opp.get("Id", "N/A")
            
            try:
                # Get full opportunity details
                opp_details = client.get_opportunity(
                    Catalog=catalog,
                    Identifier=opp_id
                )
                
                # Extract linked solutions
                related = opp_details.get("RelatedEntityIdentifiers", {}) or {}
                solution_ids = related.get("Solutions", [])
                
                if solution_ids:
                    # Get opportunity info
                    project = opp_details.get("Project", {}) or {}
                    lifecycle = opp_details.get("LifeCycle", {}) or {}
                    customer = opp_details.get("Customer", {}) or {}
                    account = customer.get("Account", {}) or {}
                    
                    opp_info = {
                        "id": opp_id,
                        "title": project.get("Title") or f"Opportunity {opp_id}",
                        "customer": account.get("CompanyName", "N/A"),
                        "stage": lifecycle.get("Stage", "N/A"),
                        "type": opp_details.get("OpportunityType", "N/A"),
                        "solutions": solution_ids
                    }
                    
                    # Add any solutions not in cache (for summary purposes)
                    for sol_id in solution_ids:
                        if sol_id not in solution_cache:
                            solution_cache[sol_id] = {
                                "name": f"Solution {sol_id}",
                                "status": "Unknown",
                                "category": "N/A"
                            }
                    
                    mappings.append(opp_info)
                    
            except Exception as e:
                logging.warning(f"Could not get details for opportunity {opp_id}: {e}")
                continue
        
        if not mappings:
            return "No opportunities with linked solutions found."
        
        # Format output
        lines = []
        lines.append(f"\n{'=' * 80}")
        lines.append(f"🔗 Opportunity-to-Solution Mapping ({len(mappings)} opportunities with solutions)")
        lines.append(f"{'=' * 80}\n")
        
        for idx, mapping in enumerate(mappings, 1):
            lines.append(f"[{idx}] {mapping['title']}")
            lines.append(f"    Opportunity ID: {mapping['id']}")
            lines.append(f"    Customer: {mapping['customer']}")
            lines.append(f"    Stage: {mapping['stage']} | Type: {mapping['type']}")
            lines.append(f"    Linked Solutions:")
            
            for sol_id in mapping['solutions']:
                if include_solution_details and sol_id in solution_cache:
                    sol = solution_cache[sol_id]
                    lines.append(f"      → {sol_id}: {sol['name']} ({sol['status']})")
                else:
                    lines.append(f"      → {sol_id}")
            
            lines.append("")
        
        # Summary
        lines.append(f"{'=' * 80}")
        lines.append(f"📊 Summary:")
        lines.append(f"    Total opportunities checked: {len(opportunities)}")
        lines.append(f"    Opportunities with solutions: {len(mappings)}")
        lines.append(f"    Unique solutions linked: {len(solution_cache)}")
        
        if solution_cache:
            lines.append(f"\n📦 Solutions referenced:")
            for sol_id, sol in solution_cache.items():
                lines.append(f"    • {sol_id}: {sol['name']}")
        
        lines.append(f"\n{'=' * 80}\n")
        return "\n".join(lines)
    
    except ClientError as e:
        error = e.response.get("Error", {})
        logging.error(f"AWS error: {error.get('Message')}")
        return f"AWS Error: {error.get('Message')}"
    except Exception as e:
        logging.exception("Unexpected error mapping opportunities to solutions")
        return f"Error: {str(e)}"
