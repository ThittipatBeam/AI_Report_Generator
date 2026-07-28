import time
import asyncio
import json
from typing import Any, List, Optional, Iterator, AsyncIterator
import requests
import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage, AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_openai import ChatOpenAI, AzureChatOpenAI

from backend.config import settings

class APIMAzureChatLLM(BaseChatModel):
    """
    Custom LangChain Chat Model wrapper for Bangkok Bank's Azure APIM proxy endpoint.
    Endpoint: POST /llm/responses
    Payload: {"model": "gpt-5-mini", "input": "<prompt>", "stream": bool}
    """
    endpoint: str
    api_key: str
    model: str = "gpt-5-mini"

    @property
    def _llm_type(self) -> str:
        return "apim_azure_chat"

    def _format_messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        prompt_parts = []
        for m in messages:
            if isinstance(m, SystemMessage):
                prompt_parts.append(f"System: {m.content}")
            elif isinstance(m, HumanMessage):
                prompt_parts.append(f"User: {m.content}")
            else:
                prompt_parts.append(f"{m.type}: {m.content}")
        return "\n\n".join(prompt_parts)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = self._format_messages_to_prompt(messages)
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": prompt,
            "stream": False
        }

        max_retries = 4
        resp = None
        for attempt in range(max_retries):
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=120)
            if resp.status_code == 429 and attempt < max_retries - 1:
                print(f"⚠️ APIM Rate Limit 429 hit. Retrying in 20s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(20)
                continue
            resp.raise_for_status()
            break

        data = resp.json()

        output_text = ""
        for item in data.get("output", []):
            if item.get("type") == "message":
                for content_item in item.get("content", []):
                    if content_item.get("type") == "output_text":
                        output_text += content_item.get("text", "")

        gen = ChatGeneration(message=AIMessage(content=output_text))
        return ChatResult(generations=[gen])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        prompt = self._format_messages_to_prompt(messages)
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        payload = {
            "model": self.model,
            "input": prompt,
            "stream": True
        }

        max_retries = 4
        for attempt in range(max_retries):
            resp = requests.post(self.endpoint, headers=headers, json=payload, stream=True, timeout=120)
            if resp.status_code == 429 and attempt < max_retries - 1:
                print(f"⚠️ APIM Rate Limit 429 hit in stream. Waiting 20s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(20)
                continue
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8").strip()
                if decoded.startswith("data:"):
                    raw_data = decoded[5:].strip()
                    if raw_data == "[DONE]":
                        break
                    try:
                        data_json = json.loads(raw_data)
                        delta = data_json.get("delta", "")
                        if delta:
                            chunk = ChatGenerationChunk(message=AIMessageChunk(content=delta))
                            if run_manager:
                                run_manager.on_llm_new_token(delta, chunk=chunk)
                            yield chunk
                    except json.JSONDecodeError:
                        continue
            break

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        prompt = self._format_messages_to_prompt(messages)
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        payload = {
            "model": self.model,
            "input": prompt,
            "stream": True
        }

        max_retries = 4
        async with httpx.AsyncClient(timeout=120.0) as client:
            for attempt in range(max_retries):
                async with client.stream("POST", self.endpoint, headers=headers, json=payload) as response:
                    if response.status_code == 429 and attempt < max_retries - 1:
                        print(f"⚠️ APIM Rate Limit 429 hit in astream. Waiting 20s... (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(20)
                        continue
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        decoded = line.strip()
                        if decoded.startswith("data:"):
                            raw_data = decoded[5:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                data_json = json.loads(raw_data)
                                delta = data_json.get("delta", "")
                                if delta:
                                    chunk = ChatGenerationChunk(message=AIMessageChunk(content=delta))
                                    if run_manager:
                                        await run_manager.on_llm_new_token(delta, chunk=chunk)
                                    yield chunk
                            except json.JSONDecodeError:
                                continue
                    break


def get_llm():
    """
    Returns an initialized LangChain Chat model instance based on settings.LLM_PROVIDER.
    Supports:
      1. 'apim_azure' / 'bbl_azure': Bangkok Bank Azure APIM proxy (gpt-5-mini)
      2. 'openai_compatible': LiteLLM / vLLM / Ollama gateways
      3. 'azure': Standard Azure OpenAI endpoint
      4. 'openai': Direct OpenAI models
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider in ["apim_azure", "azure_apim", "bbl_azure"]:
        api_key = settings.APIM_AZURE_API_KEY or settings.OPENAI_API_KEY or ""
        return APIMAzureChatLLM(
            endpoint=settings.APIM_AZURE_ENDPOINT,
            api_key=api_key,
            model=settings.APIM_AZURE_MODEL or "gpt-5-mini"
        )
    elif provider in ["openai_compatible", "litellm", "vllm", "ollama"]:
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

