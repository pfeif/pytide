"""
PyTide - A program that will parse a file containing NOAA station IDs,
request tide data from NOAA for each station, parse the data, format
the data neatly, and email all aquired data to the given email address
daily.
"""

import email
import smtplib
import requests

STATION_ID_FILE = "./station_ids.txt"
EMAIL_FILE = "./email_addresses.txt"


class TideStation:
    '''An object that holds important NOAA tide station information like
    the station ID number, the station's name, and the low and high
    tides at the station'''
    def __init__(self, station_id, station_name=None):
        self.id = station_id
        self.name = station_name
        self.latitude = None
        self.longitude = None
        self.tide_events = []
        self._fill_empty_data()
        # self._fill_metadata()
        # self._fill_tides()

    def __str__(self):
        string_output = ('ID# {0}: {1} ({2}, {3})'.format(
            self.id, self.name, self.latitude, self.longitude))
        for tide in self.tide_events:
            string_output += '\n\t{0}'.format(tide)
        return string_output

    def _request_metadata(self):
        '''Return a dictionary containing the station's metadata.'''
        # The API used here is specifically for gathering metadata about the
        # NOAA stations. It provides us with things like the name, latitude and
        # longitude of the station. For more info, see below.
        # https://tidesandcurrents.noaa.gov/mdapi/latest/
        metadata_url = ('https://tidesandcurrents.noaa.gov/mdapi/v0.6/webapi/'
                        'stations/{0!s}.json'.format(self.id))

        # use requests to get the response and return a dict from the json
        response = requests.get(metadata_url)
        return response.json()

    def _request_prediction(self):
        '''Requests data from the NOAA API and returns the result in
        JSON format.'''
        # The API used here is for gathering tide predictions from the NOAA
        # station. It'll give us the times and levels of the high / low tides.
        # This API requires the following fields. I've split them for the sake
        # of convenient editing later. See below for further explanation:
        # https://tidesandcurrents.noaa.gov/api/
        base_url = 'https://tidesandcurrents.noaa.gov/api/datagetter?'
        parameters = ['station={0!s}'.format(self.id),
                      'date=today',
                      'product=predictions',
                      'datum=MLLW',
                      'units=english',
                      'time_zone=lst_ldt',
                      'format=json',
                      'interval=hilo',
                      'application=PyTide']
        full_url = base_url + '&'.join(parameters)

        # use requests to get the response and return a dict from the json
        response = requests.get(full_url)
        return response.json()

    def _fill_empty_data(self):
        '''This class has a number of empty attributes. It's time to
        fill them in.'''

        # dictionary containing station's name, latitude, and longitude
        meta_dict = self._request_metadata()

        # dictionary containing station's tide level, tide type, and time.
        predict_dict = self._request_prediction()

        # Start filling in the metadata.
        if self.name is None:
            # A human-readable description is useful to have.
            self.name = meta_dict['stations'][0]['name']
        # Knowing the location could be pretty useful too.
        self.latitude = meta_dict['stations'][0]['lat']
        self.longitude = meta_dict['stations'][0]['lng']

        # Start filling in the prediction data. The direct access would appear
        # as something along the lines of:
        #   predict_dict['predictions'][0]['type']
        # where the 0th list entry is the first tide event, 1st would be
        # second, and so forth.
        for event in predict_dict['predictions']:
            tide_time = event['t']      # date/time value: 'YYYY-MM-DD HH:MM'
            tide_level = event['v']     # water change value: '1.234'
            tide_type = 'Low'
            if event['type'] == 'H':    # tide type value: 'L' or 'H'
                tide_type = 'High'

            tide_string = '{0} {1} ({2})'.format(tide_time, tide_type,
                                                 tide_level)

            # Append this tide to the running list.
            self.tide_events.append(tide_string)


def main():
    """Driver function for program."""
    # gather the station IDs from the user's file
    station_dict = read_station_file()

    # create station objects for them, and put them in a list
    station_list = []
    for key in station_dict:
        station_id = key
        station_name = station_dict[key]
        station_list.append(TideStation(station_id, station_name))

    # read the email addresses from the user's file, and put them in a set
    email_set = read_email_addresses()

    for key in station_list:
        print(key)
        print()


def read_station_file():
    """Create a dictionary of NOAA stations for the given station ID
    file. The keys will be the station numbers, and the values will be
    the station name. Both pieces of information come directly from the
    user's text file."""
    station_dict = dict()
    station_file = open(STATION_ID_FILE)

    # check each line in the user's text file
    for line in station_file:
        # exclude comments and blank lines
        if not line.startswith('#') and not line.isspace():
            # station IDs are 7 digits
            station_id = line[:7]
            # that leaves the rest as a descriptor
            station_name = line.rstrip()[8:]
            # create / update the dictionary entry
            station_dict[station_id] = station_name

    # tidy up
    station_file.close()
    return station_dict


def read_email_addresses():
    '''Return a set of email addresses based on the user's text file.'''
    # the set won't allow duplicate email addresses
    email_set = set()
    email_file = open(EMAIL_FILE)

    # check each line in the email file
    for line in email_file:
        # exclude comments and blank lines
        if not line.startswith('#') and not line.isspace():
            # add the address to the set
            email_set.add(line)

    # clean up after ourselves
    email_file.close()

    return email_set


if __name__ == '__main__':
    main()
