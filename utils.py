import os
import pandas as pd
from typing import List

from crewai.tools import BaseTool
from ddgs import DDGS

from athlete_model import AthleteSummary
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

def get_athlete_filename(athlete_name: str, sport: str, category: str):
    return f"{athlete_name.replace(' ', '_')}_{sport}_{category}"

def athletes_summary_to_excel_table(athletes: List[dict], output_path: str | None = None) -> pd.DataFrame:
    """
    Convierte una lista de dicts (o AthleteSummary convertidos a dict) en un Excel expandido
    (1 fila por atleta y deporte) y devuelve el DataFrame.
    Si se pasa output_path, también lo guarda en archivo .xlsx.
    """

    # Definimos las columnas
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
            }
            rows.append(row)

    df = pd.DataFrame(rows, columns=columns)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_excel(output_path, index=False, engine="openpyxl")

    return df


def athletes_summary_to_markdown_table(
        athletes: List[AthleteSummary | dict],
        links: List[str] | None = None,
        output_path: str | None = None
) -> str:
    """
    Convierte una lista de AthleteSummary en una tabla Markdown.
    Cada nombre de atleta puede ser un enlace a otro markdown si se pasa `links`.
    """

    # Encabezados de la tabla
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
    ]

    # Markdown: encabezado de tabla
    md_lines = []
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    # Contador para los enlaces
    link_index = 0

    for athlete in athletes:
        for i, sport in enumerate(athlete.get("sports", [{}])):
            row = []
            for field in headers:
                value = None
                if field == "name_of_the_athlete":
                    name = athlete.get("name_of_the_athlete", "")
                    if links and link_index < len(links):
                        # Markdown link
                        value = f"[{name}]({links[link_index]})"
                    else:
                        value = name
                elif field in athlete:
                    value = athlete.get(field, "") if i == 0 else ""
                elif field in sport:
                    value = sport.get(field, "")
                else:
                    value = ""

                # Escapar tuberías
                if isinstance(value, str):
                    value = value.replace("|", "\\|")
                row.append(str(value))

            md_lines.append("| " + " | ".join(row) + " |")
            link_index += 1

    markdown_content = "\n".join(md_lines)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    return markdown_content