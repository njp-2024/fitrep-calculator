import os
import subprocess
import src.app.constants as constants

from pathlib import Path
from openai import OpenAI
from huggingface_hub import InferenceClient
from src.app.llm_base import BaseLLMClient, LLMRequest, LLMResponse

class OpenAIClient(BaseLLMClient):
    """
    Client for OpenAI's Responses API (GPT-4o, GPT-5 series).
    """
    def __init__(self, model: str = constants.FRONTIER_MODELS[constants.DEFAULT_FRONTIER_MODEL]["model_id"]):
        """
        Initialize the OpenAI client.

        Raises:
            ValueError: If OPENAI_API_KEY is not found in environment variables.
        """
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_DEFAULT_API_KEY")

        if not api_key:
            raise ValueError("Missing API Key: Set 'OPENAI_API_KEY' in your environment.")

        valid_ids = {cfg["model_id"] for cfg in constants.FRONTIER_MODELS.values()}
        if model not in valid_ids:
            raise ValueError(
                f"Unsupported model '{model}'. Allowed: {sorted(valid_ids)}"
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using OpenAI chat completions.
        """
        try:
            # Responses API:
            # - instructions: system/developer message
            # - input: user content (string or structured items)
            # - max_output_tokens: cap output (includes reasoning tokens for GPT-5 family)
            kwargs = {
                        "model": self.model,
                        "instructions": request.system_prompt,
                        "input": [{"role": "user", "content": request.user_prompt}],
                        "max_output_tokens": request.max_tokens,
                        "temperature": request.temperature,
                        }

            # medium effort is default - these lines can support adding effort as a param in the future
            # if request.reasoning:
            #     kwargs["reasoning"] = {"effort": "medium"}

            response = self.client.responses.create(**kwargs)

            text = (response.output_text or "").strip()

            usage = response.usage
            prompt_tokens = usage.input_tokens if usage else None
            completion_tokens = usage.output_tokens if usage else None

            return LLMResponse(
                text=text,
                model=response.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI API Error: {str(e)}") from e


class LocalModelClient(BaseLLMClient):
    """
    Client for local inference via Ollama CLI.
    """
    def __init__(self, local_path: str = None,  model: str = constants.LOCAL_MODELS[constants.DEFAULT_LOCAL_MODEL]["model_id"]):
        """
        Args:
            local_path (str): Path to ollama executable. If None, raise error.
            model (str): The model tag to run (e.g. 'llama3').
        """
        self.model = model
        self.local_path = local_path

        # Validation: Ensure we actually have a path
        if not self.local_path:
            raise ValueError("Ollama Path is missing. Please set 'OLLAMA_PATH' in constants.py")

        # Validation: Verify the file actually exists
        # (We skip this check if it's just the command "ollama" intended for system PATH)
        if "ollama" in self.local_path.lower() and "\\" in self.local_path:
            if not Path(self.local_path).exists():
                raise ValueError(f"Ollama executable not found at: {self.local_path}")

    def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Executes the model via subprocess.
        """
        full_prompt = f"{request.system_prompt}\n\n{request.user_prompt}" if request.system_prompt else request.user_prompt

        try:
            response = subprocess.run(
                [self.local_path, "run", self.model],
                input=full_prompt,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=True  # Raises CalledProcessError on non-zero exit code
            )

            return LLMResponse(
                text=response.stdout,
                model=self.model,
                prompt_tokens=None,
                completion_tokens=None
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ollama CLI Error (Exit Code {e.returncode}): {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(f"Ollama executable not found at '{self.local_path}'. Is it installed?")
        except Exception as e:
            raise RuntimeError(f"Local Inference Error: {str(e)}")


class HuggingFaceClient(BaseLLMClient):
    """
    Client for HuggingFace Inference API (Serverless).
    Uses the chat.completions format for structured prompting.
    """
    def __init__(self, model: str = constants.OPEN_WEIGHT_MODELS[constants.DEFAULT_OPEN_MODEL]["model_id"]):
        # Other models to try:
        # - "mistralai/Mixtral-8x7B-Instruct-v0.1"
        # - "meta-llama/Meta-Llama-3-70B-Instruct"
        # - "Qwen/Qwen2.5-32B-Instruct"
        self.model = model
        self.api_token = os.environ.get("HF_API_TOKEN")

        if not self.api_token:
            # We fail hard here so you know immediately if the env var is missing
            raise ValueError("Missing Token: Set 'HF_API_TOKEN' in environment variables.")

        self.client = InferenceClient(token=self.api_token)

    def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            # Build the messages list
            # Only add the System role if the prompt actually has content
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})

            messages.append({"role": "user", "content": request.user_prompt})

            # Call the API (Blocking)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=False
            )

            # Extract Content
            choice = response.choices[0]
            generated_text = choice.message.content

            if not generated_text:
                raise RuntimeError("HuggingFace returned an empty response.")

            # Attempt to extract usage stats (Available on some HF endpoints)
            usage = response.usage
            p_tokens = usage.prompt_tokens if usage else None
            c_tokens = usage.completion_tokens if usage else None

            return LLMResponse(
                text=generated_text,
                model=self.model,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
            )

        except Exception as e:
            # Wrap the error so the GUI knows it came from HF
            raise RuntimeError(f"HuggingFace API Error: {str(e)}") from e
