import os
import json
import time

from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool, WebsiteSearchTool
from crewai.tools import BaseTool
from athlete_model import AthleteSummary
from langchain_openai import AzureChatOpenAI

from ddgs import DDGS

from utils import athletes_summary_to_excel_table, athletes_summary_to_markdown_table

COUNTRY_REGION_MAP = {
    "ITA": "it-it",
    "UKR": "uk-ua",
    "USA": "en-us",
    "GBR": "en-gb",
    "CHN": "zh-cn",
    "FRA": "fr-fr",
    "MGL": "mn-mn",
    "CZE": "cs-cz",
    "KAZ": "ru-kz",
    "RUS": "ru-ru",
    "BRA": "pt-br",
    "BLR": "ru-by",
    "JPN": "ja-jp",
    "GEO": "ka-ge",
    "ESA": "es-sv",
    "AUS": "en-au",
    "CAN": "en-ca",
    "GER": "de-de",
    "KOR": "ko-kr",
    "NOR": "no-no",
    "FIN": "fi-fi",
    "POL": "pl-pl",
    "SUI": "de-ch",
    "SWE": "sv-se",
    "SVK": "sk-sk",
    "ARG": "es-ar",
    "AUT": "de-at",
    "ESP": "es-es",
    "WORLD": "wt-wt",
}

class DuckDuckGoTool(BaseTool):
    name: str = "DuckDuckGo Search"
    description: str = "Search the web using DuckDuckGo with safe filtering"

    def _run(self, query: str):
        try:
            with DDGS() as ddgs:
                results = list(
                    ddgs.text(
                        query,
                        region=COUNTRY_REGION_MAP.get(os.getenv("COUNTRY_SEARCH", "WORLD")),
                        safesearch="strict",
                        max_results=10
                    )
                )
            return results
        except Exception as e:
            print("DuckDuckGoTool failed:", e)
            raise  # re-raise so you see the full traceback

def get_athlete_filename(athlete_name: str, sport: str, category: str):
    return f"{athlete_name.replace(' ', '_')}_{sport}_{category}"

# ==========================================================
# MAIN FUNCTION
# ==========================================================

def run_research(
    athlete_name: str,
    sport: str,
    rank: int = -1,
    country: str = "",
    points: int = -1,
    category: str = "",
    gender: str = "",
    model: str = "gpt-4o-mini",
    output_dir: str = "output"
):

    load_dotenv()

    if country is not None:
        os.environ["COUNTRY_SEARCH"] = country

    azure_llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        model=model,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0,
        streaming=True,
        timeout=600
    )

    os.makedirs(output_dir, exist_ok=True)

    if sport not in ["biathlon", "cross_country"]:
        raise ValueError("Sport must be either 'biathlon' or 'cross_country'")

    # ==========================================================
    # PRIMARY SOURCE
    # ==========================================================

    primary_site = (
        "https://biathlonresults.com/"
        if sport == "biathlon"
        else "https://www.fis-ski.com/"
    )

    # ==========================================================
    # TOOLS
    # ==========================================================

    scrape_tool = ScrapeWebsiteTool()
    website_search_tool = WebsiteSearchTool()
    duckduckgo_tool = DuckDuckGoTool()
    tools = [scrape_tool, website_search_tool, duckduckgo_tool]

    # ==========================================================
    # AGENTS
    # ==========================================================

    research_agent = Agent(
        role="Paralympic Sports Research Specialist",
        goal=f"Gather verified and structured information about {athlete_name}, specifically for {sport}.",
        backstory=(
            "You are an elite sports data researcher specialized in Paralympic winter sports. "
            "You must first search the official sport-specific results website. "
            "Then, you should search additional sources including news articles, interviews, national federations, and IPC profiles using DuckDuckGo. "
            "Always verify that the information you collect corresponds exactly to the athlete in question, "
            "checking sport, country, and category to avoid confusion with athletes of similar names. "
            "All key facts must be traceable to sources. "
            "If information cannot be confirmed, explicitly write: 'Information not publicly available'. "
            "You must NOT invent data or assume anything."
        ),
        tools=tools,
        verbose=True,
        llm=azure_llm,
        allow_delegation=False
    )

    writer_agent = Agent(
        role="Professional Paralympic Sports Journalist",
        goal=f"Write a structured, analytical, fact-based article about the paralympic athlete {athlete_name}.",
        backstory=(
            "You are a senior sports journalist specialized in Paralympic winter sports. "
            "You must use only verified information from the research report. "
            "Cite sources clearly in a 'Sources' section. "
            "Do NOT speculate, infer, or add information not present in the report."
        ),
        verbose=True,
        llm=azure_llm,
        allow_delegation=False
    )

    reviewer_agent = Agent(
        role="Independent Fact-Checking Editor",
        goal=f"Perform strict fact-validation of the article about the paralympic {athlete_name}.",
        backstory=(
            "You are a skeptical fact-checker. "
            "The research report is the only source of truth. "
            "You must review the article sentence by sentence, deleting any statement that does not appear explicitly in the report. "
            "No external knowledge or inference is allowed. "
            "Remove implied conclusions, assumptions, or generalizations. "
            "Ensure logical coherence and source traceability."
        ),
        verbose=True,
        llm=azure_llm,
        allow_delegation=False
    )

    translation_agent = Agent(
        role="Professional Sports Translator",
        goal="Translate the validated article into Spanish faithfully.",
        backstory=(
            "You are a professional bilingual sports translator specialized in Paralympic reporting. "
            "Translate literally, preserving structure, headings, and sources. "
            "Do NOT summarize, reinterpret, add, or remove information. "
            "Maintain exact factual content and wording as much as possible."
        ),
        verbose=True,
        llm=azure_llm,
        allow_delegation=False
    )

    # ==========================================================
    # TASKS
    # ==========================================================

    research_task = Task(
        description=f"""
STEP 1: Scrape and analyze the official sport-specific website: {primary_site}

STEP 2: Use DuckDuckGo to find additional sources (news, interviews, national federation pages, IPC profiles) 
ensuring that each result corresponds to the athlete in {sport}, checking country and category to avoid confusion.

STEP 3: Look for other relevant participation of the athlete in other sports than {sport}

STEP 4: Extract structured data:
- Positions in {sport}
- Performance trends in {sport}
- Major achievements in {sport}
- Category in {sport} (LW10, LW10.5, B1, B2, etc.) 
- Titles won
- Participation in other sports than {sport}
- Achievements in other sports than {sport} (with results if available)
- Training/preparation approach
- Paralympic experience
- Guide (for vision impaired)
- Personal/contextual info

STEP 5: Document the source URL for each claim. 
If unverifiable, write "Information not publicly available".

Produce a structured research report with sources and mark unavailable data. Do not over extend yourself; 
focus in any information about the athlete
""",
        agent=research_agent,
        expected_output=f"Structured research report for the athlete in {sport}, with sources, verified identity, "
                        f"and unavailable data marked."
    )

    article_task = Task(
        description="""
Using ONLY the verified research report, write a well-structured analytical article about the athlete. Follow 
this structure:

1. **Introduction**  
   - Briefly introduce the athlete, including name, nationality, sport(s), and category/classification.  
   - Mention the context of their Paralympic and/or other sporting participation.

2. **Career Overview**  
   - Summarize the athlete’s career trajectory chronologically, including the sports where the athlete achieved the results.  
   - Include sports and categories participated in, avoiding speculation.

3. **Major Achievements**  
   - List all major achievements in bullet points.  
   - Clearly specify the sport and competition for each achievement.  
   - Include medals, titles, and records if available.

4. **Performance Trends**  
   - Present bullet points summarizing performance progression, improvements, or patterns over time.  
   - Only use factual data from the report.

5. **Paralympic Participations**  
   - List each Paralympic participation in bullet points.  
   - Specify sport, year, event, and result for each entry.

6. **Other Sports (if any)**  
   - List other sports the athlete participated in, with achievements in bullet points.  
   - Clearly cite the sport for each achievement.

7. **Preparation Style / Training Approach**  
   - Describe training methods, preparation style, and support team (e.g., guide for vision impaired), based solely 
   on the verified report.

8. **Notable Facts**  
   - Include any contextual or personal facts relevant to the athlete’s career or achievements.

9. **Sources**  
   - List all sources used in the research report for verification.  
   - For each claim, ensure the corresponding source is cited.  
   
**Strict Rules:**  
- Only use factual content from the verified research report.  
- Do NOT speculate, infer, or include unverified information.  
- Clearly cite sources for every claim.  
- Specify the sport for each achievement or participation.  
- Use bullet points where indicated for clarity and readability.  
- Maintain a professional, analytical tone suitable for an informative sports article.
""",
        agent=writer_agent,
        expected_output="Complete fact-based article with sources."
    )

    review_task = Task(
        description=f"""
STRICT FACT VALIDATION:

- Check EVERY factual claim in the article about {athlete_name}.
- Only retain claims explicitly supported by the verified research report.
- If a claim is not in the report, remove it or mark it as `N/A`.
- No external knowledge or assumptions allowed.
- Remove implied conclusions, generalizations, or speculative statements.
- Maintain logical coherence and paragraph structure.
- Ensure every retained claim is traceable to a documented source.

Return ONLY the cleaned, validated article with the original section structure preserved.
""",
        agent=reviewer_agent,
        expected_output="Fully validated article."
    )

    translation_task = Task(
        description="""
Translate the FULL validated article into Spanish.

Strict rules:
- Preserve structure, headings, and Sources section.
- Do NOT summarize, reinterpret, add, or remove content.
- Translate literally and faithfully.
Return ONLY the translated article.
""",
        agent=translation_agent,
        expected_output="Full Spanish translation of the validated article."
    )

    json_task = Task(
        description=f"""
From the verified Spanish article, generate a JSON summary in spanish language strictly following the AthleteSummary Pydantic schema:

AthleteSummary structure:
{{
    "name_of_the_athlete": "str",
    "date_of_birth": "str",
    "gender": "str",
    "sport_under_study": "str",
    "world_cup_rank": "int",
    "country": "str",
    "world_cup_points": "int",
    "category": "str",
    "paralympic_category_lw": "str",
    "sports": [
        {{
            "sport_name": "str",
            "major_achievements": "str",
            "paralympic_participation": "str",
            "participation": "str",
            "achievements": "str",
            "guide": "str",
            "performance_trends": "str",
            "preparation_style": "str",
            "personal_contextual_info": "str"
        }}
    ],
    "personal_data": "str"
}}

Rules:
- Only use information from the verified article.
- If data is unavailable → "Information not publicly available"
- Do NOT invent or infer data
- Include each sport the athlete participates in as a separate entry in the "sports" array
- Output ONLY valid JSON compatible with the AthleteSummary Pydantic model
""",
        agent=research_agent,
        output_json=AthleteSummary,
        expected_output="Validated structured JSON output."
    )

    # ==========================================================
    # CREW
    # ==========================================================

    crew = Crew(
        agents=[research_agent, writer_agent, reviewer_agent, translation_agent],
        tasks=[research_task, article_task, review_task, translation_task, json_task],
        verbose=True
    )

    results = crew.kickoff()
    tasks_output = results.tasks_output

    # ==========================================================
    # SAVE OUTPUT
    # ==========================================================

    english_article = tasks_output[-3].raw
    spanish_article = tasks_output[-2].raw
    final_json = tasks_output[-1].json_dict

    base_filename = get_athlete_filename(athlete_name=athlete_name, sport=sport, category=category)

    english_path = os.path.join(output_dir, base_filename + "_EN.md")
    spanish_path = os.path.join(output_dir, base_filename + "_ES.md")
    json_path = os.path.join(output_dir, base_filename + "_summary.json")

    with open(english_path, "w", encoding="utf-8") as f:
        f.write(english_article)

    with open(spanish_path, "w", encoding="utf-8") as f:
        f.write(spanish_article)

    # We hardcode available information
    final_json["sport_under_study"] = sport
    final_json["gender"] = gender
    final_json["world_cup_rank"] = rank
    final_json["country"] = country
    final_json["world_cup_points"] = points
    final_json["category"] = category

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)

    print("\n✅ Files successfully generated:")
    print(english_path)
    print(spanish_path)
    print(json_path)

    return spanish_article, final_json


# ==========================================================
# EXAMPLE EXECUTION
# ==========================================================

if __name__ == "__main__":

    model = "gpt-4o-mini"
    athletes_metadata_path = r"C:\Users\pablo\OneDrive\Profesional\Proyectos\Paralympic Agent Researcher\athletes"
    output_base_path = rf".\results\{model}"

    markdown_files = {}

    for sport in ["parabiatlon", "paraski"]:
        markdown_files[sport] = {}
        for category in ["sitting", "standing", "vision"]:
            markdown_files[sport][category] = {}
            for gender  in ["male", "female"]:
                athlete_results, athlete_links = [], []
                for athlete_conf in json.load(open(os.path.join(athletes_metadata_path, f"{sport}_{category}_{gender}.json"))):

                    json_result = None
                    for i in range(5):
                        try:
                            _, json_result = run_research(
                                athlete_name=athlete_conf["name"],
                                sport="biathlon" if sport == "parabiatlon" else "cross_country",
                                rank=athlete_conf["rank"],
                                country=athlete_conf["country"],
                                points=athlete_conf["points"],
                                category=athlete_conf["class"],
                                gender=gender,
                                output_dir=os.path.join(output_base_path, "articles")
                            )
                            if json_result is not None:
                                break
                        except Exception as e:
                            print(f"Attempt {i+1} failed: {e}")
                            time.sleep(1)  # optional delay between retries

                    if json_result is None:
                        output_name = f"{sport}_{category}_{gender}_{athlete_conf['name'].replace(' ', '_')}"
                        with open(f"{output_name}_error.txt", "w", encoding="utf-8") as f:
                            f.write(f"Unable to find information about {athlete_conf['name']} in sport {sport}")

                    athlete_results.append(json_result)
                    athlete_links.append(os.path.join(rf"../articles/{get_athlete_filename(athlete_name=athlete_conf['name'], sport=sport, category=athlete_conf['class'])}_ES.md"))

            try:
                output_name = f"{sport}_{category}_{gender}"
                markdown_table = os.path.join(output_base_path, "tables", f"{output_name}.md")
                markdown_files[sport][category][gender] = markdown_table

                athletes_summary_to_excel_table(athletes=athlete_results, output_path=markdown_table.replace(".md", ".xlsx"))

                athletes_summary_to_markdown_table(
                        athletes=athlete_results,
                        links=athlete_links,
                        output_path=markdown_table
                )
            except Exception as e:
                output_name = f"{sport}_{category}_{gender}"
                print(f"Unable to dump {output_name}: {e}")
                with open(f"{output_name}_error.txt", "w", encoding="utf-8") as f:
                    f.write(f"Unable to dump {output_name} with:\n{athlete_results}\n{athlete_links}")

    with open(r".\tables\athlete_navigation_tables.md", "w", encoding="utf-8") as f:
        for sport, categories in markdown_files.items():
            f.write("# " + sport.capitalize() + "\n")
            for category, genders in categories.items():
                f.write("## " + category.capitalize() + "\n")
                for gender, file in genders.items():
                    f.write(f"[{gender}]({file})\n")