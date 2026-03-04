# 🏔️ Paralympic Athlete Reporter Agent

An AI-powered multi-agent research system designed to generate verified, 
structured reports about Paralympic winter sport athletes (Biathlon and 
Cross-Country Skiing).

This project orchestrates a research workflow using CrewAI agents and OpenAI 
models deployed through Azure AI Foundry, producing:

- ✅ A fact-checked English article
- ✅ A validated Spanish translation
- ✅ A structured JSON summary (Pydantic schema compliant)
- ✅ Excel and Markdown summary tables

The system focuses on strict factual validation, source traceability, trying 
to minimize the hallucination impact.

<details><summary>Click here to read about project motivation</summary>

Recently, as an athlete with the Spanish Biathlon and Cross-Country Ski Federation, 
I was selected to serve as a commentator for [RTVE](https://www.rtve.es/) during 
the [Milano Cortina 2026 Paralympic Winter Games](https://www.olympics.com/en/milano-cortina-2026/paralympic-games), 
covering parabiathlon and para cross-country skiing.

As part of my preparation for this role, I began gathering information about the athletes 
competing in the Games. However, given the large number of participants, I decided to 
develop a multi-agent system to assist me by providing detailed insights on each athlete.

To achieve this, I compiled the current standings of the Paralympic World Cup across 
all categories, structured the data into a JSON file, and used this functionality to 
generate a collection of Markdown files containing summaries and reports for each athlete.

I am aware that, even though this multi-agent system retrieves information from the 
internet, its outputs may still contain inaccuracies or hallucinations, so the results 
should be interpreted with appropriate caution. Additionally, this project was developed 
and deployed within just a few hours, so there is significant room for improvement and 
further refinement.

</details>

# 🚀 Architecture Overview

The pipeline is built using:

- Multi-agent orchestration with CrewAI
- Azure OpenAI models via AI Foundry
- Website scraping & DuckDuckGo search
- Structured data validation with Pydantic
- Automated article generation + fact-checking
- Structured JSON export
- Excel & Markdown table generation

# 🤖 Agents Workflow

The system uses multiple agents with different purposes, in order to gather the
most reliable information possible

1. Research Agent
   - Scrapes official sport websites:
     - Biathlon → https://biathlonresults.com/
     - Cross-country → https://www.fis-ski.com/
   - Searches external sources using DuckDuckGo
   - Extracts structured verified data
2. Writer Agent
   - Produces a structured analytical article
   - Uses only verified research content
3. Reviewer Agent
   - Performs strict fact validation
   - Removes unsupported claims
   - Ensures full traceability
4. Translation Agent
   - Translates the validated article to Spanish
   - Preserves structure and sources
5. JSON Structuring Task
   - Converts the Spanish article into a structured JSON
   - Validated against the `AthleteSummary` Pydantic schema

# 📦 Installation & Setup
## 1️⃣ Clone the Repository
```bash
git clone <your-repository-url>
cd <your-project-folder>
```
## 2️⃣ Create a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```
## 3️⃣ Install Requirements
```bash
pip install -r requirements.txt
```

# 🔐 Environment Configuration (.env)

Create a .env file in the project root:

```
AZURE_OPENAI_API_KEY=your-token
OPENAI_API_KEY=your-token
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
AZURE_OPENAI_API_VERSION=yyyy-mm-dd
```

Where

| Variable                       | Description                     |
| ------------------------------ | ------------------------------- |
| `AZURE_OPENAI_API_KEY`         | API Key from Azure AI Foundry   |
| `AZURE_OPENAI_ENDPOINT`        | Your Azure OpenAI endpoint      |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Deployment name of your model   |
| `AZURE_OPENAI_API_VERSION`     | API version configured in Azure |
| `OPENAI_API_KEY`               | Optional fallback key           |


# 🧠 Models

This project uses OpenAI models deployed through Azure AI Foundry using:

```python
from langchain_openai import AzureChatOpenAI

Example initialization:

azure_llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    model="gpt-4o-mini",
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0,
    streaming=True,
    timeout=600
)
```

However, you can replace this model with any model compatible with CrewAI.


# 🏃 How to Run the Research
## Basic Example

Using the main method `run_research`, you will be able to do the research, just providing
the name of the athlete, the country in ISO code, and, optionally, world cup stats and its
category. For example:

```
spanish_article, json_summary = run_research(
    athlete_name="John Doe",
    sport="biathlon",  # or "cross_country"
    llm=azure_llm,
    world_cup_rank=5,
    country="GER",
    world_cup_points=350,
    category="standing",
    gender="male",
    output_dir="results/articles"
)
```

For each athlete, the system generates the report in English and Spanish language, and
the summarized information, following the pydantic `AthleteSummary` json schema stated 
in [athlete_model.py](athlete_model.py).

```
output/
 ├── AthleteName_sport_category_EN.md
 ├── AthleteName_sport_category_ES.md
 ├── AthleteName_sport_category_summary.json
```

Additionally, you can use the methods in `utils` to dump the information of the summary
jsons into tables by using `athletes_summary_to_excel_table` and `athletes_summary_to_markdown_table`
methods.
