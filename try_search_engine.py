import json

from ddgs import DDGS
from crewai.tools import BaseTool

BLOCKED_DOMAINS = [
    "xnxx.com",
    "pornhub.com",
    "xvideos.com",
    "xhamster.com",
    "redtube.com"
]

class DuckDuckGoTool(BaseTool):
    name: str = "DuckDuckGo Search"
    description: str = "Search the web using DuckDuckGo with safe filtering"

    def _run(self, query: str):
        with DDGS() as ddgs:
            results = list(
                ddgs.text(
                    query,
                    region="es-es",        # o "wt-wt"
                    safesearch="strict",   # 🔥 CLAVE
                    max_results=10
                )
            )

        # 🔒 Filtrado manual de dominios
        filtered_results = [
            {
                "title": r.get("title"),
                "href": r.get("href"),
                "body": r.get("body")
            }
            for r in results
            if r.get("href") and not any(
                blocked in r["href"].lower()
                for blocked in BLOCKED_DOMAINS
            )
        ]

        return filtered_results

if __name__ == "__main__":
    search = DuckDuckGoTool()

    print(json.dumps(search._run("RIVERO FERNANDEZ Higinio biathlon"), indent=4))