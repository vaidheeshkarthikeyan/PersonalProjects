# Book Reviews Sentiment Analysis

A Python/NLP project that classifies the sentiment of Amazon book reviews using both a lexicon-based approach (VADER) and a transformer-based approach (Hugging Face `pipeline`), so the two methods can be compared side by side.

## Overview

The notebook (`book_reviews.ipynb`) takes a small sample of book reviews, cleans and normalizes the text, then scores each review's sentiment two different ways:

1. **VADER** (Valence Aware Dictionary and sEntiment Reasoner) — a rule-based sentiment scorer well suited to short, informal text.
2. **Hugging Face Transformers** — a pretrained transformer sentiment-analysis pipeline for a deep-learning-based comparison.

## Dataset

`book_reviews_sample.csv` — 100 book reviews with the following columns:

| Column | Description |
|---|---|
| `index` | Original review index/ID |
| `reviewText` | Raw text of the review |
| `rating` | Star rating given by the reviewer (1–5) |

## Workflow

### 1. Text Cleaning & Preprocessing
- Lowercasing
- Stopword removal (NLTK English stopwords)
- Punctuation removal
- Tokenization (`nltk.word_tokenize`)
- Lemmatization (`WordNetLemmatizer`)

### 2. Sentiment Analysis — VADER
- Computes a compound polarity score for each cleaned review using `vaderSentiment`.
- Scores are bucketed into `negative`, `neutral`, and `positive` labels using threshold bins (`-1 to -0.1`, `-0.1 to 0.1`, `0.1 to 1`).
- Results are visualized as a bar chart of label counts.

### 3. Sentiment Analysis — Transformers
- Runs each cleaned review through Hugging Face's default `sentiment-analysis` pipeline.
- Produces a `POSITIVE`/`NEGATIVE` label per review.
- Results are visualized as a bar chart of label counts.

## Project Structure

```
Sentiment Analysis/
├── book_reviews.ipynb        # Main notebook: cleaning, VADER, transformer analysis
└── book_reviews_sample.csv   # Sample dataset (100 reviews)
```

## Requirements

```
pandas
numpy
nltk
spacy
vaderSentiment
transformers
```

Also download the required NLTK corpora before running:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

## Usage

1. Install dependencies:
   ```bash
   pip install pandas numpy nltk spacy vaderSentiment transformers
   ```
2. Open and run `book_reviews.ipynb` cell by cell (Jupyter Notebook / JupyterLab).
3. Review the two bar charts at the end of the notebook to compare VADER vs. transformer sentiment distributions.

## Possible Improvements

- Evaluate both methods against the `rating` column as ground truth (e.g., treat ratings ≥4 as positive, ≤2 as negative) to measure accuracy.
- Add a neutral class to the transformer pipeline output (default pipeline is binary) by swapping in a 3-class model.
- Expand beyond the 100-review sample to test scalability.
- Wrap the pipeline into a reusable script/function instead of a linear notebook.

## License

For personal/portfolio use.
