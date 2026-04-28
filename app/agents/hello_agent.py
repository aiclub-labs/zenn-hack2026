"""
Minimal Semantic Kernel agent used to validate end-to-end wiring.

Swap this module for theme-specific agents once the problem is frozen
(e.g., Scanner / Style Arbiter / Planner for PPT Polish Agent).
"""
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory

from app.config import settings

_SYSTEM_PROMPT = (
    "You are a baseline wiring-check agent. Reply concisely and confirm "
    "which Azure OpenAI deployment answered the request."
)


def _build_kernel() -> Kernel:
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(
            deployment_name=settings.azure_openai_deployment_small,
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            service_id="small",
        )
    )
    return kernel


async def run_hello_agent(user_message: str) -> str:
    kernel = _build_kernel()
    chat = kernel.get_service("small")
    history = ChatHistory(system_message=_SYSTEM_PROMPT)
    history.add_user_message(user_message)
    result = await chat.get_chat_message_content(
        chat_history=history,
        settings=chat.instantiate_prompt_execution_settings(service_id="small"),
    )
    return str(result)
