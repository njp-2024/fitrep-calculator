import copy

import streamlit as st
from pathlib import Path
import sys

# [TODO] DevOps: Standardize path handling
# needed to get project imports to work w/ streamlit
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

import src.app.models as models
import src.app.calc_eng as calc_eng
import src.app.constants as constants


####################################################################################
##################################  Logic  #########################################
####################################################################################
def reset_attribute_buttons():
    """Resets all attribute keys in session_state to 'C' (Average)."""
    for cat in constants.USMC_CATEGORIES:
        st.session_state[f"btn_{cat}"] = "C"


def load_mro_data():
    """
    Callback function triggered when MRO Name changes.
    Checks DB:
      - If exists: Loads saved scores into button keys.
      - If new: Resets button keys to default.
    """
    # Get the name entered (st.session_state is already updated by the widget)
    new_name = st.session_state.reports_name
    db = st.session_state.rpt_db

    # Check DB
    if db.is_name_in_db(new_name):
        report = db.get_report_by_name(new_name)
        rpt_scores = report.get_letter_scores()
        # Load scores into the session keys that control the widgets
        for cat, score in rpt_scores.items():
            st.session_state[f"btn_{cat}"] = score
        st.toast(f"Loaded existing data for {new_name}")
    else:
        # Reset to defaults for a new entry
        reset_attribute_buttons()


def render_navigation():
    """Renders the top navigation bar and action buttons."""
    c1, c2, c3, c4 = st.columns([1.3, 1, 1, 4], gap='small')
    has_reports = st.session_state.rpt_db.get_num_reports() > 0

    with c1:
        st.subheader("Report Data")

    with c2:
        if st.button("◀ Reset Profile", use_container_width=True, help="This will erase all reports and re-set the profile"):
            st.session_state.original_profile = None
            st.session_state.active_profile = None
            st.session_state.rpt_db = models.ReportDB()
            st.session_state.page = 'profile'
            st.rerun()

    with c3:
        if st.button("Generate Section I's ▶", type='primary', use_container_width=True, disabled=not has_reports):
            new_db = copy.deepcopy(st.session_state.rpt_db)
            new_prof = copy.deepcopy(st.session_state.active_profile)
            st.session_state.display_db = new_db
            st.session_state.display_profile = new_prof
            st.session_state.page = 'narratives'
            st.rerun()

    with c4:
        if not has_reports:
            st.warning("Save reports to unlock Sect I generation")


def run_reports_page():
    render_navigation()

    rank_prof = st.session_state.active_profile
    if not rank_prof:
        st.error("No Profile Found. Please configure profile first.")
        return

    # Rank and Name
    c1, c2 = st.columns(2)
    with c1:
        #mro_rank = rank_prof.rank
        st.text_input("MRO Rank - Must match Profile Rank", key='reports_rank', value=rank_prof.rank, disabled=True)

    with c2:
        #mro_name = st.text_input("MRO Name", key='reports_name', placeholder="LAST", disabled=False)
        st.text_input(
            "MRO Name",
            key='reports_name',
            placeholder="e.g. SMITH",
            on_change=load_mro_data
        )

    # Determine Mode (Edit vs New)
    # We check this purely for UI feedback (Warning/Success messages)
    # The actual data loading happened in the callback above.
    current_name = st.session_state.reports_name
    editing = st.session_state.rpt_db.is_name_in_db(current_name)

    if editing:
        c2.warning("Currently editing this report")

    # show table of scores
    st.subheader("Attributes")
    st.caption(
        "Mark based on descriptions on the FitRep, do NOT mark to your profile.  Use this for validation and refinement only.")

    # The Table of Buttons

    current_scores = {}

    for cat in constants.USMC_CATEGORIES:
        # row_label is the name, row_buttons is the button bar
        row_label, row_buttons = st.columns([0.4, 2], gap="small")  # st.columns([1, 2])

        with row_label:
            st.markdown(f"**{cat}**")

        with row_buttons:
            val = st.segmented_control(
                label=cat,
                # TODO: make attribute scors a constant
                options=constants.SCORE_LETTER_VALS,
                #default="C",
                key=f"btn_{cat}",
                label_visibility="collapsed",  # Hides the label so it looks like a table row
                selection_mode='single',
                disabled=not current_name
            )
            current_scores[cat] = val

    # Real time calculation updates based on current scores
    # check inputs for validitity
    valid_rpt_msg, valid_rpt_data = calc_eng.validate_rpt_inputs(current_name, current_scores)

    if valid_rpt_data:
        st.success(valid_rpt_msg)
        copy_of_prof = copy.deepcopy(st.session_state.active_profile)
        copy_of_db = copy.deepcopy(st.session_state.rpt_db)
        working_rpt_db, working_rank_prof, working_rpt = calc_eng.update_calcs(copy_of_db, st.session_state.original_profile,
                                                                               copy_of_prof, rank_prof.rank,
                                                                               current_name, current_scores)
        st.session_state.display_db = working_rpt_db
        st.session_state.display_profile = working_rank_prof
        st.session_state.display_rpt = working_rpt

    else:
        st.error(valid_rpt_msg)
        st.session_state.display_rpt = None
        st.session_state.display_profile = None
        st.session_state.display_db = None

    bt_label = "Add to profile" if not editing else "Save Changes"
    if st.button(bt_label, disabled=not valid_rpt_data):
        new_db = copy.deepcopy(st.session_state.display_db)
        new_prof = copy.deepcopy(st.session_state.display_profile)
        st.session_state.rpt_db = new_db
        st.session_state.active_profile = new_prof
        if editing:
            saved_report_msg = "Changes Saved"
        else:
            saved_report_msg = "Report added to profile"
        st.session_state.save_rpt_msg = saved_report_msg
        st.rerun()

    if st.session_state.save_rpt_msg:
        st.success(st.session_state.save_rpt_msg)
        st.session_state.save_rpt_msg = None
