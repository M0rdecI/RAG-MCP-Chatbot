# RAG-BASED AI Assistant — Project Documentation

---

## **Project Overview**

This is an AI-powered assistant designed to help users with context-related queries. It leverages document processing, vector search, and large language models (LLMs) to provide accurate, conversational answers. The system is accessible via both CLI and REST API, and is **Model Context Protocol (MCP) compliant** for interoperability with other AI systems.

---

## **Architecture Overview**

The architecture is modular and layered, with clear separation of concerns:

- **Core Layer:** Orchestrates tools and manages execution.
- **Tools Layer:** Implements document processing, vector search, LLM integration, response formatting, and web search.
- **Interfaces Layer:** Provides CLI and API endpoints for user interaction.
- **Utils Layer:** Offers configuration, logging, file, and chat history utilities.
- **Data Layer:** Stores vector embeddings, chat history, and logs.

### **High-Level Flow**

1. **User Query** (CLI/API)  
   ⬇
2. **MCPServer** orchestrates tools  
   ⬇
3. **Vector Store** retrieves relevant document chunks  
   ⬇
4. **Response Formatter** cleans and structures context  
   ⬇
5. **LLM Tool** generates a conversational answer  
   ⬇
6. **Response** returned to user (with optional sources)

---

## **Module-by-Module Analysis**

### 1. **Core Layer (`src/core/`)**

#### **mcp_server.py**

- **Purpose:**  
  The "Master Control Program" (MCP) is the orchestrator. It registers tools (functions/classes), manages their execution (sync/async), and provides a unified interface for all backend operations.
- **Key Features:**
  - Tool registration and lookup
  - Async and thread-pooled execution
  - Centralized error handling

#### **tool_registry.py**

- **Purpose:**  
  Provides a registry for tools, categorizing them (document, search, LLM, utility, etc.) and tracking their metadata.
- **Key Features:**
  - Decorator-based tool registration
  - Tool categorization and listing
  - Tool removal and clearing

---

### 2. **Tools Layer (`src/tools/`)**

#### **document_processing.py**

- **Purpose:**  
  Handles ingestion and processing of PDF/DOCX files. Splits documents into manageable chunks, extracts text, and generates metadata. Converts processed documents to MCP context objects for protocol compliance.
- **Key Features:**
  - PDF and DOCX parsing
  - Text chunking (with overlap for context)
  - Metadata extraction (source, type, chunk, size, etc.)
  - MCP context conversion

#### **vector_store.py**

- **Purpose:**  
  Stores document embeddings and enables fast similarity search using ChromaDB and SentenceTransformers.
- **Key Features:**
  - Embedding generation
  - Persistent vector storage
  - Similarity search for top-k relevant chunks
  - Document indexing and counting

#### **llm_tools.py**

- **Purpose:**  
  Integrates with Ollama LLMs (e.g., qwen2:7b), manages conversation history, and builds context for model inference.
- **Key Features:**
  - Connection pooling for efficiency
  - Model verification and auto-pull
  - Smart context building (history + document context)
  - Response generation with system prompt
  - Conversation history tracking

#### **response_tools.py**

- **Purpose:**  
  Cleans, extracts, and formats context for LLM consumption. Classifies queries and applies response templates if needed.
- **Key Features:**
  - Text cleaning (removes OCR artifacts, normalizes)
  - Section extraction based on query
  - Query classification (greeting, info, instruction, etc.)
  - Batch formatting for efficiency

#### **web_search.py**

- **Purpose:**  
  Provides a fallback mechanism to search the web for answers if internal knowledge is insufficient.
- **Key Features:**
  - Async web search (DuckDuckGo API)
  - HTML parsing for results
  - Top-3 result extraction

---

### 3. **Interfaces Layer (`src/interfaces/`)**

#### **cli.py**

- **Purpose:**  
  Provides an interactive command-line interface for users.
- **Key Features:**
  - User input and command parsing
  - Animated response display
  - Chat history management
  - Document indexing via CLI

#### **api.py**

- **Purpose:**  
  Exposes a FastAPI-based REST API for programmatic access.
- **Key Features:**
  - `/query`: Standard query endpoint
  - `/index`: Document indexing endpoint
  - `/mcp/infer`: **MCP-compliant inference endpoint**
  - API key authentication
  - Rate limiting
  - Error handling

---

### 4. **Utils Layer (`src/utils/`)**

#### **config.py**

- **Purpose:**  
  Centralizes configuration using Pydantic and .env files.
- **Key Features:**
  - API, LLM, vector store, and storage settings
  - Environment variable support

#### **logging_utils.py**

- **Purpose:**  
  Sets up application-wide logging (file + rich console).
- **Key Features:**
  - Rotating file handler
  - Rich console handler
  - Customizable log level

#### **file_utils.py**

- **Purpose:**  
  Provides file and directory management utilities.
- **Key Features:**
  - Directory creation
  - File backup with timestamp
  - Safe deletion
  - File listing with extension filtering

#### **chat_store.py**

- **Purpose:**  
  Manages chat session history, including persistence and retrieval.
- **Key Features:**
  - Session-based chat storage (JSON)
  - Message addition, retrieval, and clearing

#### **mcp_schema.py**

- **Purpose:**  
  Defines Pydantic models for the **Model Context Protocol** (MCP).
- **Key Features:**
  - `MCPContext`, `MCPModelInfo`, `MCPInferenceRequest`, `MCPInferenceResponse`
  - Used for protocol-compliant API requests and responses

---

### 5. **Data Layer (`data/` and `logs/`)**

- **vector_store/**: Persistent storage for document embeddings (ChromaDB)
- **chat_history/**: Stores chat session logs (JSON)
- **logs/**: Application logs (rotating files)

---

## **Model Context Protocol (MCP) Compliance**

- **Schemas:**  
  Defined in mcp_schema.py for context, model info, and inference.
- **API Endpoint:**  
  `/mcp/infer` in api.py accepts and returns MCP-compliant payloads.
- **Document Mapping:**  
  `DocumentProcessingTool.to_mcp_context()` converts internal docs to MCPContext.
- **Interoperability:**  
  Enables integration with other MCP-aware AI systems.

---

## **Other Notable Features**

- **Batch Processing:**  
  Used in document processing and vector indexing for efficiency and progress tracking.
- **Async-First Design:**  
  Most operations are async, supporting scalable concurrent workloads.
- **Extensibility:**  
  New tools can be registered easily via the MCPServer or ToolRegistry.
- **Security:**  
  API key authentication and rate limiting protect the API.

---

## **How to Extend**

- **Add new document types:**  
  Implement a new processor in document_processing.py and register it.
- **Integrate new LLMs:**  
  Extend llm_tools.py with new model clients.
- **Add new endpoints:**  
  Define in api.py and register with FastAPI.
- **Support more MCP context types:**  
  Extend `MCPContext` and mapping logic.

---

## **Summary Table**

| Layer      | Module/File                  | Purpose/Functionality                                  |
| ---------- | ---------------------------- | ------------------------------------------------------ |
| Core       | mcp_server.py                | Tool orchestration, async execution                    |
| Core       | tool_registry.py             | Tool registration, categorization                      |
| Tools      | document_processing.py       | Document parsing, chunking, MCP context conversion     |
| Tools      | vector_store.py              | Embedding, vector search, ChromaDB integration         |
| Tools      | llm_tools.py                 | LLM integration, context building, response generation |
| Tools      | response_tools.py            | Text cleaning, context extraction, formatting          |
| Tools      | web_search.py                | Web search fallback                                    |
| Interfaces | cli.py                       | Command-line interface, chat history                   |
| Interfaces | api.py                       | REST API, MCP endpoint, rate limiting, authentication  |
| Utils      | config.py                    | Centralized configuration                              |
| Utils      | logging_utils.py             | Logging setup                                          |
| Utils      | file_utils.py                | File/directory utilities                               |
| Utils      | chat_store.py                | Chat session management                                |
| Utils      | mcp_schema.py                | MCP protocol schemas                                   |
| Data       | vector_store/, chat_history/ | Persistent storage                                     |
| Data       | logs/                        | Application logs                                       |

---

## **Conclusion**

This is a robust, extensible, and standards-compliant AI assistant platform.

- **MCP compliance** ensures interoperability.
- **Modular design** allows easy extension and maintenance.
- **Efficient processing** and **secure interfaces** make it suitable for production use.

**For further development:**

- Add more context types to MCP.
- Enhance LLM prompt engineering.
- Integrate advanced analytics or monitoring.

---
