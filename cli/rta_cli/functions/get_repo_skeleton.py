from rta_cli.index.manager import BM25Indexer


def get_repo_skeleton(working_directory: str):
    """
    Returns a high-level map of the project's classes and functions.
    Useful for understanding the overall architecture.
    """
    try:
        indexer = BM25Indexer(working_directory)
        # Ensure skeleton is up to date
        indexer.index_project()
        return indexer.get_skeleton()
    except Exception as e:
        return f"Error getting repo skeleton: {e}"


schema_get_repo_skeleton = {
    "name": "get_repo_skeleton",
    "description": "Returns a markdown skeleton of the project, showing all classes and functions across all files. Use this to understand the codebase structure.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}
