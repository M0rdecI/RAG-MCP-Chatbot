from typing import Dict, Callable, Any, Optional
import logging
from pydantic import BaseModel
from enum import Enum
import inspect

class ToolCategory(str, Enum):
    DOCUMENT = "document"
    SEARCH = "search"
    LLM = "llm"
    UTILITY = "utility"
    OTHER = "other"

class ToolMetadata(BaseModel):
    name: str
    description: str
    category: ToolCategory
    async_support: bool = False
    version: str = "1.0.0"

class Tool:
    def __init__(
        self,
        func: Callable,
        metadata: ToolMetadata
    ):
        self.func = func
        self.metadata = metadata
        self.is_async = inspect.iscoroutinefunction(func)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[ToolCategory, Dict[str, Tool]] = {
            category: {} for category in ToolCategory
        }
    
    def register(
        self,
        name: str,
        description: str,
        category: ToolCategory = ToolCategory.OTHER,
        version: str = "1.0.0"
    ) -> Callable:
        """Decorator to register a tool with the registry."""
        def decorator(func: Callable) -> Callable:
            metadata = ToolMetadata(
                name=name,
                description=description,
                category=category,
                async_support=inspect.iscoroutinefunction(func),
                version=version
            )
            
            tool = Tool(func, metadata)
            self._tools[name] = tool
            self._categories[category][name] = tool
            
            logging.info(f"Registered tool: {name} ({category})")
            return func
        return decorator
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> Dict[str, ToolMetadata]:
        """List all tools or tools in a specific category."""
        if category:
            return {
                name: tool.metadata 
                for name, tool in self._categories[category].items()
            }
        return {
            name: tool.metadata 
            for name, tool in self._tools.items()
        }
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool from the registry."""
        if name in self._tools:
            tool = self._tools[name]
            del self._tools[name]
            del self._categories[tool.metadata.category][name]
            logging.info(f"Removed tool: {name}")
            return True
        return False
    
    def clear(self):
        """Clear all tools from the registry."""
        self._tools.clear()
        for category in self._categories:
            self._categories[category].clear()
        logging.info("Tool registry cleared")