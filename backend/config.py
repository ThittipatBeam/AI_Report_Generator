import os
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=env_path)

class Settings:
    # LLM Provider Configuration: 'openai_compatible', 'azure', or 'openai'
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai_compatible")
    
    # OpenAI / LiteLLM / vLLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL")
    
    # Custom model name displayed on Open WebUI
    DISPLAY_MODEL_NAME: str = os.getenv("DISPLAY_MODEL_NAME", "AI-Report-Generator")

    # Azure OpenAI Settings
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION")

    # Feature Toggles
    SHOW_RETRIEVED_SNIPPETS: bool = os.getenv("SHOW_RETRIEVED_SNIPPETS", "true").lower() == "true"
    
    # Knowledge Base Path
    KNOWLEDGE_BASE_PATH: str = os.getenv(
        "KNOWLEDGE_BASE_PATH", 
        os.path.join(BASE_DIR, "knowledge", "knowledge_base.txt")
    )

settings = Settings()
