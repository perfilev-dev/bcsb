import sys
import unittest

from os import path, environ
from py2neo import Graph

# Export dir for import module like from root directory
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


class TestConfig(unittest.TestCase):

    def test_database_access(self):
        from util import configure_for_unittest

        configure_for_unittest()

        graph = Graph(environ['NEO4J_REST_URL'])
        cypher = graph.cypher
