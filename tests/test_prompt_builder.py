import pytest
from src.app.models import Report, ExampleData
from src.app.prompt_builder import build_local_prompt, _get_tier_config
import src.app.constants as c


@pytest.fixture
def mock_example_data():
    """Creates a fake ExampleData object so we don't need real YAML files."""

    class MockData:
        def __init__(self):
            self.examples = {'top_third': [{'section_i': 'Outstanding performance example.'}]}
            self.recs = {'top_third': {'promotion': ['Promote Now'], 'assignment': ['Command']}}

    return MockData()


def test_tier_logic():
    # Test that RV maps to correct keys
    assert _get_tier_config(80.0)['key'] == 'bottom_third'
    assert _get_tier_config(99.0)['key'] == 'water_walkers'


def test_local_prompt_construction(mock_example_data):
    rpt = Report("Capt", "Jones")
    rpt.rv_cum_min = 99.0  # Water walker
    rpt.accomplishments = "- Saved the world"

    # We expect the builder to handle missing keys gracefully (defaulting to empty)
    # or use the provided mock data if keys match.
    # Since our mock only has 'top_third' and we passed 99 RV (water_walker),
    # it should gracefully handle the missing example key.

    prompt = build_local_prompt(mock_example_data, rpt)

    assert "Jones" in prompt
    assert "Capt" in prompt
    assert "Saved the world" in prompt
    assert "US Marine Corps" in prompt