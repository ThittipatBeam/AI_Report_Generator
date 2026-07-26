from langchain_openai import ChatOpenAI, AzureChatOpenAI
from backend.config import settings

def get_llm():
    """
    Returns an initialized LangChain Chat model instance based on settings.LLM_PROVIDER.
    Supports:
      1. 'openai_compatible': LiteLLM / vLLM / Ollama gateways
      2. 'azure': Azure OpenAI 
      3. 'openai': Standard OpenAI models
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider in ["openai_compatible", "litellm", "vllm", "ollama"]:
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
            temperature=0.7,
        )
    elif provider == "azure":
        return AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=0.7,
        )
    elif provider == "openai":
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.7,
        )
    else:
        # Default fallback to OpenAI Compatible
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
            temperature=0.7,
        )
