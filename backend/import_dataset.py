import os
import pandas as pd
import math
import logging
from dotenv import load_dotenv
from rta_backend.db import get_supabase_client
from rta_backend.utils import Sanitizer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def estimate_tokens(text):
    if not text or not isinstance(text, str):
        return 0
    # Heuristic: ~4 characters per token
    return len(text) // 4

def import_excel_to_telemetry(file_path, user_id, batch_size=500, dry_run=True):
    """
    Imports codeforces dataset from Excel to Supabase telemetry.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return

    logger.info(f"Reading {file_path}...")
    try:
        # Load excel file
        df = pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        return

    # Expected columns: Question, Language, Solution Code
    # Mapping to lowercase for easier access
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Define mapping based on user description
    # Columns expected in Excel: 'question', 'language', 'solution code'
    col_map = {
        'question': 'ai_prompt',
        'solution code': 'ai_response',
        'language': 'language'
    }

    # Verify columns exist
    for col in col_map.keys():
        if col not in df.columns:
            logger.error(f"Missing required column in Excel: '{col}'")
            logger.info(f"Found columns: {list(df.columns)}")
            return

    records = []
    logger.info(f"Transforming {len(df)} rows...")

    for index, row in df.iterrows():
        prompt = str(row['question'])
        response = str(row['solution code'])
        lang = str(row['language'])

        record = {
            "user_id": user_id,
            "ai_prompt": prompt,
            "ai_response": response,
            "tokens_in": estimate_tokens(prompt),
            "tokens_out": estimate_tokens(response),
            "file_info": {
                "language": lang,
                "source": "codeforces_dataset_import",
                "import_index": index
            },
            "provider": "dataset",
            "model_used": "human_expert",
            "models_tried": ["human_expert"],
            "tokens_cached": 0,
            "tool_calls": "[]",
            "latency_ms": 0
        }
        records.append(record)

    if dry_run:
        logger.info("--- DRY RUN MODE ---")
        logger.info(f"Would import {len(records)} records.")
        if records:
            logger.info("Sample record (first row):")
            import json
            print(json.dumps(records[0], indent=2))
        logger.info("To actually import, run with --commit")
        return

    # Actual Import
    client = get_supabase_client()
    total = len(records)
    num_batches = math.ceil(total / batch_size)

    logger.info(f"Starting upload of {total} records in {num_batches} batches...")

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        try:
            client.table("telemetry").insert(batch).execute()
            logger.info(f"Uploaded batch {i//batch_size + 1}/{num_batches}")
        except Exception as e:
            logger.error(f"Failed to upload batch starting at index {i}: {e}")
            if input("Continue with next batch? (y/n): ").lower() != 'y':
                break

    logger.info("Import process completed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Import Excel dataset to Rta Telemetry")
    parser.add_argument("file", help="Path to the Excel file")
    parser.add_argument("--user_id", default="9d9e6129-e3f1-4932-b2d1-93d3f6a4a531", help="User ID to associate records with")
    parser.add_argument("--batch", type=int, default=500, help="Batch size for bulk insert")
    parser.add_argument("--commit", action="store_true", help="Actually perform the insert (defaults to dry-run)")

    args = parser.parse_args()

    # Load environment variables from .env
    load_dotenv()
    
    import_excel_to_telemetry(
        file_path=args.file,
        user_id=args.user_id,
        batch_size=args.batch,
        dry_run=not args.commit
    )
