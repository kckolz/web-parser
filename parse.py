import requests
import json
from bs4 import BeautifulSoup

json_site = 'https://vergrabber.kingu.pl/vergrabber.json'
xml_site = 'https://patchmypc.com/freeupdater/definitions/definitions.xml'
html_site = 'https://chromestatus.com/features/schedule'

xml_targets = ["acrobatreaderdcver", "anydeskver", "avastantivirusver"]


def parse_json_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    parsed_json = json.loads(soup.text)
    return parsed_json["server"]


def parse_xml_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'lxml')
    return find_versions(soup, xml_targets)


def save_json(data, file_name):
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile)


def find_versions(soup, targets):
    versions = []
    for target in targets:
        version = soup.find(target)
        if version:
            versions.append({
                "name": version.name,
                "version": version.text
            })
    return versions


try:

    parsed_xml_page = parse_xml_page(xml_site)
    save_json(parsed_xml_page, 'xml-page-versions.json')

    parsed_json_page = parse_json_page(json_site)
    save_json(parsed_json_page, 'json-page-versions.json')

except Exception as e:
    print("Error: {0}".format(e))

