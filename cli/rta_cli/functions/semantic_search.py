from rta_cli.index.manager import BM25Indexer


def semantic_search(working_directory: str, query: str, limit: int = 5):
    """
    Search codebase using natural language.
    Automatically indexes the project if not already done or if files changed.
    """
    try:
        indexer = BM25Indexer(working_directory)
        # Background indexing/update
        indexer.index_project()

        results = indexer.search(query, limit=limit)

        if not results:
            return "No relevant code found for query."

        formatted = []
        for res in results:
            formatted.append(
                f"--- {res['file_path']} (lines {res['start_line']}-{res['end_line']}) ---\n"
                f"{res['text']}\n"
            )

        return "\n".join(formatted)
    except Exception as e:
        return f"Error during semantic search: {e}"


schema_semantic_search = {
    "name": "semantic_search",
    "description": "Searches the codebase for relevant snippets using natural language semantic search. Useful when you don't know where a specific logic is located.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The natural language query (e.g., 'how is authentication handled?')",
            },
            "limit": {
                "type": "integer",
                "description": "Number of results to return (default 5)",
            },
        },
        "required": ["query"],
    },
}
