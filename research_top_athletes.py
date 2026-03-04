import os
import json
import time
from typing import Any

from crewai import BaseLLM, LLM
from pydantic import InstanceOf

from config import REPORTER_LOGGER
from reporter_agent import run_research
from utils import athletes_summary_to_excel_table, athletes_summary_to_markdown_table, get_athlete_filename, get_output_filenames


def build_navigable_markdown_file(markdown_files: dict, output_base_path: str):
    """
    Generates a navigable Markdown file linking to individual athlete tables.

    This function creates a Markdown file named "athlete_navigation_tables.md" inside
    the `tables` directory under the given `output_base_path`. It organizes the links
    by sport, category, and gender, allowing users to navigate easily to each athlete's
    summary table.

    The Markdown structure is as follows:
    # Sport
    ## Category
    [Gender](link_to_markdown_file)

    :param markdown_files: Nested dictionary containing the structure:
        {
            sport: {
                category: {
                    gender: markdown_file_path
                }
            }
        }
    :param output_base_path: Base directory where the "tables" folder exists
                             and where the navigation file will be created.
    """

    with open(os.path.join(output_base_path, "tables", "athlete_navigation_tables.md"), "w", encoding="utf-8-sig") as f:
        for sport, categories in markdown_files.items():
            f.write("# " + sport.capitalize() + "\n")
            for category, genders in categories.items():
                f.write("## " + category.capitalize() + "\n")
                for gender, file in genders.items():
                    f.write(f"[{gender}]({file})\n")


def research_for_top_k_athletes(llm: str | InstanceOf[BaseLLM] | Any, athletes_metadata_path: str, output_base_path: str, top_k: int = 15):
    """
    Performs automated research on the top K athletes for selected sports and categories,
    saves their data as JSON, Excel, and Markdown tables, and builds a navigable Markdown index.

    For each sport, category, and gender, the function:
    1. Loads athlete metadata from JSON files.
    2. Limits processing to the top `top_k` athletes.
    3. Runs research using the specified `llm` (Large Language Model or wrapper).
    4. Saves results in JSON format for caching.
    5. Generates Markdown and Excel tables summarizing the athlete data.
    6. Updates a navigation Markdown file linking all tables.

    Retries research up to 5 times if it fails, and logs any errors in separate `_error.txt` files.

    :param llm: A string identifier, LLM instance, or compatible object used for research.
    :param athletes_metadata_path: Path to JSON files containing athletes metadata.
    :param output_base_path: Base directory where articles, tables, and navigation files are saved.
    :param top_k: Maximum number of athletes to process per sport/category/gender combination.
                  Default is 15.
    """
    markdown_files = {}

    for sport in ["biathlon", "cross_country"]:
        markdown_files[sport] = {}
        for category in ["sitting", "standing", "vision"]:
            markdown_files[sport][category] = {}
            for gender in ["male", "female"]:
                athlete_results, athlete_links = [], []
                for athlete_i, athlete_conf in enumerate(json.load(open(os.path.join(athletes_metadata_path, f"para_{sport}_{category}_{gender}.json")))):

                    # We control the maximum amount of athletes to research
                    if top_k is not None and athlete_i >= top_k:
                        break

                    _, _, json_result_path = get_output_filenames(athlete_name=athlete_conf["name"], sport=sport, category=category, output_dir=os.path.join(output_base_path, "articles"))

                    # Control to not rerun previous experiments
                    if os.path.exists(json_result_path):
                        athlete_results.append(json.load(open(json_result_path)))
                        athlete_filename = get_athlete_filename(athlete_name=athlete_conf['name'], sport=sport, category=athlete_conf['class'])
                        athlete_links.append(os.path.join(rf"../articles/{athlete_filename}_ES.md"))
                        REPORTER_LOGGER.info(f"Cached info of {athlete_filename}")
                        continue

                    json_result = None
                    # Sometimes, the web research abruptly stops. We added a retrial logic
                    for retry_i in range(5):
                        try:
                            _, json_result = run_research(
                                athlete_name=athlete_conf["name"],
                                sport=sport,
                                llm=llm,
                                world_cup_rank=athlete_conf["rank"],
                                country=athlete_conf["country"],
                                world_cup_points=athlete_conf["points"],
                                category=athlete_conf["class"],
                                gender=gender,
                                output_dir=os.path.join(output_base_path, "articles")
                            )
                            if json_result is not None:
                                break
                        except Exception as e:
                            REPORTER_LOGGER.warning(f"Attempt {retry_i +1} failed: {e}")
                            time.sleep(60)  # optional delay between retries

                    if json_result is None:
                        output_name = f"{sport}_{category}_{gender}_{athlete_conf['name'].replace(' ', '_')}"
                        with open(f"{output_name}_error.txt", "w", encoding="utf-8") as f:
                            f.write(f"Unable to find information about {athlete_conf['name']} in sport {sport}")

                    athlete_results.append(json_result)
                    athlete_links.append(os.path.join(rf"../articles/{get_athlete_filename(athlete_name=athlete_conf['name'], sport=sport, category=athlete_conf['class'])}_ES.md"))

            try:
                output_name = f"para_{sport}_{category}_{gender}"
                markdown_table = os.path.join(output_base_path, "tables", f"{output_name}.md")
                markdown_files[sport][category][gender] = markdown_table

                athletes_summary_to_excel_table(athletes=athlete_results, output_path=markdown_table.replace(".md", ".xlsx"))

                athletes_summary_to_markdown_table(
                    athletes=athlete_results,
                    links=athlete_links,
                    output_path=markdown_table
                )
            except Exception as e:
                output_name = f"para_{sport}_{category}_{gender}"
                REPORTER_LOGGER.error(f"Unable to dump {output_name}: {e}")
                with open(f"{output_name}_error.txt", "w", encoding="utf-8-sig") as f:
                    f.write(f"Unable to dump {output_name} with:\n{athlete_results}\n{athlete_links}")

    build_navigable_markdown_file(markdown_files=markdown_files, output_base_path=output_base_path)


if __name__ == "__main__":
    model = "gpt-4o-mini"
    athletes_metadata_path = r".\athletes"
    output_base_path = rf".\results\{model}"

    # We initialize the model inferencer
    llm = LLM(
        model=f"openai/{model}",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    research_for_top_k_athletes(
        llm=llm,
        athletes_metadata_path=athletes_metadata_path,
        output_base_path=output_base_path,
        top_k = 20
    )
