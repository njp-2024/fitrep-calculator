# FitRep Calculator & Section I Generator

**An offline-capable decision support tool for USMC Reporting Seniors.**

![Version](https://img.shields.io/badge/Version-0.2.0-green) ![Status](https://img.shields.io/badge/Status-Prototype-blueviolet) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B)

## Overview

The **FitRep Calculator** is a designed to assist USMC Reporting Seniors (RS) in preparing Fitness Reports. It addresses two critical needs:

1.  **Relative Value (RV) Forecasting:** Allows an RS to see how a specific set of attribute marks will impact a report's Relative Value (RV) and Cumulative RV *before* submitting the report.
2.  **Section I Narrative Generation:** Leverages Large Language Models (LLMs) to assist Reporting Seniors in drafting Section I comments that align in tone and language with the relative value of the report(s). It supports three tiers of AI inference:
    * **Local (Offline):** Runs entirely on your CPU via Ollama (Mistral/Llama). *Requires local deployment* - controlled by `ENABLE_LOCAL_OPTION` environment variable.
    * **Foundation (Cloud):** Uses OpenAI models for maximum reasoning capability. Available in both web app and local deployment.
    * **Open Weights (Hybrid):** Connects to Hugging Face Inference endpoints (Qwen) for flexible experimentation. *Requires local deployment* - controlled by `ENABLE_OPEN_WEIGHT_OPTION` environment variable.
    * The application also prints the prompts for users to copy if they choose to use other LLM services.

⚠️  **Note:**  The Section I LLM integration is experimental. The local (offline) mode keeps all data on your machine. When using Foundation or Open Weight options, narrative data is transmitted to third-party API providers (OpenAI/HuggingFace). Per API policies, this data is not used for model training. Use placeholder names and avoid entering Controlled Unclassified Information (CUI).

⚠️ **Disclaimer:** This is an unofficial decision-support tool and is not endorsed by the USMC or DoW. All outputs are advisory only and must be reviewed by the Reporting Senior prior to use.

---
## Deployment & Access

### Option 1: Live Web Application (Streamlit Cloud)
The latest stable version is hosted on Streamlit Cloud:
**[🔗 Launch FitRep Calculator](https://fitrep-calculator.streamlit.app/)**

**Available Features:**
- ✅ RV Calculation & Forecasting
- ✅ Foundation AI Models (OpenAI)

**Limitations:**
- ❌ Local (Ollama) model disabled - requires local infrastructure
- ❌ OpenWeight (HuggingFace) model disabled - requires local infrastructure

### Option 2: Local Deployment (Full Feature Set)
For access to all AI model options, deploy locally:

**Benefits:**
- ✅ Full feature set including Local (Ollama) and OpenWeight (HuggingFace) models
- ✅ Customizable configuration via environment variables

**See Installation section below for setup instructions.**

### Option 3: Deploy Your Own Private Cloud Instance
If you prefer to host this strictly for your own unit within Streamlit Cloud:

1.  **Fork** this repository to your own GitHub account.
2.  Log in to [Streamlit Cloud](https://streamlit.io/cloud).
3.  Click **"New App"** and select your forked repository.
4.  Set the **Main File Path** to `src/ui/gui_main.py`.
5.  **Secrets:** Go to App Settings > Secrets and add:
    ```toml
    OPENAI_API_KEY = "sk-..."
    # Optional: Enable experimental features (not recommended in cloud)
    # ENABLE_LOCAL_OPTION = "false"  
    # ENABLE_OPEN_WEIGHT_OPTION = "false"
    ```
6.  Click **Deploy**.


---

## Installation

### Prerequisites
* **Python 3.10+**
* **[Ollama](https://ollama.com/)** (Optional, required only for offline AI features)
    * *Model used in development:* `mistral:7b-instruct-v0.3-q4_K_M`

### Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/njp-2024/fitrep-calculator.git
    cd fitrep-calculator
    ```

2.  **Create and Activate Virtual Environment**

    **Why?** A virtual environment isolates project dependencies and makes command-line tools like `streamlit` available.

    **Windows:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

    **Mac/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

    You'll know it's activated when you see `(venv)` in your terminal prompt.

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the project root:
    ```bash
    # Required for Foundation model (OpenAI)
    OPENAI_API_KEY=sk-...

    # Optional: Enable Local model (requires Ollama installation)
    ENABLE_LOCAL_OPTION=true

    # Optional: Enable OpenWeight model (requires HuggingFace token)
    ENABLE_OPEN_WEIGHT_OPTION=true
    HF_API_TOKEN=hf_...
    ```

    **Notes:**
    - Foundation models work with just `OPENAI_API_KEY`
    - Local model requires Ollama installation (see step 4 below) AND `ENABLE_LOCAL_OPTION=true`
    - OpenWeight model requires HuggingFace token AND `ENABLE_OPEN_WEIGHT_OPTION=true`
    - If these variables are not set, those options will not appear in the UI

    
### Running the Local Model (Ollama) - Local Deployment Only

The prospect of using local models is attractive to an expeditionary organization. This feature allows experimentation with a simple use case.

1.  **Install Ollama**: Download from [ollama.com](https://ollama.com).
2.  **Pull the Model**: Run `ollama pull mistral:7b-instruct-v0.3-q4_K_M` in your terminal.
3.  **Enable in Environment**: Set `ENABLE_LOCAL_OPTION=true` in your `.env` file.
4.  **Configure the Path** (if needed):
    * `constants.py` attempts to find Ollama automatically via `shutil.which("ollama")`
    * If auto-detection fails, open `src/app/constants.py` and set:
      ```python
      OLLAMA_PATH = r"C:\Users\YourName\AppData\Local\Programs\Ollama\ollama.exe"
      ```
    * *Note: On Mac/Linux, auto-detection usually works without manual configuration.*

---

## Usage

**Note:** Always run commands from the project root folder (fitrep_calculator/).

### 1. The GUI (Streamlit)
The primary interface is a responsive web app that runs locally in your browser.

**Important:** You must activate the virtual environment before running the app.

**Windows:**
```bash
# From the project root
venv\Scripts\activate
streamlit run src/ui/gui_main.py
```

**Mac/Linux:**
```bash
# From the project root
source venv/bin/activate
streamlit run src/ui/gui_main.py
```

The app will open automatically in your browser at `http://localhost:8501`.

**Workflow:**

1.  **Profile Page:** Initialize your RS Profile (Rank, High, Low, Average, Total Reports).
2.  **Reports Page:** Add Marines. Toggle attribute -buttons (A-H) to see real-time impact on RV.
3.  **Narratives Page:** Enter accomplishments and context. *Choose your model to draft text OR copy the prompt into your preferred browser based LLM*.


### 2. The CLI (Command Line) - **DEPRECATED**

⚠️ **The CLI has been deprecated.** Use the Streamlit GUI for the full experience.

The CLI remains in the codebase for reference but is no longer maintained. 

---
## Architecture

The application follows a **Model-View-Controller (MVC)** pattern adapted for Streamlit:

**Architecture Layers:**

* **Models** (`src/app/models.py`): Core business objects
  - `RankProfile` - RS statistics and RV calculation state
  - `ReportDB` - In-memory report storage with insertion-order preservation
  - `Report` - Individual report with scores, RV, and narrative data
  - `ExampleData` - Cached YAML configuration loader

* **Controller** (`src/app/calc_eng.py`): Business logic orchestration
  - RV calculation engine with precision error handling
  - LLM request routing and prompt building
  - Profile state management (original/active/display)

* **View** (`src/ui/`): Streamlit page modules
  - `gui_main.py` - Application router and initialization
  - `gui_profile.py` - Profile data entry and validation
  - `gui_reports.py` - Report entry with real-time RV preview
  - `gui_narratives.py` - LLM-powered narrative generation
  - `gui_sidebar.py` - Context-aware status display

* **LLM Integration** (`src/app/llm_*.py`): Polymorphic AI interface
  - `llm_base.py` - Abstract base class and data structures
  - `llm_clients.py` - Concrete implementations (OpenAI, HuggingFace, Ollama)
  - `prompt_builder.py` - RV-tiered prompt generation

**Data Flow:**
- Session-based state management (no persistence)
- Shadow state for "what-if" calculations
- Deep copy strategy prevents state mutations

---

## Data Privacy & Security

**Session-Based Storage:**
- All data stored in temporary session memory only (Streamlit session state)
- No database, no file persistence, no user accounts
- Data automatically erased on browser close/refresh

**Local vs Cloud Models:**
- **Local Mode (Ollama):**
  - All data remains on your machine
  - Zero external transmission
- **Foundation/OpenWeight Modes:**
  - Accomplishments and context sent to API providers (OpenAI/HuggingFace)
  - Transmitted via encrypted HTTPS
  - Per OpenAI API policy: data not used for model training
  - Per HuggingFace policy: similar data protection guarantees

**Web Application Security:**
- Hosted on Streamlit Community Cloud
- No persistent backend or database
- Each user session isolated in separate container
- See [Streamlit Security Policy](https://streamlit.io/security) for infrastructure details

---


## Testing
The project includes a basic test suite.  To run the tests, use the following command from the root folder.  The `conftest.py` file in the root directory is empty, but is an easy work-around that allows the tests to access the `/src` folder.  Tests are currently focused on calculation logic and data integrity.
```bash
pytest
```

---

## Contributing

Please contact me if you are interested in the tool. Open an Issue for bug reports.

**Current Roadmap:**
- [ ] Get user feedback, improve experience
- [ ] Improve prompt_builder / LLM outputs.
- [ ] Improve test suite.

---

## License

MIT License - See the LICENSE file for details.
