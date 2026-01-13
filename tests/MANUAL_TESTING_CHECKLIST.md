# Manual Testing Checklist

**Purpose:** Quick pre-deployment verification of UI functionality and calculation accuracy

**Time Required:** ~5 minutes

**When to Use:** Before every deployment or after any UI/calculation changes

---

## Quick Verification Workflow

### Before Every Deployment:

1. **Run Automated Tests** (30 seconds)
   ```bash
   # From project root
   pytest -v

   # Expected output: ✓ 30+ tests passed
   ```

2. **Manual UI Checklist** (5 minutes) - See sections below

3. **Smoke Test on Deployed App** (2 minutes)
   - Visit: https://fitrep-calculator.streamlit.app
   - Quick profile → report → generate flow
   - Verify no errors in browser console

---

## UI Functionality Testing

### Profile Page

- [ ] Enter valid profile data (Rank, High, Low, Avg, Reports) → Click Save
- [ ] Verify navigation to Reports page after save
- [ ] Enter invalid data (e.g., Low > High) → Verify Save button disabled
- [ ] Edit profile after saving → Verify changes persist
- [ ] Try to navigate away without saving → Verify appropriate behavior

**Test Data:**
```
Rank: Capt
High: 4.08
Low: 2.00
Avg: 3.47
Reports: 10
```

---

### Reports Page

- [ ] Enter Marine name → Verify attribute buttons enabled
- [ ] Change 2-3 attribute scores (click buttons A-H) → Verify sidebar updates in real-time
- [ ] Add report → Verify appears in sidebar list with correct color
- [ ] Edit existing report (change attributes) → Verify changes reflected immediately
- [ ] Add second report → Verify both visible with correct RVs
- [ ] Try to add report with no name → Verify Add button disabled
- [ ] Verify RV display shows range (e.g., 92.15 - 92.40)
- [ ] Click "Generate Section I" button → Verify navigation to Narratives page

**Test Marines:**
- SMITH (All C's - Middle third)
- JONES (Mix of D's and E's - Top third)
- DOE (Mix of B's and C's - Bottom third)

---

### Narratives Page

- [ ] Select report from dropdown → Verify shows correct Marine data
- [ ] Enter accomplishments (>50 chars) → Verify Save enabled
- [ ] Enter too few chars (<50) → Verify Save disabled
- [ ] Save inputs → Verify Prompt expander becomes available
- [ ] Open prompt expander → Verify correct tier/RV shown
- [ ] Verify tier label matches RV (Bottom/Middle/Top/Water Walker)
- [ ] Select Foundation model → Verify privacy warning appears
- [ ] Click Generate → Verify text appears in ~3 seconds (if API key configured)
- [ ] Edit generated text → Verify character counter updates
- [ ] Save Section I → Verify success message
- [ ] Generate again → Verify counter decrements (3 → 2 → 1)
- [ ] Generate 3 times → Verify button disables
- [ ] Click Reset Lock → Verify button re-enables
- [ ] Click Export Summary → Verify file downloads

**Test Accomplishments:**
```
Led 15-Marine logistics section through deployment readiness inspection,
achieving 98% equipment accountability. Managed $2.3M in inventory with
zero discrepancies. Mentored 3 junior NCOs, all promoted on first look.
```

---

### Sidebar

- [ ] **Profile page:** Shows "No Profile Saved" initially
- [ ] **Profile page:** Shows profile summary after save
- [ ] **Reports page:** Shows current working report RV
- [ ] **Reports page:** Lists all saved reports with color coding:
  - 🟥 Red: Bottom third (RV < 86.67)
  - 🟨 Yellow: Middle third (86.67 ≤ RV < 93.34)
  - 🟩 Green: Top third (93.34 ≤ RV < 98)
  - 🟦 Blue: Water walkers (RV ≥ 98)
- [ ] **Narratives page:** Shows selected report details

---

### Navigation

- [ ] Click "Back to Profile" → Returns to profile page
- [ ] Click "Back to Reports" → Returns to reports page
- [ ] Click "Generate Section I" → Goes to narratives page
- [ ] Verify session state persists across page navigation
- [ ] Refresh browser → Verify session resets (expected behavior)

---

## Calculation Accuracy Spot Checks

### Test Case 1: Profile Average Report

**Setup:**
- Profile: Capt, High 5.0, Low 3.0, Avg 4.0, Reports 10
- Add report: All C's (average = 3.0)

**Expected Result:**
- RV Cum: ~90.0 (at profile average)
- Verify: RV displayed in sidebar matches calculation

**Actual Result:** ___________

---

### Test Case 2: Low Performer (RV Floor)

**Setup:**
- Same profile as above
- Add report: All A's and B's (average ~1.5)

**Expected Result:**
- RV Cum: 80.0 (floor)
- Verify: Report shows 80.0 exactly

**Actual Result:** ___________

---

### Test Case 3: RV Spread Calculation

**Setup:**
- Profile: Capt, High 5.0, Low 3.0, Avg 4.12, Reports 10 (note decimal avg)
- Add any report (e.g., all C's)

**Expected Result:**
- RV Cum shows range (e.g., 92.15 - 92.40)
- Spread is < 5.0 points
- Verify: Min < Max

**Actual Result:** ___________

---

### Test Case 4: Multiple Reports Ordering

**Setup:**
- Add 3 reports in order: ALPHA, BRAVO, CHARLIE

**Expected Result:**
- Sidebar lists reports in insertion order
- Name list: ["ALPHA", "BRAVO", "CHARLIE"]

**Actual Result:** ___________

---

## Cross-Browser Testing

**When:** Before major releases only

**Browsers to Test:**
- [ ] Chrome (primary)
- [ ] Firefox
- [ ] Safari (Mac/iOS)
- [ ] Edge

**What to Check:**
- [ ] Buttons work correctly
- [ ] Text inputs accept data
- [ ] Sidebar displays correctly
- [ ] No console errors (F12 developer tools)
- [ ] Layout renders properly (no overlapping elements)

---

## LLM Integration Checks

### Foundation Model (OpenAI)

**Prerequisites:** OPENAI_API_KEY must be set

- [ ] Select Foundation option → Privacy warning appears
- [ ] Generate button enabled after saving inputs
- [ ] Click Generate → Text appears within 5 seconds
- [ ] Verify generated text length: 1150-1250 characters
- [ ] Verify tier-appropriate tone (check for "outstanding" in top third)
- [ ] Verify mandatory ending appears in output

---

### Local Model (Ollama)

**Prerequisites:**
- ENABLE_LOCAL_OPTION=true
- Ollama installed and running

- [ ] Verify Local option appears in dropdown
- [ ] Select Local → No privacy warning (local processing)
- [ ] Generate → Text appears (may take 10-30 seconds)
- [ ] Verify output is coherent English text

---

### OpenWeight Model (HuggingFace)

**Prerequisites:**
- ENABLE_OPEN_WEIGHT_OPTION=true
- HF_API_TOKEN set

- [ ] Verify OpenWeight option appears in dropdown
- [ ] Select OpenWeight → Privacy warning appears
- [ ] Generate → Text appears within 10 seconds
- [ ] Verify output matches expected format

---

## Common Issues to Watch For

### Red Flags (DO NOT DEPLOY if found):

- ❌ RV calculation returns NaN or undefined
- ❌ Adding report causes crash or infinite loop
- ❌ Profile validation allows invalid data (Low > High)
- ❌ Sidebar doesn't update after adding report
- ❌ Generate button remains enabled after 3 uses (without reset)

### Warnings (Fix if possible, acceptable for deploy):

- ⚠️ Slow LLM response (>10 seconds) - API latency issue
- ⚠️ Character counter off by 1-2 characters - minor cosmetic
- ⚠️ Privacy warning doesn't dismiss automatically - user can still see it

---

## Deployment Checklist

Use this before every Streamlit Cloud deployment:

1. ✅ All automated tests pass (`pytest -v`)
2. ✅ Profile → Reports → Narratives flow works
3. ✅ RV calculations spot-checked (Test Cases 1-3)
4. ✅ No red flags identified
5. ✅ Commit message describes changes
6. ✅ Git push triggers Streamlit Cloud rebuild
7. ✅ Smoke test on deployed URL within 2 minutes of deploy

---

## Test Data Reference

### Standard Test Profile
```
Rank: Capt
High: 4.08
Low: 2.00
Avg: 3.47
Reports: 10
```

### Test Marines

**SMITH (Middle Third):**
- Performance: C, Proficiency: C, Courage: C
- All others: C
- Expected RV: ~90

**JONES (Top Third):**
- Performance: E, Proficiency: E, Courage: E
- All others: D
- Expected RV: ~96

**DOE (Bottom Third):**
- Performance: B, Proficiency: B, Courage: B
- All others: B, C
- Expected RV: ~85

### Test Accomplishments
```
Led 15-Marine logistics section through deployment readiness inspection,
achieving 98% equipment accountability. Managed $2.3M in inventory with
zero discrepancies. Mentored 3 junior NCOs, all promoted on first look.
```

---

## Notes

- **Session Reset:** Refreshing browser clears all data (expected behavior)
- **Color Coding:** RV ranges determine report card colors in sidebar
- **RV Spread:** Due to ±0.005 precision error in Profile Avg, RV shows min-max range
- **Generation Limit:** 3 generations per report (enforced by counter)
- **Privacy:** Local model keeps data on-device; Foundation/OpenWeight send to API

---

**Last Updated:** 2026-01-13
**Test Suite Version:** 1.0
