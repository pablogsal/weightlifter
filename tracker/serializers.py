from rest_framework import serializers
from .models import PythonVersion, Configuration, SizeMeasurement


class PythonVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PythonVersion
        fields = "__all__"


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = "__all__"


class SizeMeasurementSerializer(serializers.ModelSerializer):
    python_version = PythonVersionSerializer()
    configuration = ConfigurationSerializer()

    class Meta:
        model = SizeMeasurement
        fields = "__all__"
