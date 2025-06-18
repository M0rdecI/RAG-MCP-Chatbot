from typing import List, Dict
import ollama
from ollama import AsyncClient
from pydantic import BaseModel
import logging

class OllamaConfig(BaseModel):
    model: str = "qwen2:7b"
    temperature: float = 0.7
    system_prompt: str = """
        You are a helpful and friendly AI assistant for [provide context of what you need the chatbot to do]. 
        Your primary role is to help users with parking-related queries and provide information about [the system in question].

        RESPONSE GUIDELINES:
        1. Be naturally conversational and friendly
        2. Acknowledge the user's query
        3. Provide clear, concise information
        4. Use a professional yet approachable tone
        5. Format responses in clear, readable paragraphs
        6. Maintain context from previous exchanges
        7. If referencing documentation, present it naturally without technical markers
        8. Handle greetings and farewells naturally without using templates

        When you don't have specific information:
        - Be honest about limitations
        - Suggest alternatives or direct to customer support
        - Maintain the friendly tone

        Remember: You're having a natural conversation, not reading from a manual."""

class OllamaTool:
    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()
        self._client_pool = []
        self._max_clients = 4
        self.conversation_history = []
        self._verify_model()
    
    async def _get_client(self):
        """Get an available client from the pool or create new one"""
        if not self._client_pool:
            client = AsyncClient()
            self._client_pool.append(client)
            return client
        return self._client_pool[0]  # Simple round-robin
    
    def _verify_model(self):
        """Verify model exists and pull if needed"""
        try:
            response = ollama.list()
            available_models = [m.get('model') for m in response.get('models', [])]
            
            if not self.config.model in available_models:
                logging.warning(f"Model {self.config.model} not found. Pulling...")
                try:
                    ollama.pull(self.config.model)
                    logging.info(f"Successfully pulled model {self.config.model}")
                except Exception as pull_error:
                    logging.error(f"Failed to pull model: {pull_error}")
                    raise RuntimeError(f"Could not pull required model {self.config.model}")
        except Exception as e:
            logging.error(f"Error verifying Ollama model: {e}")
            raise RuntimeError("Failed to verify Ollama model availability") from e
    
    def _build_context(self, prompt: str, context: str = None, relevant_history: List[Dict] = None) -> str:
        """Build context from conversation history and provided context"""
        parts = []
        
        # Add relevant history if available
        if relevant_history:
            history_context = "\n".join([
                f"User: {msg['user']}\nAssistant: {msg['assistant']}"
                for msg in relevant_history
            ])
            parts.append(f"Previous conversation:\n{history_context}")
        
        # Add document context if available
        if context:
            parts.append(f"Reference information:\n{context}")
        
        # Add current query
        parts.append(f"Current question: {prompt}")
        
        return "\n\n".join(parts)
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Smartly truncate text to max length at sentence boundary"""
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period != -1:
            return truncated[:last_period + 1]
        return truncated
    
    def _get_relevant_history(self, query: str, max_items: int = 3) -> List[Dict]:
        """Get most relevant conversation history items"""
        if not self.conversation_history:
            return []
            
        # Calculate simple relevance scores
        scores = []
        for item in self.conversation_history:
            score = sum(
                word in item['assistant'].lower() 
                for word in query.lower().split()
            )
            scores.append((item, score))
        
        # Get top relevant items
        relevant = sorted(scores, key=lambda x: x[1], reverse=True)[:max_items]
        return [item for item, _ in relevant]
    
    async def generate_response(self, prompt: str, context: str = None) -> str:
        try:
            # Smart context truncation
            max_context_length = 2000
            if context and len(context) > max_context_length:
                context = self._smart_truncate(context, max_context_length)
            
            # Use semantic similarity for history relevance
            relevant_history = self._get_relevant_history(prompt)
            
            conversation_context = self._build_context(
                prompt, 
                context, 
                relevant_history
            )

            client = await self._get_client()
            response = await client.generate(
                model=self.config.model,
                prompt=conversation_context,
                system=self.config.system_prompt,
                options={
                    'temperature': self.config.temperature
                },
                stream=False
            )
            
            # Store the exchange
            self.conversation_history.append({
                'user': prompt,
                'assistant': response['response']
            })
            
            return response['response']
            
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"I encountered an error processing your request: {str(e)}"