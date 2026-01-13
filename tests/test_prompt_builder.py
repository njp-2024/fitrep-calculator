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


####################################################################################
########################  NEW TESTS: Prompt Building  ###############################
####################################################################################
def test_all_tier_configs():
    """Test all 4 tier configurations"""
    configs = [
        (_get_tier_config(85.0), 'bottom_third', 'average performer'),
        (_get_tier_config(91.0), 'middle_third', 'above-average performer'),
        (_get_tier_config(96.0), 'top_third', 'top performer'),
        (_get_tier_config(99.0), 'water_walkers', 'exceptional performer'),
    ]

    for config, expected_key, expected_label in configs:
        assert config['key'] == expected_key
        assert expected_label in config['label']


def test_foundation_prompt_structure(mock_example_data):
    """Test Foundation prompt has required components"""
    from src.app.prompt_builder import build_foundation_prompt

    rpt = Report("Capt", "Smith")
    rpt.rv_cum_min = 95.0
    rpt.accomplishments = "Test accomplishments"
    rpt.context = "Test context"

    sys_prompt, user_prompt = build_foundation_prompt(mock_example_data, rpt)

    # System prompt should have key components
    assert "United States Marine" in sys_prompt
    assert "TASK:" in sys_prompt
    assert "NARRATIVE STRUCTURE:" in sys_prompt
    assert "GUIDELINES:" in sys_prompt

    # User prompt should have report details
    assert "Smith" in user_prompt
    assert "Capt" in user_prompt
    assert "accomplishments" in user_prompt.lower()
    assert "Test accomplishments" in user_prompt


def test_openweight_prompt_structure(mock_example_data):
    """Test OpenWeight prompt differs from Foundation"""
    from src.app.prompt_builder import build_open_weights_prompt, build_foundation_prompt

    rpt = Report("Capt", "Smith")
    rpt.rv_cum_min = 95.0
    rpt.accomplishments = "Test accomplishments"

    foundation_sys, _ = build_foundation_prompt(mock_example_data, rpt)
    openweight_sys, _ = build_open_weights_prompt(mock_example_data, rpt)

    # Should be different (OpenWeight has different formatting)
    assert foundation_sys != openweight_sys

    # OpenWeight should have specific structure
    assert "United States Marine" in openweight_sys
    assert "STRICT OUTPUT RULES:" in openweight_sys


def test_missing_yaml_graceful_handling():
    """Test prompt builder handles missing example files"""
    # This requires that ExampleData doesn't crash if files are missing
    # For now, just verify ExampleData can be instantiated
    example_data = ExampleData()

    assert isinstance(example_data.examples, dict)
    assert isinstance(example_data.recs, dict)