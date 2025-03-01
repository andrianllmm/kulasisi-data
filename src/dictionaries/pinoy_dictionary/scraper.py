import argparse
import bs4
import json
import os
from datetime import datetime
from utils.logger import logger
from utils.fetch_page import fetch_page
from utils.graceful_exit import on_exit


SUPPORTED_LANGS = {
    "tgl": "Tagalog",
    "ceb": "Cebuano",
    "hil": "Hiligaynon",
    # "ilo": "Ilocano",
}
DEFINITION_LANG = "eng"
STARTING_LETTERS = "abcdeghijklmnoprstuwxyz"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    # Parse arguments
    argparser = argparse.ArgumentParser(
        description="Scrape dictionary entries from https://pinoydictionary.com."
    )
    argparser.add_argument(
        "-l",
        "--lang",
        choices=SUPPORTED_LANGS,
        default="tgl",
        help=f"The language to scrape (e.g., 'tgl', 'ceb'). Defaults to 'tgl'.",
    )
    args = argparser.parse_args()

    lang = args.lang

    # Main data store
    scraped_data: list[dict] = []

    # Handle graceful exit
    on_exit(
        lambda: export_scraped_data(lang, scraped_data),
        message="Process interrupted. Saving scraped data...",
    )

    scrape(lang, scraped_data)

    export_scraped_data(lang, scraped_data)


def scrape(lang: str, scraped_data: list[dict]) -> bool:
    """Scrapes dictionary entries."""
    for letter in STARTING_LETTERS:
        page_number = 1

        while True:
            logger.info(
                f"Scraping: {lang.upper()} - Letter: {letter.upper()} - Page {page_number}"
            )

            # Construct url
            base_url = f"https://{SUPPORTED_LANGS[lang].lower()}.pinoydictionary.com/list/{letter}/"
            url = f"{base_url}{page_number}/" if page_number > 1 else base_url

            # Get page
            response = fetch_page(url)

            # If there's no page left, goto the next letter
            if not response:
                break

            soup = bs4.BeautifulSoup(response, "html.parser")

            # Scrape entries
            entries: bs4.ResultSet[bs4.element.Tag] = soup.find_all(class_="word-group")
            if not entries:
                logger.info(
                    f"No entries found on page {page_number}. Moving to next letter."
                )
                break

            for entry in entries:
                if processed_entry := process_entry(entry):
                    scraped_data.append(processed_entry)

            page_number += 1

    logger.info(f"Scraping completed. Total entries collected: {len(scraped_data)}")
    return True


def process_entry(entry: bs4.element.Tag) -> dict | None:
    """Processes a dictionary entry."""
    try:
        word_element = entry.find(class_="word").find(class_="word-entry").find("a")
        definition_element = entry.find(class_="definition").find("p")

        word = word_element.text.strip()
        definition = str(definition_element)
        source_url = word_element.get("href")

        logger.info(f"Processing entry: {word}")

        return {
            "word": word,
            "definition": definition,
            "source": source_url,
        }

    except Exception as e:
        logger.error(
            f"Error processing entry for word '{entry.get('word', 'Unknown')}': {e}"
        )
        return None


def export_scraped_data(
    lang: str, scraped_data: list[dict], overwrite: bool = False
) -> bool:
    """Exports scraped data to a file."""
    if not scraped_data:
        logger.warning("No data to export.")
        return False

    current_date = datetime.now().strftime("%Y-%m-%d")

    output_dir = os.path.join(SCRIPT_DIR, "scraped")
    os.makedirs(output_dir, exist_ok=True)

    output_filename = (
        f"dictionary_{lang}_{DEFINITION_LANG}_{len(scraped_data)}_{current_date}.json"
    )
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
            "lang": lang,
            "definition_lang": DEFINITION_LANG,
            "date": current_date,
            "total_entries": len(scraped_data),
            "source_title": f"{SUPPORTED_LANGS[lang]} Pinoy Dictionary",
            "source_link": f"https://{SUPPORTED_LANGS[lang].lower()}.pinoydictionary.com",
        },
        "entries": scraped_data,
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
