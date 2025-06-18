import asyncio
from typing import List, Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.markdown import Markdown
from core.mcp_server import MCPServer
from utils.chat_store import ChatStore, ChatMessage
import time
from datetime import datetime
from pathlib import Path
import logging

class CLIInterface:
    def __init__(self, mcp_server: MCPServer):
        self.console = Console()
        self.mcp = mcp_server
        self.chat_store = ChatStore()
        self.session_id = f"session_{int(time.time())}"
        
        # Load existing history if any
        self.history = self.chat_store.get_session_history(self.session_id)
    
    async def _process_query(self, query: str):
        """Process query with fallback strategy"""
        try:
            # Get context from vector store
            results = await self.mcp.execute_tool("query_vector_store", query)
            
            # Get formatted context if available
            context = None
            if results:
                context = await self.mcp.execute_tool(
                    "format_response", 
                    query, 
                    results
                )
            
            # Generate response using LLM with context
            response = await self.mcp.execute_tool(
                "generate_response",
                query,
                context
            )
            
            # Store in conversation history
            if hasattr(self.mcp.tools["generate_response"], "conversation_history"):
                self.conversation_history = (
                    self.mcp.tools["generate_response"].conversation_history
                )
        
            return response, results, False
        
        except Exception as e:
            logging.error(f"Error processing query: {e}")
            return ("I apologize, but I'm having trouble processing your request. "
                    "Please try again."), [], False

    async def _animate_response(self, query: str):
        """Show animated spinner while processing"""
        spinner = Spinner("dots", text=Text("Processing...", style="yellow"))
        with Live(spinner, refresh_per_second=10) as live:
            start_time = time.time()
            response, _, _ = await self._process_query(query)
            elapsed = time.time() - start_time
            
            # Clean panel display
            live.update(Panel(
                Markdown(response),
                title="Assistant",
                subtitle=f"Time: {elapsed:.2f}s",
                style="green",
                padding=(1, 2)
            ))
            
            # Store messages
            user_msg = ChatMessage(
                role="user",
                content=query,
                timestamp=datetime.now().isoformat()
            )
            response_msg = ChatMessage(
                role="assistant",
                content=response,
                timestamp=datetime.now().isoformat(),
                sources=[]
            )
            self.chat_store.add_message(self.session_id, user_msg)
            self.chat_store.add_message(self.session_id, response_msg)
            self.history.extend([user_msg, response_msg])
    
    def _display_history(self):
        """Display chat history with rich formatting"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Time", style="dim")
        table.add_column("Role", min_width=10)
        table.add_column("Content", min_width=40)
        
        for msg in self.history:
            time_str = datetime.fromisoformat(msg.timestamp).strftime("%H:%M:%S")
            role_style = "blue" if msg.role == "user" else "green"
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            table.add_row(
                time_str,
                Text(msg.role.capitalize(), style=role_style),
                content
            )
        
        self.console.print(Panel(table, title="Chat History"))
    
    async def _handle_index_command(self, cmd: List[str]):
        """Handle document indexing command"""
        path = cmd[1] if len(cmd) > 1 else "files_data"
        path = Path(path)
        
        if not path.exists():
            self.console.print(f"❌ Directory not found: {path}", style="red")
            return
        
        if not any(path.iterdir()):
            self.console.print("❌ Directory is empty", style="red")
            return
        
        self.console.print(f"📁 Indexing documents from {path}...", style="yellow")
        
        # Process documents
        docs = await self.mcp.execute_tool("process_documents", str(path))
        if not docs:
            self.console.print("❌ No supported documents found to process", style="red")
            return
        
        # Show document summary
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File")
        table.add_column("Type")
        table.add_column("Size")
        
        for doc in docs:
            table.add_row(
                doc['metadata']['source'],
                doc['metadata']['type'],
                f"{len(doc['content'])} chars"
            )
        
        self.console.print(Panel(table, title="Processed Documents"))
        
        # Index the documents
        success = await self.mcp.execute_tool("index_documents", docs)
        if success:
            doc_count = await self.mcp.execute_tool("get_document_count")
            self.console.print(
                f"✅ Successfully indexed {len(docs)} documents. "
                f"Total documents in store: {doc_count}",
                style="green"
            )
        else:
            self.console.print("❌ Failed to index documents", style="red")
    
    async def run(self):
        self.console.print(Panel(
            "[bold green] RAG based AI Assistant[/]\n"
            "[dim]Type /help for commands[/]",
            subtitle=f"Session: {self.session_id}"
        ))
        
        while True:
            try:
                user_input = self.console.input("[bold blue]>> [/]").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    cmd = user_input[1:].lower().split()
                    if not cmd:
                        continue
                        
                    if cmd[0] == "index":
                        await self._handle_index_command(cmd)
                    
                    elif cmd[0] == "exit":
                        break
                    
                    elif cmd[0] == "history":
                        self._display_history()
                    
                    elif cmd[0] == "clear":
                        self.chat_store.clear_session(self.session_id)
                        self.history = []
                        self.console.print("🗑️ Chat history cleared", style="yellow")
                    
                    elif cmd[0] == "help":
                        help_text = """[bold]Available commands:[/]
/index [path] - Index documents from directory
/history - Show chat history
/clear - Clear current session history
/exit - Exit the application
/help - Show this help"""
                        self.console.print(Panel(help_text, style="cyan"))
                    
                    else:
                        self.console.print("❌ Unknown command", style="red")
                else:
                    await self._animate_response(user_input)
            
            except KeyboardInterrupt:
                self.console.print("\n🛑 Interrupted. Type /exit to quit.", style="red")
                continue
            except Exception as e:
                self.console.print(f"❌ Error: {str(e)}", style="red")