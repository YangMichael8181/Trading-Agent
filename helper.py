import time
import requests

def make_request(url:str, thread:bool = False):

    print(f"Sending GET request to {url} . . .")
    """
    Function used to send requests
    Parameters:
        url: string, the url to send a GET request to
        thread: if gathering data from a post (post content) or from a thread (comments)
    """

    # NOTE: Must send a User-Agent header that looks like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
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

                return data

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
    
    print("Error occured: Please try again")
    return None