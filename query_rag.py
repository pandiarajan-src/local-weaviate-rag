#!/usr/bin/env python3
"""
RAG Query Script for Local Weaviate RAG

This script performs hybrid search in Weaviate to retrieve relevant context
and queries GPT-4.1 (GPT-4-turbo) to generate responses based on the context.

Usage:
    python query_rag.py "What is machine learning?"
    python query_rag.py --query "Explain the concept" --max-results 3
"""

import argparse
import os
import sys
from typing import List, Dict, Any, Optional
import logging

from openai import OpenAI
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('query_rag.log')
    ]
)
logger = logging.getLogger(__name__)


class WeaviateSearcher:
    """Handles Weaviate connection and search operations."""
    
    def __init__(self, url: str, api_key: str = None, timeout: int = 60):
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.client = None
        self.collection_name = os.getenv('COLLECTION_NAME', 'DocumentChunks')
    
    def connect(self):
        """Connect to Weaviate instance."""
        try:
            auth = Auth.api_key(self.api_key) if self.api_key else None
            self.client = weaviate.connect_to_local(
                host=self.url.replace('http://', '').replace('https://', ''),
                auth=auth,
                timeout=self.timeout
            )
            logger.info(f"Connected to Weaviate at {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            return False
    
    def hybrid_search(self, query: str, limit: int = 5, alpha: float = 0.7) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and keyword search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            alpha: Weight for vector vs keyword search (0.0 = keyword only, 1.0 = vector only)
        
        Returns:
            List of search results with content and metadata
        """
        try:
            collection = self.client.collections.get(self.collection_name)
            
            # Perform hybrid search
            response = collection.query.hybrid(
                query=query,
                limit=limit,
                alpha=alpha,
                return_metadata=MetadataQuery(score=True, distance=True)
            )
            
            results = []
            for obj in response.objects:
                result = {
                    'content': obj.properties.get('content', ''),
                    'source': obj.properties.get('source', ''),
                    'chunk_index': obj.properties.get('chunk_index', 0),
                    'token_count': obj.properties.get('token_count', 0),
                    'score': obj.metadata.score if obj.metadata else 0,
                    'distance': obj.metadata.distance if obj.metadata else 0
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {str(e)}")
            raise
    
    def close(self):
        """Close Weaviate connection."""
        if self.client:
            self.client.close()
            logger.info("Closed Weaviate connection")


class RAGProcessor:
    """Handles RAG processing with OpenAI GPT models."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", 
                 max_tokens: int = 4096, temperature: float = 0.1):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate response using GPT model with retrieved context.
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks from Weaviate
        
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Prepare context
            context_text = self._prepare_context(context_chunks)
            
            # Create prompt
            prompt = self._create_prompt(query, context_text)
            
            logger.info(f"Generating response with {len(context_chunks)} context chunks")
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant that answers questions based on the provided context. "
                                   "Use only the information from the context to answer questions. "
                                   "If the context doesn't contain enough information to answer the question, "
                                   "say so clearly. Be accurate, concise, and cite relevant parts of the context."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False
            )
            
            result = {
                'response': response.choices[0].message.content,
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'context_sources': self._get_sources(context_chunks),
                'context_count': len(context_chunks)
            }
            
            logger.info(f"Generated response ({result['usage']['total_tokens']} tokens)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise
    
    def _prepare_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Prepare context text from retrieved chunks."""
        context_parts = []
        
        for i, chunk in enumerate(context_chunks, 1):
            source = chunk.get('source', 'Unknown')
            content = chunk.get('content', '')
            score = chunk.get('score', 0)
            
            context_part = f"[Context {i} - Source: {source}, Relevance: {score:.3f}]\n{content}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create the prompt for the GPT model."""
        return f"""Context Information:
{context}

Question: {query}

Please answer the question based on the context information provided above. If the context doesn't contain sufficient information to answer the question, please state that clearly."""
    
    def _get_sources(self, context_chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract unique sources from context chunks."""
        sources = set()
        for chunk in context_chunks:
            source = chunk.get('source', 'Unknown')
            if source:
                sources.add(source)
        return list(sources)


def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    
    config = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'weaviate_url': os.getenv('WEAVIATE_URL', 'http://localhost:8080'),
        'weaviate_api_key': os.getenv('WEAVIATE_API_KEY'),
        'weaviate_timeout': int(os.getenv('WEAVIATE_TIMEOUT', '60')),
        'gpt_model': os.getenv('GPT_MODEL', 'gpt-4-turbo-preview'),
        'max_tokens': int(os.getenv('MAX_TOKENS', '4096')),
        'temperature': float(os.getenv('TEMPERATURE', '0.1')),
        'max_chunks_per_query': int(os.getenv('MAX_CHUNKS_PER_QUERY', '5')),
        'collection_name': os.getenv('COLLECTION_NAME', 'DocumentChunks'),
    }
    
    # Validate required config
    if not config['openai_api_key']:
        raise ValueError("OPENAI_API_KEY is required")
    
    return config


def validate_query(query: str) -> str:
    """Validate and sanitize user query."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    query = query.strip()
    
    # Basic length validation
    if len(query) > 10000:
        raise ValueError("Query too long (max 10000 characters)")
    
    return query


def print_results(query: str, result: Dict[str, Any], context_chunks: List[Dict[str, Any]], 
                 verbose: bool = False):
    """Print results in a formatted way."""
    print("=" * 80)
    print(f"Query: {query}")
    print("=" * 80)
    
    print(f"\n📝 Response:")
    print("-" * 40)
    print(result['response'])
    
    if verbose:
        print(f"\n📊 Metadata:")
        print("-" * 40)
        print(f"Model: {result['model']}")
        print(f"Tokens used: {result['usage']['total_tokens']} "
              f"(prompt: {result['usage']['prompt_tokens']}, "
              f"completion: {result['usage']['completion_tokens']})")
        print(f"Context chunks: {result['context_count']}")
        
        print(f"\n📚 Sources:")
        print("-" * 40)
        for source in result['context_sources']:
            print(f"• {source}")
        
        print(f"\n🔍 Context Details:")
        print("-" * 40)
        for i, chunk in enumerate(context_chunks, 1):
            print(f"Chunk {i}: {chunk['source']} (score: {chunk.get('score', 0):.3f})")
            if verbose:
                content_preview = chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
                print(f"  Content: {content_preview}")
                print()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Query the RAG system for answers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python query_rag.py "What is machine learning?"
    python query_rag.py --query "Explain neural networks" --max-results 3
    python query_rag.py "How does AI work?" --verbose
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('query', nargs='?', help='Query to search for')
    group.add_argument('--query', '-q', help='Query to search for')
    
    parser.add_argument('--max-results', '-m', type=int, default=5,
                       help='Maximum number of context chunks to retrieve (default: 5)')
    parser.add_argument('--alpha', '-a', type=float, default=0.7,
                       help='Hybrid search weight: 0.0=keyword only, 1.0=vector only (default: 0.7)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output with metadata')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get query (from positional argument or named argument)
    query = getattr(args, 'query', None)
    
    try:
        # Validate query
        query = validate_query(query)
        
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Override max results from config if specified
        max_results = min(args.max_results, config['max_chunks_per_query'])
        
        # Initialize components
        searcher = WeaviateSearcher(
            url=config['weaviate_url'],
            api_key=config['weaviate_api_key'],
            timeout=config['weaviate_timeout']
        )
        
        rag_processor = RAGProcessor(
            api_key=config['openai_api_key'],
            model=config['gpt_model'],
            max_tokens=config['max_tokens'],
            temperature=config['temperature']
        )
        
        # Connect to Weaviate
        logger.info("Connecting to Weaviate...")
        if not searcher.connect():
            logger.error("Failed to connect to Weaviate. Make sure it's running.")
            print("❌ Failed to connect to Weaviate. Please ensure Weaviate is running.")
            print("   Run: ./start_weaviate.sh")
            sys.exit(1)
        
        # Perform hybrid search
        logger.info(f"Searching for: {query}")
        context_chunks = searcher.hybrid_search(
            query=query,
            limit=max_results,
            alpha=args.alpha
        )
        
        if not context_chunks:
            print("❌ No relevant context found for your query.")
            print("   Make sure you have embedded some text using embed_text.py")
            sys.exit(1)
        
        # Generate response
        logger.info("Generating response...")
        result = rag_processor.generate_response(query, context_chunks)
        
        # Print results
        print_results(query, result, context_chunks, args.verbose)
        
        logger.info("✅ Query processed successfully")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n❌ Operation cancelled")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        print(f"❌ {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ An error occurred: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            searcher.close()
        except:
            pass


if __name__ == "__main__":
    main()