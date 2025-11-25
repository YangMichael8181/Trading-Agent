from pathlib import Path
import classes

def initialize_global_variables():

    global NASDAQ
    # global VISITED_URLS
    NASDAQ = classes.NASDAQ()
    
    # grab visited threads to prevent re-visiting same threads
    # Search unvisited threads
    # with open("visited_links.txt", "r") as file:
    #     links = file.read().split("\n")
    #     globals.visited_urls = set(links)


CURRENT_DIRECTORY = Path(__file__).parent

PROMPTS_DIR = CURRENT_DIRECTORY / "prompts"
DOCS_DIR = CURRENT_DIRECTORY / "docs"

# Threads already seen and scraped
VISITED_URLS = set()

NASDAQ = None
