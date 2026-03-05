import os
import json
from typing import Any

from crewai import Agent, Task, Crew, BaseLLM
from crewai_tools import ScrapeWebsiteTool, WebsiteSearchTool
from pydantic import InstanceOf

from athlete_model import AthleteSummary
from crewai import LLM

from config import REPORTER_LOGGER
from utils import DuckDuckGoTool, get_output_filenames, get_primary_website


# ==========================================================
# MAIN FUNCTION
# ==========================================================

def run_research(
    athlete_name: str,
    sport: str,
    llm: str | InstanceOf[BaseLLM] | Any,
    world_cup_rank: int = -1,
    country: str = "",
    world_cup_points: int = -1,
    category: str = "",
    gender: str = "",
    output_dir: str = "output"
):

    """
    Run a multi-agent research pipeline to generate a verified article and
    structured JSON summary for a Paralympic winter sport athlete.

    The workflow:
    1. Research verified information from official and public sources.
    2. Write a structured English article.
    3. Strictly validate all factual claims.
    4. Translate the validated article into Spanish.
    5. Generate a JSON summary compliant with the AthleteSummary schema.
    6. Save all outputs to disk.

    Parameters
    ----------
    athlete_name : str
        Full name of the athlete.
    sport : str
        Must be "biathlon" or "cross_country".
    llm : str | BaseLLM | Any
        LLM identifier or instance used by the agents.
    world_cup_rank : int, optional
        Injected into the final JSON output.
    country : str, optional
        Athlete country code.
    world_cup_points : int, optional
        Injected into the final JSON output.
    category : str, optional
        Athlete classification/category.
    gender : str, optional
        Athlete gender.
    output_dir : str, optional
        Directory where output files are stored.

    Returns
    -------
    tuple[str, dict]
        Spanish validated article and structured JSON dictionary.

    Raises
    ------
    ValueError
        If sport is not supported.
    """

    if country is not None:
        os.environ["COUNTRY_SEARCH"] = country

    os.makedirs(output_dir, exist_ok=True)

    # ==========================================================
    # PRIMARY SOURCE
    # ==========================================================

    primary_site = get_primary_website(sport)

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
            "Then, you should search additional sources including news articles, interviews, national federations, "
            "and IPC profiles using DuckDuckGo. "
            "Always verify that the information you collect corresponds exactly to the athlete in question, "
            "checking sport, country, and category to avoid confusion with athletes of similar names. "
            "All key facts must be traceable to sources. "
            "If information cannot be confirmed, explicitly write: 'Information not publicly available'. "
            "You must NOT invent data or assume anything."
        ),
        tools=tools,
        verbose=True,
        llm=llm,
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
        llm=llm,
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
        llm=llm,
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
        llm=llm,
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
focus in any information about the athlete without exceeding 10k tokens.
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
    "personal_data": "str",
    "reference_urls": ["str"]
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

    english_path, spanish_path, json_path = get_output_filenames(
        athlete_name=athlete_name,
        sport=sport,
        category=category,
        output_dir=output_dir
    )

    with open(english_path, "w", encoding="utf-8-sig") as f:
        f.write(english_article)

    with open(spanish_path, "w", encoding="utf-8-sig") as f:
        f.write(spanish_article)

    # We hardcode available information
    if sport: final_json["sport_under_study"] = sport
    if gender: final_json["gender"] = gender
    if world_cup_rank != -1: final_json["world_cup_rank"] = world_cup_rank
    if country: final_json["country"] = country
    if world_cup_points != -1: final_json["world_cup_points"] = world_cup_points
    if category: final_json["category"] = category

    with open(json_path, "w", encoding="utf-8-sig") as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)

    REPORTER_LOGGER.info("-- Files successfully generated --")
    REPORTER_LOGGER.info(english_path)
    REPORTER_LOGGER.info(spanish_path)
    REPORTER_LOGGER.info(json_path)

    return spanish_article, final_json


# ==========================================================
# EXAMPLE EXECUTION
# ==========================================================

if __name__ == "__main__":

    from dotenv import load_dotenv
    load_dotenv(".env")

    model = "gpt-4o-mini"

    llm = LLM(
        model=f"openai/{model}",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    _, result = run_research(
        athlete_name="RIVERO FERNANDEZ Higinio",
        sport="biathlon",
        country="ESP",
        world_cup_rank=13,
        world_cup_points=310,
        category="Sitting",
        gender="Male",
        output_dir=os.path.join(".", "borrar_articles", model),
        llm=llm,
    )
