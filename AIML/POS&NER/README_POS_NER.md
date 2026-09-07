# BBC News: POS Tagging & Named Entity Recognition

A Python/NLP project that applies Part-of-Speech (POS) tagging and Named Entity Recognition (NER) to BBC News headlines using spaCy, after cleaning and normalizing the text with NLTK.

## Overview

The notebook (`bbc_news.ipynb`) takes a set of BBC News article titles and:

1. Cleans and normalizes the text.
2. Tags each token with its part of speech (noun, verb, adjective, etc.) using spaCy.
3. Extracts named entities (people, organizations, locations, dates, etc.) from the titles.
4. Summarizes the most frequent POS tags and named entities found across the headlines.

## Dataset

`bbc_news.csv` — 1,000 BBC News articles with the following columns:

| Column | Description |
|---|---|
| `index` | Original article index/ID |
| `title` | Headline text (the field analyzed in this notebook) |
| `pubDate` | Publication date |
| `guid` | Article GUID/URL |
| `link` | RSS link to the article |
| `description` | Short article description |

## Workflow

### 1. Load Data
- Reads `bbc_news.csv` and isolates the `title` column for analysis.

### 2. Text Cleaning & Preprocessing
- Lowercasing
- Stopword removal (NLTK English stopwords)
- Punctuation removal
- Tokenization — both a "raw" (unfiltered) token set and a "clean" (stopwords/punctuation removed) token set
- Lemmatization (`WordNetLemmatizer`) on the clean tokens

### 3. POS Tagging
- Loads spaCy's `en_core_web_sm` model.
- Runs POS tagging on the **raw** (uncleaned) tokens, since word order and function words matter for accurate tagging.
- Counts token/tag frequency and pulls out the top 10 most common **nouns**, **verbs**, and **adjectives** across all headlines.

### 4. Named Entity Recognition (NER)
- Uses the same spaCy document to extract named entities (`spacy_doc.ents`).
- Builds a frequency table of entity text + entity type (e.g., `PERSON`, `ORG`, `GPE`, `DATE`), sorted by count.

## Project Structure

```
POS&NER/
├── bbc_news.ipynb   # Main notebook: cleaning, POS tagging, NER
└── bbc_news.csv     # Dataset (1,000 BBC News headlines + metadata)
```

## Requirements

```
pandas
nltk
spacy
matplotlib
```

Also required:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

```bash
python -m spacy download en_core_web_sm
```

## Usage

1. Install dependencies:
   ```bash
   pip install pandas nltk spacy matplotlib
   python -m spacy download en_core_web_sm
   ```
2. Open and run `bbc_news.ipynb` cell by cell (Jupyter Notebook / JupyterLab).
3. Review the top-10 noun/verb/adjective tables and the named-entity frequency table produced at the end.

## Possible Improvements

- Visualize POS and NER frequency tables as bar charts (currently only shown as DataFrames).
- Run POS/NER on the full `description` field as well, not just titles, for richer context.
- Group NER results by entity type to see which categories (people, places, orgs) dominate the headlines.
- Track POS/NER trends over time using the `pubDate` field.

## License

For personal/portfolio use.
