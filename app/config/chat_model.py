"""
app/config/chat_model.py
────────────────────────
Returns the correct Pydantic AI model instance based on .env configuration.

.env examples
─────────────
# OpenAI
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL_NAME=claude-3-5-haiku-20241022
ANTHROPIC_API_KEY=sk-ant-...

# Ollama (local)
LLM_PROVIDER=ollama
LLM_MODEL_NAME=llama3.2
LLM_BASE_URL=http://localhost:11434/v1

# vLLM (local / self-hosted)
LLM_PROVIDER=vllm
LLM_MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2
LLM_BASE_URL=http://localhost:8000/v1
"""
from dotenv import load_dotenv
from pydantic_ai.models import Model
from app.config.settings import settings

load_dotenv()

def get_model() -> Model:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        from pydantic_ai.models.openai import OpenAIChatModel
        return OpenAIChatModel(settings.LLM_MODEL_NAME)

    elif provider == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel
        return AnthropicModel(settings.LLM_MODEL_NAME)

    elif provider == "gemini":
        # Updated: GeminiModel is now GoogleModel
        from pydantic_ai.models.google import GoogleModel
        return GoogleModel(settings.LLM_MODEL_NAME)
        # Note: Under the hood, this now automatically reads GOOGLE_API_KEY

    elif provider == "ollama":
        from pydantic_ai.models.ollama import OllamaModel
        from pydantic_ai.providers.ollama import OllamaProvider

        base_url = settings.LLM_BASE_URL or "http://localhost:11434/v1"
        return OllamaModel(
            settings.LLM_MODEL_NAME,
            provider=OllamaProvider(base_url=base_url)
        )

    elif provider == "vllm":
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        base_url = settings.LLM_BASE_URL or "http://localhost:8000/v1"
        return OpenAIChatModel(
            settings.LLM_MODEL_NAME,
            provider=OpenAIProvider(base_url=base_url)
        )

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{settings.LLM_PROVIDER}'. "
            "Choose from: openai, anthropic, gemini, ollama, vllm"
        )