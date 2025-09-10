#!/usr/bin/env python3
import sys
import argparse
import logging
from typing import List

from dotenv import load_dotenv, find_dotenv
import weaviate
from weaviate.classes.init import AdditionalConfig
from weaviate.collections import Collection
from openai import OpenAI

from .utils import env, logger, backoff_retry, get_weaviate_client

_env_path = find_dotenv(usecwd=True)
if _env_path:
    load_dotenv(_env_path)
else:
    load_dotenv()
logging.getLogger("weaviate").setLevel(logging.WARNING)


@backoff_retry
def hybrid_search(coll: Collection, query: str, query_vector: List[float], alpha: float, limit: int):
    """
    Perform hybrid search combining BM25 and vector similarity.
    
    Args:
        coll: Weaviate collection instance
        query: Search query string
        query_vector: Vector representation of the query
        alpha: Balance between BM25 (0.0) and vector (1.0) search
        limit: Maximum number of results to return
        
    Returns:
        Search results from Weaviate
    """
    return coll.query.hybrid(
        query=query,
        vector=query_vector,
        alpha=alpha,
        limit=limit,
        return_metadata=["distance"],
        return_properties=["text", "source", "chunk_id"]
    )

def build_prompt(question: str, contexts: List[str]) -> str:
    """
    Build a prompt for the LLM with retrieved context and user question.
    
    Args:
        question: User's question
        contexts: List of relevant text chunks from retrieval
        
    Returns:
        Formatted prompt string for the LLM
    """
    context_text = "\n\n---\n\n".join(contexts)
    return (
        "You are a helpful assistant that answers questions based on the provided context.\n"
        "Use the information from the context to answer the question as completely as possible.\n"
        "If you cannot find a direct answer in the context, provide the most relevant information available.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

def main():
    parser = argparse.ArgumentParser(description="Query Weaviate (hybrid) and answer with GPT-4o.")
    parser.add_argument("query", help="User query")
    args = parser.parse_args()

    collection_name = env("RAG_COLLECTION", "Documents")
    alpha = float(env("HYBRID_ALPHA", "0.5"))
    top_k = int(env("TOP_K", "5"))
    max_ctx = int(env("MAX_CONTEXT_CHUNKS", "6"))
    embed_model = env("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    # First, create query embedding using OpenAI
    openai_key = env("OPENAI_API_KEY", required=True)
    openai_base = env("OPENAI_BASE_URL", "")

    try:
        oa_kwargs = {"api_key": openai_key}
        if openai_base and openai_base.strip():
            oa_kwargs["base_url"] = openai_base.strip()
        else:
            # Explicitly set the default OpenAI API base URL to avoid environment conflicts
            oa_kwargs["base_url"] = "https://api.openai.com/v1"
        oa = OpenAI(**oa_kwargs)
        
        # Create query vector
        query_response = oa.embeddings.create(model=embed_model, input=[args.query])
        query_vector = query_response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to create query embedding: {e}")
        sys.exit(1)

    # Weaviate hybrid search
    client = get_weaviate_client()
    try:
        coll = client.collections.get(collection_name)
        res = hybrid_search(coll, args.query, query_vector, alpha=alpha, limit=top_k)
        if not res.objects:
            print("No results found.")
            return

        contexts = []
        for o in res.objects[:max_ctx]:
            props = o.properties
            contexts.append(props.get("text", ""))

        # Display input query
        print("=" * 80)
        print("INPUT QUERY:")
        print("=" * 80)
        print(args.query)
        print()

        # Display retrieved vector search results
        print("=" * 80)
        print("RETRIEVED VECTOR SEARCH:")
        print("=" * 80)
        print(f"Found {len(res.objects)} results, using top {len(contexts)} for context")
        print()
        for i, context in enumerate(contexts, 1):
            print(f"Result {i}:")
            print("-" * 40)
            print(context.strip())
            print()

        # OpenAI generate (reuse the same client)
        model = env("OPENAI_COMPLETIONS_MODEL", "gpt-4o")
        prompt = build_prompt(args.query, contexts)

        # Display full prompt being sent to GPT-4o
        print("=" * 80)
        print("FULL DETAILS (QUERY + CONTEXT) TO BE SENT:")
        print("=" * 80)
        print(f"Model: {model}")
        print(f"Temperature: 0.2")
        print(f"Prompt length: {len(prompt)} characters")
        print()
        print("Full prompt:")
        print("-" * 40)
        print(prompt)
        print()

        # Use Chat Completions API for GPT-4o
        resp = oa.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        answer = resp.choices[0].message.content
        
        # Display final answer
        print("=" * 80)
        print("GENERATED ANSWER:")
        print("=" * 80)
        print(answer.strip())

    except Exception as e:
        logger.error(f"Query failed: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()
