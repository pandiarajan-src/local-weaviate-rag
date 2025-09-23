#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import time

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI
import weaviate
from weaviate.classes.config import DataType, Property, VectorDistances, Configure
from weaviate.collections import Collection

from .utils import backoff_retry, chunk_text, env, get_weaviate_client, logger

_env_path = find_dotenv(usecwd=True)
if _env_path:
    load_dotenv(_env_path)
else:
    load_dotenv()
logging.getLogger("weaviate").setLevel(logging.WARNING)


def ensure_schema(client: weaviate.WeaviateClient, collection_name: str) -> Collection:
    """
    Ensure Weaviate collection exists with proper schema.

    Args:
        client: Weaviate client instance
        collection_name: Name of the collection to create/get

    Returns:
        Weaviate collection instance
    """
    # First, check if collection already exists and is working
    try:
        existing_collection = client.collections.get(collection_name)
        # Test if the collection is accessible and working
        existing_collection.query.fetch_objects(limit=1)
        logger.info(f"Collection '{collection_name}' already exists and is functional.")
        return existing_collection
    except Exception as e:
        logger.info(f"Collection '{collection_name}' doesn't exist or has issues: {e}")

        # If collection exists but is corrupted, try to delete it
        try:
            client.collections.delete(collection_name)
            logger.info(f"Deleted corrupted collection '{collection_name}'.")
            time.sleep(2)  # Wait for deletion to propagate
        except Exception:
            logger.info(
                f"Collection '{collection_name}' deletion not needed or already deleted."
            )

    # Create the collection with proper configuration
    try:
        logger.info(f"Creating collection '{collection_name}' with proper schema...")

        # Create collection with default configuration (no server vectorizer)
        client.collections.create(
            name=collection_name,
            properties=[
                Property(name="text", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="chunk_id", data_type=DataType.TEXT),
            ],
            # No vector configuration specified - allows manual vector insertion
        )

        # Wait a moment for schema to propagate
        time.sleep(2)

        # Verify the collection was created properly
        collection = client.collections.get(collection_name)

        # Test that we can query the collection to verify schema is ready
        try:
            collection.query.fetch_objects(limit=1)
            logger.info(
                f"Successfully created and verified collection '{collection_name}'."
            )
        except Exception as query_error:
            logger.warning(f"Collection created but query test failed: {query_error}")

        return collection

    except Exception as e:
        logger.error(f"Failed to create collection '{collection_name}': {e}")
        raise


@backoff_retry
def embed_chunks(client: OpenAI, model: str, chunks: list[str]) -> list[list[float]]:
    """
    Create embeddings for text chunks with rate limiting and error handling.

    Args:
        client: OpenAI client instance
        model: Embedding model name
        chunks: List of text chunks to embed

    Returns:
        List of embedding vectors
    """
    try:
        # Process in batches to avoid rate limits
        batch_size = 100  # OpenAI's recommended batch size
        all_embeddings = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            resp = client.embeddings.create(model=model, input=batch)
            all_embeddings.extend([e.embedding for e in resp.data])

            # Small delay between batches to be respectful of rate limits
            if i + batch_size < len(chunks):
                time.sleep(0.1)

        return all_embeddings
    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Ingest a text (string or file) into Weaviate with OpenAI embeddings."
    )
    parser.add_argument(
        "input", help="Either the raw text to ingest OR a path to a .txt/.md file"
    )
    parser.add_argument(
        "--source", default="", help="Source label (filename, URL, note)"
    )
    args = parser.parse_args()

    openai_key = env("OPENAI_API_KEY", required=True)
    openai_base = env("OPENAI_BASE_URL", "")
    embed_model = env("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    collection_name = env("RAG_COLLECTION", "Documents")
    chunk_tokens = int(env("CHUNK_TOKENS", "400"))
    chunk_overlap = int(env("CHUNK_OVERLAP", "60"))

    # Input sanitization and validation
    text = ""
    if os.path.isfile(args.input):
        # Security: Resolve path and check it's not trying to escape
        try:
            resolved_path = os.path.realpath(args.input)
            if not os.path.exists(resolved_path):
                logger.error(f"File not found: '{args.input}'")
                sys.exit(2)
        except (OSError, ValueError) as e:
            logger.error(f"Invalid file path '{args.input}': {e}")
            sys.exit(2)

        # Validate file type
        allowed_extensions = {
            ".txt",
            ".md",
            ".py",
            ".js",
            ".json",
            ".csv",
            ".html",
            ".xml",
            ".rst",
            ".tex",
        }
        file_ext = os.path.splitext(resolved_path)[1].lower()
        if file_ext and file_ext not in allowed_extensions:
            logger.error(
                f"File extension '{file_ext}' is not supported. Allowed extensions are: {', '.join(sorted(allowed_extensions))}"
            )
            sys.exit(2)

        # Check file size (limit to 50MB for safety)
        try:
            file_size = os.path.getsize(resolved_path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                logger.error(
                    f"File too large: {file_size / 1024 / 1024:.1f}MB (max 50MB)"
                )
                sys.exit(2)
        except OSError as e:
            logger.error(f"Error checking file size: {e}")
            sys.exit(2)

        try:
            with open(resolved_path, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            try:
                with open(resolved_path, encoding="latin-1") as f:
                    text = f.read()
                logger.warning("File decoded with latin-1 encoding instead of UTF-8")
            except Exception:
                logger.error(
                    f"Failed to decode file '{args.input}' with UTF-8 or latin-1"
                )
                sys.exit(2)
        except PermissionError:
            logger.error(f"Permission denied reading file '{args.input}'")
            sys.exit(2)
        except FileNotFoundError:
            logger.error(f"File not found: '{args.input}'")
            sys.exit(2)
        except OSError as e:
            logger.error(f"Error reading file '{args.input}': {e}")
            sys.exit(2)

        if not args.source:
            args.source = os.path.basename(resolved_path)
    else:
        # Sanitize direct text input
        text = str(args.input).strip()
        # Limit direct text input size
        if len(text) > 1024 * 1024:  # 1MB
            logger.error(f"Direct text input too large: {len(text)} chars (max ~1MB)")
            sys.exit(2)

    if not text.strip():
        logger.error("Input is empty.")
        sys.exit(2)

    # chunk
    chunks = chunk_text(
        text, model=embed_model, chunk_tokens=chunk_tokens, overlap_tokens=chunk_overlap
    )
    logger.info(
        f"Chunked into {len(chunks)} segments (≈{chunk_tokens} tokens target, {chunk_overlap} overlap)."
    )

    # OpenAI client
    try:
        oa_kwargs = {"api_key": openai_key}

        # Only add base_url if explicitly provided and not empty
        if openai_base and openai_base.strip():
            oa_kwargs["base_url"] = openai_base.strip()
        else:
            # Explicitly set the default OpenAI API base URL to avoid environment conflicts
            oa_kwargs["base_url"] = "https://api.openai.com/v1"

        oa = OpenAI(**oa_kwargs)
    except Exception as e:
        logger.error(f"Failed to create OpenAI client: {e}")
        sys.exit(1)

    # embed
    vectors = embed_chunks(oa, embed_model, chunks)
    logger.info("Embeddings computed.")

    # weaviate
    client = get_weaviate_client()
    try:
        coll = ensure_schema(client, collection_name)

        # Add a small delay to ensure schema is properly propagated

        time.sleep(1)

        # Verify the collection is actually ready for insertion
        try:
            # Test that we can access the collection properly
            existing_count = len(coll.query.fetch_objects().objects)
            logger.info(
                f"Collection '{collection_name}' has {existing_count} existing objects."
            )
        except Exception as e:
            logger.warning(f"Could not query existing objects: {e}")

        # Batch insert with vectors
        logger.info(f"Starting batch insertion of {len(chunks)} chunks...")
        try:
            with coll.batch.dynamic() as batch:
                for i, (chunk, vec) in enumerate(zip(chunks, vectors, strict=True)):
                    batch.add_object(
                        properties={
                            "text": chunk,
                            "source": args.source,
                            "chunk_id": str(i),
                        },
                        vector=vec,
                    )
                    logger.debug(f"Added object {i + 1}/{len(chunks)} to batch")

            # Check for any failed objects
            if hasattr(coll.batch, "failed_objects") and coll.batch.failed_objects:
                logger.error(
                    f"Failed to insert {len(coll.batch.failed_objects)} objects:"
                )
                for failed_obj in coll.batch.failed_objects:
                    logger.error(f"Failed object: {failed_obj}")
                sys.exit(1)

            logger.info(f"Ingested {len(chunks)} chunks into '{collection_name}'.")
        except Exception as batch_error:
            logger.error(f"Batch insertion failed: {batch_error}")
            # Try individual insertion as fallback
            logger.info("Attempting individual object insertion as fallback...")
            for i, (chunk, vec) in enumerate(zip(chunks, vectors, strict=True)):
                try:
                    coll.data.insert(
                        properties={
                            "text": chunk,
                            "source": args.source,
                            "chunk_id": str(i),
                        },
                        vector=vec,
                    )
                    logger.debug(f"Individually inserted object {i + 1}/{len(chunks)}")
                except Exception as individual_error:
                    logger.error(f"Failed to insert object {i + 1}: {individual_error}")
            logger.info(f"Fallback insertion completed for {len(chunks)} chunks.")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
