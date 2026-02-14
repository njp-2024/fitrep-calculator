"""
run_benchmark.py

Entry point for Model Benchmark experiments.

Run from project root with: python -m experiments.prelim_benchmark.run_benchmark
"""

from datetime import datetime, timezone

from src.app.llm_base import LLMRequest
from src.app import llm_clients


def main():
    print("=== Model Benchmark Runner ===")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"Run ID: {run_id}")
    print()

    client = llm_clients.OpenAIClient()
    req = LLMRequest(
        system_prompt="Always answer with a one-sentence joke.",
        user_prompt="Say hello world.",
        max_tokens=50,
        temperature=0.3
        )
    resp = client.generate(req)

    print(resp.text)
    print("Model: ", resp.model)
    print("Tokens: ", resp.prompt_tokens," input, ", resp.completion_tokens," output")
    print()

    print("Benchmark harness initialized successfully.")


if __name__ == "__main__":
    main()