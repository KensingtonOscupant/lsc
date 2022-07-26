# LSC Sync

This project maintains the events page of <a href="https://www.laws-of-social-cohesion.de/Events/index.html">Laws of Social Cohesion</a>. It automates the curation of events from LSC's partner institutions Freie Universität Empirical Legal Studies Center (<a href="https://www.jura.fu-berlin.de/en/forschung/fuels">FUELS</a>), the Law and Society Institute (<a href="https://www.rewi.hu-berlin.de/en/lf/oe/lsi?set_language=en">LSI</a>) at Humboldt University of Berlin and <a href="https://www.rechtimkontext.de/en/start/">Recht im Kontext</a>. 

A log of the application's recent activity can be found at <a href="https://www.lscwebservice.com">lscwebservice.com</a>.

## Table of Contents

[I. Context](#i-context)  
[II. Challenge](#ii-challenge)  
[III. Description](#iii-description)  
&nbsp;&nbsp;&nbsp;&nbsp;[1. Backend](#1-Backend)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[a. "Before the click"](#a-before-the-click)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[aa. Database](#aa-Database)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[bb. Retrieving website contents](#bb-retrieving-website-contents)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[b. "After the click"](#b-after-the-click)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[2. Frontend](#2-Frontend)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[3. Deployment](#3-Deployment)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[a. Preliminary remarks](#a-preliminary-remarks)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[b. Initial setup](#b-initial-setup)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[c. Amended setup](#c-amended-setup)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[d. Virtualizing Chrome on Linux](#d-virtualizing-chrome-on-linux)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[e. Cron jobs](#e-cron-jobs)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[f. Proxying traffic through Cloudflare](#f-proxying-traffic-through-cloudflare)  

## I. Context

Since late 2021, I have been supporting in an interdisciplinary research project called “Laws of Social Cohesion” (LSC) mostly in its administrative tasks. The project aims to explore the manyfold ways in which the law affects social cohesion. The researchers involved are affiliated with three different partner institutes: Freie Universität Empirical Legal Studies Center (FUELS) at Freie Universität Berlin, the Law and Society Institute (LSI) at Humboldt University of Berlin and Recht im Kontext (RiK), also at Humboldt University. LSC has a <a href="https://www.laws-of-social-cohesion.de/About-us/index.html">website</a> that showcases the progress made by the different research teams.

## II. Challenge

I had previously built the website using a simple CMS that we had to use for organizational reasons. I was tasked i.a. with keeping the events section of the project up to date. Events would be hosted by one of the three institutes and announcements would be published on their websites. I should monitor the three events sections and if a new one showed up, I should ask the one in charge at the respective institute whether the event is considered relevant to the project and should be listed on the LSC page, and if so, create a brief note following a consistent format and add it there to link back to the institute’s event page for that event. After I had done this a few times, I thought: Why not automate it? So I set out on my journey to (hopefully) make myself obsolete.

What seemed incredibly trivial at first turned out to be more of a day’s work. I ended up working on it for several weeks. Although this was not my first project, little did I know that I had just embarked on a journey leading me through the full stack and discover a lot of fascinating subjects I had never spent much detailed thought on before.

## III. Description

The project is centered around a single click: The one that happens if the email recipient decides to accept or reject an event. Anything that happens before this "event" of clicking is kept in <a href="https://github.com/KensingtonOscupant/lsc/blob/main/before_event.py">before_event.py</a>, anything that routinely happens after it resides in <a href="https://github.com/KensingtonOscupant/lsc/blob/main/after_event.py">after_event.py</a>. 

### 1. Backend

#### a. "Before the click"

Tasks executed before someone decides which link to click in their email include -- if necessary -- setting up the database, scraping events and sending said notification emails.

##### aa. Database

For the database, I decided in favour of an SQL database because of the very predictable and consistent data format, which made it easy to define a schema. I ended up deciding in favour of a server database over a SQLite database because despite it seeming unlikely that I would ever be in a situation where I would have to make multiple writes to the database simultaneously, I wanted to ensure that the project could be moved to the university servers to make use of the MySQL capacities there if the servers should be properly maintained at some point (for challenges in deployment see the section “Deployment” down below). Furthermore, although it is possible to put a SQLite database on a server, it is not among its intended use cases. I considered using an ORM but decided against it because the use case was too simple. To be able to execute SQL queries in Python, I used pymysql.

##### bb. Retrieving website contents

My first intuition to retrieve data was to get (read-only) API access to the three websites and use the endpoints to generate the content on the LSC page. This idea failed right away because the pages were run on content management systems that were made for universities. They were focused on graphical user interfaces and only in one out of three cases provided an API, which was for Ruby on Rails only, had to be requested and did not cover all sections of the website. Hence, I had to fetch the content “manually” from the websites myself using Python’s Requests library and parsing the HTML either with BeautifulSoup or directly with lxml. 

The CMS I had to use for the LSC website also did not have a viable API access, which is why I had to use Selenium to make changes to the website. I do not like this setup because it is not very stable in the long run and could break if there are changes made to the HTML of the website, but I could not think of a better way around the problem.

#### b. "After the click"

Anything that routinely happens after the click is kept in after_events.py, i.e. logging on to the website and changing it according to the contents of a database table that indiciates the events that should currently be on the events page.

### 2. Frontend

However, not _everything_ that needs to happen after the click can happen through the execution of a script since the decision whether the event has been accepted or rejected first needs to find its way into the database. The web server setup for this is kept in a <a href="https://github.com/KensingtonOscupant/lsc-webserver">separate repository</a>.

### 3. Deployment

#### a. Preliminary remarks

My first idea for the environment to deploy the project in came from a random discovery during the time I had to make the decision: Freie Universität offers up to three free MySQL databases. Since this was a work-related project, I thought that it would be a good idea to make use of the offer on this occasion. However, once I had generated my credentials and tried to create the first database, I found out that it was only possible to connect to the databases via a specific server by Freie Universität. Any applications that needed access to said databases had to run on this server. I moved the database to AWS RDS and tried to at least run the rest of the backend on the university server, but permissions issues and I the Debian release was not quite up to date. Hence, I set up an up-to-date version in my home directory using pyenv. However, as soon as I wanted to set up the web server, I was met with more permissions challenges, the only difference being that I was unable to configure a more recent Python version to run by default if a Python script is called directly through the browser.

It was at this point that I noticed that I probably spent too much time on the wrong problems, focusing on fixing issues related to outdated releases and a lack of access rights that I could not solve and that would also not provide me with any experience worth continuing. Additionally, I realized that handling credentials on an outdated server was also a bad idea in terms of security. Therefore I decided to shift the entire setup to AWS.

#### b. Initial setup

As I had already made the decision to set up MySQL on an AWS RDS instance earlier, it made sense to build the other parts of the project in the AWS ecosystem as well.  The main question I had to answer was how to run the code. While I was creating this project, I was also preparing for the AWS Certified Cloud Practitioner (CCP) exam and learned that the most efficient way to achieve such a task was through serverless computing. The sub-units of containers that allow this on AWS are called Lambda functions, which I decided to use. However, in my case, there was a catch: Code can be run on Lambda very easily, but the program I wanted to run also relied on Selenium, which again relies on a web driver.  I could fix this by making use of the functionality of Lambda to allow deployment of functions in images by packaging the code in Docker along with snapshots of Chrome, deploying it with the Serverless Framework. The setup looked like this:

[Insert AWS architecture diagram here]

However, this raised a new challenge because of the nature of Lambda functions: Since they can generally either (1) solely interact with services within a VPC, in this case the default VPC of my AWS account, or (2) only access the public internet, but not the AWS services inside, I had to set up a NAT gateway to allow the function to both send requests to websites to check for updates and insert these records into the database located in the VPC. This worked out, however, a pre-configured NAT gateway on AWS costs $0.045 per hour, which would amount to roughly $30 per month, which I found was too much to be spent on a project like this. The alternatives I considered were <a href="https://medium.com/@ihor.mudrak.uk/aws-how-to-call-a-lambda-from-another-lambda-inside-vpc-or-how-to-publish-to-sns-from-lambda-6b4c52bc5cf7">running two functions, one within the VPS and one outside of it</a>; however, I could not entirely gauge the implications of the Selenium build which is why I decided against it.

#### c. Amended setup

Instead, I used the more traditional cloud approach of deploying the program from an EC2 instance. This solved multiple problems: Firstly, it eliminated the cost problem since smaller instances like t2.micro are included in the AWS free tier. Secondly, there was no need to store the CSV file in S3 anymore; with my previous plan, this was necessary as Lambda functions only have a temporary directory /tmp which does not allow for permanent storage. With an EC2 instance, it is simple to store the CSV file in the same directory as the code. This also allows the program to access the file as a CSV, which is not necessarily the case on S3 because every file stored on S3 is an AWS object the contents of which are typically accessed via the boto3 module in Python. I noticed that this can cause problems because using the .get() method from boto3 instead of with open … as file does not work well with processing a CSV file. Finally, I also did not have to rely on further AWS infrastructure anymore to store environment variables (even though Lambda functions make this surprisingly easy).

[Insert new AWS diagram here]

#### d. Virtualizing Chrome on Linux

My next challenge was to run Selenium on the EC2 instance. At first, I thought that it would be necessary have a virtual frame buffer like Xfvb for running Chrome properly, no matter with which setup Selenium and Chrome Driver are used. However, this turned out to be false: With the correct flags for the Chrome Driver set in the Python script, there was no need for any additional tools. Furthermore, I found an even easier option later by using webdriver-manager which automatically manages the webdriver.

#### e. Cron jobs

To automate executions, I used the built-in Linux scheduler cron. In order to run Python files in their virtual environment, I created bash scripts that start the venv before running python. Additionally, I redirected the output to a log file instead of using the standard MAILTO variable to avoid the risk of unnecessary SMTP errors. Alternatives for proper queueing instead of the rigidity of cron jobs would have been Celery and huey as a more light-weight alternative.

#### f. Proxying traffic through Cloudflare

All traffic to the website is proxied through CloudFlare.







