import sys
try:
    from googlesearch import search
    res = list(search("Tim Cook Apple email", advanced=True, num_results=3))
    for r in res:
        print(r.url, r.title, r.description)
except Exception as e:
    print("Error:", e)
