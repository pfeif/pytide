"""
Pytide: An application for retrieving tide predictions from the National
Oceanic and Atmospheric Administration (NOAA) and emailing that data to
a list of recipients.
"""

import os
import sys
from configparser import ConfigParser
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import make_msgid
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
OUTPUT_FILE = 'output.txt'      # like CONFIG_FILE but for output


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
    map_image: bytes = field(init=False, repr=False)
    map_image_cid: str = field(init=False, repr=False)

    def __post_init__(self):
        # Make sure we have metadata before proceeding.
        if not TideStation._metadata_list:
            TideStation._get_all_metadata()

        # Fill in the gaps in our data.
        self._add_station_metadata()
        self._add_map_image()
        self._add_tide_predictions()

    def __str__(self) -> str:
        output = f'ID# {self.id_}: {self.name} '\
                 f'({self.latitude}, {self.longitude})'
        for tide in self.tide_events:
            output += f'\n\t{tide}'
        return output

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

        # Use Requests to get a response and set _metadata_dict to contain only
        # the "stations" portion of the returned JSON.
        response = requests.get(metadata_url)
        cls._metadata_list = response.json()['stations']

    def _add_station_metadata(self) -> None:
        """Add the station name (if not present), latitude, and
        longitude to the TideStation."""
        for station in TideStation._metadata_list:
            if self.id_ == station['id']:
                if not self.name:
                    self.name = station['name']

                # Six digits of decimal precision is plenty.
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

        # Get a response from the API and hold on to the raw image bytes.
        response = requests.get(api_url, params=parameters, stream=True)
        self.map_image = response.content

        # Set a Content-ID string for use in the HTML and EmailMessage later.
        self.map_image_cid = make_msgid(self.id_, 'pfeifer.co')

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

        # Use Requests to get a response and create a dictionary from the JSON.
        predictionary = requests.get(api_url, params=parameters).json()

        # Verify prediction data is present.
        if 'predictions' in predictionary:
            # Start filling in the prediction data. The direct access would
            # appear as something along the lines of:
            #   predictionary['predictions'][0]['type'],
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
    # config.items returns a list of (name, value) tuples for each section.
    TideStation.api_key = config.get('GOOGLE MAPS API', 'key')
    station_list = [TideStation(item[0], item[1])
                    for item in config.items('STATIONS')]
    email_set = {item[0] for item in config.items('RECIPIENTS')}
    smtp_dict = dict(config.items('SMTP SERVER'))

    # Craft a single HTML message body for use in all of the messages.
    message = compose_email(station_list)

    # Save the message body locally for reviewing?
    if SAVE_EMAIL_BODY:
        with open(OUTPUT_FILE, mode='wt', encoding='utf-8') as file:
            file.writelines(message.as_string())

    # Compose and send those emails.
    if SEND_EMAIL:
        send_email(message, email_set, smtp_dict)


def compose_email(station_list: list[TideStation]) -> EmailMessage:
    """Create an email containing station data from each of the stations
    in the given station_list."""
    # Create a plain text version of the message with only station and tides.
    plain_body = '\n\n'.join(str(station) for station in station_list)

    # Move on to creating an HTML message body. Jinja's Environment is used to
    # load templates and store config settings.
    jinja_env = Environment(
        loader=FileSystemLoader('templates'),   # sets the templates directory
        autoescape=True)                        # prevents cross-site scripting

    # Asks the loader for the template and returns a Template object.
    email_template = jinja_env.get_template('email-template.html')

    # Pass the station list as an argument to the email_template for processing
    # and rendering; then, return a Unicode string with the resulting HTML.
    html_body = email_template.render(station_list=station_list)

    # Create the message and add its primary parts. The EmailMessage class is
    # unnecessarily complicated, but behind the scenes, it automagically sets
    # header information and mutates the message structure to fit our needs.
    message = EmailMessage()
    message['Subject'] = 'Your customized Pytide report'
    message.set_content(plain_body)
    message.add_alternative(html_body, subtype='html')

    # Add the static map images as attachments to the message... This is not a
    # simple method call. I've debugged, followed the stack traces, generated
    # UML diagrams, and I finally understand - it's author(s) hold an unhealthy
    # view on mental anguish... Just give it raw image bytes, make sure the
    # string passed to cid has angle brackets around it, and make sure those
    # angle brackets are stripped from the cid in your HTML. Everything should
    # be fine.
    for station in station_list:
        message.add_attachment(station.map_image,
                               maintype='image',
                               subtype='png',
                               cid=station.map_image_cid)

    # Return the (mostly) complete EmailMessage for sending.
    return message


def send_email(message: EmailMessage, email_set: set[str],
               smtp_dict: dict[str, str]) -> None:
    """Send the email to each address in the email_set."""
    # The message has to come from someone.
    message['From'] = smtp_dict['sender']

    # Create a connection to the email server.
    with SMTP(smtp_dict['host'], int(smtp_dict['port'])) as connection:
        # Enter TLS mode. Everything from here, on is encrypted.
        connection.starttls()
        connection.login(smtp_dict['user'], smtp_dict['password'])

        # Each recipient should receive a copy.
        for address in email_set:
            if not message['To']:
                message['To'] = address
            else:
                message.replace_header('To', address)

            # Press send.
            connection.send_message(message)


if __name__ == '__main__':
    main(sys.argv[1:])
