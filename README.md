# USMC FitRep Calculator & Section I Generator

**An offline-capable decision support tool for USMC Reporting Seniors.**

![Status](https://img.shields.io/badge/Status-Prototype-blueviolet) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.39%2B-FF4B4B)

## Overview

The **FitRep Calculator** is a desktop-grade application designed to assist USMC Reporting Seniors (RS) in preparing Fitness Reports. It addresses two critical needs:

1.  **Relative Value (RV) Forecasting:** Allows an RS to see *exactly* how a specific set of attribute marks will impact a report's Relative Value (RV) and Cumulative RV *before* submitting the report.
2.  **Section I Narrative Generation:** Leverages Large Language Models (LLMs) to assist Reporting Seniors in drafting Section I comments that align in tone and language with the relative value of the report(s). It supports three tiers of AI inference:
    * **Local (Offline):** Runs entirely on your CPU via Ollama (Mistral/Llama). *Not available in the web app currently.*
    * **Foundation (Cloud):** Uses OpenAI (GPT-4o-mini) for maximum reasoning capability.
    * **Open Weights (Hybrid):** Connects to Hugging Face Inference endpoints (Qwen/Mixtral) for flexible experimentation.

⚠️  **Note:**  The Section I LLM integration is experimental.  The local (offline) mode is as safe to use as the computer you use it on.  **DO NOT** use the Foundation or Open Weight options with unauthorized data, though.  Those options are intended for experimentation with synthetic data only right now.

⚠️ **Disclaimer:** This is an unofficial decision-support tool and is not endorsed by the USMC or DoW. All outputs are advisory only and must be reviewed by the Reporting Senior prior to use.

---
## Deployment & Access

### Option 1: Live Web Application
The latest stable version is hosted on Streamlit Cloud and is accessible at:
**[🔗 Launch FitRep Calculator](https://fitrep-calculator.streamlit.app/)**

### Option 2: Deploy Your Own Private Instance
If you prefer to host this strictly for your own unit or within a private infrastructure:

1.  **Fork** this repository to your own GitHub account.
2.  Log in to [Streamlit Cloud](https://streamlit.io/cloud).
3.  Click **"New App"** and select your forked repository.
4.  Set the **Main File Path** to `src/ui/gui_main.py`.
5.  **Secrets:** If using OpenAI, go to App Settings > Secrets and add:
    ```toml
    OPENAI_API_KEY = "sk-..."
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
    git clone [https://github.com/yourusername/fitrep_calculator.git](https://github.com/yourusername/fitrep_calculator.git)
    cd fitrep_calculator
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment (Optional)**
    If you plan to use OpenAI or HuggingFace models, create a `.env` file or set environment variables:
    ```bash
    export OPENAI_API_KEY="sk-..."
    export HF_API_TOKEN="hf_..."
    ```

---

## Usage

**Note:** Always run commands from the project root folder (fitrep_calculator/).

### 1. The GUI (Streamlit)
The primary interface is a responsive web app that runs locally in your browser.

```bash
# Run from the project root
streamlit run src/ui/gui_main.py
```

**Workflow:**

1.  **Profile Page:** Initialize your RS Profile (Rank, High, Low, Average, Total Reports).
2.  **Reports Page:** Add Marines. Toggle attribute buttons (A-G) to see real-time impact on RV.
3.  **Narratives Page:** Enter accomplishments and context. *Choose your model to draft text*.


### 2. The CLI (Command Line)
A lightweight, text-based interface for quick calculations without the browser.

```bash
python src/ui/cli.py
```

### 3. Running the Local Model (Ollama)

To use the "Local" model option without sending data to the cloud:

1.  **Install Ollama**: Download from [ollama.com](https://ollama.com).
2.  **Pull the Model**: Run `ollama pull mistral:7b-instruct-v0.3-q4_K_M` in your terminal.
3.  **Configure the Path**:
    * Open `src/app/constants.py`.
    * Find `OLLAMA_PATH`.
    * Update it to point to your `ollama.exe` location (e.g., `C:\Users\YourName\...\ollama.exe`).
    * *Note: On Mac/Linux, you can usually set this to just "ollama".*


---
## Architecture

The application follows a **Model-View-Controller (MVC)** pattern adapted for Streamlit:



[Diagram Pending]


* **`src/app/models.py`**: Contains the `RankProfile`, `ReportDB`, and `Report` object classes.
* **`src/app/calc_eng.py`**: The **"Controller."** Handles complex calculations, simulations, and routing LLM requests.
* **`src/ui/`**: The **"View."** Split into modular pages (`gui_profile`, `gui_reports`, `gui_narratives`) to manage Streamlit's session state effectively.
* **`src/app/llm_clients.py`**: A polymorphic interface for AI. 

No external database, authentication service, or persistent backend is used in the current architecture.

---


## Testing
The project includes a basic test suite.  To run the tests, use the following command from the root folder.  The `conftest.py` file in the root directory is empty, but is an easy work-around that allows the tests to access the `/src` folder.  Tests are currently focused on calculation logic and data integrity.
```bash
pytest
```


---


## Data Privacy & OPSEC

* **Local Mode:** Using local mode keeps all data private.  Nothing will leave your computer.   7-8b parameter models can run on a CPU.
* **Cloud Mode:** When "Foundation" or "Open Weight" is selected, data is sent to OpenAI or HuggingFace APIs, respectively.  Specifically, the prompts are built from user inputted narrative data and publicly available synthetic example language.
* **Persistence:** This app currently uses in-memory session state. No external database server is used or required.  All data is lost on browser close/refresh.


---

## Contributing

Contributions are welcome, but please coordinate with me before opening any pull requests.  Open an Issue for bug reports.

**Current Roadmap:**
- [ ] Improve prompt_builder / improve LLM outputs.
- [ ] Improve test suite.
- [ ] Obtain DoW GenAI and/or CamoGPT API keys for official integration and adoption.


---


## License

MIT License - See the LICENSE file for details.
