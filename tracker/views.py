# tracker/views.py

import logging
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.utils import timezone
from .models import PythonVersion, Configuration, SizeMeasurement
from .serializers import (
    PythonVersionSerializer,
    ConfigurationSerializer,
    SizeMeasurementSerializer,
)

logger = logging.getLogger(__name__)


class DashboardView(TemplateView):
    template_name = "tracker/dashboard.html"


class PythonVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PythonVersion.objects.all()
    serializer_class = PythonVersionSerializer


class ConfigurationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer


class SizeMeasurementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SizeMeasurement.objects.all()
    serializer_class = SizeMeasurementSerializer

    @action(detail=False, methods=["get"])
    def size_evolution(self, request):
        logger.info(f"size_evolution called with params: {request.query_params}")

        start_date = timezone.make_aware(
            timezone.datetime.strptime(
                request.query_params.get("start_date"), "%Y-%m-%d"
            )
        )
        end_date = timezone.make_aware(
            timezone.datetime.strptime(request.query_params.get("end_date"), "%Y-%m-%d")
        )
        config_ids = request.query_params.get("config_ids", "").split(",")

        logger.info(
            f"Filtering measurements with date range: {start_date} to {end_date}, config_ids: {config_ids}"
        )

        measurements = self.queryset.filter(
            python_version__commit_date__range=[start_date, end_date],
            configuration_id__in=config_ids,
        ).order_by("python_version__commit_date")

        logger.info(f"Found {measurements.count()} measurements")

        result = {}
        for measurement in measurements:
            config_name = measurement.configuration.name
            if config_name not in result:
                result[config_name] = []
            sections = {
                section[1:].replace(".", "_"): value["filesize"]
                for section, value in measurement.get_size_data().items()
                if section.startswith(".")
            }
            result[config_name].append(
                {
                    "date": measurement.python_version.commit_date.isoformat(),
                    "total_size": measurement.total_size,
                    **sections,
                }
            )

        logger.info(f"Returning result with {len(result)} configurations")
        return Response(result)
