# ⚡ DataGuru — Private Data Engineering Knowledge Assistant

DataGuru is a **RAG-powered (Retrieval-Augmented Generation)** knowledge assistant built for Data Engineering teams. It enables engineers to query their private internal documentation, runbooks, and incident histories using natural language — through a premium **Streamlit Web UI**.

It also integrates with **Jira** to analyze support tickets — identifying errors, suggesting solutions, and recommending prevention strategies based on your knowledge base.

---

## 🚀 Key Features

- **Premium Web UI**: Beautiful Streamlit interface with dark-teal theme, animated onboarding, file upload, and streaming responses.
- **Single-User, Clone & Use**: No auth, no login — just clone, add your credentials, and run.
- **Jira Integration**: Analyze Jira tickets directly from chat (e.g., "analyze jira SCRUM-2") — fetches issue details + comments and provides structured analysis.
- **MCP Integration**: Uses the **Model Context Protocol (MCP)** to securely fetch documents from GitHub and interact with Jira.
- **Multi-Format Ingestion**: Supports PDF, DOCX, Markdown, SQL, JSON, YAML, Python, shell scripts, and more.
- **Semantic Search**: Local vector embeddings find the most relevant chunks based on *meaning*, not keywords.
- **Source Citations**: Every answer includes the exact file and relevance score.
- **Self-Learning**: Passively learns patterns from your Q&A sessions and stores them for future retrieval.
- **Skill Generation**: Automatically generates reusable "skill documents" when enough similar patterns are detected.
- **File Attachment**: Attach logs, SQL, configs, etc. for contextual analysis against the knowledge base.
- **Chat Export**: Export conversations as TXT or PDF.
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
    - Cosine similarity search in ChromaDB retrieves the top-K most relevant chunks.
    - Also searches the learned patterns collection for previously captured insights.
3. **Generation**:
    - Retrieved chunks + chat history + optional file attachment / Jira issue data are injected into a grounding prompt.
    - Sent to **LLaMA 3.3 70b** via Groq API.
    - Returns a cited, structured answer.
4. **Jira Analysis**:
    - Detects Jira issue keys (e.g., `SCRUM-2`) in user queries.
    - Fetches issue details + comments via Jira REST API.
    - Correlates error logs from the ticket with knowledge base documentation.
    - Returns structured analysis: Issue Summary → Error Analysis → Solution Ideas → Prevention Strategy.
5. **Learning Loop**:
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
| **Jira Integration** | REST API v3 with Basic Auth (API token) |
| **Document Parsing** | pdfplumber, PyPDF2, python-docx, PyMuPDF |
| **Language** | Python 3.11+ |

---

## 📂 Project Structure

```text
DataGuru/
├── app.py                    # Streamlit Web UI (single-user, premium design)
├── run_dataguru.bat          # One-click Windows launcher
├── src/
│   ├── main.py               # CLI entry point and chat loop
│   ├── ingest.py             # MCP Client: connects to server, embeds, stores
│   ├── mcp_github_server.py  # MCP Server: fetches docs from GitHub
│   ├── mcp_jira_server.py    # MCP Server: Jira integration (9 tools)
│   ├── retriever.py          # Semantic search across ChromaDB collections
│   ├── llm_client.py         # RAG prompt engineering and Groq API calls
│   ├── config.py             # Central settings and hyperparameters
│   ├── file_handler.py       # File attachment parsing and diagnostics
│   ├── chat_export.py        # Export chat as TXT/PDF
│   ├── learning_agent.py     # Self-learning: extracts patterns from sessions
│   ├── skill_generator.py    # Generates skill documents from learned patterns
│   └── user_config.py        # Credential management
├── chroma_db/                # Persistent vector store (auto-created)
├── requirements.txt          # Project dependencies
├── .env                      # API keys and config (user-created)
└── .gitignore
```

---

## 🏁 Getting Started

### 1. Prerequisites
- Python 3.11+
- A **Groq API Key** (free tier at [console.groq.com](https://console.groq.com))
- A GitHub repository containing your knowledge base documents
- (Optional) Jira Cloud instance with an API token

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
# Required
GROQ_API_KEY=your_groq_api_key
GITHUB_REPO=owner/repo-name
GITHUB_TOKEN=ghp_xxx          # Optional for public repos

# Jira (Optional)
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_PASSWORD=your_api_token
JIRA_VERIFY_SSL=true
```

You can also configure all credentials interactively via the Web UI sidebar.

### 4. Launch
```bash
# Option 1: Direct
streamlit run app.py

# Option 2: Windows one-click (handles venv + deps automatically)
run_dataguru.bat
```

### 5. Usage
1. Enter your Groq API key and GitHub repo in the sidebar
2. Click **Connect**
3. Click **Sync Docs** to ingest your knowledge base
4. Start chatting!

#### Jira Analysis
Just mention a Jira issue key in your prompt:
```
analyze jira SCRUM-2 and find the error reason and give me solution ideas
```

DataGuru will:
- Fetch the ticket details and comments from Jira
- Search your knowledge base for relevant documentation
- Provide a structured analysis with solutions

---

## 🎫 Jira MCP Server Tools

The Jira MCP server (`src/mcp_jira_server.py`) provides 9 tools:

| Tool | Description |
|------|-------------|
| `fetch_issue` | Get full issue details by key |
| `search_issues` | Search using JQL |
| `create_issue` | Create a new ticket |
| `add_comment` | Add a comment to a ticket |
| `get_issue_comments` | Get all comments on a ticket |
| `change_assignee` | Reassign a ticket |
| `transition_issue` | Change issue status |
| `search_users` | Find Jira users |
| `get_issue_for_analysis` | Fetch issue + comments optimized for LLM analysis |

---

## 💡 Why DataGuru?

- **Private Data Access**: Standard LLMs don't know your company's runbooks or incident history.
- **Jira-Aware**: Analyze tickets with full context from your internal docs.
- **Accurate & Cited**: Answers strictly from trusted sources with full citations.
- **Self-Improving**: Learns from every conversation to get better over time.
- **No Vendor Lock-in**: Local embeddings, local vector DB, any LLM via Groq.
- **Simple Setup**: Clone → `.env` → Run. No auth system, no deployment complexity.

---

## 👤 Author

**Tejas Pundpal** — [LinkedIn](https://linkedin.com/in/tejaspundpal)
