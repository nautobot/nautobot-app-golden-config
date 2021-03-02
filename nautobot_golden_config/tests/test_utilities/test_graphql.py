"""Unit tests for nautobot_golden_config utilities graphql.

(c) 2020-2021 Network To Code
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from unittest.mock import patch, Mock
from django.test import TestCase
from graphql.error import GraphQLSyntaxError

from nautobot_golden_config.utilities.graphql import graph_ql_query

class GraphQLTest(TestCase):
    """Test for the GraphQL Queries."""

    @patch('nautobot_golden_config.utilities.graphql.graph_ql_query')
    def test_graph_ql_query(self, mock):
        """Make sure graph_ql_query is called correctly."""
        mock('request', 'ams-edge-01', '{devices(name:"ams-edge-01"){id}}')
        mock.assert_called_with('request', 'ams-edge-01', '{devices(name:"ams-edge-01"){id}}')

    def test_bad_graph_ql_query_syntax(self):
        """Ensure invalid GraphQL query results with Error."""
        result = graph_ql_query('request', 'ams-edge-01', 'not valid query')
        self.assertEqual(result[0], 400)
        self.assertTrue(result[1]['error'])
        self.assertRegex(result[1].get('error'), r'Syntax Error GraphQL.*')


