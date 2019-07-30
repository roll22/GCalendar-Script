from __future__ import print_function
import datetime
import pickle
import os.path
import time
import googleapiclient
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

"""Shows basic usage of the Google Calendar API.
Prints the start and name of the next 10 events on the user's calendar.
"""
creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.

# checks for existing credentials
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('calendar', 'v3', credentials=creds)
print("Connected to GCalendar.")
event = {
    'summary': 'Google I/O 2015',
    'location': '800 Howard St., San Francisco, CA 94103',
    'description': 'A chance to hear more about Google\'s developer products.',
    'start': {
        'dateTime': '2019-08-01T00:20:00+03:00',
        'timeZone': 'Europe/Bucharest',
    },

    'end': {
        'dateTime': '2019-08-01T23:59:40+03:00',
        'timeZone': 'Europe/Bucharest',
    },
    'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=2'
    ],
    'attendees': [
        {'email': 'lpage@example.com'},
        {'email': 'sbrin@example.com'},
    ],
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'days': 1},
            {'method': 'popup', 'minutes': 10},
        ],
    },
}

# event = service.events().insert(calendarId='primary', body=event).execute()

# time.sleep(1)

now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
print('Getting the upcoming 10 events')
events_result = service.events().list(calendarId='primary', timeMin=now,
                                      maxResults=10, singleEvents=True,
                                      orderBy='startTime').execute()
events = events_result.get('items', [])

if not events:
    print('No upcoming events found.')
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(start, event['summary'])


# Script to parse a table from a website
import urllib.request
from html.parser import HTMLParser

from html.parser import HTMLParser


class HTMLTableParser(HTMLParser):
    def __init__(
            self,
            decode_html_entities=False,
            data_separator=' ',
    ):

        HTMLParser.__init__(self)

        self._parse_html_entities = decode_html_entities
        self._data_separator = data_separator

        self._in_td = False
        self._in_th = False
        self._current_table = []
        self._current_row = []
        self._current_cell = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        """ We need to remember the opening point for the content of interest.
        The other tags (<table>, <tr>) are only handled at the closing point.
        """
        if tag == 'td':
            self._in_td = True
        if tag == 'th':
            self._in_th = True

    def handle_data(self, data):
        """ This is where we save content to a cell """
        if self._in_td or self._in_th:
            self._current_cell.append(data.strip())

    def handle_charref(self, name):
        """ Handle HTML encoded characters """

        if self._parse_html_entities:
            self.handle_data(self.unescape('&#{};'.format(name)))

    def handle_endtag(self, tag):
        """ Here we exit the tags. If the closing tag is </tr>, we know that we
        can save our currently parsed cells to the current table as a row and
        prepare for a new row. If the closing tag is </table>, we save the
        current table and prepare for a new one.
        """
        if tag == 'td':
            self._in_td = False
        elif tag == 'th':
            self._in_th = False

        if tag in ['td', 'th']:
            final_cell = self._data_separator.join(self._current_cell).strip()
            self._current_row.append(final_cell)
            self._current_cell = []
        elif tag == 'tr':
            self._current_table.append(self._current_row)
            self._current_row = []
        elif tag == 'table':
            self.tables.append(self._current_table)
            self._current_table = []


file = open("orar.html")
xhtml = file.read()
p = HTMLTableParser()

p.feed(xhtml)
# for x in p.tables[0][0][0][0]:
#     print(x)

x = 1

# parse day
day = p.tables[0][x][0]
weekdays_ro = ['Luni', 'Marti', 'Miercuri', 'Joi', 'Vineri']
weekdays_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
day = weekdays_en[weekdays_ro.index(day)]

# parse hours
hours_raw = p.tables[0][x][1]
startHour = -1
endHour = -1
if (len(hours_raw) == 4):
    startHour = '0' + hours_raw[0:1]
    endHour = hours_raw[2:4]
else:
    startHour = hours_raw[0:2]
    endHour = hours_raw[3:5]

startHour = '2019-09-30T' + startHour + ':00:00+03:00'
endHour = '2019-09-30T' + endHour + ':00:00+03:00'

# parse frequency
frequency_raw = p.tables[0][x][2]
interval = 1
# TODO  NOT SURE WHAT the input means !!!!!!!!!!!!!!!
if frequency_raw == 'sapt. 1':
    interval = 2
elif frequency_raw == 'sapt. 2':
    interval = 3

# parse location
room_raw = p.tables[0][x][3]

# TODO  Parse the Table with rooms for locations
# TODO  Research locations
# TODO  ?:))

# parse formation
formation_raw = p.tables[0][x][4]

# parse type
type_raw = p.tables[0][x][5]
types = ['Laborator', 'Seminar', 'Curs']

# color
colors = ['Tomato', 'Banana', 'Blueberry']
color = colors[types.index(type_raw)]

# parse subject
subject_raw = p.tables[0][x][6]

# parse teacher
teacher_raw = p.tables[0][x][7]

event = {
    'summary': subject_raw,
    'location': 'Campus, etaj 4 (str. T. Mihali)',
    'description': type_raw + ', ' + room_raw + ', ' + formation_raw + ', ' + teacher_raw,
    'start': {
        'dateTime': startHour,
        'timeZone': 'Europe/Bucharest',
    },

    'end': {
        'dateTime': endHour,
        'timeZone': 'Europe/Bucharest',
    },
    'recurrence': [
        'RRULE:FREQ=WEEKLY;INTERVAL=' + str(interval) + ';COUNT=3'
    ],
    'attendees': [
        {'email': 'lpage@example.com'},
        {'email': 'sbrin@example.com'},
    ],
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': 10},
        ],
    },
}

event = service.events().insert(calendarId='primary', body=event).execute()
