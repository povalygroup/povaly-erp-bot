"""
Centralized workflow templates and configurations.

This file contains all bot commands, message templates, and workflow configurations.
You can easily add, modify, or remove features here.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class WorkflowTemplate:
    """Template for a workflow (task, support, etc.)"""
    name: str
    command: str
    description: str
    topic_id_config_key: str  # e.g., "TOPIC_TASK_ALLOCATION"
    fields: List[Dict[str, any]]
    requires_brand_selection: bool = False
    auto_delete_seconds: int = 20


# ============================================================================
# TASK ALLOCATION WORKFLOW
# ============================================================================

TASK_ALLOCATION_TEMPLATE = WorkflowTemplate(
    name="Task Allocation",
    command="/newtask",
    description="Create a new task with pre-filled template",
    topic_id_config_key="TOPIC_TASK_ALLOCATION",
    requires_brand_selection=True,
    auto_delete_seconds=20,
    fields=[
        {
            "name": "TICKET",
            "label": "Ticket ID",
            "required": True,
            "auto_generated": True,
            "help": "Auto-generated unique ticket ID"
        },
        {
            "name": "BRAND",
            "label": "Brand",
            "required": True,
            "auto_filled": True,
            "help": "Selected from brand list"
        },
        {
            "name": "TASK",
            "label": "Task Description",
            "required": False,
            "help": "Describe what needs to be done"
        },
        {
            "name": "ASSIGNEE",
            "label": "Assignee",
            "required": True,
            "format": "@username",
            "help": "Username with @ symbol"
        },
        {
            "name": "DEADLINE",
            "label": "Deadline",
            "required": False,
            "format": "DD MMM YYYY | HH:MM AM/PM GMT+6",
            "help": "Due date and time"
        },
        {
            "name": "RESOURCES",
            "label": "Resources",
            "required": False,
            "help": "Links, files, or references"
        }
    ]
)


# ============================================================================
# CORE OPERATIONS SUPPORT WORKFLOW
# ============================================================================

SUPPORT_TYPES = [
    {
        "id": "issue",
        "label": "Issue",
        "description": "Report a problem or blocker",
        "emoji": "🚨"
    },
    {
        "id": "clarification",
        "label": "Clarification",
        "description": "Ask for clarification on requirements",
        "emoji": "❓"
    },
    {
        "id": "technical",
        "label": "Technical",
        "description": "Technical help or guidance needed",
        "emoji": "🔧"
    },
    {
        "id": "coordination",
        "label": "Coordination",
        "description": "Need coordination with team/client",
        "emoji": "🤝"
    },
    {
        "id": "other",
        "label": "Other",
        "description": "Other support requests",
        "emoji": "💬"
    }
]

CORE_OPERATIONS_TEMPLATE = WorkflowTemplate(
    name="Core Operations Support",
    command="/support",
    description="Request help or report issues with ongoing tasks",
    topic_id_config_key="TOPIC_CORE_OPERATIONS",
    requires_brand_selection=False,
    auto_delete_seconds=20,
    fields=[
        {
            "name": "TYPE",
            "label": "Issue Type",
            "required": True,
            "options": SUPPORT_TYPES,
            "help": "Select the type of support needed"
        },
        {
            "name": "RELATED_TICKET",
            "label": "Related Ticket",
            "required": False,
            "format": "POV260401",
            "help": "Ticket ID if related to a specific task"
        },
        {
            "name": "SUMMARY",
            "label": "Summary",
            "required": True,
            "help": "Short description of the issue"
        },
        {
            "name": "DETAILS",
            "label": "Details",
            "required": True,
            "help": "Full explanation of the problem"
        },
        {
            "name": "EVIDENCE",
            "label": "Evidence",
            "required": False,
            "help": "Screenshot, link, or reference"
        },
        {
            "name": "EXPECTED_RESULT",
            "label": "Expected Result",
            "required": True,
            "help": "What outcome is needed"
        }
    ]
)


# ============================================================================
# REACTION WORKFLOWS
# ============================================================================

REACTION_WORKFLOWS = {
    "support": {
        "👀": {
            "action": "acknowledge",
            "description": "Admin acknowledged and working on it",
            "notify_user": False
        },
        "❤️": {
            "action": "resolve",
            "description": "Problem solved",
            "notify_user": True,
            "notification_message": "✅ **Your support request has been resolved!**\n\nYour problem is solved. You can continue your work now.\n\nIf you still need help, feel free to submit another /support request."
        }
    },
    "task": {
        "👍": {
            "action": "start_work",
            "description": "Start working on task",
            "state_transition": "ASSIGNED -> IN_PROGRESS"
        },
        "❤️": {
            "action": "submit_qa",
            "description": "Submit for QA review",
            "state_transition": "IN_PROGRESS -> PENDING_QA"
        },
        "👎": {
            "action": "reject",
            "description": "Reject and send back",
            "state_transition": "PENDING_QA -> IN_PROGRESS"
        },
        "🔥": {
            "action": "fire_exemption",
            "description": "Grant fire exemption (admin only)",
            "requires_permission": ["ADMINISTRATORS", "MANAGERS", "OWNERS"]
        }
    }
}


# ============================================================================
# BRAND CONFIGURATION
# ============================================================================

BRAND_MAPPINGS = {
    "vorosabazar": "VRB",
    "vorosabazaar": "VRB",
    "vorosa bajar": "VRB",
    "vorosabajaar": "VRB",
    "gsmaura": "GSM",
    "gsm aura": "GSM",
    "povaly": "POV",
    "pov": "POV",
}

BRAND_DISPLAY_NAMES = {
    "VRB": "VorosaBajar",
    "GSM": "GSMAura",
    "POV": "Povaly",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_workflow_template(command: str) -> Optional[WorkflowTemplate]:
    """Get workflow template by command name."""
    workflows = {
        "/newtask": TASK_ALLOCATION_TEMPLATE,
        "/support": CORE_OPERATIONS_TEMPLATE,
    }
    return workflows.get(command)


def get_all_workflows() -> List[WorkflowTemplate]:
    """Get all available workflow templates."""
    return [
        TASK_ALLOCATION_TEMPLATE,
        CORE_OPERATIONS_TEMPLATE,
    ]


def format_template(workflow: WorkflowTemplate, **kwargs) -> str:
    """
    Format a template with provided values.
    
    Args:
        workflow: WorkflowTemplate to format
        **kwargs: Field values (e.g., ticket="POV260401", brand="Povaly")
    
    Returns:
        Formatted template string
    """
    from datetime import datetime, timedelta
    
    lines = []
    for field in workflow.fields:
        field_name = field["name"]
        value = kwargs.get(field_name.lower(), "")
        
        # Special handling for DEADLINE field - add example
        if field_name == "DEADLINE" and not value:
            # Generate example deadline: today at 10:30 PM
            example_date = datetime.now()
            example_deadline = example_date.replace(hour=22, minute=30, second=0, microsecond=0)
            value = example_deadline.strftime("%d %b %Y | %I:%M %p GMT+6")
        
        # Format the line with # tag for TICKET and BRAND fields for searchability
        if field_name in ["TICKET", "BRAND"]:
            if value:
                lines.append(f"[{field_name}] #{value}")
            else:
                lines.append(f"[{field_name}] #")
        else:
            if value:
                lines.append(f"[{field_name}] {value}")
            else:
                lines.append(f"[{field_name}] ")
    
    return "\n".join(lines)


def get_field_help_text(workflow: WorkflowTemplate) -> str:
    """Generate help text for workflow fields."""
    lines = ["**Fill in:**"]
    
    for field in workflow.fields:
        if field.get("auto_generated") or field.get("auto_filled"):
            continue  # Skip auto-filled fields
        
        required = "✓" if field["required"] else "○"
        field_format = f" ({field['format']})" if field.get("format") else ""
        
        lines.append(f"{required} [{field['name']}]{field_format} - {field['help']}")
    
    return "\n".join(lines)
