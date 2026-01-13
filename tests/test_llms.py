import pytest
from unittest.mock import MagicMock, patch
from src.app.llm_clients import LocalModelClient
from src.app.llm_base import LLMRequest


# We need to mock 'subprocess.run' because your Client uses the CLI method
# We also pass local_path="dummy" to the constructor to bypass the ValueError check

def test_client_generates_successfully():
    """Verify the client returns a valid LLMResponse object on success."""

    # 1. Mock the subprocess.run call so we don't actually run Ollama
    with patch('src.app.llm_clients.subprocess.run') as mock_run:
        # 2. Configure the mock to return a fake success result
        mock_result = MagicMock()
        mock_result.stdout = "This is a generated draft."
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # 3. Instantiate Client with a DUMMY path so it doesn't complain
        client = LocalModelClient(local_path="dummy/path/ollama.exe")

        req = LLMRequest(system_prompt="Sys", user_prompt="User")
        resp = client.generate(req)

        # 4. Assertions
        assert resp.text == "This is a generated draft."
        assert resp.model == client.model
        # Verify subprocess was called with the right arguments
        args, _ = mock_run.call_args
        assert "dummy/path/ollama.exe" in args[0]  # The command list


def test_client_handles_missing_file():
    """Verify the client raises a clear error if the executable is missing."""

    # We don't mock subprocess here because we want the Validation logic in __init__ to run
    # But wait, your validation checks if the file exists using Path.exists()

    # We must mock Path.exists to simulate a missing file
    with patch('src.app.llm_clients.Path.exists') as mock_exists:
        mock_exists.return_value = False  # File not found

        # This should fail immediately upon initialization
        with pytest.raises(ValueError) as excinfo:
            # We pass a path that "looks" real but mocked to not exist
            LocalModelClient(local_path=r"C:\Fake\ollama.exe")

        assert "found" in str(excinfo.value) or "missing" in str(excinfo.value)


def test_client_handles_subprocess_error():
    """Verify the client handles runtime errors from the CLI."""

    with patch('src.app.llm_clients.subprocess.run') as mock_run:
        # Simulate the CLI command failing (e.g. exit code 1)
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="ollama", stderr="Model not found")

        client = LocalModelClient(local_path="dummy_path")

        # FIX: Added 'system_prompt' argument below
        req = LLMRequest(system_prompt="sys", user_prompt="Hi")

        with pytest.raises(RuntimeError) as excinfo:
            client.generate(req)

        assert "Ollama CLI Error" in str(excinfo.value)


####################################################################################
########################  NEW TESTS: LLM Clients & Dataclasses  ####################
####################################################################################
def test_openai_client_initialization():
    """Test OpenAI client requires API key"""
    import os

    # Save original key
    original = os.environ.get("OPENAI_API_KEY")
    original_default = os.environ.get("OPENAI_DEFAULT_API_KEY")

    # Remove keys
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    if "OPENAI_DEFAULT_API_KEY" in os.environ:
        del os.environ["OPENAI_DEFAULT_API_KEY"]

    try:
        from src.app.llm_clients import OpenAIClient

        with pytest.raises(ValueError) as excinfo:
            OpenAIClient()

        assert "API Key" in str(excinfo.value)

    finally:
        # Restore original keys
        if original:
            os.environ["OPENAI_API_KEY"] = original
        if original_default:
            os.environ["OPENAI_DEFAULT_API_KEY"] = original_default


def test_huggingface_client_initialization():
    """Test HuggingFace client requires token"""
    import os

    # Save original token
    original = os.environ.get("HF_API_TOKEN")

    # Remove token
    if "HF_API_TOKEN" in os.environ:
        del os.environ["HF_API_TOKEN"]

    try:
        from src.app.llm_clients import HuggingFaceClient

        with pytest.raises(ValueError) as excinfo:
            HuggingFaceClient()

        assert "Token" in str(excinfo.value)

    finally:
        # Restore original token
        if original:
            os.environ["HF_API_TOKEN"] = original


def test_llm_request_dataclass():
    """Test LLMRequest validation"""
    from src.app.llm_base import LLMRequest

    req = LLMRequest(
        system_prompt="Test system",
        user_prompt="Test user",
        max_tokens=500,
        temperature=0.7
    )

    assert req.system_prompt == "Test system"
    assert req.user_prompt == "Test user"
    assert req.max_tokens == 500
    assert req.temperature == 0.7


def test_llm_response_dataclass():
    """Test LLMResponse structure"""
    from src.app.llm_base import LLMResponse

    resp = LLMResponse(
        text="Generated text",
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50
    )

    assert resp.text == "Generated text"
    assert resp.model == "gpt-4o-mini"
    assert resp.prompt_tokens == 100
    assert resp.completion_tokens == 50