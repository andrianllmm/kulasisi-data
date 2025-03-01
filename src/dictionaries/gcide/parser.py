import argparse
import concurrent.futures
import json
import os
import string
from bs4 import BeautifulSoup
from html import unescape
from itertools import repeat
from utils.logger import logger
from utils.graceful_exit import on_exit


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
STARTING_LETTERS = set(string.ascii_lowercase)


def main():
    argparser = argparse.ArgumentParser(
        description="Parse dictionary entries from from GCIDE_XML."
    )
    argparser.add_argument(
        "input_dir",
        nargs="?",
        default=os.path.join(SCRIPT_DIR, "downloaded_data/gcide_xml-0.53/"),
        help="Path to the input directory. Defaults to `downloaded_data/gcide_xml-0.53/`.",
    )
    args = argparser.parse_args()

    input_dir = args.input_dir

    # Main data store
    parsed_data: list[dict] = []

    # Handle graceful exit
    on_exit(
        lambda: export_parsed_data(parsed_data),
        message="Process interrupted. Saving processed data...",
    )

    parse(parsed_data, input_dir)

    export_parsed_data(parsed_data)


def parse(parsed_data: list[dict], dir_path: str) -> bool:
    """Parses dictionary entries."""
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(process_letter, STARTING_LETTERS, repeat(dir_path))

        for result in results:
            parsed_data.extend(result)

    logger.info(f"Parsing completed. Total entries collected: {len(parsed_data)}")
    return True


def process_letter(letter: str, dir_path: str) -> list[dict]:
    """Processes dictionary entries that starts with a specified letter."""
    try:
        with open(os.path.join(dir_path, f"gcide_{letter}.xml")) as in_file:
            content = in_file.read()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return []

    soup = BeautifulSoup(content, "lxml")

    entries = soup.find_all("p")

    data = []

    for entry in entries:
        if new_entry := process_entry(entry):

            # New word
            if new_entry.get("word"):
                data.append(new_entry)

            # Previous word if word not present and there's a previous word
            elif len(data) >= 1:
                data[-1]["definitions"].extend(new_entry["definitions"])

    return data


def process_entry(entry: BeautifulSoup) -> dict:
    """Processes a dictionary entry."""
    try:
        # Find definitions
        word = None
        if word_xml := entry.find("ent"):
            word = word_xml.get_text(strip=True)
            logger.info(f"Processing entry: {word}")

        pos_xml = entry.find("pos")
        descriptions_xml = entry.find_all("def")
        origin_xml = entry.find("ety")
        synonyms_xml = entry.find("syn")
        antonyms_xml = entry.find("ant")
        sources_xml = entry.find_all("source")
        example_xml = entry.find("q") if entry.find("qex") else None

        # Convert and format definitions
        pos = pos_xml.get_text(strip=True) if pos_xml else None

        descriptions = (
            [unescape(d.get_text(strip=True)) for d in descriptions_xml]
            if descriptions_xml
            else []
        )

        origin = unescape(origin_xml.get_text().strip(" []")) if origin_xml else None

        synonyms = (
            [
                word.strip().lower()
                for word in synonyms_xml.get_text(strip=True)
                .replace("Syn. --", "")
                .split(",")
            ]
            if synonyms_xml
            else []
        )

        antonyms = (
            [
                word.strip().lower()
                for word in antonyms_xml.get_text(strip=True).split(";")
            ]
            if antonyms_xml
            else []
        )

        source = sources_xml[0].get_text(strip=True) if sources_xml else ""

        examples = [unescape(example_xml.get_text(strip=True))] if example_xml else []

        # Save definitions
        definitions = []
        for description in descriptions:
            definitions.append(
                {
                    key: value
                    for key, value in {
                        "description": description,
                        "pos": pos,
                        "origin": origin,
                        "synonyms": synonyms,
                        "antonyms": antonyms,
                        "examples": examples,
                        "source_title": source,
                    }.items()
                    if value
                }
            )

        return {"word": word, "definitions": definitions}

    except Exception as e:
        logger.error(f"Error processing entry for word: {e}")
        return None


def export_parsed_data(
    parsed_data: list[dict],
    overwrite: bool = False,
) -> bool:
    """Exports parsed data to a JSON file."""
    if not parsed_data:
        logger.warning("No data to export.")
        return

    # Sort entries by word (case-insensitive)
    parsed_data.sort(key=lambda entry: entry["word"].lower())

    output_dir = os.path.join(SCRIPT_DIR, "parsed")
    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"dictionary_eng_eng_{len(parsed_data)}.json"
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
            "lang": "eng",
            "definition_lang": "eng",
            "total_entries": len(parsed_data),
            "source_title": f"GCIDE",
            "source_link": f"https://ibiblio.org/webster/",
        },
        "entries": parsed_data,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2, ensure_ascii=False)
        logger.info(f"Data successfully exported to:\n{output_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to export data: {e}")
        return False


if __name__ == "__main__":
    main()
