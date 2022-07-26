# %%
from lxml import html
import os
import pymysql
import requests
from bs4 import BeautifulSoup
import jellyfish
import get_html as gh
import database_setup as dbs
from notifications import capacity_warning as cp
from scraping.lsc_scraping import split_into_html_blocks
from scraping import fuels_scraping, rik_scraping, lsi_scraping
from monitoring import monitoring as mo
import parsing

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

# acts accordingly.
if dbs.check_no_of_tables() == 6:
    print("All tables found!")
elif dbs.check_no_of_tables() < 6 and dbs.check_no_of_tables() >= 0:
    print("At least one table does not exist. All tables will be recreated.")
    
    # rebuilds the database
    dbs.rebuild_db()

    # splits existing HTML into blocks; also sends notification emails
    split_into_html_blocks()
     
else:
    print("Error: The number of tables does not make any sense. It is either smaller than 0 or greater than 5")


# main part of the program: monitors changes to events on the websites

# FUELS

fuels_scraping.scrape(parsing.count_events_fuelsuntr())

# checks if there are still free slots in prospective_events
cp.cap_warning()

# RiK

# gets list with no of titles of events (i bet there's a more efficient way to do this)
rik_count_num_current_events = round(gh.rik_html.tree().xpath("count(//*[@id=\"c51\"]/div/div/a)"))
rik_num_current_events = list(range(1, rik_count_num_current_events+1))

rik_scraping.scrape(parsing.rik_count_num_current_events())

# checks if there are still free slots in prospective_events
cp.cap_warning()
    
# LSI

lsi_scraping.scrape(parsing.lsi_count_current_events())

# checks if there are still free slots in prospective_events
cp.cap_warning()
    
'''check all database entries against past events on the websites. If one appears there, it is deleted from the database
(1) to keep the LSC page up to date and (2) to keep the database as small as possible.'''

mo.monitor_removals()

conn.commit()
conn.close()

# %%



