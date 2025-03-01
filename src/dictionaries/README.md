# Dictionaries

This folder contains the dictionary data, scrapers, and parsers.

## Data Format

### JSON Dictionary

```json
{
  "meta": {
    "lang": "ISO 639-3 code",
    "definition_lang": "ISO 639-3 code",
    "source_title": "Default source title for the dictionary",
    "source_link": "Default source URL for the dictionary"
  },
  "entries": [
    {
      "word": "Word",
      "source_title": "Source title for the word",
      "source_link": "Source URL for the word",
      "definitions": [
        {
          "description": "Description of the word",
          "pos": "Universal POS tag (https://universaldependencies.org/u/pos/)",
          "origin": "Origin of the word",
          "usage_note": "Usage of the word",
          "synonyms": [
            "Words similar to the word (must be present in the dictionary)"
          ],
          "antonyms": [
            "Words opposite to the word (must be present in the dictionary)"
          ],
          "inflections": [
            "Inflected forms of the word (must be present in the dictionary)"
          ],
          "examples": ["Example sentences of the word."],
          "source_title": "Source title for the definition",
          "source_link": "Source URL for the definition"
        }
      ]
    }
  ]
}
```

## Sources

- [GCIDE](https://ibiblio.org/webster/)
- [Pinoy Dictionary](https://pinoydictionary.com/)
