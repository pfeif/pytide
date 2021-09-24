"""
Pytide - A program that will parse a file containing NOAA station IDs,
request tide data from NOAA for each station, parse the data, format
the data neatly, and email all acquired data to the given email address.
"""

import base64
import os
import sys
from configparser import ConfigParser
from dataclasses import dataclass, field
from email.message import EmailMessage
from smtplib import SMTP
from typing import Any, ClassVar

import requests
from jinja2 import Environment, FileSystemLoader

# The sole configuration file is assumed to be named config.ini and is expected
# to reside in the same directory as this program.
CONFIG_FILE = 'config.ini'

# There may be a situation where one wants to save the generated email body to
# disk for viewing instead of emailing it to recipients.
SEND_EMAIL = True               # send email if true
SAVE_EMAIL_BODY = False         # save email body if true
OUTPUT_FILE = 'output.html'     # like CONFIG_FILE but for output


@dataclass()
class TideStation:
    """A class that holds important NOAA tide station information like
    a station ID, a name, and tide events for the station"""
    # class variables
    _metadata_list: ClassVar[list[dict[str, Any]]] = []
    api_key: ClassVar[str]

    # instance variables
    id_: str
    name: str = field(default='')
    latitude: float = field(init=False)
    longitude: float = field(init=False)
    tide_events: list[str] = field(default_factory=list, init=False)
    map_image: str = field(init=False, repr=False)

    def __post_init__(self):
        # Make sure we have metadata
        if not TideStation._metadata_list:
            TideStation._get_all_metadata()

        # Fill in the blanks.
        self._add_station_metadata()
        self._add_map_image()
        self._add_tide_predictions()

    @classmethod
    def _get_all_metadata(cls) -> None:
        """Return a dictionary containing ALL stations' metadata pulled
        from the NOAA metadata API."""
        # The API used here is specifically for gathering metadata about the
        # NOAA stations. It provides us with things like the name, latitude and
        # longitude of each station. For more info, see below.
        #   https://api.tidesandcurrents.noaa.gov/mdapi/prod/
        metadata_url = ('https://api.tidesandcurrents.noaa.gov/mdapi/prod'
                        '/webapi/stations.json?type=tidepredictions')

        # Use requests to get a response and set _metadata_dict to contain only
        # the "stations" portion of the JSON.
        response = requests.get(metadata_url)
        cls._metadata_list = response.json()['stations']

    def _add_station_metadata(self) -> None:
        """Add the station name (if not present), latitude, and
        longitude to the TideStation."""
        for station in TideStation._metadata_list:
            if self.id_ == station['id']:
                if not self.name:
                    self.name = station['name']
                self.latitude = round(station['lat'], 6)
                self.longitude = round(station['lng'], 6)
                break

    def _add_map_image(self) -> None:
        """Add a Google Maps image to the TideStation."""
        # Maps are not embeddable in email messages, so map images must be
        # static. They are stored with each TideStation so Jinja doesn't expose
        # our API key in the HTML.
        #   https://developers.google.com/maps/documentation/maps-static/overview
        api_url = 'https://maps.googleapis.com/maps/api/staticmap'
        parameters = {'markers': f'{self.latitude},{self.longitude}',
                      'size': '320x280',
                      'scale': '1',
                      'zoom': '15',
                      'key': f'{TideStation.api_key}'}

        # Get a response from the API, encode the retrieved image (.content) as
        # a Base64 bytes-like object, and assign the decoded string
        # representation of the Base64 image to self.map_image.
        response = requests.get(api_url, params=parameters, stream=True)
        self.map_image = base64.b64encode(response.content).decode('utf-8')

    def _add_tide_predictions(self) -> None:
        """Add NOAA tide data for the TideStation."""
        # The API used here is for gathering tide predictions from the NOAA
        # station. It'll give us the times and levels of the high / low tides.
        # See below for further explanation:
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

        # Use requests to get a response and create a dictionary from the JSON.
        predictionary = requests.get(api_url, params=parameters).json()

        # Verify prediction data is present.
        if 'predictions' in predictionary:
            # Start filling in the prediction data. The direct access would
            # appear as something along the lines of:
            #   predict_dict['predictions'][0]['type'],
            # where the 0th list entry is the first tide event, 1st would be
            # second, and so forth.
            for event in predictionary['predictions']:
                tide_time = event['t']   # date/time value: 'YYYY-MM-DD HH:MM'
                tide_level = event['v']  # water change value: '1.234'
                # tide type value: 'L' or 'H'
                tide_type = 'High' if event['type'] == 'H' else 'Low'
                tide_string = f'{tide_time} {tide_type} ({tide_level}\')'

                # Append this tide to the running list.
                self.tide_events.append(tide_string)
        else:
            self.tide_events.append('Error retrieving tides for station '
                                    f'{self.id_}.')


def main(argv):
    """Driver function for program.

    Can be called with or without a command line argument indicating a user-
    specified configuration file."""
    # Set the user's config file path based on optional command line input.
    config_path = os.path.abspath(argv[0] if argv else CONFIG_FILE)

    # Give the user the choice of excluding station names in the config.
    config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)

    # Read in that configuration data.
    with open(config_path, mode='rt', encoding='utf-8') as file:
        config.read_file(file)

    # Extract the user's config settings into more workable chunks.
    TideStation.api_key = config.get('GOOGLE MAPS API', 'key')
    station_list = [TideStation(item[0], item[1])
                    for item in config.items('STATIONS')]
    email_set = {item[0] for item in config.items('RECIPIENTS')}
    smtp_dict = dict(config.items('SMTP SERVER'))

    # Craft a single HTML message body for use in all of the messages.
    message_body = compose_email(station_list)

    # Save the message body locally for reviewing?
    if SAVE_EMAIL_BODY:
        with open(OUTPUT_FILE, mode='wt', encoding='utf-8') as file:
            file.writelines(message_body)

    # Compose and send those emails.
    if SEND_EMAIL:
        send_email(message_body, email_set, smtp_dict)


def compose_email(station_list):
    """Create an HTML message body for attachment to an email."""
    # Jinja's Environment is used to load templates and store config settings.
    jinja_env = Environment(
        loader=FileSystemLoader('templates'),   # sets the templates directory
        autoescape=True)                        # prevents cross-site scripting

    # Asks the loader for the template and returns a Template object.
    email_template = jinja_env.get_template('email-template.html')

    # Pass the station list as an argument to the email_template for processing
    # and rendering; then, return a Unicode string with the resulting HTML.
    return email_template.render(station_list=station_list)


def send_email(body_html, email_set, smtp_dict):
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


if __name__ == '__main__':
    main(sys.argv[1:])
