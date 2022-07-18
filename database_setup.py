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

# checks if the right number of tables exists

def check_no_of_tables():

    # connect to db
    conn = pymysql.connect(host=db_host,
                        user=db_user,
                        password=db_pass)
    c = conn.cursor()
    c.execute('''USE testdatabase''')

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
    conn.close()
    return project_tables

# rebuild database

def rebuild_db():

    # connect to db
    conn = pymysql.connect(host=db_host,
                        user=db_user,
                        password=db_pass)
    c = conn.cursor()
    c.execute('''USE testdatabase''')

    # deletes tables if they exist (respectively)
    c.execute('''SET foreign_key_checks = 0''')
    c.execute("DROP TABLE IF EXISTS upcoming_events")
    c.execute("DROP TABLE IF EXISTS prospective_lsc_events;")
    c.execute("DROP TABLE IF EXISTS lsc_events;")
    c.execute("DROP TABLE IF EXISTS event_header;")
    c.execute("DROP TABLE IF EXISTS num_lsc_events;")
    #c.execute("DROP TABLE IF EXISTS dashboard;")
    
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
    print("created num_lsc_events table")
    
    # add one entry with 0 to num_lsc_events table

    c.execute('''INSERT INTO num_lsc_events (num_events) VALUES (0);''')

    # creates dashboard table to show database transactions on website

    c.execute('''CREATE TABLE IF NOT EXISTS dashboard(
                id INT PRIMARY KEY AUTO_INCREMENT,
                Host VARCHAR(255),
                Title TEXT,
                Operation VARCHAR(255),
                PerformedAt DATETIME);''')
    print("created dashboard table")

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

    conn.close()
