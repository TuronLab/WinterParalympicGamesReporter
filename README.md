# 🏔️ Paralympic Athlete Reporter Agent

An AI-powered multi-agent research system designed to generate verified, 
structured reports about Paralympic winter sport athletes.

The system was originally developed for Biathlon and Cross-Country Skiing. However, 
it can be readily adapted to other sports by updating the [get_primary_website method](./utils.py). 
To do so, simply specify the sport’s name and provide the official website where the 
agent should begin retrieving athlete information—typically the relevant international 
federation’s webpage.

Built using CrewAI agents and OpenAI models via the OpenAI API, the project 
orchestrates a structured research workflow that produces:

- ✅ A fact-checked English article
- ✅ A validated Spanish translation
- ✅ A structured JSON summary (Pydantic schema compliant)
- ✅ Excel and Markdown summary tables

The system focuses on strict factual validation, source traceability, trying 
to minimize the hallucination impact, and producing an output as can be seen 
in the [athlete report navigation example panel](./results/gpt-4o-mini/tables/athlete_navigation_tables.md).

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

While the system can retrieve information from the internet, its outputs may still contain 
inaccuracies or hallucinations. The results should be interpreted with caution, and manual 
verification is recommended—made easier by the inclusion of references in each report. 
This project was developed and deployed in just a few hours, leaving room for future 
improvements and refinements.

</details>

# 🚀 Architecture Overview

The pipeline is built using:

- Multi-agent orchestration with CrewAI
- OpenAI models
- Website scraping & DuckDuckGo search
- Structured data validation with Pydantic
- Automated article generation + fact-checking
- JSON export of structured schematic article summaries
- Excel and Markdown table generation from the schematicarticle summary JSON

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


# 🧠 Models

This project uses OpenAI models, but you can configure any model compatible with CrewAI (`openai`, `anthropic`, 
`claude`, `azure`, etc). 

To employ the system as it is right now, with the OpenAI token, you will have to set the openai key by setting 
the environment variable `OPENAI_API_KEY`, or setting it manually. For example:

```python
from crewai import LLM

# Example initialization:

llm = LLM(
    model=f"openai/gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)
```


# 🏃 How to Run the Research
## Basic Example

Using the main method `run_research`, you will be able to do the research, just providing
the name of the athlete, the country in ISO code, and, optionally, world cup stats and its
category. For example:

```
spanish_article, json_summary = run_research(
    athlete_name="John Doe",
    sport="biathlon",  # or "cross_country"
    llm=llm,
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

## Multiple Athletes Example

For my personal use case, I deployed the [research_top_athletes.py](research_top_k_athletes.py) script, 
which automatically gathers reports for all athletes registered in the World Cup. It preserves the 
metadata I manually extracted from official sources.

All collected data is stored in the [athletes](athletes) folder in JSON format, organized by sport, category, and gender.

The script not only compiles all the reports but also generates a Markdown file that makes it easy to navigate the 
summaries and individual athlete reports, as the shown in 
[athlete report navigation example panel](./results/gpt-4o-mini/tables/athlete_navigation_tables.md).
