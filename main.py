import json
from collections import defaultdict

# local imports
import scraper
import globals
import llm

def main():

    # grab visited threads to prevent re-visiting same threads
    with open("visited_links", "r") as file:
        links = file.read().split("\n")
        globals.visited_urls = set(links)


    print('Starting Stickied Thread Scrape . . . ')
    # grabs threads from /u/wsbapp
    # Grabs top 20 threads, ignores latest thread
    # Do this via checking the history of wsbapp
    wsbapp_url = "https://www.reddit.com/user/wsbapp.json"
    scraped_data = scraper.get_wsb_thread(wsbapp_url)
        

    # Returns a dict {post_title : [comments]}
    # Parse comments, send to LLM to gather tickers

    with open("visited_links", "w") as file:
        for url in globals.visited_urls:
            file.write(url + "\n")

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
    
    # print('Gathering Daily DDs')
    # get_daily_dds(headers)



if __name__ == "__main__":
    main()

