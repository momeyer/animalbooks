import requests
res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "lFpB9zGJWlX67eLwpNAXLQ", "isbns": "0142501085"})
print(res.json())
