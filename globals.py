import threading
from pathlib import Path

CURRENT_DIRECTORY = Path(__file__).parent

PROMPTS_DIR = CURRENT_DIRECTORY / "prompts"
DOCS_DIR = CURRENT_DIRECTORY / "docs"

# Threads already seen and scraped
visited_urls = set()

GLOBAL_NASDAQ = None