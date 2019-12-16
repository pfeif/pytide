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

## Prerequisites

- [Python 3.5 (or later)](https://www.python.org/downloads/)
- [Requests library for Python](http://docs.python-requests.org/en/master/)
  - type `pip install requests` into your shell
- [Git](https://git-scm.com/downloads)

## Installing

 * Either
   * [clone this repository](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository): `git clone https://github.com/pfeif/pytide.git`
   * download and unzip this repo
 * edit `config.ini` with your favorite text editor.
 * type `python pytide.py` into your shell.

## License

This project is licensed under the terms of the MIT license. See
[LICENSE.md](LICENSE.md) for details.
