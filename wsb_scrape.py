import json
from helper import make_request
# from langchain.llms import Ollama


class Comment:
    ticker = ""
    author = ""
    text = ""
    link = ""
    karma = 0

    def __init__(_author, _text, _link, _karma):
        author = _author
        text = _text
        link = _link
        karma = _karma

# Finds stickied post in hot page of wsb
# Gathers comments from stickied post
# Returns list of comment objects 
def get_wsb_thread(hot_url):
    res = []
    urls = make_request(hot_url)

    for url in urls:
        for post in make_request(url, thread=True):
            res.append(Comment(post['author'], post['body'], post['permalink'], post['karma']))
    
    return res




    
def get_daily_dds(headers):

    return
    url =  "https://www.reddit.com/r/wallstreetbets/search.json?sort=top&q=flair%3ADD&restrict_sr=on&t=day"