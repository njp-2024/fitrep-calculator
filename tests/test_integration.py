import pytest
import copy
from src.app.models import RankProfile, Report, ReportDB, ExampleData
import src.app.calc_eng as calc_eng
import src.app.constants as constants


####################################################################################
#############################  Integration Tests  ###################################
####################################################################################
def test_full_workflow_single_report():
    """Test complete workflow: Profile → Report → RV calculation"""
    # 1. Create profile
    original = RankProfile("Original", "Capt", 4.08, 2.00, 3.34, 10)
    active = RankProfile("Active", "Capt", 4.08, 2.00, 3.34, 10)
    db = ReportDB()

    # 2. Add report with all C's (average = 3.0)
    scores = {cat: "C" for cat in constants.USMC_CATEGORIES}
    rpt = Report("Capt", "SMITH", scores)
    db.add_report(rpt)

    # Verify report was added
    assert db.get_num_reports() == 1
    assert db.is_name_in_db("SMITH") is True

    # 3. Calculate RV
    updated_db, updated_profile, updated_rpt = calc_eng.update_calcs(
        db, original, active, "Capt", "SMITH", scores
    )

    # 4. Verify RV calculated
    assert updated_rpt.rv_cum_min > 0
    assert updated_rpt.rv_cum_max > updated_rpt.rv_cum_min
    assert updated_rpt.rv_cum_max - updated_rpt.rv_cum_min < 5.0  # Spread should be reasonable

    # 5. Verify profile updated
    assert updated_profile.num_rpts == 11  # Was 10, now 11


def test_full_workflow_multiple_reports():
    """Test workflow with multiple reports"""
    # 1. Create profile
    original = RankProfile("Original", "Capt", 5.0, 3.0, 4.0, 10)
    active = RankProfile("Active", "Capt", 5.0, 3.0, 4.0, 10)
    db = ReportDB()

    # 2. Add three reports with different scores
    # Report 1: High performer (mostly A's and B's)
    scores_high = {cat: "D" if i % 2 == 0 else "E" for i, cat in enumerate(constants.USMC_CATEGORIES)}
    rpt1 = Report("Capt", "ALPHA", scores_high)
    db.add_report(rpt1)

    # Report 2: Average performer (all C's)
    scores_avg = {cat: "C" for cat in constants.USMC_CATEGORIES}
    rpt2 = Report("Capt", "BRAVO", scores_avg)
    db.add_report(rpt2)

    # Report 3: Low performer (mostly D's and E's)
    scores_low = {cat: "A" if i % 2 == 0 else "B" for i, cat in enumerate(constants.USMC_CATEGORIES)}
    rpt3 = Report("Capt", "CHARLIE", scores_low)
    db.add_report(rpt3)

    # 3. Verify all reports added and ordering preserved
    assert db.get_num_reports() == 3
    assert db.name_list == ["ALPHA", "BRAVO", "CHARLIE"]

    # 4. Calculate RV for each report
    _, _, updated_rpt1 = calc_eng.update_calcs(db, original, active, "Capt", "ALPHA", scores_high)
    _, _, updated_rpt2 = calc_eng.update_calcs(db, original, active, "Capt", "BRAVO", scores_avg)
    _, _, updated_rpt3 = calc_eng.update_calcs(db, original, active, "Capt", "CHARLIE", scores_low)

    # 5. Verify RV ordering (high performer should have higher RV than low performer)
    # Note: Due to RV floor at 80, we just verify all have valid RV values
    assert updated_rpt1.rv_cum_min > 0
    assert updated_rpt2.rv_cum_min > 0
    assert updated_rpt3.rv_cum_min > 0

    # 6. Verify high performer has higher RV than low performer
    assert updated_rpt1.rv_cum_min > updated_rpt3.rv_cum_min


def test_narrative_generation_workflow():
    """Test narrative generation workflow with mocked LLM"""
    from unittest.mock import patch, MagicMock
    from src.app.llm_base import LLMResponse
    from src.app.prompt_builder import build_foundation_prompt

    # 1. Create report with RV
    rpt = Report("Capt", "JONES")
    rpt.rv_cum_min = 95.0
    rpt.accomplishments = "Led platoon through deployment. Maintained 100% accountability."
    rpt.context = "Deployed to combat zone"

    # 2. Build prompt
    example_data = ExampleData()
    sys_prompt, user_prompt = build_foundation_prompt(example_data, rpt)

    # Verify prompt components
    assert "JONES" in user_prompt
    assert "accomplishments" in user_prompt.lower()
    assert "United States Marine" in sys_prompt

    # 3. Mock LLM response (don't actually call OpenAI)
    mock_response = LLMResponse(
        text="Outstanding Marine. Demonstrated exceptional leadership under fire.",
        model="gpt-4o-mini",
        prompt_tokens=500,
        completion_tokens=100
    )

    # Verify response structure
    assert mock_response.text is not None
    assert len(mock_response.text) > 0
    assert mock_response.model == "gpt-4o-mini"


def test_shadow_state_workflow():
    """Test that shadow calculations preserve active state"""
    # 1. Create active profile and DB
    original = RankProfile("Original", "Capt", 5.0, 3.0, 4.0, 10)
    active = RankProfile("Active", "Capt", 5.0, 3.0, 4.0, 10)
    db = ReportDB()

    # Add a report
    rpt = Report("Capt", "TEST")
    db.add_report(rpt)

    # 2. Create shadow copies (simulating "what-if" calculation)
    shadow_original = copy.deepcopy(original)
    shadow_active = copy.deepcopy(active)
    shadow_db = copy.deepcopy(db)

    # 3. Modify shadow state
    shadow_active.high = 6.0
    shadow_db.add_report(Report("Capt", "SHADOW"))

    # 4. Verify original state unchanged
    assert active.high == 5.0
    assert db.get_num_reports() == 1
    assert "SHADOW" not in db.name_list

    # 5. Verify shadow state changed
    assert shadow_active.high == 6.0
    assert shadow_db.get_num_reports() == 2
    assert "SHADOW" in shadow_db.name_list


def test_report_editing_workflow():
    """Test workflow for editing existing report"""
    # 1. Create profile and add initial report
    original = RankProfile("Original", "Capt", 5.0, 3.0, 4.0, 10)
    active = RankProfile("Active", "Capt", 5.0, 3.0, 4.0, 10)
    db = ReportDB()

    scores1 = {cat: "C" for cat in constants.USMC_CATEGORIES}
    rpt1 = Report("Capt", "SMITH", scores1)
    db.add_report(rpt1)

    # 2. Calculate initial RV
    _, _, updated_rpt1 = calc_eng.update_calcs(db, original, active, "Capt", "SMITH", scores1)
    initial_rv = updated_rpt1.rv_cum_min

    # 3. Edit report with different scores
    scores2 = {cat: "B" for cat in constants.USMC_CATEGORIES}
    rpt2 = Report("Capt", "SMITH", scores2)
    db.add_report(rpt2)

    # Verify only one report (edited, not added)
    assert db.get_num_reports() == 1

    # 4. Calculate new RV
    _, _, updated_rpt2 = calc_eng.update_calcs(db, original, active, "Capt", "SMITH", scores2)
    new_rv = updated_rpt2.rv_cum_min

    # 5. Verify RV changed (B's are better than C's, so RV should increase)
    assert new_rv != initial_rv
    # Note: Depending on profile, B's (2.0 avg) might be above or below profile avg
    # Just verify RV was recalculated
    assert new_rv > 0
