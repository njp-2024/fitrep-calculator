# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-04

### Added
- Initial prototype release
- RV calculation and forecasting
- Section I narrative generation (Foundation/Local/OpenWeight models)
- Profile, Reports, and Narratives pages
- Streamlit Cloud deployment

---
## [0.2.0] - 2026-02-04

### Changed
- Replaced the model selection radio button with a dropdown menu
- Updated OpenAI Client from chat completions API to responses API

### Added
- Support for additional OpenAI models (gpt-4.1 and gpt-5 families)

---
## [0.2.1] - 2026-02-05

### Added
- Prototype banner w/ 'Not an official DoW app' message

---
## [0.2.2] - 2026-02-13

### Fixed
- Fixed an issue where export/print session summary incorrectly displayed report scores

---
## [0.2.3] - 2026-02-13

### Fixed
- Corrected section I character limit from 1250 to 1056 in UI and prompt builder, added SECT_I_CHAR_LIMIT to constants.

---
## [0.3.0] - 2026-02-13

### Added
- Billet input field to narrative workflow
- Billet context integrated into LLM prompt generation

### Updated
- Validation logic to require Billet field
- Tests updated to support Billet attribute