"""
Pytide: An application for retrieving tide predictions from the National
Oceanic and Atmospheric Administration (NOAA) and emailing them to a
list of recipients.
"""

# Type hint compatibility for version 3.7 & 3.8
# See PEP 585: https://www.python.org/dev/peps/pep-0585/
from __future__ import annotations

import os
import sys
from configparser import ConfigParser
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import make_msgid
from smtplib import SMTP
from typing import Any, ClassVar

import requests
from requests.exceptions import RequestException
from jinja2 import Environment, FileSystemLoader

CONFIG = 'config.ini'
SEND_EMAIL = True
SAVE_EMAIL_LOCALLY = False
OUTPUT = 'saved_message.eml'


@dataclass()
class TideStation:
    """A class that holds important NOAA tide station information like
    a station ID, a name, and tide events for the station"""
    # class variables
    _metadata: ClassVar[list[dict[str, Any]]] = []
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
        if not TideStation._metadata:
            TideStation._get_all_metadata()

        self._add_station_metadata()
        self._add_map_image()
        self._add_tide_predictions()

    def __str__(self) -> str:
        output = f'ID# {self.id_}: {self.name} ' \
                 f'({self.latitude}, {self.longitude})'
        for tide in self.tide_events:
            output += f'\n\t{tide}'
        return output

    @classmethod
    def _get_all_metadata(cls) -> None:
        """Get metadata for all TideStations."""
        # The API used here is specifically for gathering metadata about the
        # NOAA stations. It provides us with things like the name, latitude and
        # longitude of each station. For more info, see below.
        #   https://api.tidesandcurrents.noaa.gov/mdapi/prod/
        api_url = ('https://api.tidesandcurrents.noaa.gov/mdapi/prod'
                   '/webapi/stations.json?type=tidepredictions')

        try:
            response = requests.get(api_url)
            response.raise_for_status()

            cls._metadata = response.json()['stations']
        except RequestException as error:
            raise SystemExit(f'Unable to retrieve station metadata -> {error}')

    def _add_station_metadata(self) -> None:
        """Add station name (if not present), latitude, and longitude."""
        for station in TideStation._metadata:
            if self.id_ == station['id']:
                if not self.name:
                    self.name = station['name']

                # Six digits of decimal precision is plenty.
                self.latitude = round(station['lat'], 6)
                self.longitude = round(station['lng'], 6)
                break

    def _add_map_image(self) -> None:
        """Add a static map image for the station."""
        # Maps are not embeddable in email messages, so map images must be
        # static. They are stored with each TideStation so Jinja doesn't expose
        # our API key in the rendered HTML.
        #   https://developers.google.com/maps/documentation/maps-static/overview
        api_url = 'https://maps.googleapis.com/maps/api/staticmap'
        parameters = {'markers': f'{self.latitude},{self.longitude}',
                      'size': '320x280',
                      'scale': '1',
                      'zoom': '15',
                      'key': f'{TideStation.api_key}'}

        try:
            response = requests.get(api_url, params=parameters, stream=True)
            response.raise_for_status()

            self.map_image = response.content

            # Set a Content-ID for use in the HTML and EmailMessage later.
            self.map_image_cid = make_msgid(self.id_, 'pfeifer.co')
        except RequestException as error:
            print(f'Unable to retrieve map image for station {self.id_} -> '
                  f'{error}')

    def _add_tide_predictions(self) -> None:
        """Add tide predictions for the station."""
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
                      'application': 'Pytide: https://github.com/pfeif/pytide'}

        try:
            response = requests.get(api_url, params=parameters)
            response.raise_for_status()

            predictionary = response.json()
        except RequestException as error:
            raise SystemExit(f'Unable to retrieve tide predictions -> {error}')

        for event in predictionary['predictions']:
            date_time = event['t']  # 'YYYY-MM-DD HH:MM'
            water_change = event['v']  # '1.234'
            tide_type = 'High' if event['type'] == 'H' else 'Low'  # 'L' or 'H'
            tide_string = f'{date_time} {tide_type} ({water_change}\')'

            self.tide_events.append(tide_string)


def main(argv):
    # Set the user's config file path based on optional command line input.
    config_path = os.path.abspath(argv[0] if argv else CONFIG)

    # Allow the user to exclude station names in the config.
    config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)

    with open(config_path, mode='rt', encoding='utf-8') as file:
        config.read_file(file)

    # Extract the user configuration settings.
    TideStation.api_key = config.get('GOOGLE MAPS API', 'key')
    tide_stations: list[TideStation] = [TideStation(item[0], item[1])
                                        for item in config.items('STATIONS')]
    recipients: set[str] = {item[0] for item in config.items('RECIPIENTS')}
    smtp_settings = dict(config.items('SMTP SERVER'))

    # Craft a single HTML message body for use in all messages.
    message = compose_email(tide_stations)

    if SAVE_EMAIL_LOCALLY:
        with open(OUTPUT, mode='wt', encoding='utf-8') as file:
            file.writelines(message.as_string())

    if SEND_EMAIL:
        send_email(message, recipients, smtp_settings)


def compose_email(stations: list[TideStation]) -> EmailMessage:
    """Create an email containing station data from each of the stations
    in the given stations."""
    plain_text_body = '\n\n'.join(str(station) for station in stations)

    jinja_env = Environment(
        loader=FileSystemLoader('templates'),  # sets the templates directory
        autoescape=True)  # prevents cross-site scripting

    email_template = jinja_env.get_template('email-template.html')

    html_body = email_template.render(tide_stations=stations)

    # The EmailMessage class is unnecessarily complicated, but behind the
    # scenes, it automagically sets header information and mutates the message
    # structure to fit our needs.
    message = EmailMessage()
    message['Subject'] = 'Your customized Pytide report'
    message.set_content(plain_text_body)
    message.add_alternative(html_body, subtype='html')

    # Add the static map images as attachments to the message... This is not a
    # simple method call. I've debugged, followed the stack traces, generated
    # UML diagrams, and I finally understand - it's author(s) hold an unhealthy
    # view on mental anguish... Just give it raw image bytes, make sure the
    # string passed to cid has angle brackets around it, and make sure those
    # angle brackets are stripped from the cid in your HTML. Everything should
    # be fine.
    for station in stations:
        message.add_attachment(station.map_image,
                               maintype='image',
                               subtype='png',
                               cid=station.map_image_cid)

    # Return the (mostly) complete EmailMessage for sending.
    return message


def send_email(message: EmailMessage, recipients: set[str],
               smtp_settings: dict[str, str]) -> None:
    """Email each recipient."""
    message['From'] = smtp_settings['sender']

    with SMTP(smtp_settings['host'], int(smtp_settings['port'])) as connection:
        # Enter TLS mode. Everything from here, on is encrypted.
        connection.starttls()
        connection.login(smtp_settings['user'], smtp_settings['password'])

        for address in recipients:
            if not message['To']:
                message['To'] = address
            else:
                message.replace_header('To', address)

            connection.send_message(message)


if __name__ == '__main__':
    main(sys.argv[1:])
