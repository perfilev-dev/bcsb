from configobj import ConfigObj


def configure_from_file(path_to_file):
    ''' Parse configuration from file.

    @param: path_to_file Path to config file.

    '''

    return ConfigObj(path_to_file)

def configure_for_unittest():
    ''' Configures project for unit testing. '''

    return NotImplemented
