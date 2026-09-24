# Fake News Classifier

An NLP project that explores linguistic differences between fake and factual news articles (POS tags, named entities, sentiment, and topics), then builds and evaluates machine learning classifiers to predict whether an article is fake or factual.

## Overview

The notebook (`fake_news_classifier.ipynb`) works through a full mini-pipeline:

1. **Exploratory linguistic analysis** — compares fake vs. factual articles on POS tag usage and named entities.
2. **Text preprocessing** — cleans article text for modeling.
3. **N-gram analysis** — most common unigrams/bigrams after cleaning.
4. **Sentiment analysis** — VADER sentiment scores compared across fake vs. factual articles.
5. **Topic modelling** — LDA and LSA topic models (with coherence-score tuning) on fake news text.
6. **Classification** — Logistic Regression and SGD (linear SVM) classifiers trained on a bag-of-words representation to predict fake vs. factual.

## Dataset

`fake_news_data.csv` — 198 news articles:

| Column | Description |
|---|---|
| `title` | Article headline |
| `text` | Full article body text |
| `date` | Publication date |
| `fake_or_factual` | Label: `Fake News` or `Factual News` (98 / 100 split) |

## Workflow

### 1. POS Tagging (Fake vs. Factual)
- Loads spaCy's `en_core_web_sm` model and runs it over the fake and factual article texts separately.
- Extracts `(token, ner_tag, pos_tag)` for every token via `nlp.pipe`.
- Compares the most frequent tokens/POS categories (e.g., top nouns) between the two classes.

### 2. Named Entities (Fake vs. Factual)
- Extracts named entities per class and counts frequency by `(token, ner_tag)`.
- Visualizes the top 10 named entities for fake and factual news as horizontal bar charts, colored by entity type (`ORG`, `GPE`, `NORP`, `PERSON`, `DATE`, `CARDINAL`, `PERCENT`).

### 3. Text Preprocessing
- Strips leading "source - " style prefixes from article text.
- Lowercasing, punctuation removal, stopword removal (NLTK).
- Tokenization and lemmatization.
- Unigram/bigram frequency analysis on the cleaned tokens, visualized as bar charts.

### 4. Sentiment Analysis
- Scores each article's raw text with VADER's compound sentiment score.
- Buckets scores into `negative` / `neutral` / `positive` using threshold bins.
- Compares sentiment label distribution overall and split by `fake_or_factual`.

### 5. Topic Modelling
- Builds a Gensim dictionary and bag-of-words corpus from the cleaned fake-news tokens.
- Fits LDA models across a range of topic counts (2–11) and plots coherence scores (`c_v`) to help pick the best number of topics.
- Fits a final LDA model (7 topics) and prints the top words per topic.
- Repeats the process with an LSA (`LsiModel`) model on a TF-IDF-weighted corpus for comparison.

### 6. Classification Model
- Builds a bag-of-words feature matrix (`CountVectorizer`) from the cleaned article text.
- Splits into train/test sets (70/30).
- Trains and evaluates two classifiers:
  - **Logistic Regression**
  - **SGDClassifier** (linear SVM via stochastic gradient descent)
- Reports accuracy and a full classification report (precision/recall/F1) for each model.

## Project Structure

```
Fake News Classifier/
├── fake_news_classifier.ipynb   # Main notebook: EDA, POS/NER, sentiment, topic modelling, classification
└── fake_news_data.csv           # Dataset (198 labeled news articles)
```

## Requirements

```
pandas
numpy
matplotlib
seaborn
spacy
nltk
vaderSentiment
gensim
scikit-learn
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
   pip install pandas numpy matplotlib seaborn spacy nltk vaderSentiment gensim scikit-learn
   python -m spacy download en_core_web_sm
   ```
2. Open and run `fake_news_classifier.ipynb` cell by cell (Jupyter Notebook / JupyterLab).
3. Review the POS/NER comparison charts, sentiment breakdown, topic model outputs, and final classifier metrics (accuracy + classification report) at the end.

## Possible Improvements

- Replace bag-of-words with TF-IDF or embedding-based features for classification.
- Add cross-validation instead of a single train/test split for more robust accuracy estimates.
- Try additional classifiers (Random Forest, gradient boosting, or a fine-tuned transformer) and compare against the current baselines.
- Use the topic modelling results (LDA/LSA topics) as engineered features for the classifier.
- Expand the dataset beyond 198 articles to improve generalization.

## License

For personal/portfolio use.
