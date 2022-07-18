import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
import pymysql
from notifications import emails

# connect to db

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_pass = os.environ.get('DB_PASS')
email_pass = os.environ.get('EMAIL_PASS')

conn = pymysql.connect(host=db_host,
                       user=db_user,
                       password=db_pass)

c = conn.cursor()

c.execute('''USE testdatabase''')

# load email pw from env var
email_pass = os.environ.get('EMAIL_PASS')

# set up SMTP and SSL requirements for email
port = 465
smtp_server = "smtp.gmail.com"
sender_email = "lsc.webservice@gmail.com"
password = email_pass

# generate links

def generateAcceptLink(upcoming_id):
    return "https://lscwebservice.com/" + str(upcoming_id) + "/accept/"

def generateDenyLink(upcoming_id):
    return "https://lscwebservice.com/" + str(upcoming_id) + "/deny/"

# sends the review email to the reviewer of the institution

# since different arguments need to be passed depending on the notification mail sent, they have to be optional.
def send_review_mail(plaintext_mail=None, html_mail=None, my_speaker=None, my_event=None, my_url=None, my_header=None, my_date=None, my_address=None, my_speaker_mail2=None):

    # db connection
    conn = pymysql.connect(host=db_host,
                       user=db_user,
                       password=db_pass)

    c = conn.cursor()

    c.execute('''USE testdatabase''')

    # get event id from db
    c.execute('''SELECT id FROM upcoming_events WHERE html_insert = %s ORDER BY id DESC LIMIT 1''', (my_event,))
    event_id = c.fetchall()[0][0]

    # close connection
    conn.close()

    #send mail
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
                
                text_version = plaintext_mail % (name)
                
                # general note on how emails work: if you receive an email with formatting, 
                # it always comes in two versions: plain text (above)
                # and HTML. This is necessary, only HTML is not accepted. The plain-text version is rendered first.
                if html_mail == emails.lsc_mail.html_version:
                    html_version = html_mail % (name, my_speaker, my_event, generateDenyLink(event_id))
                elif html_mail == emails.institute_mail.html_version:
                    html_version = html_mail % (name, my_speaker, my_url, my_header, my_date, my_address, my_speaker_mail2, generateDenyLink(event_id), generateAcceptLink(event_id))
                
                message = MIMEMultipart("alternative")
                message["Subject"] = "LSC | Veranstaltung mit %s" % (my_speaker)
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