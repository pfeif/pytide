# Pytide

I wrote Pytide to simplify the work of getting daily high- and low-tide
reports. It might be useful for fishing, boating, or any other activity
which revolves aroung the tides.

By updating the configuration file, the user can specify NOAA tide stations
that he or she wants to see data for and add email addresses for each person
that should see that data. The idea is to set this program to run as a
scheduled task at a prefered interval using a system like cron or systemd.

### Prerequisites

- [Python 3.5 (or later)](https://www.python.org/downloads/)
- [Requests library for Python](http://docs.python-requests.org/en/master/)
  - type `pip install requests` into your shell
- [Git](https://git-scm.com/downloads)

### Installing

1. type `git clone https://github.com/pfeif/pytide.git` into your shell.
2. edit `config.ini` with your favorite text editor.
2. type `python pytide.py` into your shell.

## License

This project is licensed under the terms of the MIT license. See
[LICENSE.md](LICENSE.md) for details.
