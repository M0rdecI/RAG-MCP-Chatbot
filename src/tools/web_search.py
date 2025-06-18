from typing import List, Dict, Optional
import aiohttp
import logging
from bs4 import BeautifulSoup
import asyncio
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    score: float = Field(default=1.0)

class WebSearchTool:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.search_url = "https://api.duckduckgo.com/"
    
    async def _ensure_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def _clean_up(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    def _parse_results(self, html_content: str) -> List[Dict]:
        """Parse HTML content and extract relevant information"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # Find search result elements (adjust selectors based on actual response)
            for result in soup.select('.result'):
                title = result.select_one('.title')
                snippet = result.select_one('.snippet')
                url = result.select_one('a')
                
                if title and snippet and url:
                    results.append({
                        'title': title.text.strip(),
                        'content': snippet.text.strip(),
                        'metadata': {
                            'source': url['href'],
                            'type': 'web'
                        },
                        'score': 1.0  # Default relevance score
                    })
            
            return results[:3]  # Return top 3 results
        
        except Exception as e:
            logging.error(f"Error parsing search results: {e}")
            return []
    
    async def search(self, query: str) -> List[Dict]:
        """
        Perform a web search and return relevant results
        
        Args:
            query (str): The search query
            
        Returns:
            List[Dict]: List of search results with content and metadata
        """
        try:
            await self._ensure_session()
            
            params = {
                'q': query,
                'format': 'html'
            }
            
            async with self.session.get(self.search_url, params=params) as response:
                if response.status != 200:
                    logging.error(f"Search request failed: {response.status}")
                    return []
                
                html_content = await response.text()
                results = self._parse_results(html_content)
                
                if not results:
                    logging.warning(f"No results found for query: {query}")
                
                return results
                
        except Exception as e:
            logging.error(f"Web search error: {e}")
            return []
        
        finally:
            await self._clean_up()
    
    def __del__(self):
        """Ensure cleanup of aiohttp session"""
        if self.session and not self.session.closed:
            asyncio.create_task(self._clean_up())