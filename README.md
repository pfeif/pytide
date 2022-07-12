# Pytide

## About

I wrote Pytide to simplify the work of getting daily high- and low-tide
reports. It might be useful for fishing, boating, or any other activity which
revolves around the tides.

By updating the configuration file, the user can specify
[NOAA tide stations][noaa] that he or she wants to see data for and add email
addresses for each person that should see that data. The idea is to set this
program to run as a scheduled task at a preferred interval using a system like
cron or systemd. Of course, you could choose to run it manually too.

## Requirements

- A current version of [Python][python-download] (currently >= 3.7)
    - [Jinja2][jinja] library for Python
    - [Requests][requests] library for Python
- [Google Maps Static][maps] API key
- [Git][git] (optional)

## Usage

- Clone (or download and unzip) this repository.
- Install dependencies (`requirements.txt` provided for pip)
- Edit `config.ini` with your favorite text editor.
- Run by typing `python pytide.py` into your shell.

## License

This project is licensed under the terms of the MIT license. See
[LICENSE.md](LICENSE.md) for details.

[git]: https://git-scm.com/
[jinja]: https://palletsprojects.com/p/jinja/
[maps]: https://developers.google.com/maps/documentation/maps-static/overview
[noaa]: https://tidesandcurrents.noaa.gov/
[python-download]: https://www.python.org/
[requests]: https://requests.readthedocs.io/en/latest/