"""
Pytide - A program that will parse a file containing NOAA station IDs,
request tide data from NOAA for each station, parse the data, format
the data neatly, and email all acquired data to the given email address.
"""

# OrderedDict allows the program to maintain user's input order.
from collections import OrderedDict

# Python's built-in configuration file parser. See below for more information:
#   https://docs.python.org/3/library/configparser.html
from configparser import ConfigParser

# Poor documentation for email.mime can be found below:
#   https://docs.python.org/3/library/email.mime.html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Jinja2 is a templating engine. It will handle the HTML for the email body.
#   https://palletsprojects.com/p/jinja/
from jinja2 import Environment, PackageLoader

import os           # os.path for cross-platform compatibility
import smtplib      # smtplib.SMTP for email server connections
import sys          # sys.argv for command line arguments
import requests     # requests for API calls and JSON decoding

# The sole configuration file is assumed to be named config.ini and is expected
# to reside in the same directory as this program.
CONFIG_FILE = 'config.ini'


class TideStation:
    """An object that holds important NOAA tide station information like
    the station ID number, the station's name, and the low and high
    tides at the station"""

    def __init__(self, station_id, station_name=None):
        self.id_ = station_id
        self.name = station_name
        self.latitude = None
        self.longitude = None
        self.tide_events = []
        self._fill_empty_data()

    def __str__(self):
        string_output = (f'ID# {self.id_}: {self.name} ({self.latitude}, '
                         f'{self.longitude}')
        for tide in self.tide_events:
            string_output += f'\n\t{tide}'
        return string_output

    def _request_metadata(self):
        """Return a dictionary containing the station's metadata."""
        # The API used here is specifically for gathering metadata about the
        # NOAA stations. It provides us with things like the name, latitude and
        # longitude of the station. For more info, see below.
        #   https://api.tidesandcurrents.noaa.gov/mdapi/prod/
        metadata_url = (f'https://api.tidesandcurrents.noaa.gov/mdapi/prod/'
                        f'webapi/stations/{self.id_!s}.json')

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
        base_url = ('https://api.tidesandcurrents.noaa.gov/api/prod/'
                    'datagetter?')
        parameters = [f'station={self.id_!s}',
                      f'date=today',
                      f'product=predictions',
                      f'datum=MLLW',
                      f'units=english',
                      f'time_zone=lst_ldt',
                      f'format=json',
                      f'interval=hilo',
                      f'application=Pytide']
        full_url = base_url + '&'.join(parameters)

        # Use requests to get a response and return a dictionary from the JSON.
        response = requests.get(full_url)
        return response.json()

    def _fill_empty_data(self):
        """This class has a number of empty attributes. It's time to
        fill them in."""

        # dictionary containing station's name, latitude, and longitude
        meta_dict = self._request_metadata()

        # Start filling in the metadata.
        if not self.name:
            # A human-readable description is useful to have.
            self.name = meta_dict['stations'][0]['name']
        # Knowing the location could be pretty useful too.
        self.latitude = meta_dict['stations'][0]['lat']
        self.longitude = meta_dict['stations'][0]['lng']

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
                tide_time = event['t']    # date/time value: 'YYYY-MM-DD HH:MM'
                tide_level = event['v']   # water change value: '1.234'
                tide_type = 'Low'
                if event['type'] == 'H':  # tide type value: 'L' or 'H'
                    tide_type = 'High'

                tide_string = f'{tide_time} {tide_type} ({tide_level})'

                # Append this tide to the running list.
                self.tide_events.append(tide_string)
        else:
            self.tide_events.append(f'Error retrieving tides for station '
                                    f'{self.id_}.')


def main(argv):
    """Driver function for program.

    Can be called with or without a command line argument indicating a user-
    specified configuration file.
    """
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

    # Bring it all together - compose and send those emails.
    email_tides(station_list, email_set, smtp_dict)


def email_tides(station_list, email_set, smtp_dict):
    """Create an email containing station data from each of the stations
    in the given station_list. Send that email to each address in the
    email_set."""
    sender = smtp_dict['sender']
    host = smtp_dict['host']
    port = int(smtp_dict['port'])
    user = smtp_dict['user']
    password = smtp_dict['password']

    # Create an SMTP connection.
    smtp_connection = smtplib.SMTP(host=host, port=port)

    # Enter TLS mode. Everything from here, on is encrypted.
    smtp_connection.starttls()
    smtp_connection.login(user=user, password=password)

    # Craft a single HTML message body for use in all of the messages.
    body_html = gen_html_body(station_list)

    # We're going to create one message for each recipient because it doesn't
    # seem to be possible change the 'To' field for each message. After I
    # dissect the MIMEMultipart module to figure out what makes it tick, I may
    # rewrite this entire function. For now, working code beats broken code.
    for address in email_set:
        # "Multipurpose Internet Mail Extensions is an internet standard that
        # extends the format of email..." There are multiple parts to it.
        # See below:
        #   https://en.wikipedia.org/wiki/MIME
        message = MIMEMultipart()

        message['From'] = sender
        message['To'] = address
        message['Subject'] = 'Your customized Pytide report'

        # HTML is swell, but we want a MIMEText object for our message body.
        message_html = MIMEText(body_html, 'html')
        message.attach(message_html)

        # method for calling SMTP.sendmail() with a Message object
        smtp_connection.send_message(message)

    # Terminate the SMTP session and close the connection.
    smtp_connection.quit()


def gen_html_body(station_list):
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
    return email_template.render(station_list=station_list)


if __name__ == '__main__':
    # Leave "python pytide.py" behind. We know that much already.
    main(sys.argv[1:])
