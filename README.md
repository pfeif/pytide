# Pytide

Pytide is designed to email a tide report to users for the tide stations they care about. This could
be useful for fishing, sailing, surfing, or any other case where tide data is important.
Configuration is handled simply in a single file, and the application can be scheduled to run using
a task scheduler like cron, systemd, or whatever else to send reports when the user desires.

## Requirements

- [Python][python] (See [this link][python-support] for currently-supported versions)
    - [Click][click]
    - [Jinja2][jinja]
    - [Requests][requests]
- [Google Maps Static][maps] API key
- [Git][git] (Optional)

## Configuration

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

1. Clone this repository with `git clone https://github.com/pfeif/pytide.git`
2. Install the dependencies with `pip install -r requirements.txt`
3. Run the application using default configuration file with `python pytide/pytide.py` or specify a
    configuration file with `python pytide/pytide.py --config-file
    <custom config path and filename>`

## License

This project is licensed under the terms of the BSD 3-Clause License. See [LICENSE.md](./LICENSE.md)
for details.


[click]: https://click.palletsprojects.com/en/8.1.x/
[git]: https://git-scm.com/
[jinja]: https://jinja.palletsprojects.com/
[maps]: https://developers.google.com/maps/documentation/maps-static/overview
[noaa]: https://tidesandcurrents.noaa.gov/
[python]: https://www.python.org/
[python-support]: https://devguide.python.org/versions/
[requests]: https://requests.readthedocs.io/en/latest/