from __future__ import print_function
import datetime
import pickle
import os.path
import time
import googleapiclient
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Defines the permissions the app gets to the connected calendar
# 'https://www.googleapis.com/auth/calendar' - gives read/write

SCOPES = ['https://www.googleapis.com/auth/calendar']

credentials = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.

# checks for existing credentials
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        credentials = pickle.load(token)

# If there are no (valid) credentials available, let the user log in.
if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        credentials = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(credentials, token)

service = build('calendar', 'v3', credentials=credentials)
print("Connected to GCalendar.")

# event = service.events().insert(calendarId='primary', body=event).execute()

# time.sleep(1)
#
# now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
# print('Getting the upcoming 10 events')
# events_result = service.events().list(calendarId='primary', timeMin=now,
#                                       maxResults=10, singleEvents=True,
#                                       orderBy='startTime').execute()
# events = events_result.get('items', [])
#
# if not events:
#     print('No upcoming events found.')
# for event in events:
#     start = event['start'].get('dateTime', event['start'].get('date'))
#     print(start, event['summary'])


# Script to parse locationList table from locationList website
import urllib.request

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
        """ This is where we save content to locationList cell """
        if self._in_td or self._in_th:
            self._current_cell.append(data.strip())

    def handle_charref(self, name):
        """ Handle HTML encoded characters """

        if self._parse_html_entities:
            self.handle_data(self.unescape('&#{};'.format(name)))

    def handle_endtag(self, tag):
        """ Here we exit the tags. If the closing tag is </tr>, we know that we
        can save our currently parsed cells to the current table as locationList row and
        prepare for locationList new row. If the closing tag is </table>, we save the
        current table and prepare for locationList new one.
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


class EventParser:

    def __init__(self, page, indexOfTable):
        self.parsedPage = page
        self.tableNumber = indexOfTable
        self.day = self.parseDay()
        self.startHour = self.parseStartHour()
        self.endHour = self.parseEndHour()
        self.frequency = self.parseFrequency()
        self.room = self.parsedPage.tables[0][self.tableNumber][3]
        self.location = self.parseLocation()
        self.formation = self.parsedPage.tables[0][self.tableNumber][4]
        self.types = ['Laborator', 'Seminar', 'Curs']
        self.type = self.parsedPage.tables[0][self.tableNumber][5]
        self.color = self.parseColor()
        self.subject = parsedPage.tables[0][self.tableNumber][6]
        self.teacher = parsedPage.tables[0][self.tableNumber][7]
        self.event = self.createEvent()

    def parseDay(self):
        finalDay = self.parsedPage.tables[0][self.tableNumber][0]
        weekdays_ro = ['Luni', 'Marti', 'Miercuri', 'Joi', 'Vineri']
        weekdays_no = ['09-30', '10-01', '10-02', '10-03', '10-04']
        finalDay = weekdays_no[weekdays_ro.index(finalDay)]
        return finalDay

    def parseStartHour(self):
        hours_raw = self.parsedPage.tables[0][self.tableNumber][1]
        if len(hours_raw) == 4:
            return '2019-' + self.day + 'T' + '0' + hours_raw[0:1] + ':00:00+03:00'
        else:
            return '2019-' + self.day + 'T' + hours_raw[0:2] + ':00:00+03:00'

    def parseEndHour(self):
        hours_raw = self.parsedPage.tables[0][self.tableNumber][1]
        if len(hours_raw) == 4:
            return '2019-' + self.day + 'T' + hours_raw[2:4] + ':00:00+03:00'
        else:
            return '2019-' + self.day + 'T' + hours_raw[3:5] + ':00:00+03:00'

    def parseFrequency(self):
        frequency_raw = self.parsedPage.tables[0][self.tableNumber][2]
        # TODO  NOT SURE WHAT the input means !!!!!!!!!!!!!!!
        if frequency_raw == 'sapt. 1':
            return 2
        elif frequency_raw == 'sapt. 2':
            return 3
        else:
            return 1

    def parseLocation(self):
        open_file = open("Legenda salilor.html")
        html_page = open_file.read()
        locationList = HTMLTableParser()
        locationList.feed(html_page)
        location = ''
        for i in locationList.tables[0]:
            if i[0] == self.room:
                location = i[1]
        return location

    def parseType(self):
        if self.parsedPage.tables[0][self.tableNumber][5] in self.types:
            return self.parsedPage.tables[0][self.tableNumber][5]
        else:
            return ''

    def parseColor(self):
        colors = ['11', '5', '9']
        return colors[self.types.index(self.type)]

    def createEvent(self):
        event = {
            'summary': self.subject,
            'location': self.location,
            'description': self.type + ', ' + self.room + ', ' + self.formation + ', ' + self.teacher,
            'start': {
                'dateTime': self.startHour,
                'timeZone': 'Europe/Bucharest',
            },

            'end': {
                'dateTime': self.endHour,
                'timeZone': 'Europe/Bucharest',
            },
            'recurrence': [
                'RRULE:FREQ=WEEKLY;INTERVAL=' + str(self.frequency) + ';UNTIL=20200530T000000Z'
            ],
            'colorId': self.color,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        return event

    def insertEvent(self):
        event = service.events().insert(calendarId='primary', body=self.event).execute()
        print(event)


file = open("orar.html")
html_page = file.read()
parsedPage = HTMLTableParser()

parsedPage.feed(html_page)
event = EventParser(parsedPage, 1)
event.insertEvent()

