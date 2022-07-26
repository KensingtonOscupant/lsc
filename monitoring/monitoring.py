import pymysql
import os
import get_html as gh
import requests
import jellyfish
from bs4 import BeautifulSoup
from lxml import html

'''check all database entries against past events on the websites. If one appears there, it is deleted from the database
(1) to keep the LSC page up to date and (2) to keep the database as small as possible.'''

'''Note: This could be modularized further, the process is very similar for all institutes'''

# gets number of current or past events
def count_events_fuelsuntr(current_or_past):
    xpath_count = "count(//*[@id=\"" + current_or_past + "_events\"]/div)"
    count = round(gh.fuels_html.tree().xpath(xpath_count))
    return count

# gets FUELS list with no. of titles of events (i bet there's a more efficient way to do this)
num_current_events = list(range(1, count_events_fuelsuntr("current")+1))
num_past_events = list(range(1, count_events_fuelsuntr("past")+1))

# gets LSI list with no. of titles of events
lsi_count_current_events = round(gh.lsi_current_events_html.tree().xpath("count(//article)"))
lsi_count_past_events = round(gh.lsi_past_events_html.tree().xpath("count(//article)"))
lsi_num_current_events = list(range(1, lsi_count_current_events))
lsi_num_past_events = list(range(1, lsi_count_past_events))

# gets list with no of titles of events (i bet there's a more efficient way to do this)
rik_count_num_current_events = round(gh.rik_html.tree().xpath("count(//*[@id=\"c51\"]/div/div/a)"))
rik_count_num_past_events = round(gh.rik_html.tree().xpath("count(//*[@id=\"c111\"]/div/div/a)"))
rik_num_current_events = list(range(1, rik_count_num_current_events+1))
rik_num_past_events = list(range(1, rik_count_num_past_events+1))

def monitor_removals():

    db_host = os.environ.get('DB_HOST')
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')

    #connect to db
    conn = pymysql.connect(host=db_host,
                        user=db_user,
                        password=db_pass)

    c = conn.cursor()

    c.execute('''USE testdatabase''')

    # creates a list with all past titles

    # FUELS
    past_events_titles = list()
    for events in num_past_events:
        past_event = gh.fuels_html.tree().xpath('//*[@id="past_events"]/div[' + str(events) + ']/div[1]/h3/a/text()[1]')
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
        new_event = gh.fuels_html.tree().xpath('//*[@id="current_events"]/div[' + str(event) + ']/div[1]/h3/a/text()[1]')[0]
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
        past_event = gh.lsi_past_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')
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
        new_event = gh.lsi_current_events_html.tree().xpath('//article[' + str(event) + ']/div[2]/h2/a/span/text()[1]')[0]
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
        past_event = gh.rik_html.tree().xpath('//*[@id="c111"]/div/div/a[' + str(event) + ']/@title')
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
        new_event = gh.rik_html.tree().xpath('//*[@id="c51"]/div/div/a[' + str(event) + ']/@title')
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
    count = round(gh.lsc_html.tree().xpath(xpath_count))
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
    soup = BeautifulSoup(gh.lsc_html.fulltext(), "html.parser")
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
    
    conn.close()