import re

def gather_invalid_tickers() -> list:
    # Opens file
    # Grabs file contents, then clears file content

    invalid_tickers = []
    with open("stderr_output.txt", "r+") as file:
        data = file.read()
        file.seek(0)
        file.truncate()

    for line in data.split('\n'):
        if "YFPricesMissingError" in line:
            bracket_start = line.find('[') + 1
            bracket_end = line.find(']')
            substr = line[bracket_start:bracket_end]
            if ',' in substr:
                tickers_list = substr.split(',')
                for t in tickers_list:
                    t = re.sub(r'[^a-zA-Z]', '', t)
                    invalid_tickers.append(t)
            else:
                substr = re.sub(r'[^a-zA-Z]', '', substr)
                invalid_tickers.append(substr)
    
    return invalid_tickers