"""
PyTide - A program that will parse a file containing NOAA station IDs,
request tide data from NOAA for each station, parse the data, format
the data neatly, and email all aquired data to the given email address
daily.
"""

import requests

STATION_ID_FILE = "./station_ids.txt"


class NOAAStation:
    '''An object that holds important NOAA tide station information like
    the station ID number, the station's name, and the low and high
    tides at the station'''
    def __init__(self, station_id, station_name):
        self.sid = station_id
        self.sname = station_name
        self.tide_events = []
        self.fill_tides()

    def __str__(self):
        output = ''
        output += '{0} - {1}\n'.format(self.sid, self.sname)
        for tide in self.tide_events:
            output += '\t{0}\n'.format(tide)
        return output

    def request_data(self):
        '''Requests data from the NOAA API and returns the result in
        JSON format.'''
        # The API requires the following fields. I've split them for the sake
        # of convenient editing later. See below for further explanation:
        # https://tidesandcurrents.noaa.gov/api/
        base_url = 'https://tidesandcurrents.noaa.gov/api/datagetter?'
        parameters = ['station={0!s}'.format(self.sid),
                      'date=today',
                      'product=predictions',
                      'datum=MLLW',
                      'units=english',
                      'time_zone=lst_ldt',
                      'format=json',
                      'interval=hilo',
                      'application=PyTide']
        full_url = base_url + '&'.join(parameters)

        # returns a dictionary of the parsed json
        return requests.get(full_url).json()

    def fill_tides(self):
        '''Fill the object's parameters with tidal data taken from a
        dictionary.'''
        # At this point, I expect to have a dictionary with a single key of
        # 'predictions'. Inside of that dictionary, I should probably have 4
        # separate dictionaries, each with a key of 'v', 'type', and 't'.
        # 'v' will hold a string of a float for the tide level. 'type' will
        # hold a string of either 'H' or 'L' indicating high or low tide. 't'
        # will hold a string with the date and time of the time formatted
        # 'YYYY-MM-DD HH:MM'.

        predict_dict = self.request_data()

        # The direct access would appear as something like:
        # predict_dict['predictions'][0]['type']
        for event in predict_dict['predictions']:
            tide_time = event['t']
            tide_level = event['v']
            tide_type = 'Low'
            if event['type'] == 'H':
                tide_type = 'High'

            tide_string = '{0} {1} ({2})'.format(tide_time, tide_type,
                                                 tide_level)

            self.tide_events.append(tide_string)


def main():
    """Driver function for program."""
    station_dict = org_input()
    station_list = []
    for station in station_dict:
        sid = station
        sname = station_dict[station]
        station_list.append(NOAAStation(sid, sname))

    for station in station_list:
        print(station)


def org_input():
    """Create a dictionary of NOAA stations for the given station ID
    file. The keys will be the station numbers, and the values will be
    the station name. Both pieces of information come directly from the
    user's text file."""
    stations = dict()
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
            stations[station_id] = station_name

    # tidy up
    station_file.close()
    return stations

# def email_data():
#     pass


if __name__ == '__main__':
    main()
