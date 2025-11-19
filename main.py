import os
import scraper
import globals


def main():

    print('Starting Stickied Thread Scrape . . . ')
    # URL for hot page of /r/wallstreetbets
    # Gathers top 50 posts, finds stickied thread, gathers comments
    # Returns a dict: {post_title : [comments]}
    wsb_hot_url = "https://www.reddit.com/r/wallstreetbets/hot.json?limit=50"
    scraped_data = wsb_scrape.get_wsb_thread(wsb_hot_url)

    for title, comments in scraped_data.items():
        cleaned_title = title.replace('/', '-').replace('\\', '-')
        cleaned_title = globals.docs_dir / cleaned_title
        with open(cleaned_title, "w") as file:
            for comment in comments:
                comment_str = f"Author: {comment.author}\n Body: {comment.body} \n Link: {comment.link} \n Score: {comment.score} \n"
                file.write(comment_str + "---------------------------------------------------------------------------------------------------------\n")
    
    return

    print('Gathering Daily DDs')
    get_daily_dds(headers)




if __name__ == "__main__":
    main()

