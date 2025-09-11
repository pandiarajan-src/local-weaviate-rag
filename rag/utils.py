import logging
import os
import sys
import time

from dotenv import find_dotenv, load_dotenv
import tiktoken
import weaviate
from weaviate.classes.init import AdditionalConfig

# Load .env even if running from a subdir
_env_path = find_dotenv(usecwd=True)
if _env_path:
    load_dotenv(_env_path)
else:
    load_dotenv()

# --- Logging ---
logger = logging.getLogger("rag")
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# --- Config helpers ---
def env(name: str, default: str | None = None, required: bool = False) -> str:
    """
    Get environment variable with optional default and validation.

    Args:
        name: Environment variable name
        default: Default value if not found
        required: Whether to raise error if missing

    Returns:
        Environment variable value

    Raises:
        RuntimeError: If required variable is missing
    """
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing required env var: {name}")
    return val or ""


# --- Tokenizer cache ---
_enc_cache = {}


def get_encoder(model: str = "text-embedding-3-small") -> tiktoken.Encoding:
    """
    Get tiktoken encoder for model with caching.

    Args:
        model: Model name for tokenizer selection

    Returns:
        Tiktoken encoding instance
    """
    if model in _enc_cache:
        return _enc_cache[model]
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        # Fallback to GPT-4 encoding for unknown models
        enc = tiktoken.get_encoding("cl100k_base")
    _enc_cache[model] = enc
    return enc


def count_tokens(text: str, model: str) -> int:
    """
    Count tokens in text using model's tokenizer.

    Args:
        text: Text to tokenize
        model: Model name for tokenizer selection

    Returns:
        Number of tokens
    """
    enc = get_encoder(model)
    return len(enc.encode(text))


def sentence_split(text: str) -> list[str]:
    """
    Improved sentence splitter that handles common edge cases.
    Split on paragraph lines and sentence enders, but avoid splitting on:
    - Abbreviations like "Dr.", "Mr.", "U.S.A."
    - Numbers like "3.14" or "v1.0"
    - URLs and file extensions
    """
    import re

    parts = []
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue

        # Simple sentence pattern - split on sentence endings followed by space and capital letter
        # Avoid complex lookbehind that causes regex issues
        sentence_pattern = r"[.!?]+\s+(?=[A-Z])"

        # Split but keep the punctuation
        sentences = re.split(sentence_pattern, para)

        # If regex didn't split anything, fall back to simple method
        if len(sentences) == 1:
            tmp = []
            buf = []
            for i, ch in enumerate(para):
                buf.append(ch)
                if ch in ".!?" and i < len(para) - 1:
                    # Check if next character is space/newline and followed by capital
                    if (
                        para[i + 1].isspace()
                        and i + 2 < len(para)
                        and para[i + 2].isupper()
                    ):
                        tmp.append("".join(buf).strip())
                        buf = []
            if buf:
                tmp.append("".join(buf).strip())
            sentences = tmp

        parts.extend([s.strip() for s in sentences if s.strip()])

    return parts if parts else [text.strip()]


def chunk_text(
    text: str,
    model: str,
    chunk_tokens: int = 400,
    overlap_tokens: int = 60,
) -> list[str]:
    """
    Recursive-ish chunking by sentences using token-based packing with overlap.

    Args:
        text: Text to chunk
        model: Model name for tokenizer selection
        chunk_tokens: Target tokens per chunk
        overlap_tokens: Tokens to overlap between chunks

    Returns:
        List of text chunks with overlaps
    """
    enc = get_encoder(model)
    sents = sentence_split(text)
    chunks = []
    cur = []
    cur_toks = 0

    for s in sents:
        stoks = len(enc.encode(s))
        if cur and cur_toks + stoks > chunk_tokens:
            # finalize current
            chunk = " ".join(cur).strip()
            chunks.append(chunk)

            # overlap: take last "overlap_tokens" worth of tokens
            if overlap_tokens > 0:
                # walk backwards to build overlap
                overlap = []
                toks = 0
                for sent in reversed(cur):
                    t = len(enc.encode(sent))
                    if toks + t > overlap_tokens:
                        break
                    overlap.insert(0, sent)
                    toks += t
                cur = overlap[:]  # carryover
                cur_toks = sum(len(enc.encode(x)) for x in cur)
            else:
                cur = []
                cur_toks = 0

        cur.append(s)
        cur_toks += stoks

    if cur:
        chunks.append(" ".join(cur).strip())

    # trim empties
    return [c for c in chunks if c]


def backoff_retry(
    fn,
    *,
    retries: int = 5,
    base_delay: float = 0.5,
    factor: float = 2.0,
    exceptions=(Exception,),
):
    """
    Decorator for exponential backoff retry logic.

    Args:
        fn: Function to wrap
        retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        factor: Multiplier for delay on each retry
        exceptions: Tuple of exception types to catch

    Returns:
        Wrapped function with retry logic
    """

    def wrapper(*args, **kwargs):
        delay = base_delay
        for attempt in range(1, retries + 1):
            try:
                return fn(*args, **kwargs)
            except exceptions as e:
                if attempt == retries:
                    logger.error(f"Operation failed after {retries} attempts: {e}")
                    raise
                logger.warning(
                    f"Error: {e} — retrying in {delay:.1f}s (attempt {attempt}/{retries})"
                )
                time.sleep(delay)
                delay *= factor

    return wrapper


def get_weaviate_client() -> weaviate.WeaviateClient:
    """Create and return a configured Weaviate client."""
    scheme = env("WEAVIATE_SCHEME", "http")
    host = env("WEAVIATE_HOST", "localhost")
    port = env("WEAVIATE_PORT", "8080")
    api_key = env("WEAVIATE_API_KEY", required=True)

    try:
        return weaviate.connect_to_custom(
            http_host=host,
            http_port=int(port),
            http_secure=(scheme == "https"),
            grpc_host=host,
            grpc_port=int(env("WEAVIATE_GRPC_PORT", "50051")),
            grpc_secure=(scheme == "https"),
            auth_credentials=weaviate.auth.AuthApiKey(api_key=api_key),
            additional_config=AdditionalConfig(timeout=(5, 60)),
        )
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate at {scheme}://{host}:{port}: {e}")
        raise
