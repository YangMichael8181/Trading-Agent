import wsb_scrape

comments = []


def main():

    print('Starting Stickied Thread Scrape . . . ')
    # URL for hot page of /r/wallstreetbets
    # Gathers top 50 posts, finds stickied thread, gathers comments
    wsb_hot_url = "https://www.reddit.com/r/wallstreetbets/hot.json?limit=50"
    comments = wsb_scrape.get_wsb_thread(wsb_hot_url)
    for comment in comments:
        print(f"Author: {comment.author}\n Body: {comment.body} \n Link: {comment.permalink} \n Score: {comment.score}")
    
    return

    print('Gathering Daily DDs')
    get_daily_dds(headers)

    # TODO: write code to access LLM here
    # Use Ollama.invoke("...")



if __name__ == "__main__":
    main()
