import sys

schema_question = {
    "name": "question",
    "description": "Ask the user a clarifying question to get more details or confirm decisions.",
    "parameters": {
        "type": "object",
        "properties": {
            "header": {
                "type": "string",
                "description": "Short label for the question (max 30 chars)",
            },
            "question": {
                "type": "string",
                "description": "The question to ask the user",
            },
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of choices to present to the user",
            },
            "multiple": {
                "type": "boolean",
                "description": "Allow selecting multiple options",
            },
        },
        "required": ["question"],
    },
}


def ask_question(
    working_directory, header=None, question=None, options=None, multiple=False
):
    if options is None:
        options = []

    output = []
    if header:
        output.append(f"\n{header}")
    output.append(question)

    if options:
        for i, opt in enumerate(options, 1):
            output.append(f"  {i}. {opt}")
        output.append("Type the number of your choice")
    else:
        output.append("Type your answer:")

    print("\n" + "\n".join(output) + "\n", file=sys.stdout)

    try:
        answer = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return "Cancelled"

    if not answer:
        return "No answer provided"

    if options:
        try:
            idx = int(answer) - 1
            if 0 <= idx < len(options):
                return options[idx]
            return f"Invalid choice: {answer}"
        except ValueError:
            for opt in options:
                if opt.lower() == answer.lower():
                    return opt
            return f"Unknown choice: {answer}"

    return answer
