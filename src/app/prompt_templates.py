"""
This module is used to store prompt templates that were tried, with notes on their performance.
Set up as dictionaries to enable future use in testing/evaluation.  Currently, not used, though.
"""

##############################################################################################
#################################### Foundation Prompts ######################################
##############################################################################################
# Use these as generic phrases to provide extra context to the LLM in the prompt.
# Sometimes used, sometimes not used.  Overall, they seem to help.
CONTEXT_PHRASES = {
    "v1_baseline": {
        "date":     "Dec 2025",
        "notes":    "Using phrases like these seemed to help.",
        "lower_third": {
                "perf_level":       "lower performer",
                "context_phrase":   "Keep the tone and language professional and positive but without praise.",
                "combined_phrase":  "{mro_rank} {mro_name} is a low performer.  Keep the tone and language professional and positive but without praise."
            },
            "middle_third": {
                "perf_level":       "average performer",
                "context_phrase":   "Use lofty praise sparingly unless explicitly instructed otherwise.",
                "combined_phrase":  "{mro_rank} {mro_name} is an average performer. Keep the tone and language professional and positive and use lofty praise sparingly."
            },
            "top_third": {
                "perf_level":       "top performer",
                "context_phrase":   "Highlight his performance with lofty praise.",
                "combined_phrase":  "{mro_rank} {mro_name} is a top performer.  Keep the tone and language professional and positive and highlight his performance with lofty praise."
            },
            "elite": {
                "perf_level":       "exceptional performer, best of the best",
                "context_phrase":   "Use language that sets him apart and highlights his exceptional accomplishments and superior performance.",
                "combined_phrase":  "{mro_rank} {mro_name} is one of the best.  Use tone and language that sets him apart and highlights his exceptional accomplishments and superior performance."
            }
    },
    "v2_updated": {
        "date":     "Jan 2026",
        "notes":    "Updated w/ help of Gemini 3.0 pro. These were combined into a tier config function. Evaluating results",
        "lower_third": {
                "perf_level":       "low performer",
                "context_phrase":   "professional and positive but without praise.",
                "combined_phrase":  "Not used"
            },
        "middle_third": {
            "perf_level":       "average performer",
            "context_phrase":   "professional with light praise. Focus on reliability.",
            "combined_phrase":  "Not used."
        },
        "top_third": {
            "perf_level":       "top performer",
            "context_phrase":   "highly praiseworthy and strong. Highlight impact.",
            "combined_phrase":  "Not used"
        },
        "elite": {
            "perf_level":       "exceptional performer (Top 2%)",
            "context_phrase":   "distinguished, sets him apart. Use language like 'unprecedented' or 'vital'.",
            "combined_phrase":  "Not used"
        }
    }

}

##############################################################################################
#################################### Foundation Prompts ######################################
##############################################################################################
# These are designed for large foundation models, sepcifically ChatGPT 4o-mini.
FOUNDATION_PROMPTS = {
    "v1_baseline": {
        "date":     "Dec 2025",
        "notes":    ("Original attempt.  The LLM focused too much on summarizing accomplishments, rather than "
                     "highlighting traits. Still, did OK."
                     ),
        "system":   ("Write fitness report section I comments for {mro_rank} {mro_name}:\n"
                     "Use the provided CONTEXT and ACCOMPLISHMENTS. "
                     "{context_phrase} Use the same style and structure as the EXAMPLE.\n"
                     ),
        "user" :    ("Example: \n{examples[0]['section_i']}\n"
                     "Context: {user_context} \n"
                     "Accomplishments:\n{accomplishments}\n"
                     "Constraints:  The section I comments must be between 1200 and 1250 characters in length (including spaces)\n"
                     "The comments must end with this recommendation: {promotion_rec} {assignment_rec}"
                     )
    },
    "v2_negative_constraints": {
        "date" :    "Dec 2025",
        "notes" :   ("This one focused more on highlighting Marine's traits, but tended to make negative comments on "
                     "lower performers (like: 'while they do well, they could use improvement').  Also, this one is long "
                     "and complicated for a prompt."
                     ),
        "system" :  ("You are a Marine Corps fitness report writing assistant.\n\n"
                    "Your role is to write Section I comments that evaluate a Marine’s traits, "
                    "leadership, judgment, professionalism, and overall impact.\n\n"        
                    "You must NOT:\n"
                    "- summarize or restate accomplishments\n"
                    "- repeat bullet points provided as input\n"
                    "- use negative langauge or highlight negative traits\n\n"        
                    "Accomplishments are provided only as background context to infer qualities and support the narrative.\n"
                    "Your output must describe who the Marine is, not what the Marine did.\n\n"
                    "Write in professional Marine Corps fitness report language.\n"
                    "Use evaluative, qualitative phrasing.\n"
                    "Match the tone to the stated performance level without being negative.\n\n"
                     ),
        "user" :  ("Write Marine Corps Fitness Report Section I comments for {mro_rank} {mro_name}.\n\n"
                    "Performance level: {perf_level}\n\n"
                    "Use the same general style and sentence structure as the EXAMPLE, but do not copy its content or restate duties.\n"
                    "Example (style only):\n"
                    "{examples[0]}\n"
                    "Context (background only):\n"
                    "{user_context}\n"
                    "Accomplishments:\n"
                    "{accomplishments}\n\n"
                    "Output constraints:\n"
                    "- 1200–1250 characters (including spaces)\n"
                    "- No bullets\n"
                    "- Must end with: {promotion_rec} {assignment_rec}"
                   )
    },
    "v3_role_based": {
        "date" :    "Jan 2026",
        "notes":    "Developed w/ review and assistance of Gemini 3.0 pro. Ok in some situations and on bigger models.",
        "system":   (
                    "You are a Marine Corps fitness report writing assistant.\n"
                    "Your goal is to write a Section I narrative that evaluates performance, character, leadership, intellect, and impact.\n\n"
                    "CRITICAL RULES:\n"
                    "1. NO BULLET POINTS. Write a flowing narrative.\n"
                    "2. ATTRIBUTES OVER ACTIONS: Do not merely restate accomplishments. Use them to infer traits.\n"
                    "3. TONE: {tone}\n"
                    "4. LENGTH: 1200-1250 characters.\n"
                    ),
        "user":     (
                    "Write Section I comments for {rank} {name}.\n"
                    "Performance Level: {perf_level} (RV: {rv:.2f})\n\n"
                    "Style Reference (Mimic this structure):\n{example_text}\n\n"
                    "Context: {user_context}\n"
                    "Accomplishments: {accomplishments}\n\n"
                    "Mandatory Ending: {prom_rec} {assign_rec}"
                    )
    },

"v4_comprehensive": {
        "date" :    "Jan 2026",
        "notes":    "Developped using the tester app. It was getting decent results there - seems to struggle on lower tier reports",
        "system":   ("""### IDENTITY AND ROLE ###
You are a Marine Reporting Senior. Your role is to provide an accurate assessment of your subordinates' performance. In a single paragraph, you must paint a word picture of the total Marine - his performance, technical proficiency, character, leadership, and intellect - using his accomplishments as context and support.

### MANDATORY GUIDELINES ###
- Be professional, objective, and authoritative.
- Align your narrative to the Marine's performance tier.
- Describe the Marine's traits and impact during the reporting period.
- Be clear and concise.
- Use the provided EXAMPLE for tone and style.

### PROHIBITIONS ###
- You MUST NOT summarize the accomplishments.
- You MUST NOT use negative language or highlight traits that need improvement.

### CONSTRAINTS ###
- Write the narrative in 1150 - 1250 characters.
- Write in narrative form, 1 single paragraph.
- Use the provided mandatory ending sentence.
"""),
        "user":     ("""### PERFORMANCE DATA ###
Marine: {rpt.rank} {rpt.name}
Performance level: {config['label']} (Relative Value: {rpt.rv_cum:.2f})

### STYLE EXAMPLE ###
{example_text}

### ACCOMPLISHMENTS ###
{rpt.accomplishments}

### ADDITIONAL CONTEXT ###
{user_context}

### MANDATORY ENDING ###
{prom_rec} {assign_rec}
""")
    }

}


##############################################################################################
##################################### Local Prompts ##########################################
##############################################################################################
# These are designed for smaller models being run locally (7-8b parameter models).
LOCAL_PROMPTS = {
    "v1_baseline": {
        "date":     "Dec 2025",
        "notes":    "This one may be too long/complicated for a 7b parameter model.  Didn't produce very good results.",
        "prompt":   (
                    "Marine Corps Fitrep Section I comments present a word picture in 5-6 sentences describing a Marine's performance during a "
                    "reporting period. They summarizes his performance, proficiency, character, intellect, initiative, leadership "
                    "and decision making in the context of his accomplishments.  Here is an example:\n"
                    "Accomplishments: \n{examples[0]['accomplishments']}\n"
                    "Section I Comments: \n{examples[0]['section_i']}"
                    "{examples[0]['recommendation']}\n"
                    "{context_phrase} Now write section I comments for {mro_rank} {mro_name}:\n"
                    "Context: {user_context}\n"
                    "Accomplishments:\n{accomplishments}\n"
                    "Section I Comments: "
                    )
    },
    "v2_mistral_simple": {
        "date":     "Jan 2026",
        "notes":    "Developed w/ assistance from Gemini 3.0 pro. Currently under evaluation.",
        "prompt":   (
                    "Write a US Marine Corps Fitness Report narrative for {rpt.rank} {rpt.name}.\n"
                    "Level: {config['label']}\n\n"
                    "INSTRUCTIONS:\n"
                    "1. {config['tone']}\n"
                    "2. Infer traits from the accomplishments below.\n"
                    "3. Write exactly one paragraph (~1200 chars).\n\n"
                    "STYLE EXAMPLE:\n{example_text}\n\n"
                    "INPUT DATA:\n"
                    "Context: {user_context}\n"
                    "Accomplishments: {rpt.accomplishments}\n"
                    "RESPONSE:"
                    )
    }
}
