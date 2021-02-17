import requests
import json
from bs4 import BeautifulSoup

json_site = 'https://vergrabber.kingu.pl/vergrabber.json'

xml_sites = [{
    "url": 'https://patchmypc.com/freeupdater/definitions/definitions.xml',
    "targets": [
        "acrobatreaderdcver",
        "anydeskver",
        "avastantivirusver"
    ]
}]

html_sites = [
    {
        "url": 'http://hg.openjdk.java.net/jdk8u/jdk8u/rev/',
        "targets": [
            {
                "version": {
                    "type": "class",
                    "target": "description"
                },
                "date": {
                    "type": "class",
                    "target": "age"
                }
            }
        ],
    },
    {
        "url": 'https://github.com/corretto/corretto-11/releases/',
        "targets": [
            {
                "version": {
                    "type": "class",
                    "target": "css-truncate-target"
                },
                "date": {
                    "type": "tag",
                    "target": "relative-time"
                }
            }
        ],
    }
]


def parse_html_page(html_config):
    page = requests.get(html_config["url"])
    soup = BeautifulSoup(page.content, 'html.parser')
    return find_versions_html(soup, html_config["targets"])


def parse_json_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    parsed_json = json.loads(soup.text)
    return parsed_json["server"]


def parse_xml_page(xml_config):
    page = requests.get(xml_config["url"])
    soup = BeautifulSoup(page.content, 'lxml')
    return find_versions_xml(soup, xml_config["targets"])


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
            version = soup.find(class_=version_description["target"]).text
        elif version_description["type"] == "id":
            version = soup.find(id=version_description["target"]).text
        elif version_description["type"] == "tag":
            version = soup.find(version_description["target"]).string

        date_description = target["date"]
        if date_description["type"] == "class":
            date = soup.find(class_=date_description["target"]).text
        elif date_description["type"] == "id":
            date = soup.find(id=date_description["target"]).text
        elif date_description["type"] == "tag":
            date = soup.find(date_description["target"]).string

        versions.append({
            "name": version,
            "date": date
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
    parsed_json_page = parse_json_page(json_site)
    save_json(parsed_json_page, 'json-page-versions.json')

    for xml_site in xml_sites:
        parsed_xml = []
        parsed_xml_page = parse_xml_page(xml_site)
        for xml in parsed_xml_page:
            parsed_xml.append(xml)
        save_json(parsed_xml, 'xml-page-versions.json')

    for html_site in html_sites:
        parsed_html = []
        parsed_html_page = parse_html_page(html_site)
        for html in parsed_html_page:
            parsed_html.append(html)
        save_json(parsed_html, 'html-page-versions.json')


except Exception as e:
    print("Error: {0}".format(e))

