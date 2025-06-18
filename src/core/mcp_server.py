from typing import Dict, Callable, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio
import inspect

class MCPServer:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def register_tool(self, name: str, tool: Callable):
        self.tools[name] = tool
        logging.info(f"Registered tool: {name}")
    
    async def execute_tool(self, tool_name: str, *args, **kwargs) -> Any:
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not registered")
        
        tool = self.tools[tool_name]
        
        try:
            if inspect.iscoroutinefunction(tool):
                # Handle async tools
                return await tool(*args, **kwargs)
            else:
                # Run synchronous tools in thread pool
                return await asyncio.get_event_loop().run_in_executor(
                    self.executor, 
                    tool, 
                    *args
                )
        except Exception as e:
            logging.error(f"Error executing tool {tool_name}: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)