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