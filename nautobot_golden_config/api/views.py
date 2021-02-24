"""View for Golden Config APIs."""
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from nautobot.dcim.models import Device

from ..models import GoldenConfigSettings
from ..utilities.graphql import graph_ql_query
from .serializer import GraphQLSerializer


class SOTAggDeviceDetailView(APIView):
    """Detail REST API view showing graphql, with a potential "transformer" of data on a specific device."""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Get method serialize for a dictionary to json response."""
        device = Device.objects.get(name=kwargs["device_name"])
        global_settings = GoldenConfigSettings.objects.get(id="aaaaaaaa-0000-0000-0000-000000000001")
        status_code, data = graph_ql_query(request, device, global_settings.sot_agg_query)
        data = json.loads(json.dumps(data))
        return Response(GraphQLSerializer(data=data).initial_data, status=status_code)
