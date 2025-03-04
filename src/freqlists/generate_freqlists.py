import csv
import sys
from pathlib import Path
from utils.logger import logger
from utils.graceful_exit import on_exit

csv.field_size_limit(sys.maxsize)

SCRIPT_DIR = Path(__file__).resolve().parent


def main():
    wordlists_dir = SCRIPT_DIR.parent / "wordlists" / "parsed"
    freq_lists: dict[str, dict[str, int]] = {}

    on_exit(
        lambda: export_freq_lists(freq_lists),
        message="Process interrupted. Saving frequency lists...",
    )

    generate_freq_lists(wordlists_dir, freq_lists)
    export_freq_lists(freq_lists)


def generate_freq_lists(
    wordlists_dir: Path, freq_lists: dict[str, dict[str, int]]
) -> bool:
    """Generate frequency lists from parsed word lists and existing frequency lists."""
    for file_path in wordlists_dir.glob("*.txt"):
        # Assumes filename format: <prefix>_<lang>.txt
        try:
            lang = file_path.stem.split("_")[1]
        except IndexError:
            logger.warning(
                f"Filename {file_path.name} does not match expected format. Skipping."
            )
            continue

        logger.info(f"Processing '{lang}' word list: {file_path}")

        freq_lists.setdefault(lang, {})

        with file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if word := line.strip().lower():
                    freq_lists[lang][word] = freq_lists[lang].get(word, 0) + 1

        apply_existing_freqlist(freq_lists, lang)

    logger.info(f"Generated {len(freq_lists)} frequency lists.")
    return True


def apply_existing_freqlist(freq_lists: dict[str, dict[str, int]], lang: str) -> bool:
    """Apply existing frequency list data from the Leipzig corpus."""
    dir = SCRIPT_DIR / "downloaded_data" / "leipzig"

    source_file = next(dir.glob(f"{lang}_*"), None)
    if source_file is None:
        logger.warning(f"No frequency list source file found for {lang}.")
        return False

    logger.info(f"Applying existing '{lang}' frequency list: {source_file}.")

    with source_file.open("r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter="\t")
        for row in reader:
            if len(row) < 2:
                continue

            word = row[1].lower()
            try:
                freq = int(row[-1])
            except ValueError:
                continue

            if word in freq_lists[lang]:
                freq_lists[lang][word] = freq_lists[lang].get(word, 0) + freq

    return True


def export_freq_lists(freq_lists: dict[str, dict[str, int]]) -> bool:
    """Export frequency lists to CSV files."""
    if not freq_lists:
        logger.warning("No word lists to export.")
        return False

    output_dir = SCRIPT_DIR / "parsed"
    output_dir.mkdir(exist_ok=True)

    for lang, words in freq_lists.items():
        output_path = output_dir / f"freqlist_{lang}.csv"
        with output_path.open("w", newline="") as output_file:
            writer = csv.writer(output_file)
            sorted_words = sorted(words.items(), key=lambda item: item[1], reverse=True)
            for word, freq in sorted_words:
                writer.writerow([word, freq])

    logger.info(f"Frequency lists exported to {output_dir}.")
    return True


if __name__ == "__main__":
    main()
