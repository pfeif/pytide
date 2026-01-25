# Pytide

Pytide is designed to email a tide report to users for the tide stations they care about. This could
be useful for fishing, sailing, surfing, or any other case where tide data is important.
Configuration is handled simply in a single file, and the application can be scheduled to run using
a task scheduler like cron, systemd, or whatever else to send reports when the user desires.

The application is packaged as a standard Python command-line tool and can be run:

- Directly with Python
- As an installed console script (pytide)
- Optionally using modern tooling such as uv or Docker

## Requirements

- [Google Maps Static][maps] API key

## Configuration

Pytide uses a single INI-style configuration file (`config.ini`). The file is not bundled with the
package and must be supplied by the user.

By default, Pytide looks for the configuration file in the following locations, in order:

- Path provided via the `--config-file` command-line option
- Path specified by the `PYTIDE_CONFIG_FILE` environment variable
- `./config.ini` (current working directory)
- `~/.config/pytide/config.ini`
- `/etc/pytide/config.ini`

### Stations

You can find tide stations near you by using the [NOAA's Tides & Currents][noaa] page.

Enter the station IDs in your configuration file. You can also specify names for the stations. The
idea is that it may be more useful to use "Bob's beach house" as a descriptor than whatever the
station's actual name is.

Follow the instructions in [`config.ini`](./config.ini).

### Recipients

Enter the email addresses for each recipient that should receive a copy of the email. These emails
will be sent individually. There will not be a single email with multiple recipients CC'd on it.

Follow the instructions in [`config.ini`](./config.ini).

### Email server settings

An email server is not provided with this application. You will need to use your own email address
and find its SMTP server settings. A stubbed example has been provided, and there are slightly more
detailed notes for Gmail users in the configuration file.

Follow the instructions in [`config.ini`](./config.ini).

### Google maps

Normal interactive maps are not embeddable in emails. This project uses Google's
[Maps Static API][maps] to to provide the images. However, an API key is not provided with this
application. You must sign up for the service and provide your own API key in order to retrieve map
images.

This is not a free service. However, for personal use cases, you are very unlikely to make enough
API queries to get charged. Last I checked, it would take roughly 100,000 map images retrieved
before charges are incurred.

Follow the instructions in [`config.ini`](./config.ini).

Alternatively, the API key may be provided through the command line using the `--maps-api-key`
command line option or by specifying a `PYTIDE_MAPS_API_KEY` environment variable.

## Usage

### [System Python][python]

1. Install the package.

    ```text
    pip install .
    ```

1. Run the application using the default configuration file.

    ```text
    pytide
    ```

1. Optionally, pass a configuration file explicitly.

    ```text
    pytide --config-file /path/to/config.ini
    ```

You may also run pytide as a module.

```text
python -m pytide
```

### [uv][uv]

1. Install the dependencies.

    ```text
    uv sync
    ```

1. Run the application.

    ```text
    uv run pytide
    ```

1. If needed, specify the configuration file.

    ```text
    uv run pytide --config-file /path/to/config.ini
    ```

### [Docker][docker]

1. Ensure a config.ini file exists on the host system.
1. Run the container using Docker Compose.

    ```text
    docker compose up --detach
    ```

The provided [`compose.yaml`](./compose.yaml) mounts the configuration file into the container and
sets the required environment variable so Pytide can locate it.

## License

This project is licensed under the terms of the BSD 3-Clause License. See [LICENSE.md](./LICENSE.md)
for details.

[docker]: https://www.docker.com/
[maps]: https://developers.google.com/maps/documentation/maps-static/overview
[noaa]: https://tidesandcurrents.noaa.gov/
[python]: https://www.python.org/
[uv]: https://docs.astral.sh/uv/
