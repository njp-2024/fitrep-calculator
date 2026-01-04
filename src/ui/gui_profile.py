import streamlit as st
from pathlib import Path
import sys

# [TODO] DevOps: Standardize path handling in a utility module or run from root.
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

def validate_inputs(high, low, avg, count):
    """
    Validates the mathematical integrity of the profile data.

    Returns:
        tuple: (is_valid (bool), error_message (str or None))
    """
    if count < 0:
        return False, "Report count cannot be negative."

    # If there are reports, standard logic applies
    if count > 0:
        if not (0.0 <= high <= 7.0): return False, "High must be between 0 and 7."
        if not (0.0 <= low <= 7.0): return False, "Low must be between 0 and 7."
        if not (0.0 <= avg <= 7.0): return False, "Average must be between 0 and 7."

        if low > high: return False, "Low cannot be greater than High."
        if avg > high: return False, "Average cannot be greater than High."
        if avg < low: return False, "Average cannot be lower than Low."

        if count < 3 and avg > 0: return False, "Avg must be 0 if you have fewer than 3 reports."

    elif count == 0 and (high > 0 or low > 0 or avg > 0):
        return False, "High/Low/Avg must be 0 if you have 0 reports."

    return True, None

def run_profile_page():
    """
    Renders the Profile Configuration Page.
    Collects baseline RS data (Rank, High, Low, Avg, Count).
    """
    st.subheader("Profile Data")
    st.caption("Enter RS's current profile data from OMPF.  It will be used to calculate Relative Values of new reports and to generate the Section I comments.")

    # Create 5 columns of equal width for the inputs
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        rank = st.selectbox("Rank", constants.USMC_RANKS, key='prof_rank')
    with col2:
        high = st.number_input("Profile High", key='prof_high', min_value=0.0, max_value=7.0, value=4.0, step=0.01)
    with col3:
        low = st.number_input("Profile Low", key='prof_low', min_value=0.0, max_value=7.0, value=2.0, step=0.01)
    with col4:
        avg = st.number_input("Profile Avg", key='prof_avg', min_value=0.0, max_value=7.0, value=3.5, step=0.01)
    with col5:
        num_reports = st.number_input("Total Reports", key='prof_num_rpts', min_value=0, step=1)

    st.divider()

    is_valid, error_msg = validate_inputs(high, low, avg, num_reports)
    if not is_valid:
        st.error(error_msg)

    if st.button("Save Profile", type='primary', disabled=not is_valid):
        unrounded_high = calc_eng.unround_score(high)
        unrounded_low = calc_eng.unround_score(low)
        st.session_state.original_profile = models.RankProfile("Original", rank, unrounded_high, unrounded_low, avg, num_reports)
        st.session_state.active_profile = models.RankProfile("Active", rank, unrounded_high, unrounded_low, avg, num_reports)
        st.session_state.page = 'reports'
        st.rerun()
    st.caption("Save profile to add reports - profile will be locked while entering reports")
