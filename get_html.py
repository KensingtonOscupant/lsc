from lxml import html, etree
import requests

"""Requests the HTML tree and the HTML as text for the page of the respective institute."""

class InstituteHTML:

    my_parser = html.HTMLParser(encoding="utf-8")

    def __init__(self, url):
        self.url = url

    def tree(self):
        parser = self.my_parser
        r = requests.get(self.url)
        tree = html.fromstring(r.content, parser=parser)
        return tree

    def fulltext(self):
        parser = self.my_parser
        r = requests.get(self.url)
        fulltext = r.text
        return fulltext

fuels_html = InstituteHTML('https://www.jura.fu-berlin.de/en/forschung/fuels/Upcoming/index.html')
lsc_html = InstituteHTML('https://www.laws-of-social-cohesion.de/Events/index.html')
rik_html = InstituteHTML('https://www.rechtimkontext.de/veranstaltungen/')
lsi_current_events_html = InstituteHTML('https://www.rewi.hu-berlin.de/de/lf/oe/lsi/event_listing?mode=future')
lsi_past_events_html = InstituteHTML('https://www.rewi.hu-berlin.de/de/lf/oe/lsi/event_listing?mode=past')