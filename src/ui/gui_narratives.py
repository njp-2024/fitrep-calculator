import hashlib

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
######################  Load and Cache Examples  ###################################
####################################################################################
@st.cache_resource
def get_cached_data():
    return models.ExampleData()

####################################################################################
######################  Navigation and Rpt Summary  ################################
####################################################################################
def render_navigation():
    """Renders top navigation buttons and header"""
    c1, c2, c3, c4 = st.columns([1.3, 1, 1, 4], gap='small')
    with c1:
        st.subheader("Generate Sect I")

    with c2:
        if st.button("◀ Edit Reports", use_container_width=True, help="Editing the reports will erase narrative inputs"):
            st.session_state.narrative_prev_name = None
            st.session_state.page = 'reports'
            st.rerun()

    with c4:
        if st.session_state.rpt_db.get_num_reports() <= 0:
            st.warning("No reports")



def render_rpt_data():
    """Displays the read-only stats for the selected Marine."""
    select_names = st.session_state.rpt_db.name_list

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        name = st.selectbox("Name", select_names, key='narrative_name')
        curr_rpt = st.session_state.rpt_db.get_report_by_name(name)
        curr_rpt_score_dict = curr_rpt.get_letter_scores()
        with st.container(border=True):
            # profile data in a table format
            h_col1, h_col2, h_col3 = st.columns(3)
            h_col1.markdown("**Rpt Avg**")
            h_col2.markdown("**Rv Proc**")
            h_col3.markdown("**RV Cum**")
            # Create the "Data Row"
            v_col1, v_col2, v_col3 = st.columns(3)
            v_col1.write(f"{curr_rpt.rpt_avg:.2f}")
            v_col2.write(f"{curr_rpt.rv_proc_min:.2f} - {curr_rpt.rv_proc_max:.2f}")
            v_col3.write(f"{curr_rpt.rv_cum_min:.2f} - {curr_rpt.rv_cum_max:.2f}")


    with c2:
        col_2_atts = constants.USMC_CATEGORIES[:5]
        for cat in col_2_atts:
            att_name, att_score = st.columns([4, 2], gap="large")
            att_name.markdown(f"{cat}")
            att_score.markdown(f"**{curr_rpt_score_dict[cat]}**")

    with c3:
        col_3_atts = constants.USMC_CATEGORIES[5:10]
        for cat in col_3_atts:
            att_name, att_score = st.columns([4, 2], gap="large")
            att_name.markdown(f"{cat}")
            att_score.markdown(f"**{curr_rpt_score_dict[cat]}**")

    with c4:
        col_4_atts = constants.USMC_CATEGORIES[10:]
        for cat in col_4_atts:
            att_name, att_score = st.columns([4, 2], gap="large")
            att_name.markdown(f"{cat}")
            att_score.markdown(f"**{curr_rpt_score_dict[cat]}**")

    return curr_rpt



####################################################################################
############################  Narrative Inputs  ####################################
####################################################################################

def get_input_hash(name, rank, scores, accomplishments, context, model_option):
    """Generates a unique signature for the current set of inputs.
    Prevents multiple LLM generations in a row for the same data"""
    combined_string = f"{name}|{rank}|{str(sorted(scores.items()))}|{accomplishments}|{context}|{model_option}"
    # Generate a unique MD5 hex digest
    return hashlib.md5(combined_string.encode()).hexdigest()


def _handle_save_inputs(name, accomplishments, user_context):
    # enforce character limits
    acc = accomplishments[:constants.MAX_ACCOMPLISHMENTS_LENGTH]
    context = user_context[:constants.MAX_USER_CONTEXT_LENGTH]

    # hack to get prompts (added after initial design)
    rpt = st.session_state.rpt_db.get_report_by_name(name)
    rpt.accomplishments = acc
    rpt.context = context
    example_data = get_cached_data()
    s, u = calc_eng.gen_prompt(rpt, example_data)

    # update rpt
    st.session_state.rpt_db.edit_report_narrative_inputs(name, acc, context, s, u)

def render_input_section(curr_rpt, changed_names):
    """
    Handles the text inputs.
    Returns: (is_saved, accomplishments_text, context_text)
    """
    st.write("**Narrative Info**")

    if changed_names or st.session_state.reset_narrative:  #st.session_state.narrative_prev_name != curr_rpt.name or st.session_state.reset_narrative:
        st.session_state.narrative_accomplishments = curr_rpt.accomplishments
        st.session_state.narrative_context = curr_rpt.context
        st.session_state.narrative_prev_name = curr_rpt.name
        st.session_state.reset_narrative = False

    accomplishments = st.text_area(f"Billet Accomplishments - ({constants.MIN_ACCOMPLISHMENTS_LENGTH} - {constants.MAX_ACCOMPLISHMENTS_LENGTH} chars)",
                                   height=300,
                                   placeholder="Copy/Paste accomplishments here OR describe what MRO did. (e.g., Managed 50 vehicles with 100% FMC rate...)",
                                   key='narrative_accomplishments')
    st.caption(f"Current length: {len(accomplishments)} char")

    user_context = st.text_area(f"Additional Context / Personalization - (optional, max {constants.MAX_USER_CONTEXT_LENGTH} chars)",
                                height=100,
                                placeholder="Any specific tone or context you want to include? (e.g., Focus on his leadership during the field exercise...)",
                                key='narrative_context')
    st.caption(f"Current length: {len(user_context)} char")

    # disable save if not valid inputs or data saved and matches saved data
    valid_narrative_inputs =  (constants.MIN_ACCOMPLISHMENTS_LENGTH < len(accomplishments) < constants.MAX_ACCOMPLISHMENTS_LENGTH) and (len(user_context) < constants.MAX_USER_CONTEXT_LENGTH)
    data_saved = curr_rpt.accomplishments != "" and accomplishments == curr_rpt.accomplishments and user_context == curr_rpt.context

    c1, c2, c3 = st.columns([1, 1, 5], gap='small')
    with c1:
        if st.button("Save Narrative Info", type='primary', disabled=not valid_narrative_inputs or data_saved):
            _handle_save_inputs(curr_rpt.name, accomplishments, user_context)
            st.rerun()

    with c2:
        if st.button("Reset / Clear", disabled=data_saved or (not accomplishments and not user_context)):
            st.session_state.reset_narrative = True
            st.rerun()

    if not valid_narrative_inputs:
        st.caption(":red[Invalid Inputs - check character limits]")
    elif data_saved:
        st.caption(":green[Inputs Saved.]")
    else:
        st.caption(":orange[Unsaved Changes - Save to enable generation.]")

    return data_saved, accomplishments, user_context


####################################################################################
##########################  Generative Section  ####################################
####################################################################################

def render_prompt_text_area(prompt_text):
    with st.expander("See Prompt"):
        st.text_area("If you don't want to generate here, you can copy and paste this into the LLM of your choice:",
                     height=500,
                     value=prompt_text,
                     disabled=True
                     )

def render_disclaimer():
    """
    Renders a security warning regarding PII/CUI and third-party API usage.
    """
    st.warning(
        "**PRIVACY WARNING: READ BEFORE GENERATING**\n\n"
        "This tool utilizes commercial third-party AI services (e.g., OpenAI, Hugging Face) "
        "to generate text. Text entered in the narrative input above is transmitted to external servers for processing.\n\n"
        "Alternative: Copy the prompt (see prompt below) into your desired LLM service.\n",
        icon="⚠️"
    )

def render_generation_section(curr_rpt, data_saved, accomplishments, user_context):
    """
    Handles Model Selection and Generation Trigger.
    """
    st.write("**Generate Sect I**")

    # button and model selection
    # disable selection if data is saved
    models = ["Manual Input", "Foundation", "Open Weight"]
    if st.session_state.is_local:
        models.insert(1, "Local")
    model_option = st.radio(
        "Choose your LLM:",
        models, # ["Manual Input", "Local", "Foundation", "Open Weight"],
        horizontal=True,
        index=0,
        key=f"radio_{curr_rpt.name}",
        help=f"Local uses {constants.OLLAMA_MODEL} via Ollama on your CPU. Foundation uses gpt-4o-mini via API. Open Weight uses Qwen2.5-72b-Instruct via API.",
        disabled=not data_saved
    )

    # check current
    current_hash = get_input_hash(curr_rpt.name, curr_rpt.rank, curr_rpt.get_letter_scores(), accomplishments,
                                  user_context, model_option)
    fresh_data = current_hash != getattr(curr_rpt, 'last_gen_hash', None)  #if model_option != 'Manual Input' else True

    # disclaimer
    if model_option == "Foundation" or "Open Weight":
        render_disclaimer()

    # give user opportunity to take prompt before generation
    if data_saved:
        render_prompt_text_area(curr_rpt.print_prompt())

    # check max gens
    max_generations = 3
    exceeded_max_gens = curr_rpt.secti_gens >= max_generations

    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        # Main Generate Button
        # can click when data is saved, there is fresh data, max gens not exceeded, and model option is not manual
        can_click = data_saved and fresh_data and not exceeded_max_gens and model_option != "Manual Input"
        generate_btn = st.button("Generate Sect I", type="primary", disabled=not can_click)

    with col2:
        # The 'Try Again' Reset
        if st.button("Reset Lock", help="Allow regeneration with same inputs", disabled=not data_saved or fresh_data or exceeded_max_gens):
            curr_rpt.last_gen_hash = None
            st.rerun()

    if generate_btn:  # st.button("Generate Sect I", type="primary"):
        _handle_llm_generation(curr_rpt, model_option, current_hash)

    st.caption(f"{max_generations - curr_rpt.secti_gens} generations remaining for {curr_rpt.rank} {curr_rpt.name}")

    if exceeded_max_gens:
        st.caption(f":red[Max usage exceeded for {curr_rpt.rank} {curr_rpt.name}]") # st.error(f"Max usage exceeded for {curr_rpt.rank} {curr_rpt.name}")
    elif not data_saved:
        st.caption(":red[Need to save inputs]")  # st.error("Need to save inputs")
    #elif model_option == "Manual Input":
    #    st.caption(":orange[Need to save inputs]")  # st.info("Type comments in the box")
    elif not fresh_data:
        st.caption(":orange[Section I already generated for these inputs. Change something to regenerate, or hit Reset to unlock.]")  # st.info("Section I already generated for these inputs. Change something to regenerate, or hit Reset to unlock.")


def _handle_llm_generation(curr_rpt, model_option, current_hash):
    """
    Internal helper to wrap API calls with error handling.

    ONly foundation will work in app.  Local and Open will be disabled.
    """
    example_data = get_cached_data()

    try:
        with st.spinner(f"Generating with {model_option}..."):
            # Map the selection to your LLM clients
            if "Local" in model_option:
                result, model = calc_eng.query_local(curr_rpt, example_data)

            elif "Foundation" in model_option:
                result, model = calc_eng.query_foundation(curr_rpt, example_data)
                st.session_state.rpt_db.increment_report_gen_counter(curr_rpt.name)
                curr_rpt.last_gen_hash = current_hash

            elif "Open" in model_option:
                result, model = calc_eng.query_open(curr_rpt, example_data)
                st.session_state.rpt_db.increment_report_gen_counter(curr_rpt.name)
                curr_rpt.last_gen_hash = current_hash

            else:
                result, model = calc_eng.query_manual()

        st.session_state['output'] = (result, model)
        st.session_state.narratives_gen_complete = True
        st.rerun()

    except Exception as e:
        st.error(f"Generation Failed: {str(e)}")


####################################################################################
############################  Review Section  ######################################
####################################################################################

def render_review_section(curr_rpt, changed_names, data_saved):
    """Renders review final text section."""
    if st.session_state.narratives_gen_complete:
        st.success(f"Generation Complete!  Model used: {st.session_state['output'][1]}")
        st.session_state.narratives_gen_complete = False
        st.session_state.narrative_final_text = st.session_state['output'][0]

    elif changed_names:
        st.session_state.narrative_final_text = curr_rpt.secti

    if st.session_state.reset_secti:
        st.session_state.narrative_final_text = curr_rpt.secti
        st.session_state.reset_secti = False

    final_text = st.text_area(
        label="Review and Edit Result:",
        #value=display_text,  # st.session_state['output'],
        key="narrative_final_text",
        height=250,
        disabled=not data_saved  # or not data_matches or lock_gen
    )

    # Character count helper
    char_count = len(final_text) if final_text else 0
    st.caption(f"Current Character Count: {char_count} / 1250")

    if char_count > 1250:
        st.error("Warning: This narrative may be too long for the standard FitRep block.")

    # write captions
    final_not_saved = False
    final_updated = False
    disable_final_msg = "Ready..."
    if not st.session_state.narrative_final_text:  # not final_text:
        final_not_saved = True
        disable_final_msg = "Generate text to save"
    elif st.session_state.narrative_final_text == curr_rpt.secti: # final_text == curr_rpt.secti:
        final_updated = True
        disable_final_msg = "Saved"
    else:
        disable_final_msg = "Unsaved Changes"

    c1, c2, c3 = st.columns([1, 1, 5], gap='small')

    with c1:
        if st.button("Save Sect I", disabled=final_not_saved or final_updated):
            st.session_state.rpt_db.edit_report_sect_i(curr_rpt.name, final_text)
            st.rerun()

    with c2:
        reset_secti_label = "Reset to saved" if curr_rpt.secti != "" else "Clear inputs"
        if st.button(reset_secti_label, key='reset_secti_btn', disabled=final_not_saved or final_updated):
            st.session_state.reset_secti = True
            st.rerun()

    if final_not_saved:
        st.caption(f":red[{disable_final_msg}]")  # st.error(disable_final_msg)
    elif final_updated:
        st.caption(f":green[{disable_final_msg}]")  # st.success(disable_final_msg)
    else:
        st.caption(f":orange[{disable_final_msg}]")

    st.divider()

    txt = calc_eng.print_profile(st.session_state.rpt_db, st.session_state.original_profile, st.session_state.active_profile)
    st.download_button("Export Summary (.txt)",
                       data=txt,
                       file_name=f"{curr_rpt.rank} Session Summary.txt",
                       mime="text/plain")

    if st.button("Print Summary"):
        st.text_area(
            label="Summary:",
            value=txt,  # st.session_state['output'],
            height=1000,
            disabled=False # or not data_matches or lock_gen
        )


####################################################################################
#############################  Main Run Method  ####################################
####################################################################################

def run_narratives_page():
    #st.write('#')
    #st.subheader("Generate Sect I")
    render_navigation()
    st.write("**Rpt Data**")
    curr_rpt = render_rpt_data()
    st.session_state.display_rpt = curr_rpt

    st.divider()

    changed_names = st.session_state.narrative_prev_name != curr_rpt.name
    st.session_state.narrative_prev_name = curr_rpt.name

    data_saved, accomplishments, user_context = render_input_section(curr_rpt, changed_names)

    st.divider()

    render_generation_section(curr_rpt, data_saved, accomplishments, user_context)

    st.divider()

    render_review_section(curr_rpt, changed_names, data_saved)
