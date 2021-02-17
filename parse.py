import requests
import json
from bs4 import BeautifulSoup

json_site = 'https://vergrabber.kingu.pl/vergrabber.json'
xml_site = 'https://patchmypc.com/freeupdater/definitions/definitions.xml'
html_site = 'http://hg.openjdk.java.net/jdk8u/jdk8u/rev/'

xml_targets = ["acrobatreaderdcver", "anydeskver", "avastantivirusver"]

html_targets = [{
    "version": {
        "type": "class",
        "target": "description"
    },
    "date": {
        "type": "class",
        "target": "age"
    }
}]


def parse_html_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    return find_versions_html(soup, html_targets)


def parse_json_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    parsed_json = json.loads(soup.text)
    return parsed_json["server"]


def parse_xml_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'lxml')
    return find_versions_xml(soup, xml_targets)


def save_json(data, file_name):
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile)


def find_versions_html(soup, targets):
    versions = []
    version = ""
    date = ""
    for target in targets:
        version_description = target["version"]
        if version_description["type"] == "class":
            version = soup.find(class_=version_description["target"])
        elif version_description["type"] == "id":
            version = soup.find(id=version_description["target"])

        date_description = target["date"]
        if date_description["type"] == "class":
            date = soup.find(class_=date_description["target"])
        elif date_description["type"] == "id":
            date = soup.find(id=date_description["target"])
        versions.append({
            "name": version.text,
            "date": date.text
        })
    return versions


def find_versions_xml(soup, targets):
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

    parsed_html_page = parse_html_page(html_site)
    save_json(parsed_html_page, 'html-page-versions.json')

except Exception as e:
    print("Error: {0}".format(e))

