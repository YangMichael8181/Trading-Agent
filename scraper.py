import json
from collections import defaultdict
import threading

from helper import make_request
import globals
import llm

# Finds stickied post in hot page of wsb
# Gathers comments from stickied post
# Returns list of comment objects 
def get_wsb_thread():
    """
    Gathers comments from the daily thread
    Parameters:
        wsbapp_url: string. The url to /u/wsbapp's page
    """

    print('Starting Stickied Thread Scrape . . . ')
    
    # Declare variables
    wsbapp_url = "https://www.reddit.com/user/wsbapp.json"
    scraped_data = defaultdict(list)
    raw_data = make_request(wsbapp_url)
    urls = []


    post_data = raw_data['data']['children']
    for i in range (1, 21):
        url = post_data[i]['data']['url'][:-1] + ".json"
        if url in globals.visited_urls:
            continue
        urls.append(url)
        globals.visited_urls.add(url)

    # Gather comments from unvisited threads
    for url in urls:
        raw_data = make_request(url, thread=True)
        post_title = raw_data[0]['data']['children'][0]['data']['title']
        raw_comments = raw_data[1]['data']['children']
        
        for comment in raw_comments:
            # TODO: MIGHT BE BROKEN
            # TRIES TO GRAB REPLIES IF EXISTS, THEN APPENDS
            if comment.get('replies', "") != "":
                raw_comments.append(comments['replies']['data']['children'])

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
            
            # Ignore short comments, no worth
            if len(comment_body) < 10:
                continue

            # Ignore comments with less than 1 karma
            # Again, more harm than good. Other people have determined this poster to be trolling/irrelevant, therefore remove
            comment_score = comment['data']['score']
            if comment_score < 1:
                continue

            scraped_data[post_title].append(comment_body)
        

    # Returns a dict {post_title : [comments]}
    # Parse comments, send to LLM to gather tickers

    for title, comments in scraped_data.items():
        comments_dict = defaultdict(list)

        for i in range(0, len(comments), 5):
            print(f"Parsing comments {i} through {i + 5}. . .")
            comment_text = [comment for comment in comments[i: i + 5]]
            llm.parse_tickers(comment_text, comments_dict)

        # Sanitize thread title
        # Place within docs directory
        cleaned_title = title.replace('/', '-').replace('\\', '-') + ".json"
        cleaned_title = globals.docs_dir / cleaned_title

        with open(cleaned_title, "w") as file:
            json.dump(comments_dict, file, indent=4)
        
        print(f"Finished parsing {cleaned_title}")
    
    with open("visited_links.txt", "w") as file:
        for url in globals.visited_urls:
            file.write(url + "\n")




    
def get_daily_dds():
    # TODO: WIP, DECIDE HOW TO USE THE DATA
    """
    Gathers any dds posted in the daily dds section

    """
    # print('Gathering Daily DDs')
    # get_daily_dds(headers)
    return
    url =  "https://www.reddit.com/r/wallstreetbets/search.json?sort=top&q=flair%3ADD&restrict_sr=on&t=day"