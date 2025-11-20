import json
from collections import defaultdict
from helper import make_request
from classes import Comment
import globals

# Finds stickied post in hot page of wsb
# Gathers comments from stickied post
# Returns list of comment objects 
def get_wsb_thread(wsbapp_url):
    res = defaultdict(list)
    raw_data = make_request(wsbapp_url)
    urls = []

    post_data = raw_data['data']['children']
    for i in range (1, 21):
        url = post_data[i]['data']['url'][:-1] + ".json"
        if url in globals.visited_urls:
            continue
        urls.append(url)
        globals.visited_urls.add(url)

    for url in urls:
        raw_data = make_request(url, thread=True)
        post_title = raw_data[0]['data']['children'][0]['data']['title']
        raw_comments = raw_data[1]['data']['children']
        
        for comment in raw_comments:
            # There are "comments" of kind "more" that is used for pagination
            # Ignore them, only focus on actual comments
            if comment['kind'] != "t1":
                continue

            # Ignore comments with images
            # No image == missing crucial context, with image == program becomes far more complicated
            # Not a statistically significant number of comments with pictures, therefore ignored
            comment_body = comment['data']['body']
            if ".jpg" in comment_body or ".jpeg" in comment_body or ".png" in comment_body:
                continue

            # Ignore comments with less than 1 karma
            # Again, more harm than good. Other people have determined this poster to be trolling/irrelevant, therefore remove
            comment_score = comment['data']['score']
            if comment_score < 1:
                continue

            res[post_title].append(comment_body)

    
    return res




    
def get_daily_dds(headers):

    return
    url =  "https://www.reddit.com/r/wallstreetbets/search.json?sort=top&q=flair%3ADD&restrict_sr=on&t=day"