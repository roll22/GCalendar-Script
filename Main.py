from __future__ import print_function
import datetime
from datetime import timedelta
import calendar
import pickle
import re
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


class EventParser:

    def __init__(self, page, table_no, week, index_from_page):
        self.parsedPage = page
        self.entryNumber = index_from_page
        self.table_no = table_no
        self.week = week
        self.day = self.parse_day()
        self.startHour = self.parse_start_hour()
        self.endHour = self.parse_end_hour()
        self.frequency = self.parse_frequency()
        self.room = self.parsedPage.tables[self.table_no][self.entryNumber][3]
        self.location = self.parse_location()
        self.formation = self.parsedPage.tables[self.table_no][self.entryNumber][4]
        self.types = ['Laborator', 'Seminar', 'Curs']
        self.type = self.parsedPage.tables[self.table_no][self.entryNumber][5]
        self.color = self.parse_color()
        self.subject = self.parsedPage.tables[self.table_no][self.entryNumber][6]
        self.teacher = self.parsedPage.tables[self.table_no][self.entryNumber][7]
        self.event = self.create_event()

    def parse_day(self):
        final_day = self.parsedPage.tables[self.table_no][self.entryNumber][0]
        weekdays_ro = ['Luni', 'Marti', 'Miercuri', 'Joi', 'Vineri']
        weekdays_no = self.week
        final_day = weekdays_no[weekdays_ro.index(final_day)]
        return final_day

    def parse_start_hour(self):
        hours_raw = self.parsedPage.tables[self.table_no][self.entryNumber][1]
        if len(hours_raw) == 4:
            return str(self.day) + 'T' + '0' + hours_raw[0:1] + ':00:00+03:00'
        else:
            return str(self.day) + 'T' + hours_raw[0:2] + ':00:00+03:00'

    def parse_end_hour(self):
        hours_raw = self.parsedPage.tables[self.table_no][self.entryNumber][1]
        if len(hours_raw) == 4:
            return str(self.day) + 'T' + hours_raw[2:4] + ':00:00+03:00'
        else:
            return str(self.day) + 'T' + hours_raw[3:5] + ':00:00+03:00'

    def parse_frequency(self):
        return self.parsedPage.tables[self.table_no][self.entryNumber][2]

    def parse_location(self):
        open_file = open("Legenda salilor.html")
        html_page1 = open_file.read()
        location_list = HTMLTableParser()
        location_list.feed(html_page1)
        location = ''
        for i in location_list.tables[0]:
            if i[0] == self.room:
                location = i[1]
        # TODO Vezi amu cauta salile la locatii mai exacte baga-le intr-o lista si asa
        return location

    def parse_type(self):
        if self.parsedPage.tables[self.table_no][self.entryNumber][5] in self.types:
            return self.parsedPage.tables[self.table_no][self.entryNumber][5]
        else:
            return ''

    def parse_color(self):
        colors = ['11', '5', '9']
        return colors[self.types.index(self.type)]

    def create_event(self):
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
            'colorId': self.color,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        return event

    def insert_event(self):
        # event = service.events().insert(calendarId='primary', body=self.event).execute()
        print('Event Created\n' + str(self.startHour) + '\n' + str(self.subject) + '\n')


class ScheduleParser:
    pass


class WeekParser:
    def __init__(self, activity, week_parity):
        print(activity.startDate)
        print("new week created " + activity.activity_name + '\n')
        self.weekDays = self.get_week_days(activity.startDate)
        for y in range(1, 21):
            event = EventParser(page=orarParsed, table_no=WeekParser.get_ind_for_group(grupa), week=self.weekDays, index_from_page=y)
            if event.subject in validSubjects and event.formation in [grupa, 'IE1', grupa+'/'+subgrupa]\
                    and activity.activity_name == 'activitate didactică':
                if event.frequency is 'sapt. 1' and week_parity % 2 == 1:
                    event.insert_event()
                    continue
                if event.frequency is 'sapt. 2' and week_parity % 2 == 0:
                    event.insert_event()
                    continue
                else:
                    event.insert_event()

    @staticmethod
    def get_ind_for_group(group):
        return int(group[len(group)-1])-1

    @staticmethod
    def get_week_days(start_date):
        returnable = []
        for x in range(7):
            returnable.append(start_date)
            start_date = start_date + timedelta(days=1)
        return returnable


class SemesterActivities:
    def __init__(self, activity):
        self.activity = activity
        self.startDate = self.start_date_parser()
        self.endDate = self.end_date_parser()
        self.activity_name = self.activity_name_parser()
        self.no_of_weeks = self.no_of_weeks_parser()
        self.weeks_creator()

    def start_date_parser(self):
        return datetime.date(int(self.activity[0][6:10]),
                             int(self.activity[0][3:5]),
                             int(self.activity[0][0:2]))

    def end_date_parser(self):
        return datetime.date(int(self.activity[0][19:23]),
                             int(self.activity[0][16:18]),
                             int(self.activity[0][13:15]))

    def activity_name_parser(self):
        return self.activity[1]

    def no_of_weeks_parser(self):
        regex = None
        try:
            regex = re.search("^[1-9][1-9]? ", self.activity[2])
        except IndexError:
            pass
        if regex is None:
            return 0
        else:
            indexes_of_number_of_weeks = regex.span()
            return int(self.activity[2][indexes_of_number_of_weeks[0]:indexes_of_number_of_weeks[1]])

    def weeks_creator(self):
        week_parity = 1
        for no in range(0, self.no_of_weeks):
            WeekParser(self, week_parity)
            week_parity += 1
            self.startDate = self.increment_week(self.startDate)

    @staticmethod
    def increment_week(date):
        return date + timedelta(weeks=1)


class SemesterStructure:
    def __init__(self, page):
        self.parsedStructure = page
        self.first_semester = self.parsedStructure.tables[0][1:8]
        self.structureEntryNumber = '1'
        for activity in self.first_semester:
            SemesterActivities(activity)



grupa = input("alege grupa (911-917): ")
subgrupa = input("alege subgrupa (1,2): ")


validSubjects = ['Algebra',
                 'Analiza matematica',
                 'Arhitectura sistemelor de calcul',
                 'Fundamentele programarii',
                 'Logica computationala',
                 'Algoritmica grafelor',
                 'Geometrie',
                 'Programare orientata obiect',
                 'Sisteme de operare',
                 'Sisteme dinamice',
                 'Structuri de date si algoritmi',
                 'Cerc de programare in C']


file = open("orar1.html", encoding='utf-8')
html_page = file.read()
orarParsed = HTMLTableParser()
orarParsed.feed(html_page)

file = open('Structura1.html', encoding='utf-8')
html_page = file.read()
parsedPage = HTMLTableParser()
parsedPage.feed(html_page)
parser = SemesterStructure(parsedPage)
