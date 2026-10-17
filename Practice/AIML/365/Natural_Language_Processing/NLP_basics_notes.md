# Natural Language Processing (NLP) Basics

NLP is a field of AI that allows computers to understand, interpret and generate human language data.

## Techniques involved

1. Statistics
2. Machine learning
3. Deep learning

## Why use NLP techniques

1. Save massive amounts of time working with text data.
2. Uncover insights that might previously have gone unnoticed.

## Supervised vs Unsupervised NLP

**Supervised:** Training an algorithm to learn the relationship between input (our data) and the output.

**Unsupervised:** Doesn't need labels.

## Data preparation

1. General cleaning
2. Removing noise from the dataset
3. Getting the data in the right format for the model to understand

---

## Setting up the environment

### Create a virtual environment with conda

conda is an environment and package manager.

1. Open Anaconda Prompt.
2. Create the environment:

   ```bash
   conda create --name env_name python==python_version
   ```

3. Activate it:

   ```bash
   conda activate env_name
   ```

### Install packages

`pip` is Python's built-in package installer.

```bash
pip install -r requirements.txt
```

Download the spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

Register the environment as a Jupyter kernel:

```bash
python -m ipykernel install --user --name=env_name
```

### Launch the notebook

1. Open Anaconda Navigator.
2. Select your kernel.
3. Install Jupyter Notebook.
4. Launch your notebook.

---

## What does each package do?

| Package | Version | What it does |
|---|---|---|
| **nltk** | 3.9.1 | The Natural Language Toolkit, one of the oldest and most widely used NLP libraries. Includes tokenizers (break text into words or sentences), stemmers and lemmatizers (simplify words to their base form), and access to large text collections and linguistic datasets. Great for learning and experimenting with NLP basics. |
| **pandas** | 2.2.3 | Provides the DataFrame structure, which makes it easy to load, clean, and organize data in rows and columns (similar to Excel, but much more powerful). Used to manipulate text datasets and combine them with other information. |
| **matplotlib** | 3.10.0 | The fundamental Python plotting library. Creates line charts, bar graphs, scatter plots, and more. Think of it as the "drawing canvas" for your data visualizations. |
| **seaborn** | 0.13.2 | Built on top of matplotlib, but with easier functions and nicer default styles. Especially good for statistical plots, like correlations between variables or distributions of data. |
| **scikit-learn** | 1.6.0 | A general-purpose machine learning toolkit. Provides algorithms for classification, regression, clustering, feature extraction, and model evaluation. Often used for building traditional ML models before moving on to deep learning. |
| **spaCy** | 3.8.3 | A modern NLP library designed for speed and production use. Handles advanced tasks like part-of-speech tagging (identifying nouns/verbs), named entity recognition (detecting people, places, organizations), and syntactic parsing. Faster and more practical than NLTK for large-scale projects. |
| **TextBlob** | 0.18.0.post0 | A beginner-friendly NLP library that wraps around NLTK and other tools. Makes common tasks like sentiment analysis, phrase extraction, and translation very simple with just a few lines of code. |
| **VADER Sentiment** | 3.3.2 | A lightweight, rule-based tool for sentiment analysis, tuned for short, casual texts like tweets, reviews, and comments. Understands things like exclamation marks, capitalization, and even emoji sentiment. |
| **gensim** | 4.3.3 | A library for topic modeling and working with word embeddings. Known for Word2Vec (learns word meanings from context) and LDA (Latent Dirichlet Allocation) for discovering hidden topics in large text collections. |
| **transformers** | 4.47.1 | From Hugging Face, the go-to library for using state-of-the-art NLP models like BERT, GPT, and other large language models. Makes it easy to load pretrained models for classification, text generation, and translation. |
| **PyTorch (torch)** | 2.5.1 | A deep learning framework that powers libraries like transformers. Used to build and train custom neural networks for NLP and beyond. Many cutting-edge AI models are implemented in PyTorch. |
| **ipywidgets** | 8.1.5 | Provides interactive controls (sliders, dropdowns, buttons) inside Jupyter notebooks. Lets you build small UIs that make experiments more visual and hands-on. |
| **NumPy** | <2.0.0 | The foundational library for numerical computing in Python. Introduces the `ndarray` object, which stores and processes large arrays and matrices efficiently. Behind almost every data science or machine learning library, it provides the fast, vectorized math that makes Python suitable for heavy computation. Used for matrix operations, statistical calculations, and data transformations that feed into models or visualizations. |

---

## Text cleaning and transformation

When preparing text for analysis or machine learning, we often perform several cleaning and transformation steps to make the text more uniform and easier to work with. Each step addresses a specific issue in raw text, from removing stopwords and punctuation to turning words into tokens and root forms.

### 1. Removing stopwords

```python
data['review_no_stopwords'] = data['review_lowercase'].apply(lambda x: ' '.join([word for word \
                               in x.split() if word \
                               not in (en_stopwords)]))
```

At first, it might look intimidating, but this code block is simply doing several small, logical steps one after another. It's written in one line to be compact, so let's break down what each part does and why it's there.

> **Note:** In Python, a backslash `\` at the end of a line means "this line of code continues on the next line." If a line is too long, or you want to break it for readability, put a `\` at the end and Python will treat the next line as part of the same command.

#### Step 1. Creating a new column

```python
data['review_no_stopwords'] = ...
```

Here, a new column is being created in the DataFrame called `data`. In the brackets, we specify the name of the new column, in this case `['review_no_stopwords']`.

Everything on the right-hand side is the result stored in this column. This lets us keep the processed version of the text without overwriting the original one.

#### Step 2. Selecting the column to transform

```python
data['review_lowercase']
```

This refers to the existing column that contains the lowercased text we want to process. We start from this column and apply a transformation to each of its entries. Because we store the result in a new column, `data['review_no_stopwords']`, the content of `['review_lowercase']` is never modified.

#### Step 3. Applying a function to each value

```python
.apply(lambda x: ...)
```

The `apply` function in pandas runs a given function on every element in a column. Here, that means it processes each text entry one by one.

The `lambda x:` part defines an anonymous function: a short, inline function that doesn't need a name because it's only used once. Each `x` represents a single text value from the column. We name it `x` to keep the code compact, but you can replace it with any valid variable name (for example `text`, `review`, or even `row`) and the code will work exactly the same way. `x` is just a variable name for each value that `apply` sends into the `lambda`.

Using a lambda lets us describe the transformation directly inside `apply`, without defining a separate function elsewhere.

#### Step 4. Inside the lambda function

This part defines what we want to do to each text entry:

```python
' '.join([word for word in x.split() if word not in (en_stopwords)])
```

Let's go through it from the inside out.

**1. Splitting the text**

```python
x.split()
```

This turns the text string into a list of individual words. We do this because we can't check or remove stopwords while the text is one long string. We need to work with separate words, and splitting lets us inspect and filter them individually.

**2. The list comprehension**

```python
[word for word in x.split() if word not in (en_stopwords)]
```

This is the heart of the operation. It builds a new list of words, but only keeps those that are **not** in the `en_stopwords` list.

Let's analyze the structure piece by piece:

- `word for word in x.split()` means: go through each word from the list created by `x.split()`. It's a loop written in compact form. Here, `word` is the loop variable, the name given to each element as the loop goes through them one by one. Any other name would work equally well. The only rule is that it must be the same name everywhere inside that comprehension, before and after the `for`.
- `if word not in (en_stopwords)` is a filtering condition. It checks every word and only keeps it if it's not found in the collection of stopwords. The condition is evaluated for each word one by one.

A list comprehension is just a shortened version of a regular `for` loop. Written in full, it would look like this:

```python
new_list = []
for word in x.split():
    if word not in en_stopwords:
        new_list.append(word)
```

In plain English, it reads: "Create a new list of `word`, for every `word` in `x.split()`, if that word is not in `en_stopwords`."

The list comprehension is essentially performing two actions at once:

1. Looping through every word in the text.
2. Selecting only those that meet the condition (not being a stopword).

We use a list comprehension because it's faster and more concise than a traditional `for` loop with `append()`, and it keeps the looping and filtering logic in a single readable structure.

**3. Joining the filtered words back**

```python
' '.join([...])
```

After filtering, we have a list of the remaining words, but the column expects text, not a list. So we join the words back together into one string, with spaces between them.

- The `' '` before `join` defines what goes between the words, in this case a single space.
- `join` is called on that space string, and the list of words is passed in as an argument.
- The result is a single text string, rebuilt from the filtered words.

#### Step 5. Why this works in one line

Each method and function in this line passes its result directly into the next one. Here's the logical chain:

1. Select the text column.
2. Apply a function to each entry.
3. Inside that function:
   - Split the text into words.
   - Filter out stopwords using a list comprehension.
   - Join the remaining words back into a string.
4. Store the final cleaned text in a new column.

Because every step produces a return value that can be used immediately by the next, the entire process can be written as a single continuous expression. In practice, this one-liner is compact but completely logical, and each part is connected by a clear flow of transformation.

#### Step 6. Key takeaways

- `apply` lets you process each value in a column individually.
- `lambda` creates a short inline function when defining a separate one isn't necessary.
- `split` prepares the text for word-level processing.
- The list comprehension both loops and filters efficiently in one step.
- `join` puts the filtered words back together into readable text.
- The entire line works as a chain of transformations, passing results from one step to the next.
