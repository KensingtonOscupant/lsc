from bs4 import BeautifulSoup
from .. import get_html
from .. import parsing
from .. import dashboard
import pymysql
import os
import datetime
import time

def split_into_html_blocks():

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

    lsc_events = list()

    soup = BeautifulSoup(get_html.lsc_html.fulltext(), 'html.parser')
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
            detected_event("Legacy event on LSC page", parsing.extract_string_between_tags(event))
            date_list = get_html.lsc_html.tree().xpath('//div[@class=\'content-wrapper main horizontal-bg-container-main\']//blockquote[' + str(k) + ']/p[1]/text()')
            date_split = date_list[0].split(",")
            lsc_event_date_unformatted = str(date_split[0])
            lsc_institution = "LSC"
            lsc_event_date_comp = lsc_event_date_unformatted.split(" ")
            datetime_1 = datetime.date(int(lsc_event_date_comp[2]), int(parsing.convert_month(lsc_event_date_comp[0])), int(lsc_event_date_comp[1]))
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