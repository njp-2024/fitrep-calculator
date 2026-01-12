import src.app.models as models
import src.app.llm_base as llm_base
import src.app.llm_clients as llm_clients
import src.app.prompt_builder as prompt_builder
import src.app.constants as constants

####################################################################################
################################  Validation  ######################################
####################################################################################

def validate_rpt_inputs(mro_name, scores_dict):
    """
    Validates report data before processing.

    Args:
        mro_name (str): The Marine's name.
        scores_dict (dict): Dictionary of {Attribute: Score}.

    Returns:
        tuple: (User Message String, Success Boolean)
    """
    if not mro_name:
        msg = "Must input a name"
        success = False
    elif len(mro_name) > 25:
        msg = "Name too long (Max 25 characters)"
        success = False
    elif None in scores_dict.values():
        msg = "Must mark all scores"
        success = False
    elif all(score == "H" for score in scores_dict.values()):
        msg = "Can't have all scores be 'H'"
        success = False
    else:
        msg = "Valid - calculations updated"
        success = True

    return msg, success

####################################################################################
################################  Profile Calcs  ###################################
####################################################################################
# These are needed to turn rounded profile values entered by user to un-rounded values
# otherwise, precision of calculations are off.  This is used for the high and low values.
# We are able to do this because there are only so many ways to get these values.
# Each rpt typically has 13-14 marks, each mark between 1-7.  We can build a table of possible rpt averages
# given that range, then build a look-up table using rounded versions as keys.
# If we could import the user's entire RS profile, we could just calculate un-rounded values
# from scratch, but that is not an option right now.

def _build_unrounded_dict():
    """
    Builds a map of rounded score -> unrounded score, based on 13 or 14 scores in the rpt
    Allows expanding of rounded scores in OMPF for more precise calculations
    """
    num_scores = [13, 14]
    scores = [1, 2, 3, 4, 5, 6, 7]
    scores_dict = {}  # { rounded : unrounded }

    for num in num_scores:
        min_sum = scores[0] * num
        max_sum = scores[-1] * num
        for score_sum in range(min_sum, max_sum + 1):
            avg = score_sum / num
            scores_dict[round(avg, 2)] = avg

    return scores_dict


def unround_score(rounded_score):
    """
    Unrounds score based on 13 or 14 scores.
    """
    unrounded_scores_dict = _build_unrounded_dict()

    return unrounded_scores_dict.get(rounded_score, rounded_score)


####################################################################################
################################  Calculations  ####################################
####################################################################################

def _rv_eq(rpt_avg, num_rpts, high, avg):
    """
    Calculates Relative Value (RV) using the standard linear interpolation formula.

    Formula: RV = 90 + 10 * ((RptAvg - ProfileAvg) / (ProfileHigh - ProfileAvg))
    Constraints:
        - Returns 0 if profile size < 3 (Small Profile).
        - Floors RV at 80.00.
        - Returns 90.00 if High == Avg.
    """
    if num_rpts < 3:
        return 0.

    if high == avg:
        return 90.

    denominator = high - avg
    # If high == avg, return 90.  Floats can get weird, so use this to check.  If differences is nearly 0,
    # assume they are equal and return 90
    if abs(denominator) < 0.0001:
        return 90.

    val = 90. + 10. * ((rpt_avg - avg) / denominator)

    return max(80., val)


def _update_profile(orig_prof, working_prof, db):
    """
    Recalculates statistics for a profile based on a list of reports.

    Performs two passes:
    1. Processing Pass: Calculates 'RV Proc' (RV at the moment of processing).
    2. Cumulative Pass: Calculates 'RV Cum' (RV based on final profile stats).
    """
    # reset working profile values to original as entered by user
    working_prof.set_values(orig_prof.high, orig_prof.low, orig_prof.avg, orig_prof.num_rpts)

    # iterate through reports in order they were entered and update as we go
    # NOTE: This assumes that reports are processed in the order they are received.  This is why order is important in
    # the rpt_db.  All RV @ proc are calculated in the order the user enters the reports.
    for name in db.name_list:
        rpt = db.rpts_dict[name]
        working_prof.update_with_rpt(rpt)

        rv_from_high = _rv_eq(rpt.rpt_avg, working_prof.num_rpts, working_prof.high, working_prof.high_avg)  # working_prof.avg) working_prof.get_average())
        rv_from_low = _rv_eq(rpt.rpt_avg, working_prof.num_rpts, working_prof.high, working_prof.low_avg)  # working_prof.avg) working_prof.get_average())

        rpt.rv_proc_min = min(rv_from_high, rv_from_low)
        rpt.rv_proc_max = max(rv_from_high, rv_from_low)

    # have to go back through and update cumulative rvs based on the final profile values
    final_high = working_prof.high
    final_avg_low = working_prof.low_avg   # working_prof.avg working_prof.get_average()
    final_avg_high = working_prof.high_avg
    final_num_rpts = working_prof.num_rpts
    for name in db.name_list:
        rpt = db.rpts_dict[name]
        rv_cum_from_high = _rv_eq(rpt.rpt_avg, final_num_rpts, final_high, final_avg_high)
        rv_cum_from_low = _rv_eq(rpt.rpt_avg, final_num_rpts, final_high, final_avg_low)

        rpt.rv_cum_min = min(rv_cum_from_low, rv_cum_from_high)
        rpt.rv_cum_max = max(rv_cum_from_low, rv_cum_from_high)


def update_calcs(display_rpt_db, orig_profile, working_profile, mro_rank, mro_name, scores_dict):
    """
    Orchestrator for the "What-If" Shadow Calculation.

    Args:
        display_rpt_db: A COPY of the report DB (not the original), safe to mutate.
        orig_profile: The baseline profile (immutable reference).
        working_profile: A reusable profile object for calculation (mutable).
        mro_rank: Rank of the Marine.
        mro_name: Name of the Marine.
        scores_dict: The raw inputs from the UI.

    Returns:
        tuple: (Updated DB copy, Updated Profile, The New Report Object)
    """
    working_rpt = models.Report(mro_rank, mro_name, scores_dict)

    if display_rpt_db.is_name_in_db(mro_name):
        display_rpt_db.replace_rpt(working_rpt)
    else:
        display_rpt_db.add_report(working_rpt)

    _update_profile(orig_profile, working_profile, display_rpt_db)

    return display_rpt_db, working_profile, working_rpt


def gen_prompt(rpt, example_data):
    """
    Hack fix to add prompt to report model.
    """
    s, u = prompt_builder.build_foundation_prompt(example_data, rpt)
    return s, u


####################################################################################
##################################  LLM Logic  #####################################
####################################################################################

def build_prompts_for_export(rpt_db):
    """
    Builds prompts for each rpt in the list.  This is called when user navigates to Narratives page.
    :param rpt_db: The report DB from memory.
    :return: a list of prompts.
    """
    # Create a clean string with headers for each report
    final_prompts = ""
    for idx, name in enumerate(rpt_db.name_list):
        final_prompts += f"{'=' * 30}\n"
        final_prompts += f"REPORT #{idx + 1}: {name}\n"
        final_prompts += f"{'=' * 30}\n\n"
        final_prompts += f"{rpt_db[name].prompt}\n\n"

    # Handle the case where the list is empty
    if not final_prompts:
        final_prompts = "No reports added to profile yet."

    return final_prompts


def query_open(curr_rpt, example_data):
    """
    Queries HuggingFace Open Weights (Qwen/Mixtral).
    Requires HF_API_TOKEN environment variable.
    """
    s_prompt, u_prompt = prompt_builder.build_open_weights_prompt(example_data, curr_rpt)

    request = llm_base.LLMRequest(
        system_prompt=s_prompt,
        user_prompt=u_prompt,
        max_tokens=constants.OPEN_MAX_TOKENS,
        temperature=constants.OPEN_TEMP
    )

    try:
        # (Defaults to Qwen/Qwen2.5-72B-Instruct unless you pass a model arg)
        # Other models to try:
        # - "mistralai/Mixtral-8x7B-Instruct-v0.1"
        # - "meta-llama/Meta-Llama-3-70B-Instruct"
        # - "Qwen/Qwen2.5-32B-Instruct"
        client = llm_clients.HuggingFaceClient()

        response = client.generate(request)
        return response.text, response.model

    except ValueError as ve:
        # Specific catch for missing API Token
        return f"Configuration Error: {str(ve)}", "Error"
    except Exception as e:
        return f"HuggingFace Error: {str(e)}", "Error"


def query_local(curr_rpt, example_data):
    """
    Queries a local Ollama instance.
    """
    prompt = prompt_builder.build_local_prompt(example_data, curr_rpt)

    request = llm_base.LLMRequest(
        system_prompt="",
        user_prompt=prompt,
        max_tokens=constants.LOCAL_MAX_TOKENS, # Added explicit token limit
        temperature=constants.LOCAL_TEMP # Added creativity param
    )

    try:
        client = llm_clients.LocalModelClient(constants.OLLAMA_PATH, constants.OLLAMA_MODEL)
        response = client.generate(request)
        return response.text, response.model

    except ValueError as ve:
        # Specific catch for missing API Token
        return f"Configuration Error: {str(ve)}", "Error"
    except Exception as e:
        return f"Local Inference Error: {str(e)}", "Error"


def query_manual():
    """Returns a placeholder for manual entry."""
    return "Type section I comments here...", "Manual"


def query_foundation(curr_rpt, example_data):
    """
    Queries OpenAI's GPT-4o-mini.
    Requires OPENAI_API_KEY environment variable.

    Other models:  gpt-5.1, gpt-5-mini, gpt-5-nano
    """
    try:
        llm = llm_clients.OpenAIClient(model="gpt-4o-mini")

        #s_prompt, u_prompt = prompt_builder.build_prompt_commercial(curr_rpt.rv_cum, curr_rpt.accomplishments, curr_rpt.context, curr_rpt.rank, curr_rpt.name)
        s_prompt, u_prompt = prompt_builder.build_foundation_prompt(example_data, curr_rpt)

        request = llm_base.LLMRequest(
            system_prompt=s_prompt,
            user_prompt=u_prompt,
            max_tokens=constants.FOUNDATION_MAX_TOKENS,
            temperature=constants.FOUNDATION_TEMP,  # increase to improve creativity, 0.2 was base
        )

        response = llm.generate(request)

        return response.text, response.model

    except Exception as e:
        return f"API Error: {str(e)}", "Error"


####################################################################################
#######################  Printing / Cosmetics  #####################################
####################################################################################

def print_profile(rpt_db, original_profile, active_profile):
    """Generates a text summary of the session for export."""
    lines = []
    lines.append("====================================")
    lines.append("Session Summary")
    lines.append("====================================")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append(f"Profile Info:")
    lines.append("--------------------------------------------------")
    lines.append(f"{original_profile}")
    lines.append(f"{active_profile}")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append(f"Reports Completed:")
    lines.append("--------------------------------------------------")
    lines.append(f"{rpt_db}")

    return "\n".join(lines)
