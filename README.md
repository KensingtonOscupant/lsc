# LSC Sync

This project maintains the events page of <a href="https://www.laws-of-social-cohesion.de/Events/index.html">Laws of Social Cohesion</a>. It automates the curation of events from LSC's partner institutions Freie Universität Empirical Legal Studies Center (<a href="https://www.jura.fu-berlin.de/en/forschung/fuels">FUELS</a>), the Law and Society Institute (<a href="https://www.rewi.hu-berlin.de/en/lf/oe/lsi?set_language=en">LSI</a>) at Humboldt University of Berlin and <a href="https://www.rechtimkontext.de/en/start/">Recht im Kontext</a>. 

A log of the application's recent activity can be found at <a href="https://www.lscwebservice.com">lscwebservice.com</a>.

## Motivation

Maintaining this event page falls within the administrative tasks I have at LSC. Before writing this application, I needed to check the different websites manually on a regular basis, see if there are new events listed, find out whether the event was considered relevant to the scope of the project and if so, write a short paragraph with key information about the event. Then I would upload the note to the website.

I noticed quickly that this was quite a repetitive process, so I decided to automate it.

## Description

The project is centered around a single click: The one that happens if the email recipient decides to accept or reject an event. Anything that happens before this "event" of clicking is kept in <a href="https://github.com/KensingtonOscupant/lsc/blob/main/before_event.py">before_event.py</a>, anything that routinely happens after it resides in <a href="https://github.com/KensingtonOscupant/lsc/blob/main/after_event.py">after_event.py</a>. 

### Before the click

Tasks executed before someone decides which link to click in their email include -- if necessary -- setting up the database, scraping events and sending said notification emails. 

### After the click

Anything that routinely happens after the click is kept in after_events.py, i.e. logging on to the website and changing it according to the contents of a database table that indiciates the events that should currently be on the events page.

However, not _everything_ that needs to happen after the click can happen through the execution of a script since the decision whether the event has been accepted or rejected first needs to find its way into the database. The web server setup for this is kept in a <a href="https://github.com/KensingtonOscupant/lsc-webserver">separate repository</a>.
