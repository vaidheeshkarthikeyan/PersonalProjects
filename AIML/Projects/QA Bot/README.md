# QA Bot (BERT Extractive Question Answering)

A simple FAQ chatbot that answers natural-language questions about a fixed passage of text using a pretrained BERT model fine-tuned for extractive question answering.

## Overview

The notebook (`QA_Bot.ipynb`) demonstrates extractive QA: given a passage of text and a question, the model finds and returns the exact span of text from the passage that best answers the question — no generation involved, just extraction.

In this example, the passage is a company profile for a fictional car dealership ("Sunset Motors"), and the bot answers questions like *"Where is the dealership located?"* or *"What make of cars are available?"* by pulling the answer directly from that text.

## How It Works

1. **Model**: Loads `bert-large-uncased-whole-word-masking-finetuned-squad` — a BERT-large model fine-tuned on SQuAD (Stanford Question Answering Dataset) — via Hugging Face `transformers`.
2. **Context**: A fixed block of text (`sunset_motors_content`) acts as the knowledge source the bot draws answers from.
3. **`faq_chatbot(question)`**:
   - Tokenizes the question + context together (`tokenizer.encode`).
   - Builds segment IDs to distinguish the question tokens from the context tokens.
   - Runs the tokenized input through the model, which predicts a **start** and **end** logit for the answer span.
   - Takes the tokens between the predicted start and end positions as the raw answer.
   - Cleans up WordPiece sub-token markers (`##`) to reconstruct readable words.
   - Returns the extracted answer string.

## Project Structure

```
QA Bot/
└── QA_Bot.ipynb   # Main notebook: BERT-based extractive QA over a fixed passage
```

## Requirements

```
transformers
torch
```

## Usage

1. Install dependencies:
   ```bash
   pip install transformers torch
   ```
2. Open and run `QA_Bot.ipynb` cell by cell (Jupyter Notebook / JupyterLab). The first run will download the pretrained model weights (~1.3GB) from Hugging Face.
3. Call `faq_chatbot("your question here")` to get an answer extracted from the `sunset_motors_content` passage.
4. Swap in your own passage by replacing `sunset_motors_content` to build a QA bot over different content.

## Possible Improvements

- Handle the "no answer found" case more gracefully — the current code only `print`s a message but still proceeds to build `corrected_answer` from an undefined `answer`, which will raise an error.
- Support longer documents by chunking text and searching across chunks (BERT has a fixed input length limit).
- Return a confidence score alongside the answer (derived from the start/end logits) so low-confidence answers can be flagged.
- Wrap the passage + QA function into a small class or config so multiple knowledge sources can be swapped in easily.
- Add a lightweight UI (Streamlit/Gradio) for interactive Q&A instead of calling the function directly in the notebook.

## License

For personal/portfolio use.
