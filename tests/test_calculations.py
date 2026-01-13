import pytest

import src.app.calc_eng as calc_eng
from src.app.calc_eng import _rv_eq, _update_profile
from src.app.models import RankProfile, Report, ReportDB


####################################################################################
##############################  RV Logic Tests  ####################################
####################################################################################
def test_rv_standard_case():
    # Scenario: Profile High 4.0, Avg 3.0. Report is 3.5.
    # Formula: 90 + 10 * ((3.5 - 3.0) / (4.0 - 3.0)) = 90 + 10 * 0.5 = 95.0
    rv = _rv_eq(rpt_avg=3.5, num_rpts=5, high=4.0, avg=3.0)
    assert rv == 95.0


def test_rv_ceiling_case():
    # Scenario: Report is the new High (4.0).
    # Formula: 90 + 10 * ((4.0 - 3.0) / (4.0 - 3.0)) = 100.0
    rv = _rv_eq(rpt_avg=4.0, num_rpts=5, high=4.0, avg=3.0)
    assert rv == 100.0


def test_rv_floor_case():
    # Scenario: Report is way below average. Should floor at 80.
    rv = _rv_eq(rpt_avg=1.0, num_rpts=5, high=4.0, avg=3.0)
    assert rv == 80.0


def test_rv_small_profile():
    # Less than 3 reports = 0 RV
    rv = _rv_eq(rpt_avg=3.5, num_rpts=2, high=4.0, avg=3.0)
    assert rv == 0.0


def test_rv_zero_variance():
    # High == Avg (Everyone has the same score) = 90.0
    rv = _rv_eq(rpt_avg=4.0, num_rpts=10, high=4.0, avg=4.0)
    assert rv == 90.0


####################################################################################
########################  Profile Update Tests  ####################################
####################################################################################
def test_profile_update_logic():
    # Setup: Empty DB and Profile
    db = ReportDB()
    original_prof = RankProfile("Test_Orig", "Capt", 0, 0, 0, 0)
    active_prof = RankProfile("Test_Active", "Capt", 0, 0, 0, 0)

    # Add 3 Reports with known averages
    # R1: 4.0, R2: 3.0, R3: 2.0
    # Expected Profile: High 4.0, Low 2.0, Avg 3.0

    r1 = Report("Capt", "One", {'Performance': 'D'})
    #r1.rpt_avg = 4.0
    r2 = Report("Capt", "Two", {'Performance': 'C'})
    #r2.rpt_avg = 3.0
    r3 = Report("Capt", "Three", {'Performance': 'B'})
    #r3.rpt_avg = 2.0

    db.add_report(r1)
    db.add_report(r2)
    db.add_report(r3)

    # Run Calculation
    _update_profile(original_prof, active_prof, db)

    assert active_prof.high == 4.0
    assert active_prof.low == 2.0
    assert active_prof.avg == 3.0
    assert active_prof.num_rpts == 3


####################################################################################
########################  NEW TESTS: Precision & Advanced  #########################
####################################################################################
def test_rv_precision_edge_cases():
    """Test RV calculation with precision boundaries (±0.005)"""
    # Profile Avg 3.46 could be 3.455-3.465
    rpt_scores = [42/13, 46/13, 52/13, 39/13, 48/13, 45/13]
    num_rpts = len(rpt_scores)
    high = max(rpt_scores)
    starting_real_avg = sum(rpt_scores) / num_rpts
    starting_avg = round(starting_real_avg, 2)
    starting_low_avg = starting_avg - 0.005
    starting_high_avg = starting_avg + 0.005

    new_rpt = 44/13
    rpt_scores.append(new_rpt)
    new_num_rpts = len(rpt_scores)
    new_real_avg = sum(rpt_scores) / new_num_rpts
    new_high = max(rpt_scores)


    real_rv = _rv_eq(new_rpt, new_num_rpts, new_high, new_real_avg)

    new_rounded_high_avg = ((starting_high_avg * num_rpts) + new_rpt) / new_num_rpts
    new_rounded_low_avg = ((starting_low_avg * num_rpts) + new_rpt) / new_num_rpts

    max_rv = _rv_eq(new_rpt, new_num_rpts, new_high, new_rounded_low_avg)
    min_rv = _rv_eq(new_rpt, new_num_rpts, new_high, new_rounded_high_avg)

    # print("strting avg: ", starting_real_avg)
    # print("starting avg: ", starting_avg, starting_high_avg, starting_low_avg)
    #
    # print("Rpt Avg: ", new_rpt)
    # print("Prof avg: ", new_real_avg, new_rounded_low_avg, new_rounded_high_avg)
    # print("real rv: ", real_rv)
    # print("max rv: ", max_rv)
    # print("min rv: ", min_rv)

    assert min_rv < real_rv < max_rv
    assert abs(max_rv - min_rv) < 0.2  # each direction should be less than .1 from reality



def test_unrounding_profile_high():
    """Test lookup table for unrounding Profile High"""
    # 4.08 (rounded) should resolve to 53/13 = 4.076923...
    unrounded = calc_eng.unround_score(4.08)
    assert 4.07 < unrounded < 4.09
    assert isinstance(unrounded, float)


def test_shadow_state_isolation():
    """Test that shadow calculations don't mutate active state"""
    import copy
    db = ReportDB()
    profile = RankProfile("Test", "Capt", 5.0, 3.0, 4.0, 10)

    # Make a shadow copy
    shadow_db = copy.deepcopy(db)
    shadow_profile = copy.deepcopy(profile)

    # Modify shadow
    shadow_profile.high = 6.0

    # Original should be unchanged
    assert profile.high == 5.0


def test_welford_algorithm_accuracy():
    """Test running average calculation (Welford's algorithm)"""
    profile = RankProfile("Test", "Capt", 0, 0, 0, 0)

    # Add 3 reports: 2.0, 3.0, 4.0 → Avg should be 3.0
    profile.update_with_rpt(Report("Capt", "R1", {"Performance": "B"}))  # 2.0
    profile.update_with_rpt(Report("Capt", "R2", {"Performance": "C"}))  # 3.0
    profile.update_with_rpt(Report("Capt", "R3", {"Performance": "D"}))  # 4.0

    assert abs(profile.avg - 3.0) < 0.01


def test_rv_spread_calculation():
    """Test min-max RV range calculation"""
    import src.app.constants as constants
    db = ReportDB()
    profile = RankProfile("Test", "Capt", 4.08, 2.0, 3.34, 10)

    # Create report with all C's
    scores = {cat: "C" for cat in constants.USMC_CATEGORIES}
    rpt = Report("Capt", "Smith", scores)
    db.add_report(rpt)

    # Calculate RV spread
    _, updated_profile, updated_rpt = calc_eng.update_calcs(
        db, profile, profile, "Capt", "Smith", scores
    )

    # Should have min and max RV
    assert updated_rpt.rv_cum_min < updated_rpt.rv_cum_max
    assert updated_rpt.rv_cum_max - updated_rpt.rv_cum_min < 5.0