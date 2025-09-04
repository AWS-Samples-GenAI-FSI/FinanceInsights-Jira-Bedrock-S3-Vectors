import re
from typing import List, Dict, Any

class TextChunker:
    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_ticket(self, ticket: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk a Jira ticket into smaller pieces for better retrieval"""
        
        # Combine ticket text
        title = ticket.get('summary', '')
        description = self._extract_description_text(ticket.get('description', ''))
        
        # Create base metadata
        base_metadata = {
            'key': ticket.get('key', ''),
            'status': ticket.get('status', ''),
            'priority': ticket.get('priority', ''),
            'assignee': ticket.get('assignee', ''),
            'component': ticket.get('component', ''),
            'created': ticket.get('created', ''),
            'updated': ticket.get('updated', '')
        }
        
        chunks = []
        
        # Chunk 1: Title + summary info (always include)
        title_chunk = {
            'text': f"Title: {title}\nStatus: {base_metadata['status']}\nPriority: {base_metadata['priority']}\nComponent: {base_metadata['component']}",
            'chunk_type': 'title',
            'chunk_id': f"{base_metadata['key']}_title",
            **base_metadata
        }
        chunks.append(title_chunk)
        
        # Chunk 2+: Description chunks (if description exists)
        if description and len(description.strip()) > 0:
            desc_chunks = self._split_text(description)
            
            for i, chunk_text in enumerate(desc_chunks):
                desc_chunk = {
                    'text': f"Ticket: {title}\n\nDescription: {chunk_text}",
                    'chunk_type': 'description',
                    'chunk_id': f"{base_metadata['key']}_desc_{i}",
                    **base_metadata
                }
                chunks.append(desc_chunk)
        
        return chunks
    
    def _extract_description_text(self, description) -> str:
        """Extract plain text from description (handles both string and Atlassian Document Format)"""
        if not description:
            return ''
        
        # If it's already a string, return as-is
        if isinstance(description, str):
            return description
        
        # If it's Atlassian Document Format, extract text
        if isinstance(description, dict) and description.get('type') == 'doc':
            text_parts = []
            content = description.get('content', [])
            
            for block in content:
                if block.get('type') == 'paragraph':
                    paragraph_content = block.get('content', [])
                    for item in paragraph_content:
                        if item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
            
            return ' '.join(text_parts)
        
        # Fallback: convert to string
        return str(description)
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_end = text.rfind('.', start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind('!', start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind('?', start, end)
                
                # If found sentence boundary, use it
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + self.chunk_size // 2:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.overlap
            if start >= len(text):
                break
        
        return chunks