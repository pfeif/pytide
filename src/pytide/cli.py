"""
Pytide: An application for retrieving tide predictions from the National Oceanic and Atmospheric
Administration (NOAA) and emailing them to a list of recipients.
"""

import os
from configparser import ConfigParser
from email.message import EmailMessage
from pathlib import Path

import click
from platformdirs import user_config_dir

from pytide.astronomy.service import hydrate_astronomical_data
from pytide.database.cache import delete_cache
from pytide.email import service
from pytide.maps.service import hydrate_map_image
from pytide.metadata.service import hydrate_metadata
from pytide.models.station import Station
from pytide.predictions.service import hydrate_predictions


@click.command(context_settings={'auto_envvar_prefix': 'PYTIDE'})
@click.option('--config-file', show_envvar=True, help='Use a custom configuration file')
@click.option(
    '--maps-api-key',
    show_envvar=True,
    help='Your Google Maps Static API key (Overrides value in configuration file)',
)
@click.option(
    '--send/--no-send',
    'send_email',
    default=True,
    show_default=True,
    help='Send the email to recipients',
)
@click.option('--save-email', is_flag=True, help='Save the email message locally')
@click.option('--save-html', is_flag=True, help='Save the HTML message body locally')
@click.option('--clear-cache', is_flag=True, help='Delete the local cache database and exit')
def main(
    config_file: str,
    maps_api_key: str,
    send_email: bool,
    save_email: bool,
    save_html: bool,
    clear_cache: bool,
) -> None:
    if clear_cache:
        _delete_cache()
        return

    config_path = Path(config_file) if config_file else _find_default_config()

    if not config_path:
        raise click.UsageError('No configuration file found. Use --config-file or set PYTIDE_CONFIG_FILE.')

    config_path = config_path.expanduser().resolve()

    config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)

    with config_path.open(encoding='utf-8') as file:
        config.read_file(file)

    maps_api_key = maps_api_key if maps_api_key else config.get('GOOGLE MAPS API', 'key')
    stations: list[Station] = [Station(item[0], item[1]) for item in config.items('STATIONS')]
    recipients: set[str] = {item[0] for item in config.items('RECIPIENTS')}
    smtp_settings = dict(config.items('SMTP SERVER'))

    for station in stations:
        hydrate_metadata(station)
        hydrate_predictions(station)
        hydrate_map_image(station, maps_api_key)
        hydrate_astronomical_data(station)

    message: EmailMessage = service.create_message(stations, save_html, save_email)

    if send_email:
        service.send_message(message, recipients, smtp_settings)


def _find_default_config() -> Path | None:
    candidates: list[str | Path | None] = [
        os.environ.get('PYTIDE_CONFIG_FILE'),
        Path.cwd() / 'config.ini',
        Path(user_config_dir('pytide')) / 'config.ini',
    ]

    for candidate in candidates:
        if not candidate:
            continue

        path = Path(candidate)
        if path.is_file():
            return path

    return None


def _delete_cache() -> None:
    cache_path, deleted = delete_cache()

    if deleted:
        click.echo(f'Successfully deleted cache at {cache_path}')
    else:
        click.echo(f'No cache found to delete at {cache_path}')
