"""
Pytide: An application for retrieving tide predictions from the National Oceanic and Atmospheric
Administration (NOAA) and emailing them to a list of recipients.
"""

import os
from configparser import ConfigParser
from email.message import EmailMessage
from pathlib import Path

import click

from pytide.models.station import Station
from pytide.services import email


@click.command(context_settings={'auto_envvar_prefix': 'PYTIDE'})
@click.option('--config-file', show_envvar=True, help='Use a custom configuration file')
@click.option(
    '--maps-api-key',
    show_envvar=True,
    allow_from_autoenv=True,
    help='Your Google Maps Static API key (Overrides value in configuration file)',
)
@click.option(
    '--send/--no-send',
    'send_email',
    default=True,
    show_default=True,
    allow_from_autoenv=True,
    help='Send the email to recipients',
)
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
    config_path = Path(config_file) if config_file else find_default_config()

    if not config_path:
        raise click.UsageError('No configuration file found. Use --config-file or set PYTIDE_CONFIG_FILE.')

    config_path = config_path.expanduser().resolve()

    # Allow the user to exclude station names in the config.
    config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)

    with config_path.open(encoding='utf-8') as file:
        config.read_file(file)

    # Set the user configuration settings.
    Station.api_key = maps_api_key if maps_api_key else config.get('GOOGLE MAPS API', 'key')
    stations: list[Station] = [Station(item[0], item[1]) for item in config.items('STATIONS')]
    recipients: set[str] = {item[0] for item in config.items('RECIPIENTS')}
    smtp_settings = dict(config.items('SMTP SERVER'))

    package_root = Path(__file__).resolve().parent

    # Craft a single HTML message body for use in all messages.
    message: EmailMessage = email.create_message(package_root.as_posix(), stations, save_html, save_email)

    if send_email:
        email.send_message(message, recipients, smtp_settings)


def find_default_config() -> Path | None:
    """
    Search for a configuration file in well-known locations.
    """
    candidates: list[str | Path | None] = [
        os.environ.get('PYTIDE_CONFIG_FILE'),
        Path.cwd() / 'config.ini',
        Path.home() / '.config' / 'pytide' / 'config.ini',
        Path('/etc/pytide/config.ini'),
    ]

    for candidate in candidates:
        if not candidate:
            continue

        path = Path(candidate)
        if path.is_file():
            return path

    return None
