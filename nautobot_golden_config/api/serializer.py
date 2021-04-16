"""REST API serializer capabilities for graphql plugin."""

from rest_framework import serializers

from nautobot_golden_config.models import BackupConfigLineRemove, BackupConfigLineReplace


class GraphQLSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for a GraphQL object."""

    data = serializers.JSONField()


class LineRemoveSerializer(serializers.ModelSerializer):
    """Serializer for Line Removal object."""

    class Meta:
        """Set Meta Data for Line Removal, will serialize all fields."""

        model = BackupConfigLineRemove
        fields = "__all__"


class LineReplaceSerializer(serializers.ModelSerializer):
    """Serializer for Line Replacement object."""

    class Meta:
        """Set Meta Data for Line Replacements, will serialize all fields."""

        model = BackupConfigLineReplace
        fields = "__all__"
