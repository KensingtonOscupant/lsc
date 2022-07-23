from lxml import html, etree
from bs4 import BeautifulSoup
import re
import get_html
import os
import pymysql
import dashboard
import requests
import datetime
import parsing
import time
import spacy
from spacy.language import Language
from spacy_langdetect import LanguageDetector
from notifications import send_mail, emails

# set up langdetect (move all NLP stuff into one class later)
def get_lang_detector(nlp, name):
    return LanguageDetector()

# load NLP models for entity recognition and langdetect
nlp = spacy.load("en_core_web_sm")
nlp2 = spacy.load("de_core_news_sm")
Language.factory("language_detector_v2", func=get_lang_detector)
nlp.add_pipe('language_detector_v2', last=True)

def scrape(lsi_num_current_events):
    for event in lsi_num_current_events:

        db_host = os.environ.get('DB_HOST')
        db_user = os.environ.get('DB_USER')
        db_pass = os.environ.get('DB_PASS')

        #connect to db
        conn = pymysql.connect(host=db_host,
                            user=db_user,
                            password=db_pass)

        c = conn.cursor()

        c.execute('''USE testdatabase''')

        # checks if event is already in database
        new_event = get_html.lsi_current_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')
        c.execute('''SELECT 1 FROM event_header WHERE name = %s''', (new_event,))
        if c.fetchone():
            print("Found LSI event!")
        # else: adds the new event to db, gets all the relevant info for building the LSC event 
        # and sends an email for review
        else:
            print("added one entry")
            header = new_event[0] # this will be one of the components for the HTML of the lsc event later
            dashboard.detected_event("LSI", header)
            print(header)
            #set url to specific events page to retrieve details
            event_link = get_html.lsi_current_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/@href')
            url = event_link[0]
            r = requests.get(url)
            tree = html.fromstring(r.content, parser=html.HTMLParser(encoding="utf-8"))
            
            new_event_split = new_event[0].split(":")
            speaker = new_event_split[0]
            print(speaker)
            doc2 = nlp(speaker)
            if doc2._.language["language"] == "de":
                #print("German detected!")
                doc3 = nlp2(speaker)
                persons = [ent.text for ent in doc3.ents if ent.label_ == 'PER']
            else:
                #print("English or any other language detected!")
                persons = [ent.text for ent in doc2.ents if ent.label_ == 'PERSON']
            try:
                speaker = persons[0]
            # if it doesn't find any names, that is most likely because several people
            # are never listed in the title of HU events. Instead, they are mentioned...somewhere.
            # often in bold. The program does not try to find them too desperately; if they are
            # not there, they are simply left out.
            except IndexError:
                print("no name detected")
                event_link = get_html.lsi_current_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/@href')
                url5 = event_link[0]
                r5 = requests.get(url5)
                tree5 = html.fromstring(r5.content, parser=html.HTMLParser(encoding="utf-8"))
                my_html5 = r5.text
        
                soup = BeautifulSoup(my_html5, "html.parser")
                data = soup.find_all("div", {"id" : "parent-fieldname-text"})
                data_string = str(data[0])
                #print(data_string)
        
                soup = BeautifulSoup(data_string, "html.parser")
                speaker_names = list()
                
                for element in soup.find_all('strong'):
                    result = re.search(r"\w+.+\w+", str(element.text))
                    speaker_names.append(result.group(0))
                if len(speaker_names) > 1:
                    print("multiple speakers!")
                    speaker = parsing.oxfordcomma(speaker_names)
                else:
                    speaker = ""
            
            print(speaker)
            speaker_db = speaker.replace("und", "and")
            
            date_day = get_html.lsi_current_events_html.tree().xpath('//span[@class=\'cal_day\']/text()')[event-1]
            date_month = get_html.lsi_current_events_html.tree().xpath('//span[@class=\'cal_month\']/text()')[event-1]
            date_year = get_html.lsi_current_events_html.tree().xpath('//span[@class=\'cal_year\']/text()')[event-1]
            print(date_day, date_month, date_year)
            
            month1 = parsing.convert_month(date_month)
            print(month1)
            datetime_1 = datetime.date(int(date_year), int(month1), int(date_day))
            lsi_event_date = round((time.mktime(datetime_1.timetuple())))
            print(lsi_event_date)
            
            url_event = url
            print(url_event)
            r_event = requests.get(url_event)
            tree_event = html.fromstring(r_event.content, parser=html.HTMLParser(encoding="utf-8"))
            
            start_time = tree_event.xpath('//abbr[@class="dtstart"]/text()')[0]

            if start_time == "\n      ":
                date = parsing.convert_month_back(month1) + " " + date_day + " " + date_year

            else:
                end_time = tree_event.xpath('//abbr[@class="dtend"]/text()')[0]
                print(start_time, end_time)
                
                formatted_start_time = parsing.uk_time(start_time)
                formatted_end_time = parsing.uk_time(end_time)
                
                date = parsing.convert_month_back(month1) + " " + date_day + " " + date_year + ", " + formatted_start_time + " to " + formatted_end_time + " p.m."

            # checks address
            address_lxml = get_html.lsi_current_events_html.tree().xpath('//span[@itemprop="address"]/text()[0]')
            address = str(address_lxml)
            print(address)
            if "Zoom" or "online" or "Link" in address:
                address = "online"

            if speaker == "":
                speaker_html = ""
            else:
                speaker_html = "<p>Seminar with <strong>%s</strong>" % (speaker_db)
                
            # creates HTML block that will potentially be added to LSC later on
            html_block = '''<hr /><h3><a href="%s">%s</a></h3>
            <blockquote>
            <p>%s, %s (physical/virtual event)</p>
            <p>%s </p>
            <p>Hosted by LSI</p>
            </blockquote>
            ''' % (url, header, date, address, speaker_html)
            print(url, header, date, address, speaker)
            
            lsi_institution = "LSI"
            
            # add html block to upcoming events table
            
            c.execute('''INSERT INTO upcoming_events (html_insert, date, institution)
                        VALUES (%s, %s, %s)''', (html_block, lsi_event_date, lsi_institution, ))
            
            c.execute('''SELECT id FROM upcoming_events
                        WHERE html_insert = %s''', (html_block, ))
            
            current_id = c.fetchall()[0]

            c.execute('''INSERT INTO event_header (id, name) 
                        VALUES (%s, %s)''', (current_id, new_event,)) # might also be new_event[0], i.e. header
            
            c.execute('''UPDATE prospective_lsc_events 
                        SET id = 
                        (SELECT id FROM upcoming_events 
                        WHERE html_insert = %s), 
                        active_slot = 1 
                        WHERE 
                        active_slot = 0 
                        LIMIT 1;''', (html_block,))
            conn.commit()
            
            conn.close()

            # this is a relic, still needs to be modularized. Handles one speaker vs multiple ones
            if speaker == "":
                speaker_mail = ""
                speaker_mail2 = ""
            else:
                speaker_mail = "mit " + speaker
                speaker_mail2 = "Seminar with <strong>%s</strong>" % (speaker)

            send_mail.send_review_mail(plaintext_mail=emails.institute_mail.plain_version, html_mail=emails.institute_mail.html_version, my_speaker=speaker_mail, my_event=html_block, my_url=url, my_header=header, my_date=date, my_address=address, my_speaker_mail2=speaker_mail2)