import pytest
import numpy as np
from src.app.models import Report, ReportDB, RankProfile


####################################################################################
###############################  Reports Tests  ####################################
####################################################################################
def test_report_initialization():
    rpt = Report("Capt", "Smith")
    assert rpt.rank == "Capt"
    assert rpt.name == "Smith"
    assert rpt.rpt_avg == 0.0


def test_score_conversion():
    scores = {
        "Performance": "A",  # 1
        "Proficiency": "B",  # 2
        "Courage": "H"  # 0 (Not Observed)
    }
    rpt = Report("Capt", "Test", scores)

    # Check underlying numpy array
    assert rpt.scores[0] == 1.0  # Performance
    assert rpt.scores[1] == 2.0  # Proficiency
    assert rpt.scores[2] == 0.0  # Courage (index 2 depends on your key order, ensuring specific mapping)
    assert rpt.scores[10] == 0.0 # Wasn't included in the scores dict, model should still have 0 set


def test_report_average_calculation():
    # A (1) + B (2) + C (3) = 6 / 3 = 2.0
    scores = {"Performance": "A", "Proficiency": "B", "Courage": "C"}
    rpt = Report("Capt", "Test", scores)
    assert rpt.rpt_avg == 2.0


def test_report_average_ignore_H():
    # A (1) + H (0) = 1 / 1 = 1.0 (H is ignored in denominator)
    scores = {"Performance": "A", "Proficiency": "H"}
    rpt = Report("Capt", "Test", scores)
    assert rpt.rpt_avg == 1.0


####################################################################################
###############################  Database Tests  ###################################
####################################################################################
def test_db_add_retrieve():
    db = ReportDB()
    rpt = Report("Sgt", "Doe")
    db.add_report(rpt)

    assert db.get_num_reports() == 1
    assert db.is_name_in_db("Doe") is True
    assert db.get_report_by_name("Doe") == rpt