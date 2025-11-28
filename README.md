# FoundryIQ Knowledge Base Demo

This sample demonstrates the capabilities of **FoundryIQ**, announced by Microsoft at **Ignite 2025**. FoundryIQ represents the next generation of Retrieval-Augmented Generation (RAG), providing a unified knowledge layer for AI agents.

## What is FoundryIQ?

FoundryIQ is Microsoft's unified knowledge layer for agents, built on Azure AI Search. Instead of building custom RAG pipelines for every agent, FoundryIQ provides:

- **Reusable Knowledge Bases**: Topic-centric collections that ground multiple agents through a single API
- **Automatic Access to Knowledge Sources**: Connect to both indexed (Azure AI Search, Azure Blob Storage, Fabric) and federated sources (SharePoint, Bing Web Search, MCP servers)
- **Agentic Retrieval Engine**: Self-reflective query engine that plans, searches, and synthesizes answers across sources with configurable "retrieval reasoning effort"
- **Enterprise-Grade Security**: Document-level access control, Microsoft Purview integration, and Entra ID-based governance

For more details, read the [official FoundryIQ announcement](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-iq-unlocking-ubiquitous-knowledge-for-agents/4470812).

## What This Demo Showcases

This sample demonstrates key FoundryIQ capabilities:

### 1. **Knowledge Bases**
A reusable knowledge base (`contoso-multi-index-kb`) that orchestrates multiple knowledge sources and provides a unified query interface.

### 2. **Multiple Knowledge Sources**
- **3 Azure AI Search Indexes** (indexed knowledge sources):
  - Contoso Insurance FAQ Index
  - Contoso Retail Index
  - Contoso Gaming Index
- **1 Bing Web Search** (federated knowledge source for real-time web data)

### 3. **Agentic Retrieval**
The knowledge base uses Azure OpenAI to:
- **Plan** which knowledge sources to query based on the question
- **Route** queries intelligently across multiple sources
- **Synthesize** coherent answers from retrieved documents
- **Provide citations** with source references and relevance scores

### 4. **Automatic Indexing Capabilities**
While this demo uses pre-existing Azure AI Search indexes, FoundryIQ can also:
- Connect directly to **Azure Blob Storage** or **Microsoft Fabric**
- **Automatically create indexing pipelines** to chunk, vectorize, and index content
- Enable **Azure Content Understanding** for layout-aware enrichment of complex documents (tables, figures, headers)
- Manage the full indexing lifecycle without custom code

## Project Structure

```
ks-sample1/
├── .env                          # Environment variables (credentials and configuration)
├── .env.example                  # Template for environment configuration
├── .gitignore                    # Git ignore file
├── requirements.txt              # Python dependencies
├── kb_query_service.py           # Shared helper for issuing KB queries
├── query_kb.py                   # Console query experience with citation display
├── web_app.py                    # FastAPI-powered responsive web app (served via Uvicorn)
├── templates/
│   └── index.html                # Web UI shell rendered by FastAPI
├── static/
│   ├── css/styles.css            # Modern responsive styling + theme definitions
│   └── js/app.js                 # Client-side interactivity, theme + retrieval controls
├── ops/                          # One-time administrative scripts
│   ├── create_knowledge_sources.py   # Creates knowledge sources from indexes and web search
│   ├── create_kb.py                  # Creates the knowledge base that orchestrates sources
│   └── list_indexes.py               # Utility to list all indexes in your search service
└── README.md                     # This file
```

## Architecture Overview

- **FastAPI + Uvicorn backend (`web_app.py`)** exposes both HTML pages and `/api/query` endpoints. Every request ultimately flows through a single `kb_query_service` instance so console and web experiences share throttling, logging, and error handling.
- **Shared knowledge client (`kb_query_service.py`)** wraps the FoundryIQ KnowledgeBaseRetrievalClient, normalizes timing metrics, and surfaces knobs for `retrieval_reasoning_effort` plus output style so either UI can override defaults without duplicating code.
- **Frontend (`templates/index.html`, `static/js/app.js`, `static/css/styles.css`)** renders the chat UI, wired theme toggle (light/dark/system) with `localStorage` persistence, exposes dropdowns for retrieval reasoning effort and answer style, and orchestrates citation modals plus performance indicators.
- **Operations scripts (`ops/*.py`)** are intentionally isolated so day-to-day app use never mixes with one-time provisioning commands (create or inspect knowledge sources, knowledge bases, and indexes).

## Prerequisites

Before running this demo, you need:

1. **Azure AI Search Service**
   - Service endpoint URL
   - API key with admin permissions
   - 3 pre-existing search indexes (or create your own)

2. **Azure OpenAI Service**
   - Endpoint URL
   - API key
   - GPT-4 or GPT-4o deployment

3. **Python Environment**
   - Python 3.8 or higher
   - Virtual environment (recommended)

## Setup Instructions

### Step 1: Clone and Set Up Environment

```powershell
# Navigate to the project directory
cd ks-sample1

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` with your Azure credentials:

   ```env
   # Azure AI Search Configuration
   search_url=https://YOUR-SEARCH-SERVICE.search.windows.net
   search_api_key=YOUR_SEARCH_API_KEY

   # Azure OpenAI Configuration
   az-openai_endpoint=https://YOUR-OPENAI-SERVICE.openai.azure.com/
   az-openai-model=gpt-4o
   az-openai-deployment=YOUR-DEPLOYMENT-NAME
   az-openai-key=YOUR_OPENAI_API_KEY

   # Azure AI Search Index Names
   index_insurance=contoso-insurance-faq-index
   index_retail=contoso-retail-index
   index_gaming=contoso-gaming-index
   ```

### Step 3: Verify Your Search Indexes

List all indexes in your Azure AI Search service to verify they exist:

```powershell
python ops/list_indexes.py
```

**If you don't have existing indexes**, you have two options:

#### Option A: Use Azure Portal to Create Indexes
1. Go to Azure Portal → Your AI Search Service
2. Create indexes manually or use the "Import data" wizard
3. Connect to Azure Blob Storage, upload sample documents
4. FoundryIQ will automatically chunk, vectorize, and index the content

#### Option B: Create Your Own Knowledge Sources
FoundryIQ can automatically create indexing pipelines from:
- **Azure Blob Storage containers**
- **Microsoft Fabric OneLake**
- **SharePoint sites** (with Microsoft Purview integration)

Update `ops/create_knowledge_sources.py` to point to your data sources, and FoundryIQ will handle the rest.

### Step 4: Create Knowledge Sources

Run the script to create knowledge sources from your indexes and web search:

```powershell
python ops/create_knowledge_sources.py
```

This creates:
- 3 **SearchIndexKnowledgeSource** objects (one for each index)
- 1 **WebKnowledgeSource** (for Bing web search)

### Step 5: Create the Knowledge Base

Create the knowledge base that orchestrates all sources:

```powershell
python ops/create_kb.py
```

This creates `contoso-multi-index-kb` with:
- Agentic retrieval configuration
- Azure OpenAI integration for answer synthesis
- Low reasoning effort (configurable)

### Step 6: Query the Knowledge Base (Console)

Launch the interactive query interface:

```powershell
python query_kb.py
```

Try these example queries:
- **"What types of insurance policies does Contoso offer?"** (queries insurance index)
- **"Tell me about Contoso retail products"** (queries retail index)
- **"My games are slowing down my computer. Suggest a remedy"** (queries gaming index + web)
- **"What's the latest news on artificial intelligence?"** (uses Bing web search)

The system will display:
- **Answer**: Synthesized response from Azure OpenAI
- **Citations**: Source documents with actual text content, URLs, and relevance scores

### Step 7: Run the Responsive Web App

Launch the FastAPI-powered web interface:

```powershell
uvicorn web_app:app --reload
```

Then browse to `http://127.0.0.1:8000` to use a modern chat-style UI featuring:

- **Session-based querying** that reuses the same KnowledgeBaseRetrievalClient as the console app.
- **Responsive layout** optimized for desktop and mobile.
- **Theme toggle + system preference sync** so users can switch light/dark modes with styles persisted via `localStorage`.
- **Retrieval controls** that let you override reasoning effort (low/medium/high) and answer style (concise vs. structured) per question.
- **Inline citation chips** – click any reference to open a modal with title, URL, and readable content/snippet.
- **Performance metrics** showing total time plus breakdown for request prep, retrieval, and response processing.

## File Descriptions

### Configuration Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `.env` | Stores Azure credentials and configuration | Edit this with your service endpoints and keys |
| `.env.example` | Template for environment variables | Copy to `.env` and fill in your values |
| `requirements.txt` | Python package dependencies | Run `pip install -r requirements.txt` to install |

### Setup Scripts (Run Once)

| File | Purpose | When to Run |
|------|---------|-------------|
| `ops/create_knowledge_sources.py` | Creates knowledge source objects from your indexes and Bing search | **First**: After configuring `.env` and verifying indexes exist |
| `ops/create_kb.py` | Creates the knowledge base that orchestrates all sources | **Second**: After knowledge sources are created |

### Utility Scripts

| File | Purpose | When to Use |
|------|---------|-------------|
| `ops/list_indexes.py` | Lists all indexes in your Azure AI Search service | Use to verify your indexes exist and get their exact names |
| `kb_query_service.py` | Shared query helper that returns structured answers, citations, and timing | Automatically used by both console and web apps |
| `query_kb.py` | Console-based interactive query interface with citation display | **Anytime**: After knowledge base is created, to test queries |
| `web_app.py` + `/templates` + `/static` | FastAPI web app with responsive UI, citation modal, performance metrics | Use when you want an end-user-friendly experience |

## Workflow Summary

```
1. Configure .env with your Azure credentials
   ↓
2. (Optional) Run ops/list_indexes.py to verify your indexes
   ↓
3. Run ops/create_knowledge_sources.py to create knowledge sources
   ↓
4. Run ops/create_kb.py to create the knowledge base
   ↓
5. Run query_kb.py to interactively query your knowledge base
```

## Understanding FoundryIQ Components in This Demo

### Knowledge Sources
Knowledge sources represent the data repositories that FoundryIQ can access:

- **Indexed Sources** (`SearchIndexKnowledgeSource`):
  - Content is chunked, vectorized, and stored in Azure AI Search
  - Enables hybrid search (keyword + semantic vector search)
  - This demo uses 3 pre-existing search indexes

- **Federated Sources** (`WebKnowledgeSource`):
  - Content is queried in real-time without indexing
  - This demo uses Bing web search for current information

### Knowledge Base
The knowledge base (`contoso-multi-index-kb`) is a reusable collection that:
- References multiple knowledge sources
- Uses Azure OpenAI for query planning and answer synthesis
- Provides a single API endpoint for agents to query
- Automatically routes queries to the most relevant sources

### Agentic Retrieval Engine
The retrieval engine inside the knowledge base:
- **Plans** how to search across sources
- **Rewrites** and decomposes complex questions
- **Iterates** when more context is needed
- **Synthesizes** answers with citations

This is configured with `retrieval_reasoning_effort: low` in this demo, but can be increased for more thorough multi-step reasoning.

## Extending This Demo

### Add More Indexes
1. Create new indexes in Azure AI Search (manually or from Blob Storage)
2. Add the index name to `.env`:
   ```env
   index_newdata=my-new-index-name
   ```
3. Update `ops/create_knowledge_sources.py` to create a knowledge source for the new index
4. Update `ops/create_kb.py` to add a reference to the new knowledge source
5. Update `query_kb.py` to include the new source in retrieval requests

### Use Automatic Indexing from Blob Storage
Instead of pre-existing indexes, you can have FoundryIQ automatically create the indexing pipeline:

```python
from azure.search.documents.knowledgebases.models import (
    BlobStorageKnowledgeSource,
    BlobStorageKnowledgeSourceParameters
)

blob_source = BlobStorageKnowledgeSource(
    name="my-blob-source",
    parameters=BlobStorageKnowledgeSourceParameters(
        storage_account_name="mystorageaccount",
        container_name="documents",
        # FoundryIQ automatically chunks, vectorizes, and indexes
    )
)
```

### Connect to Microsoft Fabric
```python
from azure.search.documents.knowledgebases.models import (
    FabricKnowledgeSource,
    FabricKnowledgeSourceParameters
)

fabric_source = FabricKnowledgeSource(
    name="my-fabric-source",
    parameters=FabricKnowledgeSourceParameters(
        workspace_id="your-workspace-id",
        item_id="your-item-id"
    )
)
```

### Increase Retrieval Reasoning Effort
In `ops/create_kb.py`, change:
```python
retrieval_reasoning_effort="low"  # → "medium" or "high"
```

Higher effort levels enable:
- More sophisticated query planning
- Iterative search refinement
- Cross-source synthesis

## Security and Governance

FoundryIQ supports enterprise-grade security:
- **Document-level access control**: Respects user permissions from source systems
- **Microsoft Purview integration**: Preserves sensitivity labels and data classifications
- **Entra ID authentication**: Use managed identities instead of API keys in production
- **Audit logging**: All retrieval operations are logged for compliance

For production deployments, replace API key authentication with Azure Managed Identity.

## Resources

- [FoundryIQ Official Announcement](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/foundry-iq-unlocking-ubiquitous-knowledge-for-agents/4470812)
- [FoundryIQ Documentation](https://aka.ms/FK-docs)
- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Azure AI Foundry Portal](https://ai.azure.com/)
- [Knowledge Base Retrieval Quality Evaluations](https://aka.ms/AISearch-KB-evals)

## License

This sample is provided as-is for demonstration purposes.

---

**Questions or Issues?** Check the Azure AI Search documentation or visit the Microsoft Tech Community for support.
