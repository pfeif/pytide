# Pytide

## About

I wrote Pytide to simplify the work of getting daily high- and low-tide reports. It might be useful
for fishing, boating, or any other activity which revolves around the tides.

By updating the configuration file, the user can specify [NOAA tide stations][noaa] that they want
to see data for and add email addresses for each person that should see that data. The idea is to
set this program to run as a scheduled task at a preferred interval using a system like cron or
systemd. Of course, you could choose to run it manually too.

## Requirements

- A [currently-supported][python-support] version of [Python][python-download] (currently >= 3.9)
    - [Click][click]
    - [Jinja2][jinja]
    - [Requests][requests]
- [Google Maps Static][maps] API key
- [Git][git] (optional)

## Setup

- Clone (or download and unzip) this repository.
    - `git clone https://github.com/pfeif/pytide.git`
- Install dependencies (`requirements.txt` provided for pip)
    - `pip install -r requirements.txt`
- Edit `config.ini` with your favorite text editor or create multiple config files which can be
    specified through the command line.

## Usage

- Run manually by executing `python pytide/pytide.py` in your shell to use the default config file or
    `python pytide/pytide.py <custom config filename>`.
- Schedule with your task scheduler of choice using one of the commands above.

## License

This project is licensed under the terms of the MIT license. See [LICENSE.md](LICENSE.md) for
details.


[click]: https://click.palletsprojects.com/en/8.1.x/
[git]: https://git-scm.com/
[jinja]: https://jinja.palletsprojects.com/
[maps]: https://developers.google.com/maps/documentation/maps-static/overview
[noaa]: https://tidesandcurrents.noaa.gov/
[python-download]: https://www.python.org/
[python-support]: https://devguide.python.org/versions/
[requests]: https://requests.readthedocs.io/en/latest/
