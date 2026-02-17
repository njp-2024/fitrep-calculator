# App Usability Feedback Study Plan

## Overview

This study evaluates the fitrep calculator app's usefulness to Marine Officers
who write fitness reports. Unlike the model benchmark (Parts A/B), which
isolates raw LLM capability on narrative generation, this study tests the
**end-to-end workflow** -- profile setup, attribute scoring, narrative
generation, and editing -- from the perspective of first-time users working
independently.

This is a rapid, exploratory usability screening. It is not a controlled
experiment or publication-grade study.

---

## Study Design

### Participants

- **Target**: 10+ Marine Officers who serve as Reporting Seniors
- **Experience**: First-time users of the app (no prior exposure)
- **Setting**: Asynchronous, independent work (not live observed)
- **Support**: Video walkthrough and written instructions provided

### Case Assignment

Each participant completes **3 synthetic cases** representing billets a Company
Commander (Captain) would realistically write fitreps for:

| Case | Rank / Billet | Target Tier |
|------|--------------|-------------|
| 1 | SSgt / Platoon Sergeant | Provided in case packet |
| 2 | Sgt / Combat Instructor | Provided in case packet |
| 3 | 2dLt / Platoon Commander (Rifle Platoon) | Provided in case packet |

**Key design decisions:**

- **3 cases** keeps total time to approximately 45-60 minutes (profile setup +
  3 full cycles + survey)
- All billets are **realistic for a single RS** (Infantry Company Commander)
- All participants receive the **same 3 cases** for consistency across
  respondents
- Attribute scores are **not provided** -- participants score the report
  attributes themselves as part of the app workflow. The case packet provides
  only enough information to understand the target tier.
- Cases are authored as new synthetic data specific to this study

Each case provides:
- Rank and name
- Billet title
- 5-7 accomplishment bullets
- Target performance tier

### Materials Provided to Participants

1. Written instructions and video walkthrough link
2. Case packet (3 cases with rank, name, billet, accomplishments, target tier)
3. RS profile data (rank, profile high/low/avg, total reports)
4. App URL
5. Survey link (Google Forms)

---

## Procedure

### Participant Steps

1. Watch walkthrough video / read instructions
2. Enter profile data (provided in case packet)
3. For each of the 3 cases:
   a. Enter report data and score the attributes in the app (aiming for the
      target tier)
   b. Enter narrative inputs (billet, accomplishments from case packet)
   c. Generate a narrative using the app
   d. Review and edit the result as desired
4. Complete the feedback survey (one survey after all 3 cases)

### Timing Estimate

| Activity | Estimated Time |
|----------|---------------|
| Walkthrough video / instructions | 5-10 min |
| Profile setup | 5 min |
| Case 1 (first use, learning curve) | 10-15 min |
| Case 2 | 8-10 min |
| Case 3 | 8-10 min |
| Survey | 5-10 min |
| **Total** | **~45-60 min** |

---

## Survey Design

A single survey is completed after all 3 cases. The survey covers four areas:

### Section 1: Narrative Quality (Q1-Q3)

Evaluates how useful the generated narratives are as drafts.

- **Q1 - Draft Usefulness**: 1-5 scale rating of overall narrative usefulness
- **Q2 - Edit Effort**: Single choice on how much editing was needed (complete
  rewrite through usable as-is)
- **Q3 - Tier Accuracy**: 1-5 scale rating of how well narratives matched the
  intended performance tier

### Section 2: App Usefulness (Q4-Q7)

Evaluates whether the tool improves on existing fitrep writing processes.

- **Q4 - Overall Usefulness**: 1-5 scale rating of tool usefulness
- **Q5 - Versus Current Process**: Single choice comparison to current approach
  (much worse through much better)
- **Q6 - Time Comparison**: Single choice comparison of speed (much slower
  through much faster)
- **Q7 - Likelihood to Use**: 1-5 scale rating of adoption likelihood

### Section 3: Ease of Use (Q8-Q10)

Evaluates the learning curve and feature value.

- **Q8 - Ease of Use**: 1-5 scale rating
- **Q9 - Learning Curve**: Single choice on how quickly participants felt
  comfortable
- **Q10 - Most Valuable Feature**: Single choice identifying the most valuable
  app feature

### Section 4: Open-Ended (Q11-Q13)

Captures qualitative feedback.

- **Q11 - What's Missing**: Free text on desired features or improvements
- **Q12 - Biggest Concern**: Free text on concerns about AI-drafted narratives
- **Q13 - Final Comments**: Free text for any additional feedback

See `usability_survey_questions.md` for the complete question text formatted for
Google Forms implementation.

---

## Data Collected

| Data Point | Source |
|------------|--------|
| Narrative quality perceptions | Survey Q1-Q3 |
| App usefulness vs. current process | Survey Q4-Q7 |
| Ease of use and learning curve | Survey Q8-Q10 |
| Feature requests and concerns | Survey Q11-Q13 |

**Note:** This study does not collect app telemetry, timing data, or generated
narrative text from participants. All assessment is self-reported via the survey.

---

## Analysis Approach

Given the exploratory nature and small sample size (10+ participants):

- **Quantitative**: Descriptive statistics (median, distribution) for scale and
  choice questions. No inferential statistics planned.
- **Qualitative**: Thematic grouping of open-ended responses to identify common
  feedback patterns.
- **Key metrics**:
  - Median draft usefulness rating (Q1)
  - Distribution of edit effort (Q2)
  - Median overall usefulness and likelihood to adopt (Q4, Q7)
  - Comparison to current process (Q5)
  - Common feature requests and concerns (Q11, Q12)

---

## Limitations

- Self-selected participants; may skew toward tech-comfortable officers
- Synthetic cases may not capture the full complexity of real fitrep writing
- Single session; does not measure long-term adoption or repeated use
- No control group (no comparison to writing without the tool in same session)
- Small sample size limits generalizability

---

## Notes

- All data used is synthetic. No real personnel or accomplishments are used.
- This study is for internal decision support only.
- Results will inform app development priorities and deployment decisions.
