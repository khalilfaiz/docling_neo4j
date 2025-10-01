"""LLM integration for answer generation with citations."""

from typing import List, Dict, Any, Optional
import re
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))


class LLMProcessor:
    """Process queries and generate answers using LLM with proper citations."""
    
    def __init__(self, llm_provider: str = "openai", api_key: Optional[str] = None):
        self.llm_provider = llm_provider
        self.api_key = api_key
        self._init_llm_client()
    
    def _init_llm_client(self):
        """Initialize LLM client based on provider."""
        if self.llm_provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                print("OpenAI not installed. Install with: pip install openai")
                self.client = None
        elif self.llm_provider == "ollama":
            try:
                import ollama
                self.client = ollama.Client()
            except ImportError:
                print("Ollama not installed. Install with: pip install ollama")
                self.client = None
        else:
            self.client = None
    
    def generate_answer_with_citations(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate answer using LLM with inline citations."""
        if not self.client or not search_results:
            return self._fallback_answer(query, search_results)
        
        # Prepare context from search results
        context_parts = []
        for i, result in enumerate(search_results[:5]):  # Top 5 results
            chunk_id = result["chunk_id"]
            text = result["text"]
            section = " > ".join(result.get("section_headings", []))
            
            context_parts.append(
                f"[{chunk_id}] (Page {result['page_num']}, {section}): {text}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Create prompt
        prompt = f"""You are a helpful assistant analyzing documents. Based on the following document excerpts, 
answer the user's question accurately. Include citations in the format [chunk_id] immediately after 
relevant statements. Be specific and cite your sources.

Document Context:
{context}

User Question: {query}

Instructions:
1. Answer the question based ONLY on the provided context
2. Include citations [chunk_id] after each relevant statement
3. If the context doesn't contain enough information, say so
4. Be concise but comprehensive

Answer:"""
        
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a document analysis assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                return response.choices[0].message.content
            
            elif self.llm_provider == "ollama":
                response = self.client.chat(
                    model="llama2",
                    messages=[
                        {"role": "system", "content": "You are a document analysis assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response['message']['content']
            
        except Exception as e:
            print(f"LLM error: {e}")
            return self._fallback_answer(query, search_results)
    
    def _fallback_answer(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Fallback answer generation without LLM."""
        if not search_results:
            return "No relevant information found in the documents."
        
        # Simple keyword-based answer
        answer_parts = [f"Based on the search for '{query}', here are the relevant findings:\n"]
        
        for i, result in enumerate(search_results[:3]):
            chunk_id = result["chunk_id"]
            text = result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"]
            answer_parts.append(f"\n{i+1}. {text} [{chunk_id}]")
        
        return "\n".join(answer_parts)
    
    def extract_query_intent(self, query: str) -> Dict[str, Any]:
        """Extract intent and key concepts from query using LLM."""
        if not self.client:
            return {"original_query": query, "concepts": [], "intent": "search"}
        
        prompt = f"""Analyze this query and extract:
1. The main intent (search, compare, explain, etc.)
2. Key concepts or entities
3. Any specific requirements

Query: {query}

Return as JSON with keys: intent, concepts, requirements"""
        
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                import json
                return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Intent extraction error: {e}")
        
        return {"original_query": query, "concepts": [], "intent": "search"}
    
    def generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations for better retrieval."""
        variations = [query]  # Original query
        
        if not self.client:
            # Simple variations without LLM
            variations.extend([
                query.lower(),
                query.replace("?", ""),
                " ".join(query.split()[:5])  # First 5 words
            ])
            return list(set(variations))
        
        prompt = f"""Generate 3 alternative phrasings of this question that would help find relevant information:
Question: {query}

Return only the alternative questions, one per line."""
        
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=150
                )
                alt_queries = response.choices[0].message.content.strip().split("\n")
                variations.extend([q.strip() for q in alt_queries if q.strip()])
            
        except Exception as e:
            print(f"Query variation error: {e}")
        
        return variations[:4]  # Return up to 4 variations
