"""
Pytide - A program that will parse a file containing NOAA station IDs,
request tide data from NOAA for each station, parse the data, format
the data neatly, and email all acquired data to the given email address.
"""

# OrderedDict allows the program to maintain user's input order.
from collections import OrderedDict

# Python's built-in configuration file parser.
from configparser import ConfigParser

# The preferred method of representing email since 3.6.
from email.message import EmailMessage

# SMTP for email server connections
from smtplib import SMTP

# Jinja2 is a templating engine. It will handle the HTML for the email body.
#   https://palletsprojects.com/p/jinja/
from jinja2 import Environment, PackageLoader

import os           # os.path for cross-platform compatibility
import sys          # sys.argv for command line arguments
import requests     # requests for API calls and JSON decoding

# The sole configuration file is assumed to be named config.ini and is expected
# to reside in the same directory as this program.
CONFIG_FILE = 'config.ini'

# There may be a situation where one wants to save the generated email body to
# disk for viewing instead of emailing it to recipients.
SEND_EMAIL = True  # send email if true
SAVE_EMAIL_BODY = False  # save email body if true
OUTPUT_FILE = 'output.html'  # like CONFIG_FILE but for output


class TideStation:
    """An object that holds important NOAA tide station information like
    the station ID number, the station's name, and the low and high
    tides at the station"""
    # a dictionary to hold all stations' metadata
    _metadata_dict = []

    def __init__(self, station_id, station_name=None):
        self.id_ = station_id
        self.name = station_name
        self.latitude = None
        self.longitude = None
        self.tide_events = []

        # Make one API call to retrieve metadata for ALL stations and read data
        # as needed.
        if not TideStation._metadata_dict:
            TideStation._metadata_dict = TideStation._request_metadata()

        # Fill missing metadata and tide events.
        self._fill_empty_data()

    def __str__(self):
        string_output = (f'ID# {self.id_}: {self.name} ({self.latitude}, '
                         f'{self.longitude})')
        for tide in self.tide_events:
            string_output += f'\n\t{tide}'
        return string_output

    @staticmethod
    def _request_metadata():
        """Return a dictionary containing the station's metadata."""
        # The API used here is specifically for gathering metadata about the
        # NOAA stations. It provides us with things like the name, latitude and
        # longitude of the station. For more info, see below.
        #   https://api.tidesandcurrents.noaa.gov/mdapi/prod/
        metadata_url = ('https://api.tidesandcurrents.noaa.gov/mdapi/prod'
                        '/webapi/stations.json?type=tidepredictions')

        # Use requests to get a response and return a dictionary from the JSON.
        response = requests.get(metadata_url)
        return response.json()

    def _request_predictions(self):
        """Return a dictionary containing the station's prediction data."""
        # The API used here is for gathering tide predictions from the NOAA
        # station. It'll give us the times and levels of the high / low tides.
        # This API requires the following fields. I've split them for the sake
        # of convenient editing later. See below for further explanation:
        #   https://api.tidesandcurrents.noaa.gov/api/prod/
        api_url = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'
        parameters = {'station': f'{self.id_!s}',
                      'date': 'today',
                      'product': 'predictions',
                      'datum': 'MLLW',
                      'units': 'english',
                      'time_zone': 'lst_ldt',
                      'format': 'json',
                      'interval': 'hilo',
                      'application': 'Pytide'}

        # Use requests to get a response and return a dictionary from the JSON.
        response = requests.get(api_url, params=parameters)
        return response.json()

    def _fill_empty_data(self):
        """Fill in the empty attributes of this station."""
        # Start filling in the metadata.
        for station in TideStation._metadata_dict['stations']:
            if self.id_ == station['id']:
                if not self.name:
                    # A human-readable description is useful to have.
                    self.name = station['name']

                # Knowing the location could be pretty useful too.
                self.latitude = station['lat']
                self.longitude = station['lng']

                # All done. Stop looking.
                break

        # dictionary containing station's tide change, tide type, and time
        predict_dict = self._request_predictions()

        # Verify prediction data is present.
        if 'predictions' in predict_dict:
            # Start filling in the prediction data. The direct access would
            # appear as something along the lines of:
            #   predict_dict['predictions'][0]['type'],
            # where the 0th list entry is the first tide event, 1st would be
            # second, and so forth.
            for event in predict_dict['predictions']:
                tide_time = event['t']   # date/time value: 'YYYY-MM-DD HH:MM'
                tide_level = event['v']  # water change value: '1.234'
                # tide type value: 'L' or 'H'
                tide_type = 'High' if event['type'] == 'H' else 'Low'
                tide_string = f'{tide_time} {tide_type} ({tide_level}\')'

                # Append this tide to the running list.
                self.tide_events.append(tide_string)
        else:
            self.tide_events.append(f'Error retrieving tides for station '
                                    f'{self.id_}.')


def main(argv):
    """Driver function for program.

    Can be called with or without a command line argument indicating a user-
    specified configuration file."""
    config_path = os.path.abspath(CONFIG_FILE)

    # Set different config file path based on optional user input.
    if argv:
        config_path = os.path.abspath(argv[0])

    # It will behoove us to allow non-values for the sake of giving users the
    # option to not include a station description.
    config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)

    # ConfigParser.read_file(file object)... With open(path) closes the
    # file for us when we're done.
    with open(config_path) as file:
        config.read_file(file)

    # ConfigParser.items('SECTION') returns a list of tuples with the user's
    # entries. It goes something like this:
    #   config.items('STATIONS') -> [('ID#A, DescripA'), ('ID#B', 'DescripB')]
    #   config.items('RECIPIENTS') -> [(EmailA, ''), ('EmailB', '')]
    #   config.items('SMTP SERVER') -> [('port', '587'), ('etc', 'etc')]
    #   config.items('GOOGLE MAPS API') -> [('key', 'LongApiKeyFromGoogle')]
    station_dict = OrderedDict(config.items('STATIONS'))

    email_set = set()
    for tuple_ in config.items('RECIPIENTS'):
        email_set.add(tuple_[0])

    smtp_dict = dict(config.items('SMTP SERVER'))

    # Create a TideStation object for each ID, and add it to the list.
    station_list = []
    for key in station_dict:
        station_id = key
        station_name = station_dict[key]
        station_list.append(TideStation(station_id, station_name))

    # Craft a single HTML message body for use in all of the messages.
    body_html = gen_html_body(
        station_list, config.get('GOOGLE MAPS API', 'key'))

    # Save the message body locally for reviewing?
    if SAVE_EMAIL_BODY:
        with open(OUTPUT_FILE, 'w') as file:
            file.writelines(body_html)

    # Compose and send those emails.
    if SEND_EMAIL:
        email_tides(body_html, email_set, smtp_dict)


def email_tides(body_html, email_set, smtp_dict):
    """Create an email containing station data from each of the stations
    in the given station_list. Send that email to each address in the
    email_set."""
    # Create the message and add some primary parts.
    message = EmailMessage()
    message['From'] = smtp_dict['sender']
    message['Subject'] = 'Your customized Pytide report'

    # The content manager adds a Content-Type header specifying maintype as
    # 'message' and subtype as 'html' if it is specified.
    message.set_content(body_html, subtype='html')

    # Create a connection to the email server.
    with SMTP(smtp_dict['host'], smtp_dict['port']) as connection:
        # Enter TLS mode. Everything from here, on is encrypted.
        connection.starttls()
        connection.login(smtp_dict['user'], smtp_dict['password'])

        # Send one message per recipient.
        for address in email_set:
            if not message['To']:
                message['To'] = address
            else:
                message.replace_header('To', address)
            connection.send_message(message)


def gen_html_body(station_list, api_key):
    """Create an HTML message body for attachment to an email."""
    # Jinja is the templating engine that will create the HTML body for the
    # email. I chose Jinja because its used in Flask, and Flask is on my list
    # of things to pick up.

    # "The core component of Jinja is the Environment." It is used to store the
    # configuration.
    jinja_env = Environment(
        loader=PackageLoader('pytide'),  # sets the package name
        autoescape=True)                 # prevents cross-site scripting

    # Asks the loader for the template and returns a Template object.
    email_template = jinja_env.get_template('email-template.html')

    # Pass the station list as an argument to the email_template for processing
    # and rendering; then, return a Unicode string with the resulting HTML.
    return email_template.render(station_list=station_list, api_key=api_key)


if __name__ == '__main__':
    # Leave "python pytide.py" behind. We know that much already.
    main(sys.argv[1:])
