# %%
from lxml import html, etree
import os
import pymysql
import spacy
import requests
import smtplib
import ssl
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import re
import datetime
import time
import calendar
import jellyfish
from spacy.language import Language
from spacy_langdetect import LanguageDetector
import certifi
from get_html import fuels_html, lsc_html, rik_html, lsi_current_events_html, lsi_past_events_html
from parsing import convert_month, convert_month_back, oxfordcomma, uk_time, extract_string_between_tags
from database_setup import check_no_of_tables, rebuild_db
from notifications import send_mail
from notifications import emails
import dashboard
from scraping.lsc_scraping import split_into_html_blocks
from scraping import fuels_scraping, rik_scraping

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_pass = os.environ.get('DB_PASS')
email_pass = os.environ.get('EMAIL_PASS')

#connect to db
conn = pymysql.connect(host=db_host,
                       user=db_user,
                       password=db_pass)

c = conn.cursor()

c.execute('''USE testdatabase''')

# this is just a remnant for where I have not refactored the code yet, will be removed soon
parser = html.HTMLParser(encoding="utf-8")

# set up SMTP and SSL requirements for email
port = 465
smtp_server = "smtp.gmail.com"
sender_email = "lsc.webservice@gmail.com"
password = email_pass

# set up langdetect
# def get_lang_detector(nlp, name):
#     return LanguageDetector()

# # load NLP models for entity recognition and langdetect
# nlp = spacy.load("en_core_web_sm")
# nlp2 = spacy.load("de_core_news_sm")
# Language.factory("language_detector", func=get_lang_detector)
# nlp.add_pipe('language_detector', last=True) 

# gets number of current or past events
def count_events_fuelsuntr(current_or_past):
    xpath_count = "count(//*[@id=\"" + current_or_past + "_events\"]/div)"
    count = round(fuels_html.tree().xpath(xpath_count))
    return count

# gets FUELS list with no. of titles of events (i bet there's a more efficient way to do this)
num_current_events = list(range(1, count_events_fuelsuntr("current")+1))
num_past_events = list(range(1, count_events_fuelsuntr("past")+1))

# gets LSI list with no. of titles of events
lsi_count_current_events = round(lsi_current_events_html.tree().xpath("count(//article)"))
lsi_count_past_events = round(lsi_past_events_html.tree().xpath("count(//article)"))
lsi_num_current_events = list(range(1, lsi_count_current_events))
lsi_num_past_events = list(range(1, lsi_count_past_events))

# acts accordingly.
if check_no_of_tables() == 6:
    print("All tables found!")
elif check_no_of_tables() < 6 and check_no_of_tables() >= 0:
    print("At least one table does not exist. All tables will be recreated.")
    
    # rebuilds the database
    rebuild_db()

    # splits existing HTML into blocks; also sends notification emails
    split_into_html_blocks()
     
else:
    print("Error: The number of tables does not make any sense. It is either smaller than 0 or greater than 5")


# main part of the program: monitors changes to events on the websites

# FUELS

fuels_scraping.scrape(num_current_events)

conn = pymysql.connect(host=db_host,
                    user=db_user,
                    password=db_pass)

c = conn.cursor()

c.execute('''USE testdatabase''')

# warning mechanism so that it does not exceed its capacity of max. 5 events stored at a time
# (this can be extended to any number if someone is willing to create the routing URLs for it)
c.execute('''SELECT active_slot FROM prospective_lsc_events WHERE slot_id = 14''')
tuple14 = c.fetchall()
c.execute('''SELECT active_slot FROM prospective_lsc_events WHERE slot_id = 15''')
tuple15 = c.fetchall()
checknum1 = tuple14[0][0]
checknum2 = tuple15[0][0]
checknum = checknum1 + checknum2

# sends email if 4/5 events are stored
if checknum == 1:
    print('''Es lässt sich nur noch eine Veranstaltung zwischenspeichern, bis der Arbeitsspeicher voll ist. Bitte entscheiden Sie über
    Veranstaltungen oder löschen Sie alle zwischengespeicherten Veranstaltungen hier.''')
    
# sends email if 5/5 events are stored
elif checknum == 2:
    print('''Speicher voll. Jede von jetzt an hinzugefügte Veranstaltung wird nicht ordnungsgemäß verarbeitet werden können,
            bis über zwischengespeicherte Veranstaltungen von FUELS, LSI und RiK entschieden worden ist.''')
    
else:
    print("alles im grünen Bereich")

# RiK

# gets list with no of titles of events (i bet there's a more efficient way to do this)
rik_count_num_current_events = round(rik_html.tree().xpath("count(//*[@id=\"c51\"]/div/div/a)"))
rik_count_num_past_events = round(rik_html.tree().xpath("count(//*[@id=\"c111\"]/div/div/a)"))
rik_num_current_events = list(range(1, rik_count_num_current_events+1))
rik_num_past_events = list(range(1, rik_count_num_past_events+1))

rik_scraping.scrape(rik_num_current_events)

conn = pymysql.connect(host=db_host,
                    user=db_user,
                    password=db_pass)

c = conn.cursor()

c.execute('''USE testdatabase''')
        
# warning mechanism so that it does not exceed its capacity of max. 5 events stored at a time
# (this can be extended to any number if someone is willing to create the routing URLs for it)
c.execute('''SELECT active_slot FROM prospective_lsc_events WHERE slot_id = 14''')
tuple14 = c.fetchall()
c.execute('''SELECT active_slot FROM prospective_lsc_events WHERE slot_id = 15''')
tuple15 = c.fetchall()
checknum1 = tuple14[0][0]
checknum2 = tuple15[0][0]
checknum = checknum1 + checknum2

# sends email if 4/5 events are stored
if checknum == 1:
    print('''Es lässt sich nur noch eine Veranstaltung zwischenspeichern, bis der Arbeitsspeicher voll ist. Bitte entscheiden Sie über
    Veranstaltungen oder löschen Sie alle zwischengespeicherten Veranstaltungen hier.''')
    
# sends email if 5/5 events are stored
elif checknum == 2:
    print('''Speicher voll. Jede von jetzt an hinzugefügte Veranstaltung wird nicht ordnungsgemäß verarbeitet werden können,
            bis über zwischengespeicherte Veranstaltungen von FUELS, LSI und RiK entschieden worden ist.''')
    
else:
    print("alles im grünen Bereich")
    
# LSI

for event in lsi_num_current_events:
    # checks if event is already in database
    new_event = lsi_current_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')
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
        event_link = lsi_current_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/@href')
        url = event_link[0]
        r = requests.get(url)
        tree = html.fromstring(r.content, parser=parser)
        
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
            event_link = lsi_current_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/@href')
            url5 = event_link[0]
            r5 = requests.get(url5)
            tree5 = html.fromstring(r5.content, parser=parser)
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
                speaker = oxfordcomma(speaker_names)
            else:
                speaker = ""
        
        print(speaker)
        speaker_db = speaker.replace("und", "and")
        
        date_day = lsi_current_events_html.tree().xpath('//span[@class=\'cal_day\']/text()')[event-1]
        date_month = lsi_current_events_html.tree().xpath('//span[@class=\'cal_month\']/text()')[event-1]
        date_year = lsi_current_events_html.tree().xpath('//span[@class=\'cal_year\']/text()')[event-1]
        print(date_day, date_month, date_year)
        
        month1 = convert_month(date_month)
        print(month1)
        datetime_1 = datetime.date(int(date_year), int(month1), int(date_day))
        lsi_event_date = round((time.mktime(datetime_1.timetuple())))
        print(lsi_event_date)
        
        url_event = url
        print(url_event)
        r_event = requests.get(url_event)
        tree_event = html.fromstring(r_event.content, parser=parser)
        
        start_time = tree_event.xpath('//abbr[@class="dtstart"]/text()')[0]

        if start_time == "\n      ":
            date = convert_month_back(month1) + " " + date_day + " " + date_year

        else:
            end_time = tree_event.xpath('//abbr[@class="dtend"]/text()')[0]
            print(start_time, end_time)
            
            formatted_start_time = uk_time(start_time)
            formatted_end_time = uk_time(end_time)
            
            date = convert_month_back(month1) + " " + date_day + " " + date_year + ", " + formatted_start_time + " to " + formatted_end_time + " p.m."

        # checks address
        address_lxml = lsi_current_events_html.tree().xpath('//span[@itemprop="address"]/text()[0]')
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
        
        conn = pymysql.connect(host=db_host,
                            user=db_user,
                            password=db_pass)

        c = conn.cursor()

        c.execute('''USE testdatabase''')
        
        # warning mechanism so that it does not exceed its capacity of max. 5 events stored at a time
        # (this can be extended to any number if someone is willing to create the routing URLs for it)
        c.execute('''SELECT active_slot FROM prospective_lsc_events WHERE slot_id = 14''')
        tuple14 = c.fetchall()
        c.execute('''SELECT active_slot FROM prospective_lsc_events WHERE slot_id = 15''')
        tuple15 = c.fetchall()
        checknum1 = tuple14[0][0]
        checknum2 = tuple15[0][0]
        checknum = checknum1 + checknum2
        
        # sends email if 4/5 events are stored
        if checknum == 1:
            print('''Es lässt sich nur noch eine Veranstaltung zwischenspeichern, bis der Arbeitsspeicher voll ist. Bitte entscheiden Sie über
            Veranstaltungen oder löschen Sie alle zwischengespeicherten Veranstaltungen hier.''')
            
        # sends email if 5/5 events are stored
        elif checknum == 2:
            print('''Speicher voll. Jede von jetzt an hinzugefügte Veranstaltung wird nicht ordnungsgemäß verarbeitet werden können,
                    bis über zwischengespeicherte Veranstaltungen von FUELS, LSI und RiK entschieden worden ist.''')
            
        else:
            print("alles im grünen Bereich")
    
# next: check all database entries against past events. If one appears there, it is deleted from the database
# for extra efficiency. Actually checking past events is not necessary (or smart) to update current events 
# I noticed later, but it might be worth keeping to automate moving events from the events homepage over to
# the past events page.

# creates a list with all past titles

# FUELS
past_events_titles = list()
for events in num_past_events:
    past_event = fuels_html.tree().xpath('//*[@id="past_events"]/div[' + str(events) + ']/div[1]/h3/a/text()[1]')
    past_events_titles.append(past_event[0])

# selects all database entries and gets their total number, which does not necessarily 
# coincide with the number of retrieved events above, and creates a list of these numbers
c.execute('''SELECT name FROM event_header 
             WHERE id IN 
             (SELECT id FROM upcoming_events
             WHERE institution = "FUELS");''')

current_events_tuples = c.fetchall()
list_num_db_entries = list(range(0, len(current_events_tuples)))

c.execute('''SELECT * FROM event_header''')
print(c.fetchall())

# checks headers of events in db against the past titles
# (meaning: checks if event was moved to FUELS archives)
for event in list_num_db_entries:
    # if the database entry is listed as a past event on the website: delete it
    print(current_events_tuples[event-1][0])
    if (current_events_tuples[event-1][0] in past_events_titles):
        print("This is a past event that will now be deleted from the database and moved to the archives.")
        delete_event = current_events_tuples[event-1][0]
        print(delete_event)
        c.execute('''DELETE FROM upcoming_events WHERE id =
                     (SELECT id FROM event_header
                     WHERE name = %s);''', (delete_event,))
        conn.commit()
        
    else:
        print("Event is at least not outdated (but has perhaps been deleted)")

# creates list of current titles
current_fuels_events = list()
for event in num_current_events:
    # checks if event is already in database
    new_event = fuels_html.tree().xpath('//*[@id="current_events"]/div[' + str(event) + ']/div[1]/h3/a/text()[1]')[0]
    current_fuels_events.append(new_event)
    
# this section needs to be run again because it might be outdated if events have been
# deleted in the step above
c.execute('''SELECT name FROM event_header 
             WHERE id IN 
             (SELECT id FROM upcoming_events
             WHERE institution = "FUELS");''')

current_events_tuples = c.fetchall()
list_num_db_entries = list(range(0, len(current_events_tuples)))
    
# checks headers of events in db against present titles
# (meaning: event was deleted and did not vanish because it was moved to the archive)
for event in list_num_db_entries:
    if (current_events_tuples[event-1][0] in current_fuels_events):
        print("Event from db is still current")
    else:
        print('''This event has been deleted from the website. 
        It will now be deleted from the database without being
        transferred to the archive.''')
        delete_event = current_events_tuples[event-1][0]
        print(delete_event)
        c.execute('''DELETE FROM upcoming_events WHERE id =
                     (SELECT id FROM event_header
                     WHERE name = %s);''', (delete_event,))
        conn.commit()

# LSI

past_events_titles = list()
for event in lsi_num_past_events:
    past_event = lsi_past_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')
    past_events_titles.append(past_event[0])

# selects all database entries and gets their total number, which does not necessarily 
# coincide with the number of retrieved events above, and creates a list of these numbers
c.execute('''SELECT name FROM event_header 
             WHERE id IN 
             (SELECT id FROM upcoming_events
             WHERE institution = "LSI");''')

current_events_tuples = c.fetchall()
list_num_db_entries = list(range(0, len(current_events_tuples)))

c.execute('''SELECT * FROM event_header''')
print(c.fetchall())

# checks headers of events in db against the past titles
# (meaning: checks if event was moved to FUELS archives)
for event in list_num_db_entries:
    # if the database entry is listed as a past event on the website: delete it
    print(current_events_tuples[event-1][0])
    if (current_events_tuples[event-1][0] in past_events_titles):
        print("This is a past event that will now be deleted from the database and moved to the archives.")
        delete_event = current_events_tuples[event-1][0]
        print(delete_event)
        c.execute('''DELETE FROM upcoming_events WHERE id =
                     (SELECT id FROM event_header
                     WHERE name = %s);''', (delete_event,))
        conn.commit()
        
    else:
        print("Event is at least not outdated (but has perhaps been deleted)")

# creates list of current titles
current_lsi_events = list()
for event in lsi_num_current_events:
    # checks if event is already in database
    new_event = lsi_current_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')[0]
    current_lsi_events.append(new_event)
print("list I'm searching for : " + str(current_lsi_events))
    
# this section needs to be run again because it might be outdated if events have been
# deleted in the step above
c.execute('''SELECT name FROM event_header 
             WHERE id IN 
             (SELECT id FROM upcoming_events
             WHERE institution = "LSI");''')

current_events_tuples = c.fetchall()
list_num_db_entries = list(range(0, len(current_events_tuples)))
    
# checks headers of events in db against present titles
# (meaning: event was deleted and did not vanish because it was moved to the archive)
for event in list_num_db_entries:
    if (current_events_tuples[event-1][0] in current_lsi_events):
        print("Event from db is still current")
    else:
        print('''This event has been deleted from the website. 
        It will now be deleted from the database without being
        transferred to the archive.''')
        delete_event = current_events_tuples[event-1][0]
        print(delete_event)
        c.execute('''DELETE FROM upcoming_events WHERE id =
                     (SELECT id FROM event_header
                     WHERE name = %s);''', (delete_event,))
        conn.commit()
        
# this is where RiK needs to be inserted

past_events_titles = list()
for event in rik_num_past_events:
    past_event = rik_html.tree().xpath('//*[@id="c111"]/div/div/a[' + str(event) + ']/@title')
    past_event = past_event[0].replace(u'\xa0', u' ')
    past_events_titles.append(past_event)

# selects all database entries and gets their total number, which does not necessarily 
# coincide with the number of retrieved events above, and creates a list of these numbers
c.execute('''SELECT name FROM event_header 
             WHERE id IN 
             (SELECT id FROM upcoming_events
             WHERE institution = "RIK");''')

current_events_tuples = c.fetchall()
list_num_db_entries = list(range(0, len(current_events_tuples)))

c.execute('''SELECT * FROM event_header''')
print(c.fetchall())

# checks headers of events in db against the past titles
# (meaning: checks if event was moved to FUELS archives)
for event in list_num_db_entries:
    # if the database entry is listed as a past event on the website: delete it
    print(current_events_tuples[event-1][0])
    if (current_events_tuples[event-1][0] in past_events_titles):
        print("This is a past event that will now be deleted from the database and moved to the archives.")
        delete_event = current_events_tuples[event-1][0]
        print(delete_event)
        c.execute('''DELETE FROM upcoming_events WHERE id =
                     (SELECT id FROM event_header
                     WHERE name = %s);''', (delete_event,))
        conn.commit()
        
    else:
        print("Event is at least not outdated (but has perhaps been deleted)")

# creates list of current titles
current_rik_events = list()
for event in rik_num_current_events:
    # checks if event is already in database (I think this is a wrong description)
    new_event = rik_html.tree().xpath('//*[@id="c51"]/div/div/a[' + str(event) + ']/@title')
    new_event = new_event[0].replace(u'\xa0', u' ')
    current_rik_events.append(new_event)
print("list I'm searching for : " + str(current_rik_events))
    
# this section needs to be run again because it might be outdated if events have been
# deleted in the step above
c.execute('''SELECT name FROM event_header 
             WHERE id IN 
             (SELECT id FROM upcoming_events
             WHERE institution = "RIK");''')

current_events_tuples = c.fetchall()
list_num_db_entries = list(range(0, len(current_events_tuples)))
    
# checks headers of events in db against present titles
# (meaning: event was deleted and did not vanish because it was moved to the archive)
for event in list_num_db_entries:
    if (current_events_tuples[event-1][0] in current_rik_events):
        print("Event from db is still current")
    else:
        print('''This event has been deleted from the website. 
        It will now be deleted from the database without being
        transferred to the archive.''')
        delete_event = current_events_tuples[event-1][0]
        print(delete_event)
        c.execute('''DELETE FROM upcoming_events WHERE id =
                     (SELECT id FROM event_header
                     WHERE name = %s);''', (delete_event,))
        conn.commit()

# updates db if there are changes in HTML on LSC page

# just general setup stuff to make everything current
parser = html.HTMLParser(encoding="utf-8")
url2 = "https://www.laws-of-social-cohesion.de/Events/index.html"
t = requests.get(url2)
tree2 = html.fromstring(t.content, parser=parser)
my_html = t.text

xpath_count = "count(//*[@class=\"editor-content hyphens\"]//h3)"
count = round(lsc_html.tree().xpath(xpath_count))
count_list = list(range(0, count-1))

c.execute('''SELECT html_insert FROM upcoming_events''')
before_html = c.fetchall()
print("before: " + str(before_html) + "\n \n \n")

# stores the HTML blocks of the different events, same as above
lsc_events = list()

## creates list of current html blocks on the LSC website, same as above 
# but current because things might change in between
# note: I am not sure if the class method will run once more here or take the original value.
# if the latter should be the case, this won't work anymore.
soup = BeautifulSoup(lsc_html.fulltext(), "html.parser")
data = soup.find_all("div", {"class" : "editor-content hyphens"})
data_string = str(data[0])
soup = BeautifulSoup(''.join(data_string))
for i in soup.prettify().split('events')[1].split('<hr/>'):
    lsc_events.append('<hr/>' + ''.join(i))
    
    
# this section needs to be run again because it might be outdated if events have been
# deleted in the process of running this script
c.execute('''SELECT html_insert FROM upcoming_events 
             WHERE id IN 
             (SELECT id FROM lsc_events);''')

current_db_events_tuples = c.fetchall()
list_num_db_entries = list(range(0, len(current_db_events_tuples)))

db_events_list = list()
for event in list_num_db_entries:
    db_events_list.append(current_db_events_tuples[event-1][0])

for page_event in lsc_events[1:-1]:
    interim_list = list()
    for db_event in db_events_list:
        print(jellyfish.jaro_distance(page_event, db_event))
        interim_list.append(jellyfish.jaro_distance(page_event, db_event))
    meta_lst = sorted(((value, index) for index, value in enumerate(interim_list)), reverse=True)
    print(meta_lst)
    #print("the highest number is: " + db_events_list[meta_lst[0][1]])
    for event in interim_list:
        if 1.0 in interim_list:
            print("event has not been updated")
        else:
            print("No exact match found. The database entry with the highest similarity will be substituted.")
            c.execute('''UPDATE upcoming_events
                         SET html_insert = %s
                         WHERE html_insert = %s''',
                         (page_event, db_events_list[meta_lst[0][1]]))
        
c.execute('''SELECT * FROM upcoming_events''')
datatest_upcoming = c.fetchall()
c.execute('''SELECT * FROM prospective_lsc_events;''')
datatest_html = c.fetchall()
c.execute('''SELECT * FROM lsc_events;''')
datatest_lsc = c.fetchall()
print(datatest_upcoming)
print(datatest_html)
print(datatest_lsc)

conn.commit()
conn.close()

# %%



