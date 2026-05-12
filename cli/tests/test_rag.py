import sys
import os
sys.path.append(os.path.abspath("cli"))

from rta_cli.functions.semantic_search import semantic_search

workspace = os.path.abspath(".")
# Search for something known in the codebase
query = "How are credentials stored and obfuscated?"
result = semantic_search(workspace, query, limit=2)
print(result)
