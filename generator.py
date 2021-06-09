import json
import os
import sys
import requests
import base64
import datetime
from dateutil import parser
import subprocess
import logging
import argparse
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from pylatex import Document, Command, TextColor, Figure, NoEscape
from pylatex.base_classes.command import Options
from pylatex.base_classes.latex_object import LatexObject
from pylatex.package import Package
from pylatex.section import Chapter, Section, Subsection
from pylatex.table import Tabular
from pylatex.utils import bold
from pylatex.lists import Itemize
from text_snippets import intro, projects

matplotlib.use("Agg")

with open(f"{os.path.dirname(os.path.abspath(__file__))}/config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(sys.modules["__main__"].__file__)
if config["debug"]:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def get_amount(amount):
    factor = 1000
    for unit in ["", "k", "m", "b", "tr"]:
        if amount < factor:
            if unit == "":
                return f"{amount}{unit}"
            return f"{amount:.2f}{unit}"
        amount /= factor

def parse_time(args):
    timerange = ()
    intervall = args["intervall"]
    endtime = args["endtime"]
    if endtime.upper() == "TODAY":
        timerange = ("", datetime.datetime.now())
    elif endtime.isnumeric():
        timerange = ("", datetime.datetime.fromtimestamp(int(endtime)))
    else:
        timerange = ("", datetime.datetime.now())
    if intervall.upper() == "MONTH":
        timerange = ((timerange[1] - datetime.timedelta(days=30)).date(), timerange[1].date())
    else:
        timerange = ((timerange[1] - datetime.timedelta(days=365)).year + 1, timerange[1].year + 1)
    return timerange

class CommandBaseBasic(LatexObject):
    def __init__(self, command):
        self.command = command

    def dumps(self):
        return f"{self.command}"

class Api:
    def __init__(self, username):
        self.urls = {
            "github": "https://api.github.com/",
            "repos": "repos/",
            "users": "users/"
        }
        self.user = username
        self.rate_limit = 100

    def _get(self, url):
        if self.rate_limit > 0:
            request = requests.get(url)
            self.rate_limit = int(request.headers.get("x-ratelimit-remaining"))
            logger.debug(f"{request.url}, {request.status_code}")
            if request.status_code == 403:
                logger.error(f"Wait until {datetime.datetime.utcfromtimestamp(int(request.headers.get('x-ratelimit-reset'))).strftime('%Y/%m/%d %H:%M:%S')} UTC to send new requests!")
            return request.json()
        return None

    def get_userinfo(self):
        response = self._get(f"{self.urls['github']}{self.urls['users']}{self.user}")
        self.userinfo = {
            "login": response["login"],
            "url": response["html_url"],
            "name": response["name"],
            "followers": response["followers"],
            "following": response["following"],
            "created": response["created_at"],
            "repos": response["public_repos"]
        }

    def get_repos(self):
        response = self._get(f"{self.urls['github']}{self.urls['users']}{self.user}/repos")
        self.repos = []
        for resp in response:
            self.repos.append({
                "name": resp["name"],
                "url": resp["html_url"],
                "description": resp["description"],
                "forked": resp["fork"],
                "languages": self.get_languages(resp["languages_url"]),
                "size": resp["size"],
                "license": resp["license"] if resp["license"] == None else resp["license"]["spdx_id"],
                "forks": resp["forks_count"],
                "stars": resp["stargazers_count"],
                "watchers": resp["watchers_count"],
                "created": resp["created_at"],
                "updated": resp["updated_at"]
                #"readme": self.get_readme(resp["url"])
            })

    def get_gists(self):
        response = self._get(f"{self.urls['github']}{self.urls['users']}{self.user}/gists")
        self.gists = []
        for resp in response:
            self.gists.append({
                "id": resp["id"],
                "url": resp["html_url"],
                "description": resp["description"],
                "files": resp["files"],
                "created": resp["created_at"],
                "updated": resp["updated_at"]
            })

    def get_languages(self, url):
        response = self._get(url)
        languages = []
        for language, bytes in response.items():
            languages.append((language, bytes))
        return languages

    def get_readme(self, url):
        response = self._get(f"{url}/readme")
        return base64.b64decode(response["content"]) if response["content"] else ""

class DocBuilder:
    def __init__(self, user={}, repos=[], gists=[], timerange=(datetime.datetime.now().year - 1, datetime.datetime.now().year)):
        self.user = user
        self.timerange = timerange
        self.repos = self._check_timerange(repos)
        self.gists = self._check_timerange(gists)
        content = [
            Command("maketitle"),
            Command("tableofcontents"),
            Command("newpage")
        ]
        self.document = Document(documentclass="scrreprt", document_options=["a4paper", "12pt"], data=content)
        self.document.packages.append(Package("babel", "english"))
        self.document.packages.append(Package("chronosys"))
        self.document.packages.append(Package("fontawesome"))
        self.document.preamble.append(Command("title", f"Project overview of {user['login']} {self.timerange[0]} - {self.timerange[1]}"))
        self.document.preamble.append(Command("author", "GitHub summary generator"))
        self.document.preamble.append(Command("date", datetime.datetime.now().strftime("%B %d, %Y")))

    def generate_pdf_file(self):
        try:
            self.document.generate_pdf(f"{os.path.dirname(os.path.abspath(__file__))}/{config['path']}generated")
        except subprocess.CalledProcessError:
            logger.warning("Could not write pdf file! Trying to write latex file...")
            self.generate_tex_file()

    def generate_tex_file(self):
        self.document.generate_tex(f"{os.path.dirname(os.path.abspath(__file__))}/{config['path']}generated")

    def append_introduction(self):
        with self.document.create(Chapter("Introduction")):
            self.document.append(CommandBaseBasic(intro(self.user["name"], self.timerange, self.user["url"])))

    def append_projects(self):
        with self.document.create(Chapter("Projects")):
            self.document.append(CommandBaseBasic(projects(self.user["name"], self.timerange, self.user["repos"])))
            with self.document.create(Section("Timeline")):
                self._append_timeline()
            for repo in self.repos:
                self._append_repo(repo)

    def append_summary(self):
        languages = {}
        for repo in self.repos:
            for lang in repo["languages"]:
                try:
                    languages[lang[0]] = languages[lang[0]] + lang[1]
                except KeyError:
                    languages[lang[0]] = lang[1]
        with self.document.create(Chapter("Summary")):
            with self.document.create(Section("Languages")):
                with self.document.create(Itemize()) as list:
                    for lang, bytes in languages.items():
                        list.add_item(f"{lang}\t{get_size(bytes)}")
                if len(languages) > 0:
                    with self.document.create(Figure(position="htbp")) as plot:
                        bars = sns.barplot(x=[lang for lang in languages.keys()], y=[lang for lang in languages.values()])
                        bars.set(xlabel="Language", ylabel="Code in bytes")
                        plot.add_plot(width=NoEscape(r"1\textwidth"), dpi=300)
                        plot.add_caption("Language distribution")
            with self.document.create(Section("Technologies")):
                self.document.append("Currently not available!")

    def generate_structure(self):
        self.append_introduction()
        self.append_projects()
        self.append_summary()

    def _check_timerange(self, list):
        start = self.timerange[0]
        end = self.timerange[1]
        if str(start).isnumeric():
            start = datetime.datetime(start, 1, 1).date()
            end = datetime.datetime(end, 1, 1).date()
        result = []
        for item in list:
            if parser.isoparse(item["updated"]).date() >= start and parser.isoparse(item["updated"]).date() < end:
                result.append(item)
        return result

    def _append_timeline(self):
        if str(self.timerange[0]).isnumeric():
            start = self.timerange[0]
            end = self.timerange[1]
        else:
            start = self.timerange[0].year - 1
            end = self.timerange[1].year
        self.document.append(Command("startchronology", options=Options(startyear=start, stopyear=end, arrow=False)))
        self.document.append(CommandBaseBasic("\\catcode`\\@=11"))
        self.document.append(CommandBaseBasic("\\def\\chron@selectmonth#1{\\ifcase#1\\or Jan\\or Feb\\or Mar\\or Apr\\or May\\or Jun\\or Jul\\or Aug\\or Sep\\or Oct\\or Nov\\or Dec\\fi}"))
        for repo in self.repos:
            created = parser.isoparse(repo["created"])
            if created.year >= start and created.year < end:
                self.document.append(CommandBaseBasic("\\chronoevent[year=False]{" + f"{created.day}/{created.month}/{created.year}" + "}{" + repo["name"] + "}"))
        self.document.append(Command("stopchronology"))

    def _append_repo(self, repo):
        other_languages = ""
        for lang in repo["languages"]:
            if not lang == repo["languages"][0]:
                other_languages = other_languages + lang[0] + ","
        other_languages = other_languages.replace(",", ", ")[:-2]
        with self.document.create(Section(repo["name"])):
            with self.document.create(Subsection("Statistics")):
                self.document.append(CommandBaseBasic(f"\\faStar {get_amount(repo['stars'])}\t\\faEye {get_amount(repo['watchers'])}\t\\faShareAlt {get_amount(repo['forks'])}\t\\faDatabase {get_size(repo['size'])}\t{repo['license']}"))
            with self.document.create(Subsection("Description")):
                self.document.append(repo["description"])
                self.document.append(CommandBaseBasic(f"\\footnote{{{repo['url']}}}"))
                self.document.append(TextColor("gray", f"since {repo['created']}"))
            if len(repo["languages"]) > 0:
                with self.document.create(Subsection("Languages")):
                    with self.document.create(Tabular("l l")) as table:
                        table.add_row(["Top used language:", bold(repo["languages"][0][0])])
                        if len(repo["languages"]) > 1:
                            table.add_row(["Other languages:", other_languages])
            with self.document.create(Subsection("Activity")):
                with self.document.create(Tabular("l l")) as table:
                    table.add_row(["Creation:", parser.isoparse(repo["created"]).strftime("%Y-%m-%d")])
                    table.add_row(["Last update:", parser.isoparse(repo["updated"]).strftime("%Y-%m-%d")])
                    table.add_row(["Development:", str((parser.isoparse(repo["updated"]) - parser.isoparse(repo["created"])).days) + " days"])
                    table.add_row(["Inactive since:", str((datetime.datetime.now().astimezone() - parser.isoparse(repo["updated"])).days) + " days"])

def example():
    user = {
        "login": "test",
        "url": "https://test.github.com/test",
        "name": "Test",
        "followers": 32,
        "following": 10,
        "created": "2020-02-05T12:39:01Z",
        "repos": 8
    }
    repos = [
        {
            "name": "test-project",
            "url": "https://test.github.com/test/test-project",
            "description": "Hello this is a test project!",
            "forked": False,
            "languages": [("Typescript", 54678), ("HTML", 3465), ("CSS", 2376)],
            "size": 52345325,
            "license": "MIT",
            "forks": 2,
            "stars": 3,
            "watchers": 1,
            "created": "2020-04-20T12:39:01Z",
            "updated": "2020-04-30T12:39:01Z",
            "readme": "Hello there! Ick bin ein Berliner!"
        }
    ]
    doc = DocBuilder(user, repos, timerange=(datetime.date(2020, 1, 9), datetime.date(2021, 6, 8)))
    doc.append_introduction()
    doc.append_projects()
    doc.append_summary()
    doc.generate_tex_file()

def main():
    parser = argparse.ArgumentParser(description="Generates a tex file summary about the given GitHub profile's projects.")
    parser.add_argument("user", metavar="user", type=str, help="the GitHub username to get the summary of")
    parser.add_argument("-i", "--intervall", metavar="intervall", type=str, default="YEAR", help="the intervall to get the summary of e.g. last YEAR*, MONTH")
    parser.add_argument("-e", "--endtime", metavar="end", type=str, default="TODAY", help="the endpoint until when to get the summary of e.g. TODAY*, 2635376")
    args = parser.parse_args()
    arguments = vars(args)
    timerange = parse_time(arguments)
    logger.info(f"Got following arguments: {arguments}")
    api = Api(arguments["user"])
    api.get_userinfo()
    api.get_repos()
    logger.info("Got all api infos!")
    builder = DocBuilder(api.userinfo, api.repos, timerange=timerange)
    logger.info("Generating latex structure...")
    builder.generate_structure()
    logger.info("Generating output file...")
    builder.generate_tex_file()

if __name__ == '__main__':
    main()