# 📝 Text Preprocessing for Hotel Reviews (NLP)

A step-by-step Natural Language Processing (NLP) pipeline to clean and preprocess hotel reviews. This project demonstrates the core text preprocessing techniques used before applying any machine learning or NLP model.

---

## 📌 Overview

Raw text data is often messy and inconsistent. Before training any NLP model (sentiment analysis, topic modeling, etc.), the text needs to be cleaned and normalized. This notebook walks through a complete preprocessing pipeline applied to real-world hotel review data.

---

## 📂 Dataset

| Property | Details |
|----------|---------|
| **File** | `tripadvisor_hotel_reviews.csv` |
| **Column used** | `Review` |


---

## 🛠️ Tech Stack

| Tool / Library | Purpose |
|----------------|---------|
| `Python` | Core programming language |
| `pandas` | Data loading and manipulation |
| `nltk` | NLP utilities (tokenization, stemming, lemmatization) |
| `re` | Regular expressions for punctuation removal |

---

## 🔄 Preprocessing Pipeline

The notebook applies the following steps in sequence, creating a new column for each transformation:

### 1. 🔡 Lowercasing
Converts all review text to lowercase to ensure uniformity.
```python
data['Review_lowercase'] = data['Review'].str.lower()
```

---

### 2. 🚫 Stopword Removal
Removes common English stopwords (e.g., *"the"*, *"is"*, *"at"*) that carry little meaning.

> **Note:** The word `"not"` is intentionally **kept** in the list, as it carries important sentiment meaning (e.g., *"not good"* vs *"good"*).

```python
en_stopwords = stopwords.words('english')
en_stopwords.remove('not')
```

---

### 3. ✂️ Punctuation Removal (via Regex)
Uses Regular Expressions to remove punctuation. The `*` symbol is first replaced with the word `"star"` to preserve its meaning before all other punctuation is removed.

```python
# Replace * with "star"
re.sub(r"[*]", " star", ...)

# Remove all remaining punctuation
re.sub(r"([^\w\s])", "", ...)
```

---

### 4. 🔤 Tokenization
Splits each review into individual words (tokens) using NLTK's `word_tokenize()`.

```python
data['tokenized_review'] = data.apply(lambda x: word_tokenize(x['Review_no_punc']), axis=1)
```

---

### 5. 🌱 Stemming
Reduces words to their root form using **Porter Stemmer** (e.g., *"running"* → *"run"*). Stemming is aggressive and may produce non-dictionary words.

```python
ps = PorterStemmer()
data['stemmed_review'] = data['tokenized_review'].apply(lambda tokens: [ps.stem(token) for token in tokens])
```

---

### 6. 📖 Lemmatization
Reduces words to their base dictionary form using **WordNet Lemmatizer** (e.g., *"better"* → *"good"*). More accurate than stemming.

```python
lemmatizer = WordNetLemmatizer()
data['lemmatized_review'] = data['tokenized_review'].apply(lambda tokens: [lemmatizer.lemmatize(token) for token in tokens])
```

---

### 7. 📊 N-gram Analysis
After preprocessing, all tokens are combined into one list and analyzed for word frequency using **unigrams** (single words) and **bigrams** (two-word pairs).

```python
tokens_clean = sum(data['lemmatized_review'], [])

unigrams = pd.Series(nltk.ngrams(tokens_clean, 1)).value_counts()
bigrams  = pd.Series(nltk.ngrams(tokens_clean, 2)).value_counts()
```

---

## 📋 Column Progression

| Column | Description |
|--------|-------------|
| `Review` | Original raw review text |
| `Review_lowercase` | Lowercased text |
| `Review_no_stopwords` | Stopwords removed |
| `Review_no_punc` | Punctuation removed |
| `tokenized_review` | List of tokens |
| `stemmed_review` | Stemmed tokens |
| `lemmatized_review` | Lemmatized tokens |

---

## 🚀 How to Run

1. Clone the repository and navigate to the project folder.
2. Install the required dependencies:
   ```bash
   pip install nltk pandas
   ```
3. Download the required NLTK data:
   ```python
   import nltk
   nltk.download('stopwords')
   nltk.download('punkt')
   nltk.download('wordnet')
   ```
4. Place the `tripadvisor_hotel_reviews.csv` file in the same directory as the notebook.
5. Open and run the notebook:
   ```bash
   jupyter notebook Text_preprocessing.ipynb
   ```

---

## 💡 Key Concepts

- **Stopword Removal** — Filters out high-frequency, low-meaning words to reduce noise.
- **Stemming vs Lemmatization** — Stemming is faster but cruder; lemmatization is slower but produces real words.
- **N-grams** — Captures word co-occurrence patterns; bigrams like *"great location"* give more context than individual words.
- **`apply()` function** — Used throughout to apply custom transformations row-by-row on DataFrame columns.

---

## 📁 Project Structure

```
📦 AIML/
 ┗ 📓 Text_preprocessing.ipynb
 ┗ 📄 tripadvisor_hotel_reviews.csv
 ┗ 📄 README.md
```
