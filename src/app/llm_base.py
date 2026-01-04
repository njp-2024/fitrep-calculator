from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class LLMRequest:
    """
    Standardized input payload for any LLM provider.

    Attributes:
        system_prompt (str): Context or persona instructions (e.g., "You are a Marine Corps expert").
        user_prompt (str): The specific task or query.
        max_tokens (int): The hard limit on output length. Defaults to 500.
        temperature (float): Creativity setting (0.0 = deterministic, 1.0 = creative). Defaults to 0.7.
    """
    system_prompt: str
    user_prompt: str
    max_tokens: int = 300
    temperature: float = 0.2


@dataclass
class LLMResponse:
    """
    Standardized output payload from any LLM provider.

    Attributes:
        text (str): The generated content.
        model (str): The name/ID of the model used (e.g., "gpt-4o-mini", "mistral-7b").
        prompt_tokens (Optional[int]): Token count for the input (for cost tracking).
        completion_tokens (Optional[int]): Token count for the output.
    """
    text: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class BaseLLMClient(ABC):
    """
    Abstract Base Class (Interface) for all LLM backends.

    Any client (OpenAI, Ollama, HuggingFace) must inherit from this
    and implement the 'generate' method.
    """

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generates text based on the provided request.

        Args:
            request (LLMRequest): The standardized prompt and parameters.

        Returns:
            LLMResponse: The standardized text and metadata.

        Raises:
            Exception: If the API call fails or connection times out.
        """
        pass
