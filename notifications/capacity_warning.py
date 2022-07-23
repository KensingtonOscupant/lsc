import os
import pymysql

def cap_warning():

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

    conn.close()