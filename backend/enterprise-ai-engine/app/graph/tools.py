import logging
from typing import List, Any
from langchain_core.tools import tool, BaseTool

logger = logging.getLogger(__name__)

# --- 1. Customer Support Tools (scope="support") ---
@tool
def track_order(order_id: str) -> str:
    """
    Checks the shipping and tracking status of a customer order using the order identifier.
    Accessible to: support (all roles)
    """
    logger.info(f"Executing track_order tool for Order ID: {order_id}")
    # Simulating API payload response
    return f"Order {order_id} status: IN_TRANSIT. Expected delivery: July 28, 2026 via FedEx. Last checkpoint: Mumbai sorting facility."

@tool
def escalate_ticket(ticket_id: str, reason: str) -> str:
    """
    Escalates an unresolved support ticket to Tier 2 engineering.
    Accessible to: support (support_agent only)
    """
    logger.info(f"Executing escalate_ticket tool for Ticket ID: {ticket_id}")
    return f"Ticket {ticket_id} has been escalated to Tier 2 engineering. Reason: '{reason}'. Response SLA: 4 hours."


# --- 2. Sales Tools (scope="sales") ---
@tool
def get_pricing(plan_name: str) -> str:
    """
    Retrieves custom subscription pricing plans and tier information for ApexTech products.
    Accessible to: sales (all roles)
    """
    logger.info(f"Executing get_pricing tool for plan: {plan_name}")
    plans = {
        "starter": "Starter Plan: $29/month per seat. Includes basic analytics, single vector store, 10,000 documents.",
        "pro": "Pro Plan: $99/month per seat. Includes hybrid RRF search, 100,000 documents, Slack integration, SLA support.",
        "enterprise": "Enterprise Custom: Contact sales@apextech.internal for custom volume pricing, dedicated hosting, and multi-tenant isolation."
    }
    return plans.get(plan_name.lower(), f"Plan '{plan_name}' not found. Available plans: Starter, Pro, Enterprise.")

@tool
def request_discount(deal_id: str, discount_pct: str) -> str:
    """
    Submits a discount approval request for a custom B2B SaaS deal.
    Accessible to: sales (sales_rep only)
    """
    logger.info(f"Executing request_discount tool for Deal: {deal_id} (discount: {discount_pct}%)")
    try:
        pct = float(discount_pct)
    except ValueError:
        return f"Error: Discount request failed. 'discount_pct' must be a valid percentage number, got '{discount_pct}'."
        
    if pct > 15.0:
        return f"Discount request of {pct}% for Deal {deal_id} submitted. STATUS: PENDING. VP of Sales approval required for discounts exceeding 15%."
    return f"Discount of {pct}% for Deal {deal_id} has been AUTOMATICALLY APPROVED. Invoices updated."


# --- 3. HR Tools (scope="hr") ---
@tool
def request_pto(employee_name: str, days: str) -> str:
    """
    Submits a paid time off (PTO) leave request on behalf of an employee.
    Accessible to: hr (employee, hr_admin)
    """
    logger.info(f"Executing request_pto tool for: {employee_name} for {days} days")
    try:
        days_int = int(days)
    except ValueError:
        return f"Error: PTO request failed. 'days' must be a valid integer, got '{days}'."
    return f"PTO Request of {days_int} days for employee '{employee_name}' has been successfully submitted to Workday. Manager notified."

@tool
def update_record(employee_id: str, field: str, value: str) -> str:
    """
    Updates a specific field in an employee's HR profile record.
    Accessible to: hr (hr_admin only)
    """
    logger.info(f"Executing update_record tool for Employee ID: {employee_id}")
    return f"HR Record for Employee {employee_id} updated. Field '{field}' set to '{value}'."


# --- 4. IT Helpdesk Tools (scope="it") ---
@tool
def reset_password(username: str) -> str:
    """
    Triggers an IT Active Directory password reset sequence and sends a reset link.
    Accessible to: it (employee, it_admin)
    """
    logger.info(f"Executing reset_password tool for user: {username}")
    return f"Password reset email containing verification code sent to {username}@apextech.internal. Okta 2FA challenge triggered."

@tool
def elevate_db_access(username: str, db_name: str) -> str:
    """
    Requests temporary elevated write permissions to a production database.
    Accessible to: it (it_admin only)
    """
    logger.info(f"Executing elevate_db_access tool for {username} on DB {db_name}")
    return f"Temporary write permissions granted to user '{username}' on production DB '{db_name}'. Expiry: 1 hour. All commands will be audited via CloudTrail."


# --- Dynamic Tool Binding Helper ---
def get_authorized_tools(scope: str, role: str) -> List[BaseTool]:
    """
    Filters and returns the list of tools the caller is authorized to execute
    based on their current scope (domain) and role.
    """
    authorized_tools = []

    # Filter by scope
    if scope == "support":
        # Guest gets basic tracking
        authorized_tools.append(track_order)
        # Agent gets escalations
        if role == "support_agent":
            authorized_tools.append(escalate_ticket)
            
    elif scope == "sales":
        # Lead gets basic pricing
        authorized_tools.append(get_pricing)
        # Sales rep gets discounts
        if role == "sales_rep":
            authorized_tools.append(request_discount)
            
    elif scope == "hr":
        # Both employee and admin get PTO requests
        if role in ["employee", "hr_admin"]:
            authorized_tools.append(request_pto)
        # Only admin gets profile updates
        if role == "hr_admin":
            authorized_tools.append(update_record)
            
    elif scope == "it":
        # Both employee and admin get password reset
        if role in ["employee", "it_admin"]:
            authorized_tools.append(reset_password)
        # Only admin gets DB access elevation
        if role == "it_admin":
            authorized_tools.append(elevate_db_access)

    logger.info(f"Authorized tools for scope={scope}, role={role}: {[t.name for t in authorized_tools]}")
    return authorized_tools
