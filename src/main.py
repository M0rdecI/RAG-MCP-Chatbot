# src/main.py
import asyncio
import logging
from dotenv import load_dotenv
from rich.console import Console
from core.mcp_server import MCPServer
from tools.document_processing import DocumentProcessingTool
from tools.vector_store import VectorStoreTool
from tools.web_search import WebSearchTool
from tools.response_tools import ResponseFormatterTool
from tools.llm_tools import OllamaTool
from interfaces.cli import CLIInterface
from interfaces.api import app as api_app
import uvicorn
import argparse
from utils.config import config
from pathlib import Path

def setup_logging():
    """Setup application-wide logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'chatbot_ai.log'),
            logging.StreamHandler()
        ]
    )

async def setup_mcp() -> MCPServer:
    # Ensure required directories exist
    required_dirs = [
        Path("data/vector_store"),
        Path("data/chat_history"),
        Path("files_data"),
        Path("logs")
    ]
    
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured directory exists: {dir_path}")

    mcp = MCPServer()
    
    # Initialize tools
    doc_tool = DocumentProcessingTool()
    vector_tool = VectorStoreTool()
    web_tool = WebSearchTool()
    response_tool = ResponseFormatterTool()
    llm_tool = OllamaTool()
    
    # Register tools with MCP
    mcp.register_tool("process_documents", doc_tool.process_directory)
    mcp.register_tool("index_documents", vector_tool.index_documents)
    mcp.register_tool("get_document_count", vector_tool.get_document_count)
    mcp.register_tool("query_vector_store", vector_tool.query)
    mcp.register_tool("web_search", web_tool.search)
    mcp.register_tool("format_response", response_tool.format)
    mcp.register_tool("generate_response", llm_tool.generate_response)
    
    # Initial document indexing
    docs_path = Path("files_data")
    if docs_path.exists() and any(docs_path.iterdir()):
        logging.info("Found documents in files_data, checking if indexing needed...")
        try:
            existing_count = await mcp.execute_tool("get_document_count")
            if existing_count == 0:
                logging.info("No documents indexed, starting initial indexing...")
                docs = await mcp.execute_tool("process_documents", str(docs_path))
                if docs:
                    await mcp.execute_tool("index_documents", docs)
                    logging.info(f"Initially indexed {len(docs)} documents")
        except Exception as e:
            logging.error(f"Error during initial indexing: {e}")
    
    return mcp

def run_cli(mcp: MCPServer):
    console = Console()
    try:
        cli = CLIInterface(mcp)
        asyncio.run(cli.run())
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")
    finally:
        console.print("[yellow]Goodbye![/]")

def run_api(mcp: MCPServer):
    uvicorn.run(
        api_app, 
        host=config.api_host, 
        port=config.api_port
    )

def main():
    load_dotenv()
    setup_logging()
    
    parser = argparse.ArgumentParser(description="RAG-based AI Agent")
    parser.add_argument("--mode", choices=["cli", "api"], default="cli",
                       help="Run in CLI or API mode")
    args = parser.parse_args()
    
    mcp = asyncio.run(setup_mcp())
    
    if args.mode == "cli":
        run_cli(mcp)
    else:
        run_api(mcp)

if __name__ == "__main__":
    main()