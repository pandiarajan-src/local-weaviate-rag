#!/usr/bin/env python3
"""
Query Processing System for Local Weaviate RAG

This script processes user queries using hybrid search in Weaviate and 
generates responses using OpenAI's GPT-4.1 model.
"""

import sys
import json
import argparse
from typing import List, Dict, Any, Optional
import weaviate
from openai import OpenAI
from config import Config

class WeaviateSearcher:
    """Handles search operations in Weaviate"""
    
    def __init__(self, url: str):
        self.client = weaviate.Client(url)
        self.collection_name = Config.COLLECTION_NAME
    
    def hybrid_search(self, query: str, limit: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + keyword) in Weaviate
        
        Args:
            query: Search query
            limit: Maximum number of results
            alpha: Balance between vector (1.0) and keyword (0.0) search
            
        Returns:
            List of search results with metadata
        """
        try:
            result = (
                self.client.query
                .get(self.collection_name, [
                    "text", 
                    "source", 
                    "chunk_id", 
                    "start_token", 
                    "end_token",
                    "metadata"
                ])
                .with_hybrid(query=query, alpha=alpha)
                .with_limit(limit)
                .with_additional(["score", "distance"])
                .do()
            )
            
            documents = result.get("data", {}).get("Get", {}).get(self.collection_name, [])
            return documents
            
        except Exception as e:
            print(f"Error performing hybrid search: {e}")
            return []
    
    def vector_search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform pure vector search in Weaviate
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            
        Returns:
            List of search results with metadata
        """
        try:
            result = (
                self.client.query
                .get(self.collection_name, [
                    "text", 
                    "source", 
                    "chunk_id", 
                    "start_token", 
                    "end_token",
                    "metadata"
                ])
                .with_near_vector({"vector": query_vector})
                .with_limit(limit)
                .with_additional(["distance"])
                .do()
            )
            
            documents = result.get("data", {}).get("Get", {}).get(self.collection_name, [])
            return documents
            
        except Exception as e:
            print(f"Error performing vector search: {e}")
            return []

class RAGQueryProcessor:
    """Main RAG query processing system"""
    
    def __init__(self):
        Config.validate()
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.searcher = WeaviateSearcher(Config.WEAVIATE_URL)
    
    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for the query"""
        try:
            response = self.openai_client.embeddings.create(
                model=Config.EMBEDDING_MODEL,
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting query embedding: {e}")
            raise
    
    def search_documents(self, query: str, search_type: str = "hybrid", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query: User query
            search_type: Type of search ("hybrid", "vector", "keyword")
            limit: Maximum number of results
            
        Returns:
            List of relevant documents
        """
        if search_type == "hybrid":
            return self.searcher.hybrid_search(query, limit)
        elif search_type == "vector":
            query_vector = self.get_query_embedding(query)
            return self.searcher.vector_search(query_vector, limit)
        else:
            raise ValueError(f"Unsupported search type: {search_type}")
    
    def generate_response(self, query: str, context_documents: List[Dict[str, Any]], 
                         system_prompt: Optional[str] = None) -> str:
        """
        Generate response using GPT-4.1 with retrieved context
        
        Args:
            query: User query
            context_documents: Retrieved documents for context
            system_prompt: Optional custom system prompt
            
        Returns:
            Generated response
        """
        # Prepare context from retrieved documents
        context_texts = []
        for i, doc in enumerate(context_documents, 1):
            source = doc.get("source", "unknown")
            chunk_id = doc.get("chunk_id", "unknown")
            text = doc.get("text", "")
            
            context_texts.append(f"[Source {i}: {source}, Chunk {chunk_id}]\n{text}")
        
        context = "\n\n".join(context_texts)
        
        # Default system prompt if none provided
        if not system_prompt:
            system_prompt = """You are a helpful AI assistant that answers questions based on the provided context documents. 

Instructions:
1. Use only the information provided in the context documents to answer the question
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Provide specific references to the source documents when possible
4. Be concise but comprehensive in your response
5. If there are conflicting information in the sources, acknowledge this"""
        
        # Prepare messages for GPT-4
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Context Documents:
{context}

Question: {query}

Please provide a comprehensive answer based on the context documents above."""}
        ]
        
        try:
            response = self.openai_client.chat.completions.create(
                model=Config.CHAT_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating response: {e}")
            raise
    
    def process_query(self, query: str, search_type: str = "hybrid", 
                     limit: int = 5, verbose: bool = False) -> Dict[str, Any]:
        """
        Process a complete RAG query
        
        Args:
            query: User query
            search_type: Type of search to use
            limit: Maximum number of context documents
            verbose: Whether to include detailed information
            
        Returns:
            Dictionary containing response and metadata
        """
        print(f"Processing query: {query}")
        
        # Search for relevant documents
        print(f"Searching for relevant documents using {search_type} search...")
        context_documents = self.search_documents(query, search_type, limit)
        
        if not context_documents:
            return {
                "query": query,
                "response": "I couldn't find any relevant documents to answer your question. Please make sure documents have been ingested into the system.",
                "context_documents": [],
                "search_type": search_type
            }
        
        print(f"Found {len(context_documents)} relevant documents")
        
        # Generate response
        print("Generating response using GPT-4...")
        response = self.generate_response(query, context_documents)
        
        result = {
            "query": query,
            "response": response,
            "context_documents": context_documents,
            "search_type": search_type
        }
        
        if verbose:
            print("\n" + "="*80)
            print("QUERY PROCESSING RESULTS")
            print("="*80)
            print(f"Query: {query}")
            print(f"Search Type: {search_type}")
            print(f"Documents Found: {len(context_documents)}")
            print("\nContext Documents:")
            for i, doc in enumerate(context_documents, 1):
                print(f"\n[Document {i}]")
                print(f"Source: {doc.get('source', 'unknown')}")
                print(f"Chunk ID: {doc.get('chunk_id', 'unknown')}")
                if 'score' in doc.get('_additional', {}):
                    print(f"Score: {doc['_additional']['score']:.4f}")
                if 'distance' in doc.get('_additional', {}):
                    print(f"Distance: {doc['_additional']['distance']:.4f}")
                print(f"Text: {doc.get('text', '')[:200]}...")
            
            print(f"\nGenerated Response:\n{response}")
            print("="*80)
        
        return result

def interactive_mode():
    """Run in interactive mode for continuous querying"""
    try:
        processor = RAGQueryProcessor()
        print("🤖 Local Weaviate RAG System - Interactive Mode")
        print("Type 'quit', 'exit', or 'q' to stop")
        print("Type 'help' for available commands")
        print("-" * 50)
        
        while True:
            try:
                query = input("\n🔍 Enter your query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye! 👋")
                    break
                
                if query.lower() == 'help':
                    print("""
Available commands:
- Enter any question to search and get an answer
- 'quit', 'exit', 'q': Exit the system
- 'help': Show this help message

The system uses hybrid search (combining vector and keyword search) by default.
                    """)
                    continue
                
                if not query:
                    print("Please enter a valid query.")
                    continue
                
                # Process the query
                result = processor.process_query(query, verbose=True)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\nError processing query: {e}")
                
    except Exception as e:
        print(f"Error starting interactive mode: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Query the local Weaviate RAG system"
    )
    parser.add_argument(
        "--query", "-q",
        help="Query to process"
    )
    parser.add_argument(
        "--search-type", "-s",
        choices=["hybrid", "vector"],
        default="hybrid",
        help="Type of search to use (default: hybrid)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=5,
        help="Maximum number of context documents (default: 5)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            interactive_mode()
            return
        
        if not args.query:
            print("Please provide a query with --query option or use --interactive mode")
            print("Use --help for more information")
            sys.exit(1)
        
        # Process single query
        processor = RAGQueryProcessor()
        result = processor.process_query(
            args.query, 
            search_type=args.search_type, 
            limit=args.limit,
            verbose=args.verbose
        )
        
        # Output results
        if not args.verbose:
            print(f"\nQuery: {result['query']}")
            print(f"Response: {result['response']}")
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()