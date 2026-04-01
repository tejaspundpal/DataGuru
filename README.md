# 🧠 DataGuru — Private Data Engineering Knowledge Assistant

DataGuru is a **RAG-powered (Retrieval-Augmented Generation)** knowledge assistant built specifically for Data Engineering teams. It enables engineers to query their own private internal documentation, runbooks, and incident histories using natural language.

Unlike general-purpose AI (like ChatGPT), DataGuru only answers from **your private documentation**, provides **direct citations** for every answer, and operates on an entirely local vector storage system.

---

## 🚀 Key Features

- **Distributed Knowledge Base**: Documents are proudly hosted in a dedicated, remote GitHub repository.
- **MCP Integration**: Uses the **Model Context Protocol (MCP)** to securely fetch documents from GitHub over the network, decoupling storage from the application.
- **Semantic Search**: Uses local vector embeddings to find the most relevant document chunks based on *meaning*, not just keywords.
- **Source Citations**: Every answer includes the exact file and relevance score from the knowledge base.
- **Zero Hallucination**: The system is grounded to only answer based on the retrieved context.
- **High Performance**: Powered by **Groq API** (LLaMA 3.3 70b) for near-instant inference speed.

---

## 🏗️ Technical Architecture (RAG Pipeline)

1. **Ingestion (via MCP)**: 
    - The `ingest.py` client securely connects to the local `mcp_github_server.py` via standard I/O.
    - The MCP server dynamically fetches `.md` documents directly from a configured remote **GitHub Repository** using its REST API.
    - Documents are split into overlapping chunks, converted into 384-dimensional vectors using a local **Sentence-Transformer** model (`all-MiniLM-L6-v2`), and stored in a local **ChromaDB** instance.
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
- **Architecture**: **Model Context Protocol (MCP)** for distributed tool use
- **Vector Database**: **ChromaDB** (Local)
- **Embeddings**: **sentence-transformers** (Local)
- **Language**: **Python 3.11+**
- **Orchestration**: Custom Agentic RAG pipeline

---

## 📂 Project Structure

```text
GenAI/
├── src/
│   ├── main.py               # CLI entry point and chat loop
│   ├── ingest.py             # MCP Client: Connects to server, embeds chunks
│   ├── mcp_github_server.py  # MCP Server: Fetches docs securely from GitHub
│   ├── retriever.py          # Semantic search and ChromaDB logic
│   ├── llm_client.py         # RAG prompt engineering and Groq API calls
│   └── config.py             # Central settings and hyperparameters
├── chroma_db/                # Local persistent vector store
└── requirements.txt          # Project dependencies
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
GITHUB_REPO=your_username/your_knowledge_base_repo
GITHUB_TOKEN=ghp_your_personal_access_token (Optional for public repos)
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
