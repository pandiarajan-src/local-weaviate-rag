#!/usr/bin/env python3
"""
Text Embedding and Storage Script for Local Weaviate RAG

This script takes input text, performs intelligent chunking, creates embeddings
using OpenAI's text-embedding-3-small model, and stores them in Weaviate.

Usage:
    python embed_text.py "Your text content here"
    python embed_text.py --file path/to/text/file.txt
"""

import argparse
import os
import sys
import json
from typing import List, Dict, Any
from pathlib import Path
import logging
from datetime import datetime

import tiktoken
from openai import OpenAI
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('embed_text.log')
    ]
)
logger = logging.getLogger(__name__)


class TextChunker:
    """Intelligent text chunking with token-aware splitting."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, model: str = "text-embedding-3-small"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap, considering token limits."""
        if not text.strip():
            return []
        
        # If text is small enough, return as single chunk
        if self.count_tokens(text) <= self.chunk_size:
            return [text.strip()]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Check if adding this paragraph exceeds chunk size
            potential_chunk = f"{current_chunk}\n\n{paragraph}".strip()
            
            if self.count_tokens(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk)
                    
                # Start new chunk with overlap
                if len(chunks) > 0 and self.chunk_overlap > 0:
                    # Add overlap from previous chunk
                    overlap_text = self._get_overlap_text(chunks[-1])
                    current_chunk = f"{overlap_text}\n\n{paragraph}".strip()
                else:
                    current_chunk = paragraph
                
                # If single paragraph is too large, split it further
                if self.count_tokens(current_chunk) > self.chunk_size:
                    sub_chunks = self._split_large_paragraph(current_chunk)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        sentences = text.split('. ')
        overlap_text = ""
        
        for sentence in reversed(sentences):
            potential_overlap = f"{sentence}. {overlap_text}".strip()
            if self.count_tokens(potential_overlap) <= self.chunk_overlap:
                overlap_text = potential_overlap
            else:
                break
        
        return overlap_text.rstrip('. ')
    
    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split a large paragraph into smaller chunks."""
        sentences = paragraph.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            potential_chunk = f"{current_chunk}. {sentence}".strip()
            
            if self.count_tokens(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


class WeaviateManager:
    """Manages Weaviate connection and operations."""
    
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
    
    def create_collection(self):
        """Create collection if it doesn't exist."""
        try:
            if self.client.collections.exists(self.collection_name):
                logger.info(f"Collection '{self.collection_name}' already exists")
                return True
            
            collection = self.client.collections.create(
                name=self.collection_name,
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="source", data_type=DataType.TEXT),
                    Property(name="chunk_index", data_type=DataType.INT),
                    Property(name="token_count", data_type=DataType.INT),
                    Property(name="created_at", data_type=DataType.DATE),
                ],
                vectorizer_config=Configure.Vectorizer.none(),
                vector_index_config=Configure.VectorIndex.hnsw()
            )
            logger.info(f"Created collection '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            return False
    
    def store_chunks(self, chunks: List[str], embeddings: List[List[float]], source: str):
        """Store text chunks with embeddings in Weaviate."""
        try:
            collection = self.client.collections.get(self.collection_name)
            
            objects = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                obj = {
                    "content": chunk,
                    "source": source,
                    "chunk_index": i,
                    "token_count": len(tiktoken.encoding_for_model("text-embedding-3-small").encode(chunk)),
                    "created_at": datetime.now().isoformat() + "Z"
                }
                objects.append({"properties": obj, "vector": embedding})
            
            # Batch insert
            result = collection.data.insert_many(objects)
            
            if result.has_errors:
                logger.error(f"Some objects failed to insert: {result.errors}")
                return False
            
            logger.info(f"Successfully stored {len(chunks)} chunks for source: {source}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store chunks: {str(e)}")
            return False
    
    def close(self):
        """Close Weaviate connection."""
        if self.client:
            self.client.close()
            logger.info("Closed Weaviate connection")


class EmbeddingGenerator:
    """Generates embeddings using OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            # Process in batches to avoid rate limits
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated {len(all_embeddings)} embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise


def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    
    config = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'weaviate_url': os.getenv('WEAVIATE_URL', 'http://localhost:8080'),
        'weaviate_api_key': os.getenv('WEAVIATE_API_KEY'),
        'weaviate_timeout': int(os.getenv('WEAVIATE_TIMEOUT', '60')),
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
        'chunk_size': int(os.getenv('CHUNK_SIZE', '1000')),
        'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', '200')),
        'collection_name': os.getenv('COLLECTION_NAME', 'DocumentChunks'),
    }
    
    # Validate required config
    if not config['openai_api_key']:
        raise ValueError("OPENAI_API_KEY is required")
    
    return config


def read_file(file_path: str) -> str:
    """Read text from file with encoding detection."""
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try UTF-8 first, then fallback to other encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
        
        for encoding in encodings:
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Could not decode file {file_path} with any supported encoding")
        
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {str(e)}")
        raise


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Embed text chunks and store in Weaviate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python embed_text.py "Your text content here"
    python embed_text.py --file document.txt
    python embed_text.py --file document.txt --source "My Document"
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('text', nargs='?', help='Text content to embed')
    group.add_argument('--file', '-f', help='Path to text file to embed')
    
    parser.add_argument('--source', '-s', help='Source identifier for the text')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Get text content
        if args.file:
            text_content = read_file(args.file)
            source = args.source or args.file
        else:
            text_content = args.text
            source = args.source or "command_line_input"
        
        if not text_content.strip():
            logger.error("No text content provided")
            sys.exit(1)
        
        logger.info(f"Processing text from source: {source}")
        logger.info(f"Text length: {len(text_content)} characters")
        
        # Initialize components
        chunker = TextChunker(
            chunk_size=config['chunk_size'],
            chunk_overlap=config['chunk_overlap'],
            model=config['embedding_model']
        )
        
        embedding_generator = EmbeddingGenerator(
            api_key=config['openai_api_key'],
            model=config['embedding_model']
        )
        
        weaviate_manager = WeaviateManager(
            url=config['weaviate_url'],
            api_key=config['weaviate_api_key'],
            timeout=config['weaviate_timeout']
        )
        
        # Process text
        logger.info("Chunking text...")
        chunks = chunker.split_text(text_content)
        logger.info(f"Created {len(chunks)} chunks")
        
        if args.verbose:
            for i, chunk in enumerate(chunks):
                logger.debug(f"Chunk {i+1}: {len(chunk)} chars, {chunker.count_tokens(chunk)} tokens")
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = embedding_generator.generate_embeddings(chunks)
        
        # Connect to Weaviate and store
        logger.info("Connecting to Weaviate...")
        if not weaviate_manager.connect():
            logger.error("Failed to connect to Weaviate")
            sys.exit(1)
        
        if not weaviate_manager.create_collection():
            logger.error("Failed to create collection")
            sys.exit(1)
        
        logger.info("Storing chunks in Weaviate...")
        if weaviate_manager.store_chunks(chunks, embeddings, source):
            logger.info("✅ Successfully embedded and stored text chunks")
            print(f"✅ Successfully processed and stored {len(chunks)} chunks from '{source}'")
        else:
            logger.error("Failed to store chunks")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            weaviate_manager.close()
        except:
            pass


if __name__ == "__main__":
    main()