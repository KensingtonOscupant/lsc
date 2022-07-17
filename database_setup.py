import pymysql
import os

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

def check_no_of_tables():
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
    c.execute('''SELECT count(*) FROM information_schema.tables WHERE table_name = 'dashboard';''')
    table6 = c.fetchall()[0][0]

    project_tables = table1 + table2 + table3 + table4 + table5 + table6
    return project_tables