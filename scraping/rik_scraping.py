from lxml import html, etree
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

# # set up langdetect
# def get_lang_detector(nlp, name):
#     return LanguageDetector()

# # # load NLP models for entity recognition and langdetect
# nlp = spacy.load("en_core_web_sm")
# nlp2 = spacy.load("de_core_news_sm")
# Language.factory("language_detector", func=get_lang_detector)
# nlp.add_pipe('language_detector', last=True) 

def scrape(rik_num_current_events):

    db_host = os.environ.get('DB_HOST')
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')

    #connect to db
    conn = pymysql.connect(host=db_host,
                        user=db_user,
                        password=db_pass)

    c = conn.cursor()

    c.execute('''USE testdatabase''')

    for event in rik_num_current_events:
        # checks if event is already in database
        new_event = get_html.rik_html.tree().xpath('//*[@id="c51"]/div/div/a[' + str(event) + ']/div/div[1]/h4/span/text()')
        c.execute('''SELECT 1 FROM event_header WHERE name = %s''', (new_event,))
        if c.fetchone():
            print("Found RiK event!")
        # else: adds the new event to db, gets all the relevant info for building the LSC event 
        # and sends an email for review
        else:
            print("added one entry")
            header = new_event[0] # this will be one of the components for the HTML of the lsc event later
            print(header)
            dashboard.detected_event("Recht im Kontext", header)
            #set url to specific events page to retrieve details
            url_pt1 = "https://www.rechtimkontext.de/"
            url_pt2 = str(get_html.rik_html.tree().xpath('//*[@id=\"c51\"]/div/div/a[' + str(event) + ']/@href')[0])
            url = url_pt1 + url_pt2
            url7 = url
            r7 = requests.get(url7)
            tree7 = html.fromstring(r7.content, parser=html.HTMLParser(encoding="utf-8"))
            
            speaker_and_uni_raw1 = get_html.rik_html.tree().xpath('//*[@id="c51"]/div/div/a[' + str(event) + ']/div/div[2]/span/p[1]/text()')
            speaker_and_uni_raw2 = speaker_and_uni_raw1[0]
            speaker_and_uni = speaker_and_uni_raw2[:-1].split(" (")
            speaker = speaker_and_uni[0]
            uni = speaker_and_uni[1]
            
            # checks date
            date_tuple = get_html.rik_html.tree().xpath('normalize-space(//*[@id="c51"]/div/div/a[' + str(event) + ']/div/div[1]/h2/span/time/text())')
            date_comps = date_tuple.split(" ")
            
            date_day = date_comps[0][:-1]
            date_month = date_comps[1]
            date_year = date_comps[2]
            
            datetime_1 = datetime.date(int(date_year), int(parsing.convert_month(date_month)), int(date_day))
            rik_event_date = round((time.mktime(datetime_1.timetuple())))
            print(rik_event_date)
            
            event_time = tree7.xpath('//div[@class="teaser-text"]//p[2]/text()')[0]
            
            try:
                event_time_split = event_time.split("–")
                print(event_time)
                
                start_time = parsing.uk_time(event_time_split[0])
                end_time = parsing.uk_time(event_time_split[1])
                
                print(start_time)
                print(end_time)
                date_time = start_time + " to " + end_time + " p.m."
                
            except ValueError:
                date_time = event_time
                
            date = date_month + " " + date_day + " " + date_year + ", " + date_time
            print(date)

            # checks address
            address_raw = tree7.xpath('//div[@class="teaser-text"]//p[2]/text()')[2:-1]
            
            address_list = list()
            for event in address_raw:
                event = event[1:].replace(u'\xa0', u' ')
                address_list.append(event)
                
            delim = ", "
            address = delim.join(address_list)
            if "Zoom" or "online" or "Link" in address:
                address = "online"

            if speaker == "":
                speaker_html = ""
            else:
                speaker_html = "<p>Seminar with <strong>%s</strong>" % (speaker)
                
            # creates HTML block that will potentially be added to LSC later on
            html_block = '''<hr /><h3><a href="%s">%s</a></h3>
            <blockquote>
            <p>%s, %s (physical/virtual event)</p>
            <p>%s </p>
            <p>Hosted by Recht im Kontext</p>
            </blockquote>
            ''' % (url, header, date, address, speaker_html)
            print(url, header, date, address, speaker)
            
            rik_institution = "RIK"
            
            # add html block to upcoming events table
            
            c.execute('''INSERT INTO upcoming_events (html_insert, date, institution)
                        VALUES (%s, %s, %s)''', (html_block, rik_event_date, rik_institution, ))
            
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
