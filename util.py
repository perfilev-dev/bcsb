import __builtin__ as shared

from shutil import rmtree
from os import environ, path
from configobj import ConfigObj
from gettext import translation
from py2neo import authenticate, Graph


def get_translations(locales):
    ''' Returns translation dictionary for locales.

    @param: locales List of locales

    '''

    return dict([(locale, translation('default',
                                      localedir='locale',
                                      languages=[locale])) for locale in locales])


def configure_from_file(path_to_file):
    ''' Parse configuration from file.

    @param: path_to_file Path to config file.

    '''

    shared.config = ConfigObj(path_to_file)
    shared.translations = get_translations(shared.config['telegram']['locales'])

    authenticate(host_port=shared.config['database']['host_port'],
                 user_name=shared.config['database']['user_name'],
                 password=shared.config['database']['password'])

    environ['NEO4J_REST_URL'] = 'http://%s/db/data' % shared.config['database']['host_port']


def configure_for_unittest():
    ''' Configures project for unit testing. '''

    configure_from_file('unittest.cfg')

    # drop database
    graph = Graph(environ['NEO4J_REST_URL'])
    graph.cypher.execute('MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r')
