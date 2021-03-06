# lsc

Written in Python and SQL (via pymysql). The code still needs to be modularized and I will add a proper readme later this month.
Deployed on an AWS EC2 Ubuntu instance with Apache and Django using AWS RDS for the database.

Project that will maintain the event website of <a href="https://www.laws-of-social-cohesion.de/Events/index.html">Laws of Social Cohesion</a>. The page consists of a curated list of events from LSC's partner institutions Freie Universität Empirical Legal Studies Center (<a href="https://www.jura.fu-berlin.de/en/forschung/fuels">FUELS</a>), the Law and Society Institute (<a href="https://www.rewi.hu-berlin.de/en/lf/oe/lsi?set_language=en">LSI</a>) at Humboldt University of Berlin and <a href="https://www.rechtimkontext.de/en/start/">Recht im Kontext</a>.

In short, this program maintains a database about events currently listed on the websites of the different partner institutions, checks them regularly and determines changes to the websites on this basis. If it notices a new event, it analyzes its content for specific information (sometimes with a tiny bit of NLP) that it then uses to generate a brief note about the event which is sent to the person in charge of the events of the respective institute with options to confirm that this event should appear on the website of our joint venture, not include it on the website or flag it for review in case it should be listed but contains errors. If it should be included, it logs on to the LSC page and adds the respective event, making the necessary changes to the database along the way.
