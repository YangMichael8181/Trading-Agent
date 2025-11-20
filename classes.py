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