import json
from pathlib import Path
from utils.logger import logger
from utils.graceful_exit import on_exit


SCRIPT_DIR = Path(__file__).resolve().parent


def main():
    dictionaries_dir = SCRIPT_DIR.parent / "dictionaries"
    word_lists: dict[str, set[str]] = {}

    on_exit(
        lambda: export_word_lists(word_lists),
        message="Process interrupted. Saving word lists...",
    )

    generate_word_lists(dictionaries_dir, word_lists)
    export_word_lists(word_lists)


def generate_word_lists(
    dictionaries_dir: Path, word_lists: dict[str, set[str]]
) -> bool:
    """Generates word lists from parsed dictionaries."""
    for file_path in dictionaries_dir.glob("*/parsed/*.json"):
        logger.info(f"Processing file: {file_path}")

        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
            lang = data["meta"]["lang"]

            word_lists.setdefault(lang, set())

            for entry in data["entries"]:
                word_lists[lang].add(entry["word"])

    logger.info(f"Generated {len(word_lists)} word lists.")
    return True


def export_word_lists(word_lists: dict[str, set[str]]) -> bool:
    """Exports word lists to JSON files."""
    if not word_lists:
        logger.warning("No word lists to export.")
        return False

    output_dir = SCRIPT_DIR / "parsed"
    output_dir.mkdir(exist_ok=True)

    for lang, words in word_lists.items():
        output_path = output_dir / f"wordlist_{lang}.txt"
        with output_path.open("w", encoding="utf-8") as file:
            sorted_words = sorted(words)
            file.writelines("\n".join(sorted_words))

    logger.info(f"Word lists successfully exported to {output_dir}.")
    return True


if __name__ == "__main__":
    main()
