"""
Pytide: An application for retrieving tide predictions from the National Oceanic and Atmospheric
Administration (NOAA) and emailing them to a list of recipients.
"""
import os
from configparser import ConfigParser
from email.message import EmailMessage

import click
from models.station import Station
from services import email


@click.command()
@click.option('--config-file', show_envvar=True, help='Use a custom configuration file')
@click.option('--maps-api-key', show_envvar=True, allow_from_autoenv=True,
              help='Your Google Maps Static API key (Overrides value in configuration file)')
@click.option('--send/--no-send', 'send_email', default=True, show_default=True, allow_from_autoenv=True,
              help='Send the email to recipients')
@click.option('--save-email', is_flag=True, allow_from_autoenv=True, help='Save the email message locally')
@click.option('--save-html', is_flag=True, allow_from_autoenv=True, help='Save the HTML message body locally')
def main(config_file: str, maps_api_key: str, send_email: bool, save_email: bool, save_html: bool) -> None:
    """
    Retrieve tide predictions for NOAA tide stations and email them to recipients.\f

    :param str config_email: Optional configuration file.
    :param bool send_email: Flag for sending email
    :param bool save_email: Flag for saving email message locally
    :param bool save_html: Flag for saving HTML email message body locally
    """
    source_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the user's config file path based on optional command line input.
    if config_file:
        config_path = os.path.abspath(config_file)
    else:
        config_path = os.path.join(source_dir, '..', 'config.ini')

    # Allow the user to exclude station names in the config.
    config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)

    with open(config_path, mode='rt', encoding='utf-8') as file:
        config.read_file(file)

    # Set the user configuration settings.
    Station.api_key = maps_api_key if maps_api_key else config.get('GOOGLE MAPS API', 'key')
    stations: list[Station] = [Station(item[0], item[1]) for item in config.items('STATIONS')]
    recipients: set[str] = {item[0] for item in config.items('RECIPIENTS')}
    smtp_settings = dict(config.items('SMTP SERVER'))

    # Craft a single HTML message body for use in all messages.
    message: EmailMessage = email.create_message(source_dir, stations, save_html, save_email)

    if send_email:
        email.send_message(message, recipients, smtp_settings)


if __name__ == '__main__':
    main(auto_envvar_prefix='PYTIDE')
