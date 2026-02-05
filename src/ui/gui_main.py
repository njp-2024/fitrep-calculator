import os
import streamlit as st
from pathlib import Path
import sys
from dotenv import load_dotenv

# [TODO] DevOps: When deploying, run this app as a module (python -m src.main)
# [TODO] Refactor: Move this path logic to a generic 'utils.py' or run app as a module.
# needed to get project imports to work w/ streamlit
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

import src.app.models as models
import src.app.constants as constants
import gui_profile
import gui_reports
import gui_narratives
import gui_sidebar as sidebar


# Page Configuration (Browser Tab Title)
st.set_page_config(page_title="FitRep Assistant", layout="wide")

load_dotenv()

# BRIDGE: Load secrets into os.environ for the backend to see
try:
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    if "HF_API_TOKEN" in st.secrets:
        os.environ["HF_API_TOKEN"] = st.secrets["HF_API_TOKEN"]
except FileNotFoundError:
    # This just means we are running locally without a secrets.toml file.
    # We can safely ignore this because load_dotenv() handled it above.
    pass


####################################################################################
###################################  Header ########################################
####################################################################################

def render_header():
    """Renders the global application header using custom HTML for layout."""
    # Title and Welcome Message
    st.markdown(
        """
        <div style="
            text-align: center;
            background-color: #e8f0fe;
            color: #1f2937;
            padding: 10px;
            border-radius: 6px;
            font-weight: 600;
            margin-bottom: 10px;
        ">
            -- 🚧 <strong>PROTOTYPE</strong> — Internal use only. Not an official DoW application. --
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True):
        st.markdown(f"""
                <div style='text-align: center; margin-top: -10px;'>
                    <h1 style='margin-bottom: 0px;'>FitRep Calculator</h1>
                    <p style='color: gray; margin-top: 0px;'>See projected Relative Values for FitReps before submitting. Generate accurate Section I comments quickly and easily. | v{constants.APP_VERSION}</p>
                </div>
            """, unsafe_allow_html=True)

####################################################################################
############################# Initializations ######################################
####################################################################################

def initializations():
    """
    Initializes the Streamlit Session State.

    Uses a dictionary of default values to ensure all keys exist before
    the app logic attempts to access them.
    """
    default_state = {
        # Navigation
        'page': 'profile',

        # Core Data Models
        'original_profile': None,
        'active_profile': None,
        'rpt_db': models.ReportDB(),

        # Report Editing State
        'previous_name': None,
        'save_rpt_msg': None,

        # Real-time/Shadow States (For "What-If" calculations)
        'display_rpt': None,
        'display_profile': None,
        'display_db': None,

        # Narrative Generation State
        'narrative_prev_name': None,
        'narrative_prompt_text': "",
        'narrative_accomplishments': "",
        'narrative_context': None,
        'narrative_final_text': None,
        'narratives_gen_complete': None,

        # Trigger Keys (Buttons)
        'reset_narrative': None,
        'reset_secti': None,

        # check local
        # 'is_local' : bool(constants.OLLAMA_PATH)
    }

    # Dynamic Keys (Category Buttons)
    # This prevents us from writing 14 lines of manual initialization
    for cat in constants.USMC_CATEGORIES:
        default_state[f"btn_{cat}"] = "C"

    # Apply Defaults
    for key, default_val in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = default_val


####################################################################################
##################################  main ###########################################
####################################################################################
def main():
    """
    Main Application Router.
    Controls the flow between Profile, Reports, and Narrative pages.
    """

    initializations()

    render_header()

    current_page = st.session_state['page']
    if current_page == 'profile':
        gui_profile.run_profile_page()

    elif current_page == 'reports':
        gui_reports.run_reports_page()

    elif current_page == 'narratives':
        gui_narratives.run_narratives_page()

    sidebar.render_sidebar()


if __name__ == '__main__':
    main()