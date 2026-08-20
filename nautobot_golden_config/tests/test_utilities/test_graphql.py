"""Unit tests for nautobot_golden_config utilities graphql."""

from unittest import skip
from unittest.mock import MagicMock, patch

from graphql import ExecutionResult, GraphQLError
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Device

from nautobot_golden_config.utilities.graphql import graph_ql_query


class GraphQLTest(TestCase):
    """Test for the GraphQL Queries."""

    @skip("Update to accommodate uuid vs device")
    @patch("nautobot_golden_config.utilities.graphql.graph_ql_query")
    def test_graph_ql_query(self, mock):
        """Make sure graph_ql_query is called correctly."""
        mock("request", Device.objects.get(name="ams-edge-01"), '{devices(name:"ams-edge-01"){id}}')
        mock.assert_called_with("request", Device.objects.get(name="ams-edge-01"), '{devices(name:"ams-edge-01"){id}}')

    @skip("Update to accommodate uuid vs device")
    def test_bad_graph_ql_query_syntax(self):
        """Ensure invalid GraphQL query results with Error."""
        result = graph_ql_query("request", Device.objects.get(name="ams-edge-01"), "not valid query")
        self.assertEqual(result[0], 400)
        self.assertTrue(result[1]["error"])
        self.assertRegex(result[1].get("error"), r"Syntax Error GraphQL.*")

    @patch("nautobot_golden_config.utilities.graphql.execute")
    def test_execution_error_returns_message(self, mock_execute):
        """Regression for #1106.

        When the executed GraphQL query returns errors, the helper must surface the real GraphQL
        error message in the same ``{"error": ...}`` shape used by the other error branches. It must
        not call the nonexistent ``ExecutionResult.to_dict()``, which raised an ``AttributeError``
        that masked the underlying error.
        """
        mock_execute.return_value = ExecutionResult(data=None, errors=[GraphQLError("boom")])
        device = MagicMock()
        device.pk = "00000000-0000-0000-0000-000000000000"

        status, payload = graph_ql_query(MagicMock(), device, "query { devices { id } }")

        self.assertEqual(status, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"], "boom")
