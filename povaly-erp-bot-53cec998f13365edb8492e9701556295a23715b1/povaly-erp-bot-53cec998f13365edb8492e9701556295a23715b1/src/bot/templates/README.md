# Bot Workflow Templates Configuration

This directory contains all bot commands, templates, and workflow configurations in one centralized location.

## 📁 File Structure

```
src/bot/templates/
├── workflow_templates.py  # Main configuration file (EDIT THIS!)
├── __init__.py           # Exports
└── README.md            # This file
```

## 🎯 How to Add/Modify Workflows

### **Adding a New Command**

1. Open `workflow_templates.py`
2. Add your template configuration:

```python
MY_NEW_WORKFLOW_TEMPLATE = WorkflowTemplate(
    name="My Workflow",
    command="/mycommand",
    description="What this command does",
    topic_id_config_key="TOPIC_MY_TOPIC",  # From .env
    requires_brand_selection=False,
    auto_delete_seconds=20,
    fields=[
        {
            "name": "FIELD_NAME",
            "label": "Field Label",
            "required": True,
            "help": "Help text for users"
        },
        # Add more fields...
    ]
)
```

3. Register it in `get_workflow_template()`:

```python
def get_workflow_template(command: str) -> Optional[WorkflowTemplate]:
    workflows = {
        "/newtask": TASK_ALLOCATION_TEMPLATE,
        "/support": CORE_OPERATIONS_TEMPLATE,
        "/mycommand": MY_NEW_WORKFLOW_TEMPLATE,  # Add this
    }
    return workflows.get(command)
```

4. Add to `get_all_workflows()`:

```python
def get_all_workflows() -> List[WorkflowTemplate]:
    return [
        TASK_ALLOCATION_TEMPLATE,
        CORE_OPERATIONS_TEMPLATE,
        MY_NEW_WORKFLOW_TEMPLATE,  # Add this
    ]
```

### **Modifying Existing Workflows**

#### Change Template Fields:
```python
# In TASK_ALLOCATION_TEMPLATE or CORE_OPERATIONS_TEMPLATE
fields=[
    {
        "name": "NEW_FIELD",
        "label": "New Field",
        "required": True,
        "help": "Description"
    },
]
```

#### Change Auto-Delete Time:
```python
TASK_ALLOCATION_TEMPLATE = WorkflowTemplate(
    # ...
    auto_delete_seconds=30,  # Change from 20 to 30
)
```

#### Add/Remove Support Types:
```python
SUPPORT_TYPES = [
    {
        "id": "urgent",
        "label": "Urgent",
        "description": "Critical issue requiring immediate attention",
        "emoji": "🚨"
    },
    # Add more types...
]
```

### **Modifying Reactions**

```python
REACTION_WORKFLOWS = {
    "support": {
        "👀": {
            "action": "acknowledge",
            "notify_user": False
        },
        "✅": {  # Add new reaction
            "action": "in_progress",
            "notify_user": True,
            "notification_message": "Your request is being processed..."
        }
    }
}
```

### **Modifying Brands**

```python
BRAND_MAPPINGS = {
    "newbrand": "NBR",  # Add new brand
    "new brand": "NBR",
}

BRAND_DISPLAY_NAMES = {
    "NBR": "NewBrand",  # Add display name
}
```

## 📋 Available Workflows

### 1. Task Allocation (`/newtask`)
- **Purpose**: Create new tasks with pre-filled templates
- **Topic**: Task Allocation
- **Features**: Brand selection, auto-ticket generation
- **Fields**: TICKET, BRAND, TASK, ASSIGNEE, DEADLINE, RESOURCES

### 2. Core Operations Support (`/support`)
- **Purpose**: Request help or report issues
- **Topic**: Core Operations
- **Features**: Type selection, reaction-based resolution
- **Fields**: TYPE, RELATED_TICKET, SUMMARY, DETAILS, EVIDENCE, EXPECTED_RESULT

## 🔧 Field Configuration Options

```python
{
    "name": "FIELD_NAME",           # Field identifier (uppercase)
    "label": "Display Name",        # Human-readable name
    "required": True,               # Is this field required?
    "auto_generated": False,        # Auto-filled by bot?
    "auto_filled": False,           # Pre-filled from selection?
    "format": "@username",          # Expected format hint
    "help": "Help text",            # Description for users
    "options": [...]                # List of options (for selection)
}
```

## 🎨 Reaction Configuration

```python
{
    "action": "action_name",                    # Internal action identifier
    "description": "What this reaction does",   # Human description
    "notify_user": True,                        # Send DM to user?
    "notification_message": "Message text",     # DM content
    "state_transition": "FROM -> TO",           # State change
    "requires_permission": ["ROLE"]             # Required roles
}
```

## 💡 Tips

1. **Keep it organized**: Group related workflows together
2. **Use clear names**: Make field names self-explanatory
3. **Add help text**: Users will see this in templates
4. **Test changes**: Restart bot after modifications
5. **Document custom workflows**: Add comments for complex logic

## 🚀 Quick Examples

### Add a "Bug Report" workflow:
```python
BUG_REPORT_TEMPLATE = WorkflowTemplate(
    name="Bug Report",
    command="/bug",
    description="Report a bug",
    topic_id_config_key="TOPIC_CORE_OPERATIONS",
    fields=[
        {"name": "BUG_TYPE", "required": True, "help": "Type of bug"},
        {"name": "STEPS", "required": True, "help": "Steps to reproduce"},
        {"name": "EXPECTED", "required": True, "help": "Expected behavior"},
        {"name": "ACTUAL", "required": True, "help": "Actual behavior"},
    ]
)
```

### Add a new reaction:
```python
"support": {
    "⏳": {
        "action": "pending",
        "notify_user": True,
        "notification_message": "Your request is pending review..."
    }
}
```

## 📞 Need Help?

- Check existing templates for examples
- All templates follow the same structure
- Restart bot after changes: `run.bat`
