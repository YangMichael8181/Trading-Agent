from pathlib import Path

# Comments to send to LLM
# Will be a list of Comment Objects
comments = []
directory = Path(__file__).parent

prompts_dir = directory / "prompts"
docs_dir = directory / "docs"