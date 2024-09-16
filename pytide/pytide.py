"""
Pytide: An application for retrieving tide predictions from the National Oceanic and Atmospheric
Administration (NOAA) and emailing them to a list of recipients.
"""

import os
import sys
from configparser import ConfigParser
from email.message import EmailMessage
from email.utils import make_msgid
from smtplib import SMTP

from jinja2 import Environment, FileSystemLoader
from station import Station

SEND_EMAIL = True
SAVE_EMAIL = False
SAVE_HTML = False
CODE_DIR = os.path.dirname(os.path.abspath(__file__))


def main(argv: list[str]):
    # Set the user's config file path based on optional command line input.
    if argv:
        config_path = os.path.abspath(argv[0])
    else:
        config_path = os.path.join(CODE_DIR, '..', 'config.ini')

    # Allow the user to exclude station names in the config.
    config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)

    with open(config_path, mode='rt', encoding='utf-8') as file:
        config.read_file(file)

    # Extract the user configuration settings.
    Station.api_key = config.get('GOOGLE MAPS API', 'key')
    tide_stations: list[Station] = [Station(item[0], item[1]) for item in config.items('STATIONS')]
    recipients: set[str] = {item[0] for item in config.items('RECIPIENTS')}
    smtp_settings = dict(config.items('SMTP SERVER'))

    # Craft a single HTML message body for use in all messages.
    message = compose_email(tide_stations)

    if SAVE_EMAIL:
        output_path = os.path.join(CODE_DIR, 'message.eml')

        with open(output_path, mode='wt', encoding='utf-8') as file:
            file.writelines(message.as_string())

    if SEND_EMAIL:
        send_email(message, recipients, smtp_settings)


def compose_email(stations: list[Station]) -> EmailMessage:
    """Return one EmailMessage containing data from each station in stations."""
    plain_text_body = '\n\n'.join(str(station) for station in stations)

    templates_path = os.path.join(CODE_DIR, 'templates')

    jinja_env = Environment(
        loader=FileSystemLoader(templates_path),  # sets the templates directory
        autoescape=True)  # prevents cross-site scripting

    email_template = jinja_env.get_template('bootstrap-email-template.html')

    logo_image_cid = make_msgid('pytide-logo')

    html_body = email_template.render(tide_stations=stations, logo_cid=logo_image_cid)

    if SAVE_HTML:
        output_path = os.path.join(CODE_DIR, '..', 'message.html')

        with open(output_path, mode='wt', encoding='utf-8') as file:
            file.writelines(html_body)

    # The EmailMessage class is unnecessarily complicated, but behind the scenes, it automagically
    # sets header information and mutates the message structure to fit our needs.
    message = EmailMessage()
    message['Subject'] = 'Your customized Pytide report'
    message.set_content(plain_text_body)
    message.add_alternative(html_body, subtype='html')

    # Add the static map images as attachments to the message... This is not a simple method call.
    # I've debugged, followed the stack traces, generated UML diagrams, and I finally understand -
    # it's author(s) hold an unhealthy view on mental anguish... Just give it raw image bytes, make
    # sure the string passed to cid has angle brackets around it, and make sure those angle brackets
    # are stripped from the cid in your HTML. Everything should be fine.
    for station in stations:
        message.add_attachment(station.map_image, maintype='image', subtype='png', cid=station.map_image_cid)

    logo_path = os.path.join(CODE_DIR, 'assets', 'img', 'logo-192.png')

    with open(logo_path, 'rb') as file:
        logo_image_bytes = file.read()

    message.add_attachment(logo_image_bytes, maintype='image', subtype='png', cid=logo_image_cid)

    # Return the (mostly) complete EmailMessage for sending.
    return message


def send_email(message: EmailMessage, recipients: set[str], smtp_settings: dict[str, str]) -> None:
    """Send message to each recipient in recipients using smtp_settings."""
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