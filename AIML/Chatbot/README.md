# Poetic Chatbot (Gemini + LangChain RAG)

A two-part chatbot project built on Google's Gemini API: a freeform "poetic chatbot" that answers any question in verse, and a Retrieval-Augmented Generation (RAG) chatbot built with LangChain that answers questions grounded in the content of a specific webpage.

## Overview

The notebook (`chatbot.ipynb`) has two sections:

1. **Poetic Chatbot** — a simple conversational chatbot using the Gemini API directly, instructed via a system prompt to always respond in poetic form, seeded with a couple of example exchanges for style.
2. **LangChain RAG Chatbot** — a retrieval-augmented chatbot that loads a webpage, splits it into chunks, embeds it with Gemini embeddings, stores it in a FAISS vector store, and answers questions using only the retrieved context plus running chat history.

## How It Works

### 1. Poetic Chatbot
- Connects to the Gemini API (`gemini-3.5-flash`) via the `google-genai` SDK.
- Sets a system instruction (`"You are a poetic chatbot."`) and seeds the chat history with two example Q&A pairs so the model reliably answers in verse.
- `poetic_chatbot(prompt)` starts/continues a chat session and returns the model's poetic response to any prompt.

### 2. LangChain RAG Chatbot
- **Load**: `WebBaseLoader` pulls the content of a target webpage (in this notebook, the 365 Data Science "upcoming courses" page).
- **Split**: `RecursiveCharacterTextSplitter` breaks the page into manageable text chunks.
- **Embed & Store**: Each chunk is embedded using Gemini's `gemini-embedding-001` model and stored in a local FAISS vector index.
- **Retrieve & Answer**: `ask(query)` retrieves the most relevant chunks for a question, builds a prompt containing that context plus the running conversation history, and sends it to `gemini-3.5-flash` for a grounded answer.
- Conversation turns are appended to an in-memory `chat_history` list so follow-up questions retain context.

## Project Structure

```
Chatbot/
├── chatbot.ipynb   # Main notebook: poetic chatbot + LangChain RAG chatbot
└── config.py        # Holds the Gemini API key (gemini_api_key) — DO NOT COMMIT
```

## Requirements

```
google-genai
langchain
langchain-community
langchain-text-splitters
langchain-google-genai
faiss-cpu
```

You'll also need a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

## Setup

1. Install dependencies:
   ```bash
   pip install google-genai langchain langchain-community langchain-text-splitters langchain-google-genai faiss-cpu
   ```
2. **Do not hardcode your API key in `config.py` if this repo is public.** Instead, use an environment variable:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   ```
   and load it in the notebook with:
   ```python
   import os
   gemini_api_key = os.environ["GEMINI_API_KEY"]
   ```
   Add `config.py` (or a `.env` file) to `.gitignore` so the key never gets committed.
3. Open and run `chatbot.ipynb` cell by cell (Jupyter Notebook / JupyterLab).

## Usage

- **Poetic chatbot**: call `poetic_chatbot("your question here")` — get back a poem-style answer.
- **RAG chatbot**: update the `url` variable to point at any webpage you want to query, then call `ask("your question here")` — answers are grounded in that page's content and remember prior turns in the session.

## Possible Improvements

- Move the API key out of `config.py` and into environment variables / a secrets manager before publishing.
- Persist the FAISS index to disk so the webpage doesn't need to be re-scraped and re-embedded every run.
- Support loading and indexing multiple URLs/documents instead of a single page.
- Add source citations to RAG answers (which chunk/URL the answer came from).
- Wrap both chatbots in a simple UI (e.g., Streamlit or Gradio) for easier interaction.

## License

For personal/portfolio use.
