"""REST API serializer capabilities for graphql plugin."""

from rest_framework import serializers


class GraphQLSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for a GraphQL object."""

    data = serializers.JSONField()
