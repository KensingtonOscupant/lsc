from lxml import html, etree
import os
import pymysql
import requests
import get_html
import dashboard
import re
import datetime
import time
import parsing
import jellyfish
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
Language.factory("language_detector", func=get_lang_detector)
nlp.add_pipe('language_detector', last=True)

def scrape(num_current_events):

    for event in num_current_events:

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
        new_event = get_html.fuels_html.tree().xpath('//*[@id="current_events"]/div[' + str(event) + ']/div[1]/h3/a/text()[1]')
        c.execute('''SELECT 1 FROM event_header WHERE name = %s''', (new_event,))
        if c.fetchone():
            print("Found FUELS event!")
        # else: adds the new event to db, gets all the relevant info for building the LSC event 
        # and sends an email for review
        else:
            print("added one entry")
            header = new_event[0] # this will be one of the components for the HTML of the lsc event later
            dashboard.detected_event("FUELS", header)
            print(header)
            #set url to specific events page to retrieve details
            event_link = get_html.fuels_html.tree().xpath('//*[@id="current_events"]/div[' + str(event) + ']/div[1]/h3/a/@href')
            url = "https://www.jura.fu-berlin.de/" + event_link[0]
            r = requests.get(url)
            tree = html.fromstring(r.content, parser=html.HTMLParser(encoding="utf-8"))
            
            event_abstract = tree.xpath('string(//div[@class=\'editor-content box-event-doc-abstract\'])')
            doc = nlp(str(event_abstract))
            index = 0
            limit = 2
            
            # Note that the format that we store our info in on the event pages is not ideal
            # for NLP because there is no syntax (mostly "speaker (uni)"). This could obviously be done without
            # NLP with simple string operations, but it will be necessary for LSI later on so I did it for practice
            
            # generates all entities in this section
            ents = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents]
            # gets the first item of the first entity
            try:
                speaker = ents[0][0]
                print("speaker: " + speaker)
            except:
                print("no name found!")
                pass
            
            # checks if there is a second entity, which would be the uni
            try:
                uni = "(" + ents[1][0] + ")"
                words_ent1 = len(ents[0][0].split())
                ent_2 = words_ent1 + 1
                
                # if there is a second entity, it should be an organisation, i.e. the uni that is
                # right behind the speaker. If it isn't, e.g. because the uni name isn't recognized
                # but there are more speakers coming up, it checks if the uni is FU.
                if [doc[ent_2].ent_type_] != ['ORG']:
                    substr = "Freie Universität Berlin"
                    if (event_abstract[ents[0][1]:].find(substr) == -1):
                        pass
                    else:
                        uni = "(" + substr + ")"
                    print("This is not the uni!") # confusing and incorrect in case of the else
                # if the entity should be an organisation and directly follow the speaker, it is saved
                else:
                    print("uni: " + ents[1][0])
            except:
                # if there was no second entity in the first place, it might be FU. Note: This could be
                # optimized by just running a German spaCy model instead of the English one here.
                substr = "Freie Universität Berlin"
                if (event_abstract[ents[0][1]:].find(substr) == -1):
                    uni = ""
                # expl.: if it is not not FU, it must be FU
                else:
                    uni = "(" + substr + ")"
                print("no uni found!") # confusing and incorrect in case of the else
                pass
            
            # merging speaker and uni into one for now to ease modularization, might rename later

            speaker_mail2 = speaker + '</strong> ' + uni

            # checks date
            date_tuple = tree.xpath('//div[@class=\'box-event-doc-header-date col-m-4\']/text()')
            date = date_tuple[0]
            
            result = re.search(r".+?(2023)", date)
            date_string2 = result.group(0)
            
            date_slice1 = date_string2.split(", ")
            date_slice2 = date_slice1[0].split(" ")
            
            date_year = date_slice1[1]
            date_month = date_slice2[0]
            date_day = date_slice2[1]
            
            datetime_1 = datetime.date(int(date_year), int(parsing.convert_month(date_month)), int(date_day))
            fuels_event_date = round((time.mktime(datetime_1.timetuple())))
            print(fuels_event_date)
            
            # checks address
            address = tree.xpath('normalize-space(//p[@class=\'box-event-doc-location\'])')

            # prepare date for parsing (note: I could have done this above, but I didn't want to rewrite the code)
            date = date_tuple[0].replace(",", "")
            date = date.replace(" |", ",")

            # creates HTML block that will potentially be added to LSC later on
            html_block = '''<hr /><h3><a href="%s">%s</a></h3>
            <blockquote>
            <p>%s, %s (physical/virtual event)</p>
            <p>Seminar with <strong>%s</strong> %s</p>
            <p>Hosted by FUELS</p>
            </blockquote>
            ''' % (url, header, date, address, speaker, uni)
            print(url, header, date, address, speaker, uni)
            
            fuels_institution = "FUELS"
            
            # add html block to prospective events table
            
            c.execute('''INSERT INTO upcoming_events (html_insert, date, institution)
                        VALUES (%s, %s, %s)''', (html_block, fuels_event_date, fuels_institution, ))
            
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

            send_mail.send_review_mail(plaintext_mail=emails.institute_mail.plain_version, html_mail=emails.institute_mail.html_version, my_speaker=speaker, my_event=html_block, my_url=url, my_header=header, my_date=date, my_address=address, my_speaker_mail2=speaker_mail2)