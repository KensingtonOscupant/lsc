# LSC Sync

This project maintains the events page of <a href="https://www.laws-of-social-cohesion.de/Events/index.html">Laws of Social Cohesion</a>. It automates the curation of events from LSC's partner institutions Freie Universität Empirical Legal Studies Center (<a href="https://www.jura.fu-berlin.de/en/forschung/fuels">FUELS</a>), the Law and Society Institute (<a href="https://www.rewi.hu-berlin.de/en/lf/oe/lsi?set_language=en">LSI</a>) at Humboldt University of Berlin and <a href="https://www.rechtimkontext.de/en/start/">Recht im Kontext</a>. 

A log of the application's recent activity can be found at <a href="https://www.lscwebservice.com">lscwebservice.com</a>.

## Table of Contents

[I. Context](#context)  
[II. Challenge](#challenge)
[III. Description](#description)
[1. Backend](#Backend)
[a. "Before the click"](#"Before the click")
[aa. Database](#Database)
[bb. Retrieving website contents]("Retrieving website contents")
[b. "After the click"]("After the click")
[2. Frontend](#Frontend)

## Context

Since late 2021, I have been supporting in an interdisciplinary research project called “Laws of Social Cohesion” (LSC) mostly in its administrative tasks. The project aims to explore the manyfold ways in which the law affects social cohesion. The researchers involved are affiliated with three different partner institutes: Freie Universität Empirical Legal Studies Center (FUELS) at Freie Universität Berlin, the Law and Society Institute (LSI) at Humboldt University of Berlin and Recht im Kontext (RiK), also at Humboldt University. LSC has a <a href="https://www.laws-of-social-cohesion.de/About-us/index.html">website</a> that showcases the progress made by the different research teams.

## Challenge

I had previously built the website using a simple CMS that we had to use for organizational reasons. I was tasked i.a. with keeping the events section of the project up to date. Events would be hosted by one of the three institutes and announcements would be published on their websites. I should monitor the three events sections and if a new one showed up, I should ask the one in charge at the respective institute whether the event is considered relevant to the project and should be listed on the LSC page, and if so, create a brief note following a consistent format and add it there to link back to the institute’s event page for that event. After I had done this a few times, I thought: Why not automate it? So I set out on my journey to (hopefully) make myself obsolete.

What seemed incredibly trivial at first turned out to be more of a day’s work. I ended up working on it for several weeks. Although this was not my first project, little did I know that I had just embarked on a journey leading me through the full stack and discover a lot of fascinating subjects I had never spent much detailed thought on before.

## Description

The project is centered around a single click: The one that happens if the email recipient decides to accept or reject an event. Anything that happens before this "event" of clicking is kept in <a href="https://github.com/KensingtonOscupant/lsc/blob/main/before_event.py">before_event.py</a>, anything that routinely happens after it resides in <a href="https://github.com/KensingtonOscupant/lsc/blob/main/after_event.py">after_event.py</a>. 

### Backend

#### "Before the click"

Tasks executed before someone decides which link to click in their email include -- if necessary -- setting up the database, scraping events and sending said notification emails.

##### Database

For the database, I decided in favour of an SQL database because of the very predictable and consistent data format, which made it easy to define a schema. I ended up deciding in favour of a server database over a SQLite database because despite it seeming unlikely that I would ever be in a situation where I would have to make multiple writes to the database simultaneously, I wanted to ensure that the project could be moved to the university servers to make use of the MySQL capacities there if the servers should be properly maintained at some point (for challenges in deployment see the section “Deployment” down below). Furthermore, although it is possible to put a SQLite database on a server, it is not among its intended use cases. I considered using an ORM but decided against it because the use case was too simple. To be able to execute SQL queries in Python, I used pymysql.

##### Retrieving website contents

My first intuition to retrieve data was to get (read-only) API access to the three websites and use the endpoints to generate the content on the LSC page. This idea failed right away because the pages were run on content management systems that were made for universities. They were focused on graphical user interfaces and only in one out of three cases provided an API, which was for Ruby on Rails only, had to be requested and did not cover all sections of the website. Hence, I had to fetch the content “manually” from the websites myself using Python’s Requests library and parsing the HTML either with BeautifulSoup or directly with lxml. 

The CMS I had to use for the LSC website also did not have a viable API access, which is why I had to use Selenium to make changes to the website. I do not like this setup because it is not very stable in the long run and could break if there are changes made to the HTML of the website, but I could not think of a better way around the problem.

#### "After the click"

Anything that routinely happens after the click is kept in after_events.py, i.e. logging on to the website and changing it according to the contents of a database table that indiciates the events that should currently be on the events page.

### Frontend

However, not _everything_ that needs to happen after the click can happen through the execution of a script since the decision whether the event has been accepted or rejected first needs to find its way into the database. The web server setup for this is kept in a <a href="https://github.com/KensingtonOscupant/lsc-webserver">separate repository</a>.
