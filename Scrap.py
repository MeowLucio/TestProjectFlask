from bs4 import BeautifulSoup
import requests

def scrap(url)  -> (dict, str) :
    try:
        response = requests.get(url)
        soup=BeautifulSoup(response.text, 'lxml')
        tags, counts, result = [], {}, {}
        for token in soup.find_all(True):
            tags.append(token.name)
        UniqueTags = set(tags)
        for Unique in UniqueTags:
            counts[Unique]=0
            for token in tags:
                if Unique == token:
                    counts[Unique] += 1
            if counts[Unique]== 1:
                result[Unique] = dict (count=counts[Unique], nested=len(list(soup.find(Unique).descendants)))
    except Exception as message:
        return (dict(error=str(message)),'404')
        pass
    return (result, 'done')
