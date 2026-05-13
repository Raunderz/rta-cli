from rta_cli.skills import load_skill_content, has_hidden_content

def activate_skill(working_directory, name, allow_hidden=False):
    """
    Load the instructions for a specific skill.
    """
    content = load_skill_content(name)
    if not content:
        return f"Error: Skill '{name}' not found."
    
    if has_hidden_content(content) and not allow_hidden:
        return f"Error: Skill '{name}' contains hidden HTML comments which could be malicious. (HIDDEN_CONTENT_PERMISSION_REQUIRED)"
    
    return f"<activated_skill name=\"{name}\">\n{content}\n</activated_skill>"

schema_activate_skill = {
    "name": "activate_skill",
    "description": "Loads the detailed instructions and specialized workflows for a specific skill into your context.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The unique name of the skill to activate.",
            },
        },
        "required": ["name"],
    },
}
