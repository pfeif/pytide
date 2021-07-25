# Pytide

## About

I wrote Pytide to simplify the work of getting daily high- and low-tide
reports. It might be useful for fishing, boating, or any other activity which
revolves around the tides.

By updating the configuration file, the user can specify
[NOAA tide stations](https://tidesandcurrents.noaa.gov/) that he or she wants
to see data for and add email addresses for each person that should see that
data. The idea is to set this program to run as a scheduled task at a prefered
interval using a system like cron or systemd. Of course, you could choose to
run it manually too.

## Requirements

* [A supported version of Python 3 (currently 3.6 or later)](https://www.python.org/downloads/)
  * [Jinja2 library for Python](https://jinja.palletsprojects.com/en/3.0.x/)
  * [Requests library for Python](https://2.python-requests.org/en/master/)
* [Git](https://git-scm.com/downloads) (optional)

## Usage

 * Clone (or download and unzip) this repository.
 * Install dependencies (`requirements.txt` provided for pip)
 * Edit `config.ini` with your favorite text editor.
 * Run by typing `python pytide.py` into your shell.

## License

This project is licensed under the terms of the MIT license. See
[LICENSE.md](LICENSE.md) for details.
