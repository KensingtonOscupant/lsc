import get_html as gh
from lxml import html, etree

"""Functions that support proper parsing and processing of the HTML 
retrieved from the websites of the three institutions."""

def convert_month(month):
    if month == "Jan" or month == "Januar":
        return "01"
    if month == "Feb" or month == "Februar":
        return "02"
    if month == "Mar" or month == "Mär" or month == "März":
        return "03"
    if month == "Apr" or month == "April":
        return "04"
    if month == "May" or month == "Mai":
        return "05"
    if month == "Jun" or month == "Juni":
        return "06"
    if month == "Jul" or month == "Juli":
        return "07"
    if month == "Aug" or month == "August":
        return "08"
    if month == "Sep" or month == "September":
        return "09"
    if month == "Oct" or month == "Okt" or month == "Oktober":
        return "10"
    if month == "Nov" or month == "November":
        return "11"
    if month == "Dec" or month == "Dez" or month == "Dezember":
        return "12"

def convert_month_back(month_num):
    if month_num == "01":
        return "Jan"
    if month_num == "02":
        return "Feb"
    if month_num == "03":
        return "Mar"
    if month_num == "04":
        return "Apr"
    if month_num == "05":
        return "May"
    if month_num == "06":
        return "Jun"
    if month_num == "07":
        return "Jul"
    if month_num == "08":
        return "Aug"
    if month_num == "09":
        return "Sep"
    if month_num == "10":
        return "Oct"
    if month_num == "11":
        return "Nov"
    if month_num == "12":
        return "Dec"   

# parses dates so that they appear in AM/PM format on the LSC website

def uk_time(timestamp):
    uk_time_split = timestamp.split(":")
    uk_time_result = str(int(uk_time_split[0]) - 12) + ":" + str(uk_time_split[1])
    return uk_time_result

# getting the names in the LSC review email right even if there are multiple ones:
def oxfordcomma(listed):
    if len(listed) == 0:
        return ''
    if len(listed) == 1:
        return listed[0]
    if len(listed) == 2:
        return listed[0] + ' und ' + listed[1]
    return ', '.join(listed[:-1]) + ' und ' + listed[-1]

# I didn't save the titles for the LSC events separately, so this function gets them for the dashboard
def extract_string_between_tags(html):
    start_tag = "\">"
    end_tag = "</a>"
    start_index = html.find(start_tag)
    end_index = html.find(end_tag)
    return html[start_index + len(start_tag):end_index]

# gets number of current FUELS events
def count_events_fuelsuntr():
    xpath_count = "count(//*[@id=current_events]/div)"
    count = round(gh.fuels_html.tree().xpath(xpath_count))
    num_current_events = list(range(1, count+1))
    return num_current_events

# gets number of current FUELS events
def lsi_count_current_events():
    count = round(gh.lsi_current_events_html.tree().xpath("count(//article)"))
    lsi_num_current_events = list(range(1, count))
    return lsi_num_current_events

# gets number of current RiK events

def rik_count_num_current_events():
    count = round(gh.rik_html.tree().xpath("count(//*[@id=\"c51\"]/div/div/a)"))
    rik_num_current_events = list(range(1, count))
    return rik_num_current_events