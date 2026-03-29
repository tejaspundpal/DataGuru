# 🧠 DataGuru — Private Data Engineering Knowledge Assistant

DataGuru is a **RAG-powered (Retrieval-Augmented Generation)** knowledge assistant built specifically for Data Engineering teams. It enables engineers to query their own private internal documentation, runbooks, and incident histories using natural language.

Unlike general-purpose AI (like ChatGPT), DataGuru only answers from **your private documentation**, provides **direct citations** for every answer, and operates on an entirely local vector storage system.

---

## 🚀 Key Features

- **Private Knowledge Base**: Ingests internal SOPs, incident reports, and runbooks across **Informatica, SQL, PySpark, Python, and Unix**.
- **Semantic Search**: Uses local vector embeddings to find the most relevant document chunks based on *meaning*, not just keywords.
- **Source Citations**: Every answer includes the exact file and relevance score from the knowledge base.
- **Zero Hallucination**: The system is grounded to only answer based on the retrieved context.
- **High Performance**: Powered by **Groq API** (LLaMA 3.3 70b) for near-instant inference speed.

---

## 🏗️ Technical Architecture (RAG Pipeline)

1. **Ingestion**: 
    - Internal `.md` documents are loaded and split into overlapping chunks to preserve context.
    - Chunks are converted into 384-dimensional vectors using a local **Sentence-Transformer** model (`all-MiniLM-L6-v2`).
    - Vectors and metadata are stored in a local **ChromaDB** instance.
2. **Retrieval**: 
    - User queries are embedded using the same local model.
    - A cosine similarity search is performed in ChromaDB to retrieve the top-5 most relevant chunks.
3. **Generation**: 
    - The retrieved chunks are injected into a specialized "grounding prompt."
    - This augmented prompt is sent to the **LLaMA 3.3 70b** model via the Groq API.
    - The assistant returns a technical answer citation for every source used.

---

## 🛠️ Tech Stack

- **LLM**: LLaMA 3.3 70b via **Groq Cloud API**
- **Vector Database**: **ChromaDB** (Local)
- **Embeddings**: **sentence-transformers** (Local)
- **Language**: **Python 3.11+**
- **Orchestration**: Custom RAG pipeline

---

## 📂 Project Structure

```text
GenAI/
├── src/
│   ├── main.py           # CLI entry point and chat loop
│   ├── ingest.py         # Document ingestion and vectorization script
│   ├── retriever.py      # Semantic search and ChromaDB logic
│   ├── llm_client.py     # RAG prompt engineering and Groq API calls
│   └── config.py         # Central settings and hyperparameters
├── knowledge_base/       # Source documents (Informatica, SQL, Spark, etc.)
├── chroma_db/            # Local persistent vector store
└── requirements.txt      # Project dependencies
```

---

## 🏁 Getting Started

### 1. Prerequisites
- Python 3.11+
- A **Groq API Key** (Free tier available at [console.groq.com](https://console.groq.com))

### 2. Installation
```powershell
# Clone the repository
git clone <your-repo-url>
cd DataGuru

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_actual_api_key_here
```

### 4. Ingest Documents
Before chatting, you must index your knowledge base:
```powershell
python src/ingest.py
```

### 5. Start DataGuru
```powershell
python src/main.py
```

---

## 💡 Why RAG?
DataGuru was built to solve the limitations of standard LLMs in a professional setting:
- **Private Data Access**: Standard LLMs don't know your company's private runbooks or incident history.
- **Accurate Information**: By only answering from trusted sources, hallucination is virtually eliminated.
- **Accountability**: Showing citations allows engineers to verify answers in the original documents.
- **Efficiency**: Reduces time-to-resolution for pipeline incidents by surfacing the right internal knowledge instantly.
