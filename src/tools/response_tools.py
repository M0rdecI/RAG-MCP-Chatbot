from typing import List, Dict
from rich.markdown import Markdown
import random
import logging
from functools import lru_cache

class ResponseFormatterTool:
    def __init__(self):
        pass
    
    @lru_cache(maxsize=100)
    def _clean_text(self, text: str) -> str:
        """Cached text cleaning for repeated content"""
        # Clean up common OCR artifacts and formatting issues
        text = text.replace('\n', ' ')
        text = ' '.join(text.split())
        text = text.replace(' :', ':')
        text = text.replace(' .', '.')
        text = text.replace(' ,', ',')
        text = text.replace('F or', 'For')
        text = text.replace('T o', 'To')
        text = text.replace('Y ou', 'You')
        return text
    
    def _extract_section(self, text: str, query: str) -> str:
        """Extract relevant section based on query"""
        sentences = text.split('.')
        relevant_sentences = []
        
        # Try to find the most relevant starting point
        start_idx = 0
        for idx, sentence in enumerate(sentences):
            if any(keyword in sentence.lower() for keyword in query.lower().split()):
                start_idx = idx
                break
        
        # Take a context window of sentences
        window_size = 5
        context_window = sentences[start_idx:start_idx + window_size]
        return '. '.join(s.strip() for s in context_window if s.strip()) + '.'
    
    def _format_response(self, content: str, query_type: str) -> str:
        """Format response based on query type"""
        templates = {
            "greeting": lambda x: f"Hello! {x}",
            "farewell": lambda x: f"{x} Feel free to return if you need help!",
            "error": lambda x: f"I apologize, but {x}. How can I assist you differently?",
            "information": lambda x: f"Here's what you need to know: {x}",
            "instruction": lambda x: f"Follow these steps: {x}",
            "confirmation": lambda x: f"Great! {x}"
        }
        
        template = templates.get(query_type, templates["information"])
        return template(content)
    
    def _classify_query(self, query: str) -> str:
        """Classify query type for appropriate response formatting"""
        query_lower = query.lower()
        
        classifiers = {
            "greeting": ["hello", "hi", "hey", "good"],
            "farewell": ["bye", "goodbye", "thank"],
            "help": ["help", "assist", "support", "how"],
            "problem": ["error", "issue", "problem", "wrong"],
            "information": ["what", "tell", "explain", "describe"]
        }
        
        for q_type, keywords in classifiers.items():
            if any(word in query_lower for word in keywords):
                return q_type
        
        return "information"
    
    async def format(self, query: str, results: List[Dict]) -> str:
        try:
            if not results:
                return None
            
            # Get most relevant content
            content = results[0]['content']
            cleaned_content = self._clean_text(content)
            relevant_section = self._extract_section(cleaned_content, query)
            
            # Return clean content for LLM context without formatting
            return relevant_section
            
        except Exception as e:
            logging.error(f"Error formatting response: {e}")
            return None
        
    async def format_batch(self, queries: List[Dict]) -> List[str]:
        """Process multiple queries efficiently"""
        responses = []
        for query in queries:
            cleaned_context = await self._clean_text(query['context'])
            response = await self._format_response(
                cleaned_context,
                self._classify_query(query['text'])
            )
            responses.append(response)
        return responses