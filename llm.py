from openai import OpenAI
from collections import defaultdict

from pprint import pprint


import globals

client = OpenAI(api_key="ollama",base_url="http://localhost:11434/v1")

# TODO: Work in progress
def parse_tickers(comments:list, comments_dict = None):
    res = defaultdict(list)

    with open(globals.prompts_dir / "ticker_parser_prompt", "r") as file:
        SYSTEM_PROMPT = file.read()
    
    temperature = 0.1
    # model = "gemma3:12b"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [{"role": "user", "content": comment} for comment in comments]

    response = client.chat.completions.create(
        model=globals.model,
        messages=messages,
        temperature=temperature
    )

    raw = response.choices[0].message.content
    raw = raw.replace('\n', ' ')

    processed_comments = raw.split('<new>')
    for c in processed_comments:
        c = c.strip()
        try:
            c = c.split('<split>')
            ticker, text = c[0], c[1]

            if comments_dict is not None:
                comments_dict[ticker].append(text)
            else:
                res[ticker].append(text)

        # ignore if faulty output
        except Exception as e:
            continue
    
    return res

# TODO: Use RAG to create chatbot about good stocks to pick
# Use old comment documents for vector database
# Use FAISS