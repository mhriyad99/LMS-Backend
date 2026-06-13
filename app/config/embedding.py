import asyncio
from sentence_transformers import SentenceTransformer

from app.config.settings import settings

_model: SentenceTransformer | None = None


def load_model() -> None:
    """
    Call this once at FastAPI startup.
    Downloads the model on first run, loads from cache on subsequent runs.
    """
    global _model
    print(f"[embedding] Loading model '{settings.EMBEDDING_MODEL_NAME}'...")
    _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    print(f"[embedding] Model loaded. Output dimension: {settings.EMBEDDING_DIM}")


def _get_model() -> SentenceTransformer:
    if _model is None:
        raise RuntimeError(
            "Embedding model is not loaded. "
            "Ensure load_model() is called at application startup."
        )
    return _model


# ---------------------------------------------------------------------------
# Public async function — safe to call from any async FastAPI path
# ---------------------------------------------------------------------------

async def embed(text: str) -> list[float]:
    """
    Embed a single string and return a list of floats (length = EMBEDDING_DIM).
    Runs the CPU-bound encoding in a thread pool so the async event loop
    is never blocked.
    """
    model = _get_model()
    vector = await asyncio.to_thread(
        model.encode,
        text,
        normalize_embeddings=True,   # cosine similarity works correctly when normalized
    )
    return vector.tolist()


async def embed_many(texts: list[str]) -> list[list[float]]:
    """
    Batch embed multiple strings at once — more efficient than calling
    embed() in a loop when you have several texts (e.g. bulk book import).
    """
    model = _get_model()
    vectors = await asyncio.to_thread(
        model.encode,
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]