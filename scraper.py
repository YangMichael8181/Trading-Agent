import json
from collections import defaultdict
from helper import make_request


class Comment:
    ticker = ""
    author = ""
    text = ""
    link = ""
    score = 0

    def __init__(self, _author, _body, _link, _score):
        self.author = _author
        self.body = _body
        self.link = _link
        self.score = _score

# Finds stickied post in hot page of wsb
# Gathers comments from stickied post
# Returns list of comment objects 
def get_wsb_thread(hot_url):
    res = defaultdict(list)
    urls = make_request(hot_url)

    for url in urls:
        post_title, comments = make_request(url, thread=True)
        for comment in comments:
            # Ignore comments with images
            # No image == missing crucial context, with image == program becomes far more complicated
            # Not a statistically significant number of comments with pictures, therefore ignored
            comment_body = comment['body']
            if ".jpg" in comment_body or ".jpeg" in comment_body or ".png" in comment_body:
                continue

            # Ignore comments with less than 1 karma
            # Again, more harm than good. Other people have determined this poster to be trolling/irrelevant, therefore remove
            comment_score = comment['score']
            if comment_score < 1:
                continue

            comment_author = comment['author']
            comment_link = f"https://www.reddit.com{comment['permalink']}"
            res[post_title].append(Comment(comment_author, comment_body, comment_link, comment_score))

    
    return res




    
def get_daily_dds(headers):

    return
    url =  "https://www.reddit.com/r/wallstreetbets/search.json?sort=top&q=flair%3ADD&restrict_sr=on&t=day"