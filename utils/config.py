from configobj import ConfigObj
from pymongo import MongoClient


def configure_from_file(path_to_file):
    ''' Parse configuration from file.

    @param: path_to_file Path to config file.

    '''

    return ConfigObj(path_to_file)

def configure_for_unittest():
    ''' Configures project for unit testing. '''

    config = ConfigObj('unittest.cfg')

    client = MongoClient()
    client.drop_database(config['database']['name'])
    del client

    return config
