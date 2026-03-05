import os
import pandas as pd
from typing import List

from crewai.tools import BaseTool
from ddgs import DDGS

from config import COUNTRY_REGION_MAP, REPORTER_LOGGER


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
            REPORTER_LOGGER.error("DuckDuckGoTool failed:", e)
            raise  # re-raise so you see the full traceback

def get_primary_website(sport: str):
    if sport == "biathlon":
        return "https://biathlonresults.com/"
    elif sport == "cross_country":
        return "https://www.fis-ski.com/"
    else:
        raise Exception(f"Unknown sport {sport}")

def get_athlete_filename(athlete_name: str, sport: str, category: str):
    return f"{athlete_name.replace(' ', '_')}_{sport}_{category}"

def get_output_filenames(athlete_name: str, sport: str, category: str, output_dir: str):
    base_filename = get_athlete_filename(athlete_name=athlete_name, sport=sport, category=category)

    english_path = os.path.join(output_dir, base_filename + "_EN.md")
    spanish_path = os.path.join(output_dir, base_filename + "_ES.md")
    json_path = os.path.join(output_dir, base_filename + "_summary.json")
    return english_path, spanish_path, json_path

def athletes_summary_to_excel_table(athletes: List[dict], output_path: str | None = None) -> pd.DataFrame:
    """
    Converts a list of json fashioned like AthleteSummary pydantic class into an expanded excel (one row by
    athlete and sport), and it returns the DataFrame
    If you pass the output_path, it also saves the xlsx
    """

    # Define columns
    columns = [
        "name_of_the_athlete",
        "date_of_birth",
        "sex",
        "country",
        "paralympic_category_lw",
        "sport_name",
        "participates",
        "major_achievements",
        "paralympic_participation",
        "participation",
        "achievements",
        "guide",
        "performance_trends",
        "preparation_style",
        "personal_contextual_info",
        "personal_data",
        "url_references"
    ]

    rows = []

    for athlete in athletes or []:
        athlete = athlete or {}
        sports = athlete.get("sports")
        if not sports:
            sports = [{"sport_name": athlete.get("sport_under_study")}]

        for i, sport in enumerate(sports):
            sport = sport or {}
            row = {
                "name_of_the_athlete": athlete.get("name_of_the_athlete", "") if i == 0 else "",
                "date_of_birth": athlete.get("date_of_birth", "") if i == 0 else "",
                "gender": athlete.get("gender", "") if i == 0 else "",
                "country": athlete.get("country", "") if i == 0 else "",
                "category": athlete.get("category", "") if i == 0 else "",
                "sport_under_study": athlete.get("sport_under_study", "") if i == 0 else "",
                "world_cup_rank": athlete.get("world_cup_rank", "") if i == 0 else "",
                "world_cup_points": athlete.get("world_cup_points", "") if i == 0 else "",
                "paralympic_category_lw": athlete.get("paralympic_category_lw", "") if i == 0 else "",
                "personal_data": athlete.get("personal_data", "") if i == 0 else "",
                "sport_name": sport.get("sport_name", ""),
                "participates": sport.get("participates", ""),
                "major_achievements": sport.get("major_achievements", ""),
                "paralympic_participation": sport.get("paralympic_participation", ""),
                "participation": sport.get("participation", ""),
                "achievements": sport.get("achievements", ""),
                "guide": sport.get("guide", ""),
                "performance_trends": sport.get("performance_trends", ""),
                "preparation_style": sport.get("preparation_style", ""),
                "personal_contextual_info": sport.get("personal_contextual_info", ""),
                "url_references": ";".join(sport.get("reference_urls", [""]))
            }
            rows.append(row)

    df = pd.DataFrame(rows, columns=columns)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_excel(output_path, index=False, engine="openpyxl")
        REPORTER_LOGGER.info("Excel table saved successfully in " + output_path)

    return df


def athletes_summary_to_markdown_table(
        athletes: List[dict],
        links: List[str] | None = None,
        output_path: str | None = None
) -> str:
    """
    Converts a list of json fashioned like AthleteSummary pydantic class into a markdown table, linking
    each athlete name to the `.md` file with its report.
    """

    # Table headers
    headers = [
        "name_of_the_athlete",
        "date_of_birth",
        "sex",
        "country",
        "paralympic_category_lw",
        "sport_name",
        "participates",
        "major_achievements",
        "paralympic_participation",
        "participation",
        "achievements",
        "guide",
        "performance_trends",
        "preparation_style",
        "personal_contextual_info",
        "personal_data",
        "url_references"
    ]

    # Markdown: table heading
    md_lines = []
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    # link counter
    link_index = 0

    for athlete in athletes:
        for i, sport in enumerate(athlete.get("sports", [{}])):
            row = []
            for field in headers:
                if field == "name_of_the_athlete":
                    name = athlete.get("name_of_the_athlete", "")
                    if links and link_index < len(links):
                        # Markdown link
                        value = f"[{name}]({links[link_index]})"
                    else:
                        value = name
                elif field == "url_references":
                    value = ";".join(sport.get("reference_urls", [""]))
                elif field in athlete:
                    value = athlete.get(field, "") if i == 0 else ""
                elif field in sport:
                    value = sport.get(field, "")
                else:
                    value = ""

                # Scape pipes
                if isinstance(value, str):
                    value = value.replace("|", "\\|")
                row.append(str(value))

            md_lines.append("| " + " | ".join(row) + " |")
            link_index += 1

    markdown_content = "\n".join(md_lines)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8-sig") as f:
            f.write(markdown_content)
        REPORTER_LOGGER.info("Markdown table saved successfully in " + output_path)

    return markdown_content