from pathlib import Path
import classes
import json

def initialize_global_variables(config_file_name:str = "default.json"):

    # Initialize NASDAQ object
    # Read in json file, pass to NASDAQ object
    config = CONFIG_DIR / config_file_name
    try:
        json_string = config.read_text(encoding="utf-8")
        json_file = json.loads(json_string)
    except Exception as e:
        print(f"EXCEPTION OCCURED: {e}")

    global NASDAQ
    NASDAQ = classes.NASDAQ(json_file=json_file)
    
    # grab visited threads to prevent re-visiting same threads
    # global VISITED_URLS
    # Search unvisited threads
    # with open("visited_links.txt", "r") as file:
    #     links = file.read().split("\n")
    #     globals.visited_urls = set(links)


CURRENT_DIRECTORY = Path(__file__).parent

PROMPTS_DIR = CURRENT_DIRECTORY / "prompts"
DOCS_DIR = CURRENT_DIRECTORY / "docs"
CONFIG_DIR = CURRENT_DIRECTORY / "config"

# Threads already seen and scraped
VISITED_URLS = set()

# file where invalid tickers are stored
ERROR_MESSAGE_FILE = "stderr_output.txt"

# filtered stock information
NASDAQ = None

ONE_BILLION = 1000000000
ONE_HUNDRED_MILLION = 100000000
