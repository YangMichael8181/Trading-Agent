from pathlib import Path


directory = Path(__file__).parent

prompts_dir = directory / "prompts"
docs_dir = directory / "docs"

visited_urls = set()