"""
Streaming utilities and helpers
Provides additional streaming functionality and response processing
"""

from typing import AsyncGenerator, Dict, Any, Optional
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
import asyncio


class StreamingResponseProcessor:
    """Processes streaming responses with additional features"""
    
    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size
        self.response_buffer = ""
    
    async def process_stream(
        self, 
        agent, 
        query: str, 
        context=None, 
        session=None
    ) -> AsyncGenerator[str, None]:
        """
        Process streaming response with buffering and processing
        
        Args:
            agent: The agent to run
            query: User query
            context: Optional context
            session: Optional session
            
        Yields:
            Processed response chunks
        """
        try:
            result = Runner.run_streamed(
                agent,
                query, 
                context=context,
                session=session
            )
            
            chunk_buffer = ""
            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    chunk = event.data.delta
                    chunk_buffer += chunk
                    
                    # Yield buffered chunks
                    if len(chunk_buffer) >= self.buffer_size:
                        yield chunk_buffer
                        chunk_buffer = ""
            
            # Yield remaining buffer
            if chunk_buffer:
                yield chunk_buffer
                
        except Exception as e:
            yield f"❌ **Streaming Error**: {str(e)}"
    
    def format_response_chunk(self, chunk: str) -> str:
        """Format response chunks for display"""
        # Add any special formatting here
        return chunk


# Export utilities
__all__ = ['StreamingResponseProcessor']