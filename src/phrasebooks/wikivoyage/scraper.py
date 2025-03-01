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
SOURCE_LANG = "eng"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    # Parse arguments
    argparser = argparse.ArgumentParser(
        description="Scrape phrasebook entries from https://wikivoyage.org."
    )
    argparser.add_argument(
        "-l",
        "--lang",
        choices=SUPPORTED_LANGS.keys(),
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


def scrape(lang: str, scraped_data: list) -> bool:
    """Scrapes phrasebook entries."""
    # Construct url
    url = f"https://en.wikivoyage.org/wiki/{SUPPORTED_LANGS[lang].capitalize()}_phrasebook"

    # Get page
    response = fetch_page(url)

    if not response:
        print(f"Failed to fetch {url}")
        return False

    soup = bs4.BeautifulSoup(response, "html.parser")

    # Find the phrase list section
    phrase_list_section = soup.find("h2", {"id": "Phrase_list"}).find_parent("section")
    if not phrase_list_section:
        print(f"No phrase list found for {lang}.")
        return False

    # Iterate through each sub-section within the phrase list
    sections: list[bs4.element.Tag] = phrase_list_section.find_all("section")
    for section in sections:
        category_heading = section.find("h3")
        category = (
            category_heading.get_text(strip=True).lower()
            if category_heading
            else "general"
        )

        logger.info(f"Processing section: {category}")

        # Extract terms and translations from data list (dl) tags
        data_lists: list[bs4.element.Tag] = section.find_all("dl", recursive=False)
        for dl in data_lists:
            dts: list[bs4.element.Tag] = dl.find_all("dt")
            dds: list[bs4.element.Tag] = dl.find_all("dd")

            for dt, dd in zip(dts, dds):
                phrase = str(dt)
                translation = str(dd)

                entry = {
                    "phrase": phrase,
                    "translation": translation,
                    "category": category,
                    "source": f"{url}#{category.capitalize().replace(' ', '_')}",
                }

                scraped_data.append(entry)

    return True


def export_scraped_data(lang: str, scraped_data: list, overwrite: bool = False):
    """Exports scraped data to a JSON file."""
    if not scraped_data:
        logger.warning("No data to export.")
        return

    current_date = datetime.now().strftime("%Y-%m-%d")

    output_dir = os.path.join(SCRIPT_DIR, "scraped")
    os.makedirs(output_dir, exist_ok=True)

    output_filename = (
        f"phrasebook_{SOURCE_LANG}_{lang}_{len(scraped_data)}_{current_date}.json"
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
            "lang": SOURCE_LANG,
            "translation_lang": lang,
            "date": current_date,
            "total_entries": len(scraped_data),
            "source_title": f"{SUPPORTED_LANGS[lang]} Wikivoyage Phrasebook",
            "source_link": f"https://en.wikivoyage.org/wiki/{SUPPORTED_LANGS[lang].capitalize()}_phrasebook",
        },
        "entries": scraped_data,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2, ensure_ascii=False)
        logger.info(f"Data successfully exported to:\n{output_path}")
    except IOError as e:
        logger.error(f"Failed to export data: {e}")


if __name__ == "__main__":
    main()
