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
import boto3
from selenium import webdriver
from tempfile import mkdtemp

# added from docker setup
options = webdriver.ChromeOptions()
options.binary_location = '/opt/chrome/chrome'
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280x1696")
options.add_argument("--single-process")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-dev-tools")
options.add_argument("--no-zygote")
options.add_argument(f"--user-data-dir={mkdtemp()}")
options.add_argument(f"--data-path={mkdtemp()}")
options.add_argument(f"--disk-cache-dir={mkdtemp()}")
options.add_argument("--remote-debugging-port=9222")
""" chrome = webdriver.Chrome("/opt/chromedriver",
                            options=options) """

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

# S3 setup
key = 'items.csv'
bucket = 'lsc-mailbucket'
s3_resource = boto3.resource('s3')
s3_object = s3_resource.Object(bucket, key)
data = s3_object.get()['Body'].read().decode('utf-8').splitlines()
    
lines = csv.reader(data)
headers = next(lines)

# just for debugging, remove later
#c.execute("DELETE FROM upcoming_events WHERE id > 0")
#c.execute('''UPDATE prospective_lsc_events 
#          SET html_insert = "None", 
#          active_slot = 0 WHERE id > 0''')

# set up HTTP requests and XML processing
# fuels:
parser = html.HTMLParser(encoding="utf-8")
url = "https://www.jura.fu-berlin.de/en/forschung/fuels/Upcoming/index.html"
r = requests.get(url)
tree = html.fromstring(r.content, parser=parser)

# LSC:
url2 = "https://www.laws-of-social-cohesion.de/Events/index.html"
t = requests.get(url2)
tree2 = html.fromstring(t.content, parser=parser)
my_html = t.text

# rik:
# current events
parser = html.HTMLParser(encoding="utf-8")
url6 = "https://www.rechtimkontext.de/veranstaltungen/"
r6 = requests.get(url6)
tree6 = html.fromstring(r6.content, parser=parser)

#past events # is this necessary if they are both on the same page?
url4 = "https://www.rewi.hu-berlin.de/de/lf/oe/lsi/event_listing?mode=past"
r4 = requests.get(url4)
tree4 = html.fromstring(r4.content, parser=parser)

# lsi:
# current events
url3 = "https://www.rewi.hu-berlin.de/de/lf/oe/lsi/event_listing?mode=future"
r3 = requests.get(url3)
tree3 = html.fromstring(r3.content, parser=parser)

#past events on LSI, important for moving to archive
url4 = "https://www.rewi.hu-berlin.de/de/lf/oe/lsi/event_listing?mode=past"
r4 = requests.get(url4)
tree4 = html.fromstring(r4.content, parser=parser)

# set up SMTP and SSL requirements for email
port = 465
smtp_server = "smtp.gmail.com"
sender_email = "lsc.webservice@gmail.com"
password = email_pass

# set up langdetect in function (necessary)
def get_lang_detector(nlp, name):
    return LanguageDetector()

# getting the names in the LSC review email right even if there are multiple ones:
def oxfordcomma(listed):
    if len(listed) == 0:
        return ''
    if len(listed) == 1:
        return listed[0]
    if len(listed) == 2:
        return listed[0] + ' und ' + listed[1]
    return ', '.join(listed[:-1]) + ' und ' + listed[-1]

# gets number of current or past events
def count_events_fuelsuntr(current_or_past):
    xpath_count = "count(//*[@id=\"" + current_or_past + "_events\"]/div)"
    count = round(tree.xpath(xpath_count))
    return count

# this definitely needs to be optimised
def convert_month(month):
    if month == "Jan" or month == "Januar":
        return "01"
    if month == "Feb" or month == "Februar":
        return "02"
    if month == "Mar" or month == "März":
        return "03"
    if month == "Apr" or month == "April":
        return "04"
    if month == "May" or month == "Mai":
        return "05"
    if month == "Jun" or month == "Juni":
        return "06"
    if month == "Jul" or month == "Juli":
        return "07"
    if month == "Aug" or month == "August":
        return "08"
    if month == "Sep" or month == "September":
        return "09"
    if month == "Oct" or month == "Oktober":
        return "10"
    if month == "Nov" or month == "November":
        return "11"
    if month == "Dec" or month == "Dezember":
        return "12"

def uk_time(timestamp):
    uk_time_split = timestamp.split(":")
    uk_time_result = str(int(uk_time_split[0]) - 12) + ":" + str(uk_time_split[1])
    return uk_time_result

def convert_month_back(month_num):
    if month_num == "01":
        return "Jan"
    if month_num == "02":
        return "Feb"
    if month_num == "03":
        return "Mar"
    if month_num == "04":
        return "Apr"
    if month_num == "05":
        return "May"
    if month_num == "06":
        return "Jun"
    if month_num == "07":
        return "Jul"
    if month_num == "08":
        return "Aug"
    if month_num == "09":
        return "Sep"
    if month_num == "10":
        return "Oct"
    if month_num == "11":
        return "Nov"
    if month_num == "12":
        return "Dec"

# load NLP models for entity recognition and langdetect
nlp = spacy.load("en_core_web_sm")
nlp2 = spacy.load("de_core_news_sm")
Language.factory("language_detector", func=get_lang_detector)
nlp.add_pipe('language_detector', last=True)    

# gets FUELS list with no. of titles of events (i bet there's a more efficient way to do this)
num_current_events = list(range(1, count_events_fuelsuntr("current")+1))
num_past_events = list(range(1, count_events_fuelsuntr("past")+1))

# gets LSI list with no. of titles of events
lsi_count_current_events = round(tree3.xpath("count(//article)"))
lsi_count_past_events = round(tree4.xpath("count(//article)"))
lsi_num_current_events = list(range(1, lsi_count_current_events))
lsi_num_past_events = list(range(1, lsi_count_past_events))

# email links to accept page for LSC events

def generateAcceptLink(upcoming_id):
    return "https://lscwebservice.com/polls/" + str(upcoming_id) + "/accept/"

def generateDenyLink(upcoming_id):
    return "https://lscwebservice.com/polls/" + str(upcoming_id) + "/deny/"

#sets up check for couting how many of the relevant tables exist
c.execute('''SELECT count(*) FROM information_schema.tables WHERE table_name = 'upcoming_events' ''')
table1 = c.fetchall()[0][0]
c.execute('''SELECT count(*) FROM information_schema.tables WHERE table_name = 'prospective_lsc_events';''')
table2 = c.fetchall()[0][0]
c.execute('''SELECT count(*) FROM information_schema.tables WHERE table_name = 'lsc_events';''')
table3 = c.fetchall()[0][0]
c.execute('''SELECT count(*) FROM information_schema.tables WHERE table_name = 'event_header';''')
table4 = c.fetchall()[0][0]
c.execute('''SELECT count(*) FROM information_schema.tables WHERE table_name = 'num_lsc_events';''')
table5 = c.fetchall()[0][0]

project_tables = table1 + table2 + table3 + table4 + table5 -1

# acts accordingly.
if project_tables == 5:
    print("All tables found!")
elif project_tables < 5 and project_tables >= 0:
    print("At least one table does not exist. All tables will be recreated.")
    
    # deletes tables if they exist (respectively)
    c.execute('''SET foreign_key_checks = 0''')
    c.execute("DROP TABLE IF EXISTS upcoming_events")
    c.execute("DROP TABLE IF EXISTS prospective_lsc_events;")
    c.execute("DROP TABLE IF EXISTS lsc_events;")
    c.execute("DROP TABLE IF EXISTS event_header;")
    c.execute("DROP TABLE IF EXISTS num_lsc_events;")
    
    # it would be more efficient to do execute the following queries in one executemany() statement,
    # but that would make it impossible to create debug messages in between which I think is more important
    
    # creates upcoming events table
    c.execute('''CREATE TABLE upcoming_events(
                ID INT PRIMARY KEY AUTO_INCREMENT, 
                html_insert TEXT,
                date INT(11),
                institution VARCHAR(5))''')
    print("created upcoming events table")
    
    # creates prospective LSC events table and sets it up correctly
    c.execute('''CREATE TABLE prospective_lsc_events(
                slot_id INT AUTO_INCREMENT,
                id INT,
                active_slot BOOLEAN NOT NULL DEFAULT 0,
                routing_url_pos VARCHAR(255),
                routing_url_neg VARCHAR(255),
                PRIMARY KEY (slot_id),
                CONSTRAINT fk__prospective_lsc_events__upcoming_events
                    FOREIGN KEY (id)
                    REFERENCES upcoming_events(id)
                    ON DELETE SET NULL);''')
    print("created lsc prospective events table")
    
    c.execute('''INSERT INTO prospective_lsc_events (routing_url_pos, routing_url_neg) 
             VALUES 
             ("a", "a"),
             ("b", "b"),
             ("c", "c"),
             ("d", "d"),
             ("e", "e"),
             ("f", "f"),
             ("g", "g"),
             ("h", "h"),
             ("i", "i"),
             ("j", "j"),
             ("k", "k"),
             ("l", "l"),
             ("m", "m"),
             ("n", "n"),
             ("o", "o");''') # 15 slots, five per institution. This is the "RAM" of the program.
                        # Perhaps there is a more elegant way to solve this.
    print("populated LSC prospective events table")
    
    # creates LSC events table
    c.execute('''CREATE TABLE lsc_events(
                id INT,
                timestamp INT(11),
                CONSTRAINT fk__lsc_events__upcoming_events
                    FOREIGN KEY (id)
                    REFERENCES upcoming_events(id)
                    ON DELETE CASCADE);''')
    print("created LSC events table")

    # creates table to keep track of number of LSC events

    c.execute('''CREATE TABLE num_lsc_events(
                id INT PRIMARY KEY AUTO_INCREMENT,
                num_events INT(11));''')
    
    # add one entry with 0 to num_lsc_events table

    c.execute('''INSERT INTO num_lsc_events (num_events) VALUES (0);''')

    # stores the HTML blocks of the different events
    lsc_events = list()
    
    # the following section runs the initial check on the LSC events that already exist
    # parses HTML to create these blocks and insert them into the list lsc_events
    soup = BeautifulSoup(my_html, 'html.parser')
    data = soup.find_all("div", {"class" : "editor-content hyphens"})
    data_string = str(data[0])
    soup = BeautifulSoup(''.join(data_string), 'html.parser')
    for i in soup.prettify().split('events')[1].split('<hr/>'):
        lsc_events.append('<hr/>' + ''.join(i))
    
    k = 0
    for event in lsc_events[1:-1]:
        # checks if event is already in database
        k += 1
        c.execute('''SELECT 1 FROM upcoming_events WHERE html_insert = %s''', (event,))
        if c.fetchone():
            print("Found LSC event!")
        else:
            print("added one entry")
            # insert into db
            date_list = tree2.xpath('//div[@class=\'content-wrapper main horizontal-bg-container-main\']//blockquote[' + str(k) + ']/p[1]/text()')
            date_split = date_list[0].split(",")
            lsc_event_date_unformatted = str(date_split[0])
            lsc_institution = "LSC"
            lsc_event_date_comp = lsc_event_date_unformatted.split(" ")
            datetime_1 = datetime.date(int(lsc_event_date_comp[2]), int(convert_month(lsc_event_date_comp[0])), int(lsc_event_date_comp[1]))
            lsc_event_date = round((time.mktime(datetime_1.timetuple())))
            c.execute('''INSERT INTO upcoming_events (html_insert, date, institution) VALUES (%s, %s, %s)''', (event, lsc_event_date, lsc_institution, ))
            c.execute('''INSERT INTO lsc_events (id) VALUES(
                         (SELECT id FROM upcoming_events 
                         WHERE html_insert = %s))''',
                         (event, ))
            c.execute('''UPDATE prospective_lsc_events SET id = (
                         (SELECT id FROM upcoming_events 
                         WHERE html_insert = %s)),
                         active_slot = 1
                         WHERE active_slot = 0 
                         ORDER BY active_slot DESC LIMIT 1''',
                         (event, ))
            conn.commit()
            
            # parses the blocks for the names of the speakers to be used **only** in the review email.
            # inaccuracies here do not affect the result on the website.
            # general note: regex should only be used as a last resort (especially if lxml is an option).
            # I couldn't think of anything more efficient in this case though. Hence, this could be 
            # optimized by getting rid of the regex below.

            soup = BeautifulSoup(event, "html.parser")
            speaker_names = list()
            for element in soup.find_all('strong'):
                result = re.search(r"\w+.+\w+", str(element.text))
                speaker_names.append(result.group(0))
            if len(speaker_names) > 1:
                print("multiple speakers!")
                speaker = oxfordcomma(speaker_names)
                print(speaker)
            else:
                print("one speaker")
                speaker = oxfordcomma(speaker_names)
                print(speaker)  

            # get current id of event from upcoming_events table

            def get_id(event):
                c.execute('''SELECT id FROM upcoming_events WHERE html_insert = %s''', (event,))
                return c.fetchone()[0]

            # sends the review email to the reviewer of the institution
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                server.login(sender_email, password)
                with open("items.csv") as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip header row
                    for name, email in reader:
                        
                        # excludes people on the CSV. Since this email is for a FUELS event,
                        # it is not relevant for LSI. It would be more elegant to also store this
                        # in a database, but a CSV is easier for now, might change later
                        if name == "Feneberg":
                            continue
                        
                        # note in case anyone should ever edit this: The following %s are used as normal
                        # string manipulation placeholders. Although the %s in the MySQL queries in this script
                        # look almost the same, they are used for parameter substitution and it is important to 
                        # understand this difference as using string manipulation in SQL queries makes them vulnerable
                        # to SQL injection attacks. Have a very close look at the difference in usage.
                        
                        text_version = '''\
                        Lieber Herr %s,
                        (das ist die plain-text version der Email, bei Gelegenheit noch ergänzen)
                        Dies ist eine LSC-Testmail für
                        www.laws-of-social-cohesion.de''' % (name)
                        
                        # general note on how emails work: if you receive an email with formatting, 
                        # it always comes in two versions: plain text (above)
                        # and HTML. This is necessary, only HTML is not accepted. The plain-text version is rendered first.
                        html_version = '''\
                        <html>
                            <body>
                            <p>Sehr geehrter Herr %s,<br>
                                <br>
                                wir aktualisieren gerade die Events auf der Seite des Projekts "Laws of Social Cohesion" und mir ist 
                                aufgefallen, dass dort eine Veranstaltung mit %s gelistet ist. Es wäre für mich wichtig zu erfahren, ob diese
                                Veranstaltung als "Hosted by LSI/FUELS/RiK" gekennzeichnet wurde. Wenn das der Fall ist, würde ich mich freuen,
                                wenn Sie mich darüber hier informieren könnten. Bitte folgen Sie dem Link auch dann, wenn die Veranstaltung
                                nicht von den einer der drei Partnerinstitutionen ausgerichtet werden sollte und Sie die Veranstaltung nicht
                                weiter auf der Website führen möchten (z. B. weil die Veranstaltung veraltet ist).
                                Soll ich die Meldung beibehalten, würde ich sie in folgender Form auf der Website aufführen:<br>
                                %s 
                                Sollten die Meldung entfernt werden, klicken Sie bitte <a href="%s">hier</a>. Sollten anderweitige Probleme
                                bestehen, helfe ich immer gerne.<br>
                                <br>
                                <br>
                                Mit freundlichen Grüßen,<br>
                                Ihr Benjamin Mantay<br>
                                <br>
                                -------------<br>
                                <a href="https://www.jura.fu-berlin.de/fachbereich/einrichtungen/zivilrecht/lehrende/engerta/Team/5_Externe-Wissenschaftler_innen/Benji">Dr. can. Benjamin Mantay</a> <br>
                                Head of IT und Tierischer Wissenschaftler (Postdog) am Lehrstuhl Engert<br>
                                <br>
                                <br>
                                <br>
                            </p>
                            </body>
                        </html>
                        ''' % (name, speaker, event, generateDenyLink(get_id(event)))
                        
                        message = MIMEMultipart("alternative")
                        message["Subject"] = "LSC | Veranstaltung mit %s" % (speaker)
                        message["From"] = sender_email
                        message["To"] = email
                        
                        # Turn strings into plain/html MIMEText objects
                        part1 = MIMEText(text_version, "plain")
                        part2 = MIMEText(html_version, "html")
                        
                        # Add HTML/plain-text parts to MIMEMultipart message
                        # The email client will try to render the last part first
                        message.attach(part1)
                        message.attach(part2)
                        server.sendmail(
                            sender_email,
                            email,
                            message.as_string(),
                        )
                
    # creates FUELS event header
    c.execute('''CREATE TABLE event_header(
                id INT,
                name VARCHAR(255),
                CONSTRAINT fk__event_header__upcoming_events
                    FOREIGN KEY (id)
                    REFERENCES upcoming_events(id)
                    ON DELETE CASCADE);''')
    print("created FUELS event header table")
    
    # this trigger resets active slots in prospective events if an event
    # gets deleted in the upcoming table
    c.execute('''CREATE TRIGGER reset_active_slot 
             BEFORE DELETE ON upcoming_events
             FOR EACH ROW
             UPDATE prospective_lsc_events SET active_slot = 0
             WHERE id = OLD.id''')
     
else:
    print("Error: The number of tables does not make any sense. It is either smaller than 0 or greater than 5")


# main part of the program: monitors changes to events on the websites 

lines = csv.reader(data) # these two lines

# FUELS
for event in num_current_events:
    # checks if event is already in database
    new_event = tree.xpath('//*[@id="current_events"]/div[' + str(event) + ']/div[1]/h3/a/text()[1]')
    c.execute('''SELECT 1 FROM event_header WHERE name = %s''', (new_event,))
    if c.fetchone():
        print("Found FUELS event!")
    # else: adds the new event to db, gets all the relevant info for building the LSC event 
    # and sends an email for review
    else:
        print("added one entry")
        header = new_event[0] # this will be one of the components for the HTML of the lsc event later
        print(header)
        #set url to specific events page to retrieve details
        event_link = tree.xpath('//*[@id="current_events"]/div[' + str(event) + ']/div[1]/h3/a/@href')
        url = "https://www.jura.fu-berlin.de/" + event_link[0]
        r = requests.get(url)
        tree = html.fromstring(r.content, parser=parser)
        
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
        
        # checks date
        date_tuple = tree.xpath('//div[@class=\'box-event-doc-header-date col-m-4\']/text()')
        date = date_tuple[0]
        
        result = re.search(r".+?(2022)", date)
        date_string2 = result.group(0)
        
        date_slice1 = date_string2.split(", ")
        date_slice2 = date_slice1[0].split(" ")
        
        date_year = date_slice1[1]
        date_month = date_slice2[0]
        date_day = date_slice2[1]
        
        datetime_1 = datetime.date(int(date_year), int(convert_month(date_month)), int(date_day))
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
        
        # send emails for review before upload on LSC
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, password)
            with open("items.csv") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                for name, email in reader:
                    
                    # excludes people on the CSV. Since this email is for a FUELS event,
                    # it is not relevant for LSI. It would be more elegant to also store this
                    # in a database, but a CSV is easier for now, might change later
                    if name == "Feneberg":
                        continue
                    
                    # note in case anyone should ever edit this: The following %s are used as normal
                    # string manipulation placeholders. Although the %s in the MySQL queries in this script
                    # look almost the same, they are used for parameter substitution and it is important to 
                    # understand this difference as using string manipulation in SQL queries makes them vulnerable
                    # to SQL injection attacks. Have a very close look at the difference in usage.
                    
                    text_version = '''\
                    Lieber Herr %s,
                    (das ist die plain-text version der Email, bei Gelegenheit noch ergänzen)
                    Dies ist eine LSC-Testmail für
                    www.laws-of-social-cohesion.de''' % (name)
                    
                    # general note on how emails work: if you receive an email with formatting, 
                    # it always comes in two versions: plain text (above)
                    # and HTML. This is necessary, only HTML is not accepted. The plain-text version is rendered first.
                    html_version = '''\
                    <html>
                        <body>
                        <p>Sehr geehrter Herr %s,<br>
                            <br>
                            eben ist mir aufgefallen, dass heute eine Veranstaltung mit %s auf der
                            Website gelistet wurde. Soll ich das Event auf die LSC-Seite übertragen? Falls ja, würde ich die Meldung
                            folgendermaßen gestalten:<br>
                            <h3><a href="%s">%s</a></h3>
                                    <blockquote>
                                    <p>%s, %s (physical/virtual event)</p>
                                    <p>Seminar with <strong>%s</strong> %s</p>
                                    <p>Hosted by FUELS</p>
                                    </blockquote>
                            Wenn diese Veranstaltung nicht der LSC-Seite hinzugefügt werden soll, klicken Sie bitte <a href="%s">hier</a>. 
                            Möchten Sie die Meldung in ihrer jetzigen Form annehmen, klicken Sie bitte <a href="%s">hier</a>. Sollten Sie die 
                            Meldung hochladen wollen, die Meldung aber fehlerhaft sein, können Sie mich darüber per Klick hier 
                            informieren. Sie brauchen sonst nichts weiter zu unternehmen. Ich lade sie dann später korrigiert hoch 
                            und lasse davor noch einmal einen Menschen einen Blick darauf werfen. Sollten anderweitige Probleme 
                            bestehen, helfe ich immer gerne.<br>
                            <br>
                            <br>
                            Mit freundlichen Grüßen,<br>
                            Ihr Benjamin Mantay<br>
                            <br>
                            -------------<br>
                            <a href="https://www.jura.fu-berlin.de/fachbereich/einrichtungen/zivilrecht/lehrende/engerta/Team/5_Externe-Wissenschaftler_innen/Benji">Dr. can. Benjamin Mantay</a> <br>
                            Head of IT und Tierischer Wissenschaftler (Postdog) am Lehrstuhl Engert<br>
                            <br>
                            <br>
                            <br>
                        </p>
                        </body>
                    </html>
                    ''' % (name, speaker, url, header, date, address, speaker, uni, generateDenyLink(current_id[0]), generateAcceptLink(current_id[0]))
                    
                    message = MIMEMultipart("alternative")
                    message["Subject"] = "LSC | Veranstaltung mit %s" % (speaker)
                    message["From"] = sender_email
                    message["To"] = email
                    
                    # Turn strings into plain/html MIMEText objects
                    part1 = MIMEText(text_version, "plain")
                    part2 = MIMEText(html_version, "html")
                    
                    # Add HTML/plain-text parts to MIMEMultipart message
                    # The email client will try to render the last part first
                    message.attach(part1)
                    message.attach(part2)
                    server.sendmail(
                        sender_email,
                        email,
                        message.as_string(),
                    )
        
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
               
    # set url back to general events page. This is necessary here because the URL has to be changed back
    # at the start of the for loop.
    url = "https://www.jura.fu-berlin.de/en/forschung/fuels/Upcoming/index.html"
    r = requests.get(url)
    tree = html.fromstring(r.content, parser=parser)

# RiK

lines = csv.reader(data) # these two lines

# gets list with no of titles of events (i bet there's a more efficient way to do this)
rik_count_num_current_events = round(tree6.xpath("count(//*[@id=\"c51\"]/div/div/a)"))
rik_count_num_past_events = round(tree6.xpath("count(//*[@id=\"c111\"]/div/div/a)"))
rik_num_current_events = list(range(1, rik_count_num_current_events+1))
rik_num_past_events = list(range(1, rik_count_num_past_events+1))
    
for event in rik_num_current_events:
    # checks if event is already in database
    new_event = tree6.xpath('//*[@id="c51"]/div/div/a[' + str(event) + ']/div/div[1]/h4/span/text()')
    c.execute('''SELECT 1 FROM event_header WHERE name = %s''', (new_event,))
    if c.fetchone():
        print("Found RiK event!")
    # else: adds the new event to db, gets all the relevant info for building the LSC event 
    # and sends an email for review
    else:
        print("added one entry")
        header = new_event[0] # this will be one of the components for the HTML of the lsc event later
        print(header)
        #set url to specific events page to retrieve details
        url_pt1 = "https://www.rechtimkontext.de/"
        url_pt2 = str(tree6.xpath('//*[@id=\"c51\"]/div/div/a[' + str(event) + ']/@href')[0])
        url = url_pt1 + url_pt2
        url7 = url
        r7 = requests.get(url7)
        tree7 = html.fromstring(r7.content, parser=parser)
        
        speaker_and_uni_raw1 = tree6.xpath('//*[@id="c51"]/div/div/a[' + str(event) + ']/div/div[2]/span/p[1]/text()')
        speaker_and_uni_raw2 = speaker_and_uni_raw1[0]
        speaker_and_uni = speaker_and_uni_raw2[:-1].split(" (")
        speaker = speaker_and_uni[0]
        uni = speaker_and_uni[1]
        
        # checks date
        date_tuple = tree6.xpath('normalize-space(//*[@id="c51"]/div/div/a[' + str(event) + ']/div/div[1]/h2/span/time/text())')
        date_comps = date_tuple.split(" ")
        
        date_day = date_comps[0][:-1]
        date_month = date_comps[1]
        date_year = date_comps[2]
        
        datetime_1 = datetime.date(int(date_year), int(convert_month(date_month)), int(date_day))
        rik_event_date = round((time.mktime(datetime_1.timetuple())))
        print(rik_event_date)
        
        event_time = tree7.xpath('//div[@class="teaser-text"]//p[2]/text()')[0]
        
        try:
            event_time_split = event_time.split("–")
            print(event_time)
            
            start_time = uk_time(event_time_split[0])
            end_time = uk_time(event_time_split[1])
            
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
        
        # send emails for review before upload on LSC
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, password)
            with open("items.csv") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                for name, email in reader:
                
                    # excludes people on the CSV. Since this email is for a FUELS event,
                    # it is not relevant for LSI. It would be more elegant to also store this
                    # in a database, but a CSV is easier for now, might change later
                    if name == "Feneberg":
                        continue
                    
                    # note in case anyone should ever edit this: The following %s are used as normal
                    # string manipulation placeholders. Although the %s in the MySQL queries in this script
                    # look almost the same, they are used for parameter substitution and it is important to 
                    # understand this difference as using string manipulation in SQL queries makes them vulnerable
                    # to SQL injection attacks. Have a very close look at the difference in usage.
                    
                    if speaker == "":
                        speaker_mail = ""
                        speaker_mail2 = ""
                    else:
                        speaker_mail = "mit " + speaker
                        speaker_mail2 = "Seminar with <strong>%s</strong>" % (speaker)
                        
                    text_version = '''\
                    Lieber Herr %s,
                    (das ist die plain-text version der Email, bei Gelegenheit noch ergänzen)
                    Dies ist eine LSC-Testmail für
                    www.laws-of-social-cohesion.de''' % (name)
                    
                    # general note on how emails work: if you receive an email with formatting, 
                    # it always comes in two versions: plain text (above)
                    # and HTML. This is necessary, only HTML is not accepted. The plain-text version is rendered first.
                    html_version = '''\
                    <html>
                        <body>
                        <p>Sehr geehrter Herr %s,<br>
                            <br>
                            eben ist mir aufgefallen, dass heute eine Veranstaltung %s auf der
                            Website gelistet wurde. Soll ich das Event auf die LSC-Seite übertragen? Falls ja, würde ich die Meldung
                            folgendermaßen gestalten:<br>
                            <h3><a href="%s">%s</a></h3>
                                    <blockquote>
                                    <p>%s, %s </p>
                                    <p>%s </p>
                                    <p>Hosted by Recht im Kontext</p>
                                    </blockquote>
                            Wenn diese Veranstaltung nicht der LSC-Seite hinzugefügt werden soll, klicken Sie bitte <a href="%s">hier</a>. 
                            Möchten Sie die Meldung in ihrer jetzigen Form annehmen, klicken Sie bitte <a href="%s">hier</a>. Sollten Sie die 
                            Meldung hochladen wollen, die Meldung aber fehlerhaft sein, können Sie mich darüber per Klick hier 
                            informieren. Sie brauchen sonst nichts weiter zu unternehmen. Ich lade sie dann später korrigiert hoch 
                            und lasse davor noch einmal einen Menschen einen Blick darauf werfen. Sollten anderweitige Probleme 
                            bestehen, helfe ich immer gerne.<br>
                            <br>
                            <br>
                            Mit freundlichen Grüßen,<br>
                            Ihr Benjamin Mantay<br>
                            <br>
                            -------------<br>
                            <a href="https://www.jura.fu-berlin.de/fachbereich/einrichtungen/zivilrecht/lehrende/engerta/Team/5_Externe-Wissenschaftler_innen/Benji">Dr. can. Benjamin Mantay</a> <br>
                            Head of IT und Tierischer Wissenschaftler (Postdog) am Lehrstuhl Engert<br>
                            <br>
                            <br>
                            <br>
                        </p>
                        </body>
                    </html>
                    ''' % (name, speaker_mail, url, header, date, address, speaker_mail2, generateDenyLink(current_id[0]), generateAcceptLink(current_id[0]))
                    
                    message = MIMEMultipart("alternative")
                    message["Subject"] = "LSC | Neue Veranstaltung %s" % (speaker_mail)
                    message["From"] = sender_email
                    message["To"] = email
                    
                    # Turn strings into plain/html MIMEText objects
                    part1 = MIMEText(text_version, "plain")
                    part2 = MIMEText(html_version, "html")
                    
                    # Add HTML/plain-text parts to MIMEMultipart message
                    # The email client will try to render the last part first
                    message.attach(part1)
                    message.attach(part2)
                    server.sendmail(
                        sender_email,
                        email,
                        message.as_string(),
                    )
        
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
               
    # set url back to general events page. This is necessary here because the URL has to be changed back
    # at the start of the for loop.
    url = "https://www.jura.fu-berlin.de/en/forschung/fuels/Upcoming/index.html"
    r = requests.get(url)
    tree = html.fromstring(r.content, parser=parser)
    
# LSI

lines = csv.reader(data) # these two lines

for event in lsi_num_current_events:
    # checks if event is already in database
    new_event = tree3.xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')
    c.execute('''SELECT 1 FROM event_header WHERE name = %s''', (new_event,))
    if c.fetchone():
        print("Found LSI event!")
    # else: adds the new event to db, gets all the relevant info for building the LSC event 
    # and sends an email for review
    else:
        print("added one entry")
        header = new_event[0] # this will be one of the components for the HTML of the lsc event later
        print(header)
        #set url to specific events page to retrieve details
        event_link = tree3.xpath('//article[' + str(event) + ']/div[2]/h2/a/@href')
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
            event_link = tree3.xpath('//article[' + str(event) + ']/div[2]/h2/a/@href')
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
        
        date_day = tree3.xpath('//span[@class=\'cal_day\']/text()')[event-1]
        date_month = tree3.xpath('//span[@class=\'cal_month\']/text()')[event-1]
        date_year = tree3.xpath('//span[@class=\'cal_year\']/text()')[event-1]
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
        address_lxml = tree3.xpath('//span[@itemprop="address"]/text()[0]')
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
        
        # send emails for review before upload on LSC
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, password)
            with open("items.csv") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                for name, email in reader:
                    
                    # excludes people on the CSV. Since this email is for a FUELS event,
                    # it is not relevant for LSI. It would be more elegant to also store this
                    # in a database, but a CSV is easier for now, might change later
                    if name == "Feneberg":
                        continue
                    
                    # note in case anyone should ever edit this: The following %s are used as normal
                    # string manipulation placeholders. Although the %s in the MySQL queries in this script
                    # look almost the same, they are used for parameter substitution and it is important to 
                    # understand this difference as using string manipulation in SQL queries makes them vulnerable
                    # to SQL injection attacks. Have a very close look at the difference in usage.
                    
                    if speaker == "":
                        speaker_mail = ""
                        speaker_mail2 = ""
                    else:
                        speaker_mail = "mit " + speaker
                        speaker_mail2 = "Seminar with <strong>%s</strong>" % (speaker_db)
                        
                    text_version = '''\
                    Lieber Herr %s,
                    (das ist die plain-text version der Email, bei Gelegenheit noch ergänzen)
                    Dies ist eine LSC-Testmail für
                    www.laws-of-social-cohesion.de''' % (name)
                    
                    # general note on how emails work: if you receive an email with formatting, 
                    # it always comes in two versions: plain text (above)
                    # and HTML. This is necessary, only HTML is not accepted. The plain-text version is rendered first.
                    html_version = '''\
                    <html>
                        <body>
                        <p>Sehr geehrter Herr %s,<br>
                            <br>
                            eben ist mir aufgefallen, dass heute eine Veranstaltung %s auf der
                            Website gelistet wurde. Soll ich das Event auf die LSC-Seite übertragen? Falls ja, würde ich die Meldung
                            folgendermaßen gestalten:<br>
                            <h3><a href="%s">%s</a></h3>
                                    <blockquote>
                                    <p>%s, %s </p>
                                    <p>%s </p>
                                    <p>Hosted by LSI</p>
                                    </blockquote>
                            Wenn diese Veranstaltung nicht der LSC-Seite hinzugefügt werden soll, klicken Sie bitte <a href="%s">hier</a>. 
                            Möchten Sie die Meldung in ihrer jetzigen Form annehmen, klicken Sie bitte <a href="%s">hier</a>. Sollten Sie die 
                            Meldung hochladen wollen, die Meldung aber fehlerhaft sein, können Sie mich darüber per Klick hier 
                            informieren. Sie brauchen sonst nichts weiter zu unternehmen. Ich lade sie dann später korrigiert hoch 
                            und lasse davor noch einmal einen Menschen einen Blick darauf werfen. Sollten anderweitige Probleme 
                            bestehen, helfe ich immer gerne.<br>
                            <br>
                            <br>
                            Mit freundlichen Grüßen,<br>
                            Ihr Benjamin Mantay<br>
                            <br>
                            -------------<br>
                            <a href="https://www.jura.fu-berlin.de/fachbereich/einrichtungen/zivilrecht/lehrende/engerta/Team/5_Externe-Wissenschaftler_innen/Benji">Dr. can. Benjamin Mantay</a> <br>
                            Head of IT und Tierischer Wissenschaftler (Postdog) am Lehrstuhl Engert<br>
                            <br>
                            <br>
                            <br>
                        </p>
                        </body>
                    </html>
                    ''' % (name, speaker_mail, url, header, date, address, speaker_mail2, generateDenyLink(current_id[0]), generateAcceptLink(current_id[0]))
                    
                    message = MIMEMultipart("alternative")
                    message["Subject"] = "LSC | Neue Veranstaltung %s" % (speaker_mail)
                    message["From"] = sender_email
                    message["To"] = email
                    
                    # Turn strings into plain/html MIMEText objects
                    part1 = MIMEText(text_version, "plain")
                    part2 = MIMEText(html_version, "html")
                    
                    # Add HTML/plain-text parts to MIMEMultipart message
                    # The email client will try to render the last part first
                    message.attach(part1)
                    message.attach(part2)
                    server.sendmail(
                        sender_email,
                        email,
                        message.as_string(),
                    )
        
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
               
    # set url back to general events page. This is necessary here because the URL has to be changed back
    # at the start of the for loop.
    url = "https://www.jura.fu-berlin.de/en/forschung/fuels/Upcoming/index.html"
    r = requests.get(url)
    tree = html.fromstring(r.content, parser=parser)
    
# next: check all database entries against past events. If one appears there, it is deleted from the database
# for extra efficiency. Actually checking past events is not necessary (or smart) to update current events 
# I noticed later, but it might be worth keeping to automate moving events from the events homepage over to
# the past events page.

# creates a list with all past titles

# FUELS
past_events_titles = list()
for events in num_past_events:
    past_event = tree.xpath('//*[@id="past_events"]/div[' + str(events) + ']/div[1]/h3/a/text()[1]')
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
    new_event = tree.xpath('//*[@id="current_events"]/div[' + str(event) + ']/div[1]/h3/a/text()[1]')[0]
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
    past_event = tree4.xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')
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
    new_event = tree3.xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')[0]
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
    past_event = tree6.xpath('//*[@id="c111"]/div/div/a[' + str(event) + ']/@title')
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
    new_event = tree6.xpath('//*[@id="c51"]/div/div/a[' + str(event) + ']/@title')
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
count = round(tree2.xpath(xpath_count))
count_list = list(range(0, count-1))

c.execute('''SELECT html_insert FROM upcoming_events''')
before_html = c.fetchall()
print("before: " + str(before_html) + "\n \n \n")

# stores the HTML blocks of the different events, same as above
lsc_events = list()

## creates list of current html blocks on the LSC website, same as above 
# but current because things might change in between
soup = BeautifulSoup(my_html, "html.parser")
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



