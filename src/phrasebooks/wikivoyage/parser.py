import argparse
import json
import os
import sys
from bs4 import BeautifulSoup
from utils.logger import logger
from utils.graceful_exit import on_exit


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    # Parse arguments
    argparser = argparse.ArgumentParser(
        description="Parse phrasebook entries from a JSON file scraped from https://pinoyphrasebook.com."
    )
    argparser.add_argument(
        "input_file",
        nargs="?",
        default=os.path.join(SCRIPT_DIR, "scraped", "scraped.json"),
        help="Path to the input JSON file. Defaults to `scraped/scraped.json`)",
    )
    args = argparser.parse_args()

    input_path = args.input_file
    raw_data, meta = import_raw_data(input_path)
    if not raw_data:
        logger.error(f"No raw data")
        sys.exit(1)

    # Main data store
    parsed_data: list[dict] = []

    # Handle graceful exit
    on_exit(
        lambda: export_parsed_data(parsed_data, meta),
        message="Process interrupted. Saving processed data...",
    )

    parse(raw_data, parsed_data)

    export_parsed_data(parsed_data, meta)


def parse(raw_data: list[dict], parsed_data: list[dict]) -> bool:
    """Parses phrasebook entries."""
    if not raw_data:
        logger.error("No data to process.")
        return False

    for entry in raw_data:
        if processed_entry := process_entry(entry):
            parsed_data.append(processed_entry)

    logger.info(f"Parsing completed for. Total entries collected: {len(parsed_data)}")
    return True


def process_entry(entry: dict[str, str]) -> dict | None:
    """Processes a phrasebook entry."""
    try:
        phrase = BeautifulSoup(entry.get("phrase", ""), "html.parser").get_text(
            strip=True
        )
        if not phrase or phrase.isspace():
            return None
        full_translation = BeautifulSoup(
            entry.get("translation", ""), "html.parser"
        ).get_text(strip=True)
        category = entry.get("category", "").lower()
        source = entry.get("source", "")

        logger.info(f"Processing entry: {phrase}")

        translations = (
            [
                {
                    "content": full_translation.strip(),
                }
            ]
            if full_translation
            else []
        )

        return {
            key: value
            for key, value in {
                "phrase": phrase,
                "categories": [category],
                "source_link": source,
                "translations": translations,
            }.items()
            if value
        }

    except Exception as e:
        logger.error(
            f"Error processing entry for phrase '{entry.get('phrase', 'Unknown')}': {e}"
        )
        return None


def import_raw_data(file_path: str) -> tuple[list[dict], dict]:
    """Loads data from a file."""
    logger.info(f"Loading data from {file_path}...")

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return [], {}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            meta = data["meta"]
            entries = data["entries"]
        logger.info(f"Successfully loaded {len(entries)} entries from {file_path}")
        return entries, meta
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return [], {}


def export_parsed_data(
    parsed_data: list[dict],
    meta: dict,
    overwrite: bool = False,
) -> bool:
    """Exports processed data to a file."""
    if not parsed_data:
        logger.warning("No data to export.")
        return False

    output_dir = os.path.join(SCRIPT_DIR, "parsed")
    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"phrases_{meta['lang']}_{meta['translation_lang']}_{meta['total_entries']}_{meta['date']}_parsed.json"
    output_path = os.path.join(output_dir, output_filename)

    if not overwrite:
        # Append counter to duplicate file names
        counter = 2
        base, ext = os.path.splitext(output_path)
        while os.path.exists(output_path):
            output_path = f"{base}_{counter}{ext}"
            counter += 1

    json_data = {
        "meta": {
            "lang": meta["lang"],
            "translation_lang": meta["translation_lang"],
            "source_title": meta["source_title"],
            "source_link": meta["source_link"],
        },
        "entries": parsed_data,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2, ensure_ascii=False)
        logger.info(f"Data successfully exported to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        return False


if __name__ == "__main__":
    main()
