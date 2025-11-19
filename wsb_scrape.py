import json
from helper import make_request
# from langchain.llms import Ollama


class Comment:
    ticker = ""
    author = ""
    text = ""
    link = ""
    score = 0

    def __init__(self, _author, _body, _permalink, _score):
        self.author = _author
        self.body = _body
        self.permalink = _permalink
        self.score = _score

# Finds stickied post in hot page of wsb
# Gathers comments from stickied post
# Returns list of comment objects 
def get_wsb_thread(hot_url):
    res = []
    urls = make_request(hot_url)

    for url in urls:
        for post in make_request(url, thread=True):
            fixed_link = f"https://www.reddit.com{post['permalink']}"
            res.append(Comment(post['author'], post['body'], post['permalink'], post['score']))
    
    return res




    
def get_daily_dds(headers):

    return
    url =  "https://www.reddit.com/r/wallstreetbets/search.json?sort=top&q=flair%3ADD&restrict_sr=on&t=day"