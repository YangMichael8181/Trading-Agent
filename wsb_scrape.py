import requests
import json
import time
# from langchain.llms import Ollama


# Data to write to file
# Will be stored as a list of strings
write_data = []


class Comment:
    author = ""
    text = ""
    link = ""
    karma = 0


def main():
    # NOTE: Must send a User-Agent header that looks like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Grab the top 50 posts from hot page of /r/wallstreetbets
    # Search hot page, find stickied threads
    url = "https://www.reddit.com/r/wallstreetbets/hot.json?limit=50"
    urls = []
    
    urls = make_request(headers=headers, url=url, test=True)


    # Send threads to gather comments
    # Read comments to gather sentiment about certain tickers, which tickers are popular
    get_wsb_thread(headers, urls)
    
    return

    get_daily_dds(headers)

    # TODO: write code to access LLM here
    # Use Ollama.invoke("...")


def get_wsb_thread(headers, urls):
    for url in urls:
        for post in make_request(headers, url, thread=True):
            print(post)
            input('pause program')
            comment_author = post['author']
            comment_karma = post['score']
            comment_text = post['body']




    
def get_daily_dds(headers):

    return
    url =  "https://www.reddit.com/r/wallstreetbets/search.json?sort=top&q=flair%3ADD&restrict_sr=on&t=day"


def make_request(headers, url, **kwargs):
    
    # Variables to check status of request
    request_status = False
    attempts = 0
    res = []

    # Scared of making too many requests at once, thus limit request to at most once every 2 seconds
    while request_status == False and attempts < 5:
        time.sleep(2)
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                request_status = True

                if kwargs.get('thread', None) is not None:
                    res = [post['data'] for post in data[1]['data']['children'] if post['kind'] == 't1']

                else:
                    posts = data['data']['children']
                    res = [post['data'] for post in posts if post['stickied'] == True]

            elif response.status_code == 429:
                print("Error: Too many requests. Reddit is rate-limiting you.")
            else:
                print(f"Error: Failed to fetch data. Status Code: {response.status_code}")

        except Exception as e:
            print(f"An error occurred: {e}")

        if request_status == False:
            print("Unable to gather urls, trying again in 2 seconds . . .")
            attempts += 1
        if attempts == 5:
            print('Too many attempts, try again another time . . .')
    
    return res


if __name__ == "__main__":
    main()
