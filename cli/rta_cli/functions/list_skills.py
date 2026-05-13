from rta_cli.skills import list_available_skills

def list_skills(working_directory=None):
    """
    Returns a list of all globally installed skills with their descriptions.
    """
    skills = list_available_skills()
    if not skills:
        return "No skills found in ~/.rta/skills/"
    
    result = "Available Skills:\n"
    for s in skills:
        result += f"- {s['name']}: {s['description']}\n"
    return result

schema_list_skills = {
    "name": "list_skills",
    "description": "List all available specialized skills with their descriptions. Call this if you need domain-specific expertise not covered by your core instructions.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}
