'''
PyTide - A program that will parse a file containing NOAA station IDs,
request tide data from NOAA for each station, parse the data, format
the data neatly, and email all aquired data to the given email address
daily.
'''

# Poor documentation for email.mime can be found below:
#   https://docs.python.org/3.5/library/email.mime.html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import os           # os.path for cross-platform compatibility
import smtplib      # smtplib.SMTP for email server connections
import sys          # sys.argv for command line arguments
import requests     # requests for API calls and JSON decoding

# These are the file names that the program will go to for the station IDs and
# the email addresses. They are assumed to be in the same directory as this
# file.
STATION_ID_FILE = 'station_ids.txt'
EMAIL_FILE = 'email_addresses.txt'

EMAIL_SENDER = 'sender@example.com'     # Replace with sender email.
SMTP_HOST = 'smtp.example.com'          # Replace with sender host.
SMTP_PORT = 587                         # Standard TLS port.
SMTP_USER = 'sender@example.com'        # Replace with sender user name.
SMTP_PASS = 'password'                  # Replace with sender password.


class TideStation:
    '''An object that holds important NOAA tide station information like
    the station ID number, the station's name, and the low and high
    tides at the station'''
    def __init__(self, station_id, station_name=None):
        self.id_ = station_id
        self.name = station_name
        self.latitude = None
        self.longitude = None
        self.tide_events = []
        self._fill_empty_data()

    def __str__(self):
        string_output = ('ID# {0}: {1} ({2}, {3})'.format(
            self.id_, self.name, self.latitude, self.longitude))
        for tide in self.tide_events:
            string_output += '\n\t{0}'.format(tide)
        return string_output

    def _request_metadata(self):
        '''Return a dictionary containing the station's metadata.'''
        # The API used here is specifically for gathering metadata about the
        # NOAA stations. It provides us with things like the name, latitude and
        # longitude of the station. For more info, see below.
        # https://tidesandcurrents.noaa.gov/mdapi/latest/
        metadata_url = ('https://tidesandcurrents.noaa.gov/mdapi/v0.6/webapi/'
                        'stations/{0!s}.json'.format(self.id_))

        # Use requests to get a response and return a dictionary from the JSON.
        response = requests.get(metadata_url)
        return response.json()

    def _request_predictions(self):
        '''Return a dictionary containing the station's prediction data.'''
        # The API used here is for gathering tide predictions from the NOAA
        # station. It'll give us the times and levels of the high / low tides.
        # This API requires the following fields. I've split them for the sake
        # of convenient editing later. See below for further explanation:
        # https://tidesandcurrents.noaa.gov/api/
        base_url = 'https://tidesandcurrents.noaa.gov/api/datagetter?'
        parameters = ['station={0!s}'.format(self.id_),
                      'date=today',
                      'product=predictions',
                      'datum=MLLW',
                      'units=english',
                      'time_zone=lst_ldt',
                      'format=json',
                      'interval=hilo',
                      'application=PyTide']
        full_url = base_url + '&'.join(parameters)

        # Use requests to get a response and return a dictionary from the JSON.
        response = requests.get(full_url)
        return response.json()

    def _fill_empty_data(self):
        '''This class has a number of empty attributes. It's time to
        fill them in.'''

        # dictionary containing station's name, latitude, and longitude
        meta_dict = self._request_metadata()

        # dictionary containing station's tide change, tide type, and time
        predict_dict = self._request_predictions()

        # Start filling in the metadata.
        if not self.name:
            # A human-readable description is useful to have.
            self.name = meta_dict['stations'][0]['name']
        # Knowing the location could be pretty useful too.
        self.latitude = meta_dict['stations'][0]['lat']
        self.longitude = meta_dict['stations'][0]['lng']

        # Start filling in the prediction data. The direct access would appear
        # as something along the lines of:
        #   predict_dict['predictions'][0]['type'],
        # where the 0th list entry is the first tide event, 1st would be
        # second, and so forth.
        for event in predict_dict['predictions']:
            tide_time = event['t']      # date/time value: 'YYYY-MM-DD HH:MM'
            tide_level = event['v']     # water change value: '1.234'
            tide_type = 'Low'
            if event['type'] == 'H':    # tide type value: 'L' or 'H'
                tide_type = 'High'

            tide_string = '{0} {1} ({2})'.format(tide_time, tide_type,
                                                 tide_level)

            # Append this tide to the running list.
            self.tide_events.append(tide_string)


def main(argv):
    '''Driver function for program.

    Can be called with or without command line arguments. If using
    command line arguments, both a station id file and an email address
    file must be included. Without those arguments, the program defaults
    to using station_ids.txt and email_addresses.txt for its input.
    '''
    station_path = os.path.abspath(STATION_ID_FILE)
    email_path = os.path.abspath(EMAIL_FILE)

    # Set file paths based on optional user input.
    if argv:
        station_path = os.path.abspath(argv[0])
        email_path = os.path.abspath(argv[1])

    # Gather the station IDs from the user's file.
    station_dict = read_station_file(station_path)

    # Gather the recepient email addresses from the user's file, and put them
    # in a set.
    email_set = read_email_file(email_path)

    # Create a TideStation object for each ID, and add it to the list.
    station_list = []
    for key in station_dict:
        station_id = key
        station_name = station_dict[key]
        station_list.append(TideStation(station_id, station_name))

    # Bring it all together - compose and send those emails.
    email_tides(station_list, email_set)


def read_station_file(station_path):
    '''Create a dictionary of TideStations for the given station ID
    file. The keys will be the station numbers, and the values will be
    the station name. Both pieces of information come directly from the
    user's text file.'''
    station_dict = dict()
    station_file = open(station_path)

    # Check each line in the user's file.
    for line in station_file:
        # Exclude comments and blank lines.
        if not line.startswith('#') and not line.isspace():
            # Station IDs are 7 digits.
            station_id = line[:7]
            # That leaves the rest as a descriptor.
            # Note: If there is no user-defined descriptor, station_name will
            #   remain an empty string.
            station_name = line.rstrip()[8:]
            # Create or update the dictionary entry.
            station_dict[station_id] = station_name

    # Tidy up.
    station_file.close()
    return station_dict


def read_email_file(email_path):
    '''Return a set of email addresses based on the user's text file.'''
    # Sets won't allow duplicate email addresses.
    email_set = set()
    email_file = open(email_path)

    # Check each line in the email file.
    for line in email_file:
        # Exclude comments and blank lines.
        if not line.startswith('#') and not line.isspace():
            # Add the address (with newline stripped) to the set.
            email_set.add(line.strip())

    # Clean up after ourselves.
    email_file.close()

    return email_set


def gen_html_body(station_list):
    '''Create an HTML message body for attachment to an email.'''
    # I'm sure there are a lot of options here, but this one is pretty straight
    # forward. Start building the HTML for the body and add as we go along.
    # See below for a quick reference from Python about the matter.
    #   https://docs.python.org/3.5/library/email-examples.html
    html = '<html><head></head><body>'
    for station in station_list:
        # The Google Maps url string for searching by coordinates is:
        #   https://www.google.com/maps/search/?api=1&query={lat},{long}
        maps_url = ('https://www.google.com/maps/search/?api=1&query={0},{1}'
                    .format(station.latitude, station.longitude))

        html += ('<p>ID# {0}: {1} <a href="{2}">({3}, {4})</a><br>'
                 .format(station.id_, station.name, maps_url, station.latitude,
                         station.longitude))

        for tide in station.tide_events:
            html += '&nbsp;&nbsp;&nbsp;&nbsp;{0}<br>'.format(tide)

        html += '<br></p>'

    # Finish off by closing the tags.
    html += '</body></html>'

    return html


def email_tides(station_list, email_addresses):
    '''Create an email containing station data from each of the stations
    in the given station_list. Send that email to each address in the
    email_addresses set.'''
    # Create an SMTP connection.
    smtp_connection = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
    # Enter TLS mode. Everything from here, on is encrypted.
    smtp_connection.starttls()
    smtp_connection.login(user=SMTP_USER, password=SMTP_PASS)

    # Craft a single HTML message body for use in all of the messages.
    body_html = gen_html_body(station_list)

    # We're going to create one message for each recipient because it doesn't
    # seem to be possible change the 'To' field for each message. After I
    # dissect the MIMEMultipart module to figure out what makes it tick, I may
    # rewrite this entire function. For now, working code beats broken code.
    for address in email_addresses:
        # "Multipurpose Internet Mail Extensions is an internet standard that
        # extends the format of email..." There are multiple parts to it.
        # See below:
        #   https://en.wikipedia.org/wiki/MIME
        message = MIMEMultipart()

        message['From'] = EMAIL_SENDER
        message['To'] = address
        message['Subject'] = 'Your customized PyTide report'

        # HTML is swell, but we want a MIMEText object for our message body.
        message_html = MIMEText(body_html, 'html')
        message.attach(message_html)

        # method for calling SMTP.sendmail() with a Message object
        smtp_connection.send_message(message)

    # Terminate the SMTP session and close the connection.
    smtp_connection.quit()

if __name__ == '__main__':
    # Leave "python pytide.py" behind. We know that much already.
    main(sys.argv[1:])
