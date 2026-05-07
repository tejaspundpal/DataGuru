# 🧠 DataGuru — Private Data Engineering Knowledge Assistant

DataGuru is a **RAG-powered (Retrieval-Augmented Generation)** knowledge assistant built for Data Engineering teams. It enables engineers to query their private internal documentation, runbooks, and incident histories using natural language — through a premium **Streamlit Web UI** or a full-featured **CLI**.

Unlike general-purpose AI, DataGuru only answers from **your private documentation**, provides **direct source citations**, and learns from your conversations over time.

---

## 🚀 Key Features

- **Premium Web UI**: Beautiful Streamlit interface with dark-teal theme, animated onboarding, file upload, and streaming responses.
- **CLI Mode**: Full-featured terminal interface with file attachment, learning stats, and skill generation commands.
- **MCP Integration**: Uses the **Model Context Protocol (MCP)** to securely fetch documents from GitHub, decoupling storage from application logic.
- **Multi-Format Ingestion**: Supports PDF, DOCX, Markdown, SQL, JSON, YAML, Python, shell scripts, and more.
- **Semantic Search**: Local vector embeddings find the most relevant chunks based on *meaning*, not keywords.
- **Source Citations**: Every answer includes the exact file and relevance score.
- **Self-Learning (Level 1)**: Passively learns patterns from your Q&A sessions and stores them for future retrieval.
- **Skill Generation (Level 2)**: Automatically generates reusable "skill documents" when enough similar patterns are detected.
- **File Attachment**: Attach logs, SQL, configs, etc. for contextual analysis against the knowledge base.
- **Zero Hallucination**: Strictly grounded — only answers from retrieved context.
- **High Performance**: Powered by **Groq API** (LLaMA 3.3 70b) for near-instant inference.

---

## 🏗️ Technical Architecture (RAG Pipeline)

1. **Ingestion (via MCP)**:
    - `ingest.py` connects to `mcp_github_server.py` over stdio using the MCP protocol.
    - The MCP server fetches files from a configured GitHub repository (supports PDF, DOCX, and text formats).
    - Documents are chunked with sliding-window overlap, embedded into 384-dim vectors using **all-MiniLM-L6-v2**, and stored in **ChromaDB**.
2. **Retrieval**:
    - User queries are embedded with the same local model.
    - Cosine similarity search in ChromaDB retrieves the top-K most relevant chunks (configurable threshold).
    - Also searches the learned patterns collection for previously captured insights.
3. **Generation**:
    - Retrieved chunks + chat history + optional file attachment are injected into a grounding prompt.
    - Sent to **LLaMA 3.3 70b** via Groq API.
    - Returns a cited, structured answer.
4. **Learning Loop**:
    - After each session, the learning agent extracts reusable patterns and stores them.
    - The skill generator clusters related patterns and produces standalone skill documents.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | LLaMA 3.3 70b via Groq Cloud API |
| **Architecture** | Model Context Protocol (MCP) for distributed tool use |
| **Vector Database** | ChromaDB (persistent, cosine similarity) |
| **Embeddings** | sentence-transformers / all-MiniLM-L6-v2 (local) |
| **Web UI** | Streamlit with custom CSS |
| **Document Parsing** | pdfplumber, PyPDF2, python-docx |
| **Language** | Python 3.11+ |

---

## 📂 Project Structure

```text
DataGuru/
├── app.py                    # Streamlit Web UI (premium design)
├── src/
│   ├── main.py               # CLI entry point and chat loop
│   ├── ingest.py             # MCP Client: connects to server, embeds, stores
│   ├── mcp_github_server.py  # MCP Server: fetches docs from GitHub
│   ├── retriever.py          # Semantic search across ChromaDB collections
│   ├── llm_client.py         # RAG prompt engineering and Groq API calls
│   ├── config.py             # Central settings and hyperparameters
│   ├── file_handler.py       # File attachment parsing and diagnostics
│   ├── learning_agent.py     # Self-learning: extracts patterns from sessions
│   ├── skill_generator.py    # Generates skill documents from learned patterns
│   └── user_config.py        # Per-user credential management
├── chroma_db/                # Local persistent vector store (auto-created)
├── learned_skills/           # Generated skill documents (auto-created)
├── requirements.txt          # Project dependencies
└── .env                      # API keys and config (user-created)
```

---

## 🏁 Getting Started

### 1. Prerequisites
- Python 3.11+
- A **Groq API Key** (free tier at [console.groq.com](https://console.groq.com))
- A GitHub repository containing your knowledge base documents

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/tejaspundpal/DataGuru.git
cd DataGuru

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Credentials
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key
GITHUB_REPO=owner/repo-name
GITHUB_TOKEN=ghp_xxx  # Optional for public repos
```

Or configure interactively via the Web UI sidebar or `setup` command in CLI.

### 4. Launch Web UI (Recommended)
```bash
streamlit run app.py
```
The UI will guide you through syncing documents and chatting.

### 5. Launch CLI
```bash
python src/main.py
```

#### CLI Commands
| Command | Description |
|---------|-------------|
| `ingest` | Re-index documents from GitHub |
| `attach <path>` | Attach a file for contextual analysis |
| `detach` | Remove attached file |
| `skills` | Generate skill documents from learned patterns |
| `stats` | Show learning statistics |
| `setup` | Reconfigure credentials |
| `clear` | Clear terminal |
| `quit` | Exit (triggers learning agent) |

---

## 💡 Why DataGuru?

- **Private Data Access**: Standard LLMs don't know your company's runbooks or incident history.
- **Accurate & Cited**: Answers strictly from trusted sources with full citations.
- **Self-Improving**: Learns from every conversation to get better over time.
- **No Vendor Lock-in**: Local embeddings, local vector DB, any LLM via Groq.
- **Efficiency**: Reduces time-to-resolution for pipeline incidents by surfacing the right internal knowledge instantly.

---

## 👤 Author

**Tejas Pundpal** — [LinkedIn](https://linkedin.com/in/tejaspundpal)
