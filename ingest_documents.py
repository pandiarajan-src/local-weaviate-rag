#!/usr/bin/env python3
"""
Document Ingestion System for Local Weaviate RAG

This script processes documents, chunks them, creates embeddings using OpenAI's 
text-embedding-3-small model, and stores them in a local Weaviate instance.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any
import tiktoken
import weaviate
from openai import OpenAI
from config import Config

class DocumentChunker:
    """Handles text chunking with overlap"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces with overlap
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to include with each chunk
            
        Returns:
            List of chunks with metadata
        """
        if not text.strip():
            return []
        
        # Encode text to tokens
        tokens = self.encoding.encode(text)
        chunks = []
        
        start = 0
        chunk_id = 0
        
        while start < len(tokens):
            # Calculate end position
            end = start + self.chunk_size
            
            # Get chunk tokens
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # Create chunk metadata
            chunk_metadata = {
                "chunk_id": chunk_id,
                "start_token": start,
                "end_token": min(end, len(tokens)),
                "total_tokens": len(tokens),
                "chunk_tokens": len(chunk_tokens)
            }
            
            # Add original metadata if provided
            if metadata:
                chunk_metadata.update(metadata)
            
            chunks.append({
                "text": chunk_text.strip(),
                "metadata": chunk_metadata
            })
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            chunk_id += 1
            
            # Break if we've processed all tokens
            if end >= len(tokens):
                break
        
        return chunks

class WeaviateManager:
    """Manages Weaviate connection and operations"""
    
    def __init__(self, url: str):
        self.client = weaviate.Client(url)
        self.collection_name = Config.COLLECTION_NAME
    
    def create_schema(self):
        """Create Weaviate schema for document storage"""
        schema = {
            "class": self.collection_name,
            "description": "Document chunks with embeddings for RAG",
            "vectorizer": "none",  # We'll provide our own vectors
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"],
                    "description": "The text content of the chunk"
                },
                {
                    "name": "source",
                    "dataType": ["string"],
                    "description": "Source document or file"
                },
                {
                    "name": "chunk_id",
                    "dataType": ["int"],
                    "description": "Chunk identifier within document"
                },
                {
                    "name": "start_token",
                    "dataType": ["int"],
                    "description": "Starting token position"
                },
                {
                    "name": "end_token",
                    "dataType": ["int"],
                    "description": "Ending token position"
                },
                {
                    "name": "total_tokens",
                    "dataType": ["int"],
                    "description": "Total tokens in original document"
                },
                {
                    "name": "chunk_tokens",
                    "dataType": ["int"],
                    "description": "Number of tokens in this chunk"
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "Additional metadata as JSON"
                }
            ]
        }
        
        # Check if schema already exists
        existing_classes = self.client.schema.get()["classes"]
        existing_names = [cls["class"] for cls in existing_classes]
        
        if self.collection_name not in existing_names:
            self.client.schema.create_class(schema)
            print(f"✓ Created schema for class '{self.collection_name}'")
        else:
            print(f"✓ Schema for class '{self.collection_name}' already exists")
    
    def add_documents(self, chunks_with_embeddings: List[Dict[str, Any]]):
        """Add document chunks with embeddings to Weaviate"""
        with self.client.batch as batch:
            batch.batch_size = 50
            
            for i, item in enumerate(chunks_with_embeddings):
                properties = {
                    "text": item["text"],
                    "source": item["metadata"].get("source", "unknown"),
                    "chunk_id": item["metadata"]["chunk_id"],
                    "start_token": item["metadata"]["start_token"],
                    "end_token": item["metadata"]["end_token"],
                    "total_tokens": item["metadata"]["total_tokens"],
                    "chunk_tokens": item["metadata"]["chunk_tokens"],
                    "metadata": json.dumps(item["metadata"])
                }
                
                batch.add_data_object(
                    data_object=properties,
                    class_name=self.collection_name,
                    vector=item["embedding"]
                )
                
                if (i + 1) % 10 == 0:
                    print(f"  Added {i + 1}/{len(chunks_with_embeddings)} chunks...")
        
        print(f"✓ Successfully added {len(chunks_with_embeddings)} chunks to Weaviate")

class DocumentIngestor:
    """Main document ingestion orchestrator"""
    
    def __init__(self):
        Config.validate()
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.chunker = DocumentChunker(Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
        self.weaviate_manager = WeaviateManager(Config.WEAVIATE_URL)
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from OpenAI for a list of texts"""
        try:
            response = self.openai_client.embeddings.create(
                model=Config.EMBEDDING_MODEL,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            raise
    
    def process_text(self, text: str, source: str = "manual_input") -> int:
        """
        Process a single text document
        
        Args:
            text: The text content to process
            source: Source identifier for the document
            
        Returns:
            Number of chunks created
        """
        print(f"Processing text from source: {source}")
        
        # Chunk the document
        chunks = self.chunker.chunk_text(text, {"source": source})
        
        if not chunks:
            print("No chunks created from the provided text")
            return 0
        
        print(f"Created {len(chunks)} chunks")
        
        # Get embeddings for all chunks
        print("Getting embeddings from OpenAI...")
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = self.get_embeddings(chunk_texts)
        
        # Combine chunks with embeddings
        chunks_with_embeddings = []
        for chunk, embedding in zip(chunks, embeddings):
            chunks_with_embeddings.append({
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "embedding": embedding
            })
        
        # Store in Weaviate
        print("Storing chunks in Weaviate...")
        self.weaviate_manager.add_documents(chunks_with_embeddings)
        
        return len(chunks)
    
    def process_file(self, file_path: str) -> int:
        """
        Process a text file
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Number of chunks created
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return self.process_text(text, source=file_path)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ingest documents into local Weaviate RAG system"
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to text file to ingest"
    )
    parser.add_argument(
        "--text", "-t",
        help="Text content to ingest directly"
    )
    parser.add_argument(
        "--source", "-s",
        default="manual_input",
        help="Source identifier for the content"
    )
    parser.add_argument(
        "--setup-schema",
        action="store_true",
        help="Set up Weaviate schema only"
    )
    
    args = parser.parse_args()
    
    try:
        ingestor = DocumentIngestor()
        
        # Setup schema
        print("Setting up Weaviate schema...")
        ingestor.weaviate_manager.create_schema()
        
        if args.setup_schema:
            print("Schema setup complete!")
            return
        
        # Process content
        if args.file:
            chunks_created = ingestor.process_file(args.file)
            print(f"\n✓ Successfully processed file: {args.file}")
            print(f"✓ Created {chunks_created} chunks")
        elif args.text:
            chunks_created = ingestor.process_text(args.text, args.source)
            print(f"\n✓ Successfully processed text content")
            print(f"✓ Created {chunks_created} chunks")
        else:
            print("Please provide either --file or --text option")
            print("Use --help for more information")
            sys.exit(1)
        
        print(f"\n✓ Document ingestion complete!")
        print(f"✓ Your documents are now searchable in the RAG system")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()