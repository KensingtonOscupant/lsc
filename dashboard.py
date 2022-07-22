import pymysql
import os

'''Concerns the rudimentary "dashboard" (currently rather a log) on lscwebservice.com. 
Functions for rejecting or accepting events are (and need to be) in the lsc_webservice repo.'''

def detected_event(host_name, event_title_for_dashboard):

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

    operation_performed = "Event detected"
    c.execute("INSERT INTO dashboard (Host, Title, Operation, PerformedAt) VALUES (%s, %s, %s, NOW())", (host_name, event_title_for_dashboard, operation_performed, ))
    conn.commit()
    conn.close()