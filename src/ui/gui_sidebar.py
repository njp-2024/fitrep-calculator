import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# [TODO] Refactor: Move this path logic to a generic 'utils.py' or run app as a module.
# needed to get project imports to work w/ streamlit
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

import src.app.models as models
import src.app.constants as constants


####################################################################################
##################################  Sidebar ########################################
####################################################################################
def render_about_section():
    """Expanding area to provide info about the app"""
    with st.expander("ℹ️ About"):
        st.markdown("""
                **RV Calculations**
                - Are estimates (OMPF rounding limits precision)
                - Order matters (assumes reports are processed in the order received, not report end/due dates)
                - RV= 0  if # rpts < 3
                - RV= 90 if high == profile average
                - RV= 90 + 10 * ((rpt_avg - prof_avg) / (high - prof_avg))
                - RV floor is 80

                **Section I Comments**
                - Generated using few shot prompts
                - Examples selected based on RV
                - Prompts available via 'Print/Export Summary'

                **Note:** All generated text is DRAFT and should be reviewed for accuracy.
                """)


def render_profile_summary():
    """
    Renders the Profile Summary table at the top of the sidebar.

    Displays a comparison between the Original Profile (historical data)
    and the New Profile (including currently added reports).
    """
    prof = st.session_state.get('display_profile') or st.session_state.get('active_profile')
    orig_prof = st.session_state.get('original_profile')

    if not prof or not orig_prof:
        st.warning("Profile data unavailable.")
        return

    st.header(f"{prof.rank} Profile Summary")

    # Layout: 5 columns for tight data display
    # [Refactor Note]: Markdown tables are brittle. Consider st.dataframe if this gets complex.
    h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([1.2, 1, 1, 1, 1])
    h_col1.markdown("**Profile**")
    h_col2.markdown("**High**")
    h_col3.markdown("**Low**")
    h_col4.markdown("**Avg**")
    h_col5.markdown("**# Rpts**")

    h_col1.markdown("Orig.")
    h_col2.markdown(f"{orig_prof.high:.2f}")
    h_col3.markdown(f"{orig_prof.low:.2f}")
    h_col4.markdown(f"{orig_prof.avg:.2f}")
    h_col5.markdown(f"{orig_prof.num_rpts}")

    h_col1.markdown("*NEW*")
    h_col2.markdown(f"*{prof.high:.2f}*")
    h_col3.markdown(f"*{prof.low:.2f}*")
    h_col4.markdown(f"*{prof.avg:.2f}*")
    h_col5.markdown(f"*{prof.num_rpts}*")


def _render_active_report_card(mro_name: str, mro_rank: str, report_obj):
    """
    Internal helper to render the 'Current Report' card.

    Args:
        mro_name (str): Name of the Marine.
        mro_rank (str): Rank of the Marine.
        report_obj (Report): The working report object containing scores.
    """
    rpt_avg = report_obj.rpt_avg if report_obj else 0.0
    rpt_rv = report_obj.rv_cum if report_obj else 0.0

    with st.container(border=True):
        if not mro_name:
            st.markdown("**No Name Entered**")
        else:
            st.markdown(f"**{mro_rank} {mro_name}**")

        # Comparison Metrics
        c1, c2 = st.columns(2)
        c1.metric("Report Avg", f"{rpt_avg:.2f}")
        c2.metric("Estimated RV", f"{rpt_rv:.2f}")


def render_reports_summary():
    """Renders the summary card for the Reports Entry page."""
    mro_name = st.session_state.get('reports_name', '')
    mro_rank = st.session_state.get('reports_rank', '')
    display_rpt = st.session_state.get('display_rpt')

    _render_active_report_card(mro_name, mro_rank, display_rpt)


def render_narratives_summary():
    """Renders the summary card for the Narratives page."""
    mro_name = st.session_state.get('narrative_name', '')
    prof = st.session_state.get('active_profile')
    mro_rank = prof.rank if prof else "Unknown"
    display_rpt = st.session_state.get('display_rpt')

    _render_active_report_card(mro_name, mro_rank, display_rpt)


def render_rpts_list():
    """
    Renders the list of all reports currently in the working database.
    """
    db = st.session_state.get('display_db') or st.session_state.get('rpt_db')
    if not db or not db.name_list:
        st.caption("No reports added yet.")
        return

    st.write("**Working Reports**")

    # Prepare Data for Dataframe
    # We build a list of dicts to create a clean DataFrame
    data = []
    for name in db.name_list:
        rpt = db.get_report_by_name(name)
        data.append({
            "Name": rpt.name[:8],
            "Avg": float(f"{rpt.rpt_avg:.2f}"),
            "RV": float(f"{rpt.rv_proc:.2f}"),
            "Cum": float(f"{rpt.rv_cum:.2f}")
        })

    df = pd.DataFrame(data)

    # Define Styling Logic - for colors
    def color_rv(val):
        """
        Returns CSS color strings based on USMC RV brackets.
        """
        if val > 93.33:
            return 'color: #2ecc71; font-weight: bold'  # Green
        elif val > 86.66:
            return 'color: #f1c40f; font-weight: bold'  # Yellow/Gold
        else:
            return 'color: #e74c3c'  # Red

    # Apply Styling
    df = df.rename(columns={
        "Name": "MRO",
        "Avg": "Avg",
        "RV": "RV Proc",
        "Cum": "RV Cum"
    })

    # reset index column to remove the extra column of index #'s
    df.set_index('MRO', inplace=True)

    styled_df = (df.style
                 .format("{:.2f}", subset=["Avg", "RV Proc", "RV Cum"])
                 .map(color_rv, subset=["RV Proc", "RV Cum"]))

    # Render Static Table
    st.table(styled_df)


def render_rv_overview():
    """
    Renders the RV Lookup Table (RV vs Report Average).

    Wraps the long list in an expander to save UI space.
    """
    prof = st.session_state.get('display_profile') or st.session_state.get('active_profile')
    if not prof:
        return

    st.write("RV Reference Table")

    rv_dict = prof.calc_scores_for_rv()

    # Convert dictionary to DataFrame for cleaner display
    # Slicing for reasonable range (100 down to 80)
    data = [{"RV": k, "Req. Avg": v} for k, v in rv_dict.items() if 100 >= k >= 80]
    df = pd.DataFrame(data)
    df.set_index('RV', inplace=True)

    st.table(df)


def render_sidebar():
    """
    Main controller for the sidebar.
    Determines which components to render based on current app page state.
    """
    with st.sidebar:
        if not st.session_state.get('active_profile'):
            st.header("Profile Summary")
            st.warning("No Profile Saved")
            return

        render_profile_summary()
        st.divider()

        current_page = st.session_state.get('page')
        if current_page == 'reports':
            render_reports_summary()
        elif current_page == 'narratives':
            render_narratives_summary()
        #st.divider()

        render_rpts_list()
        st.divider()

        render_about_section()

        # TODO: Add calc_rv_table to cacl_eng so we can display the projected RV table
        # render_rv_overview()
