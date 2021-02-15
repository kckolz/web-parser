import requests
import json
from bs4 import BeautifulSoup

def parse_page(url):
    page = requests.get(url)
    return BeautifulSoup(page.content, 'html.parser')

try:
    # instantiate API class
    parsedPage = parse_page('https://vergrabber.kingu.pl/vergrabber.json')
    newDictionary = json.loads(str(parsedPage))
    print(newDictionary)

except Exception as e:
    print("Error: {0}".format(e))

