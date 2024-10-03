# models.py

from django.db import models
import json


class PythonVersion(models.Model):
    commit_hash = models.CharField(max_length=40, unique=True)
    commit_date = models.DateTimeField()
    version_string = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.version_string} ({self.commit_hash[:7]})"


class Configuration(models.Model):
    name = models.CharField(max_length=100, unique=True)
    configure_flags = models.TextField()

    def __str__(self):
        return self.name


class SizeMeasurement(models.Model):
    python_version = models.ForeignKey(PythonVersion, on_delete=models.CASCADE)
    configuration = models.ForeignKey(Configuration, on_delete=models.CASCADE)
    measurement_date = models.DateTimeField(auto_now_add=True)
    size_data = (
        models.TextField()
    )  # This will store the JSON string of all section sizes
    total_size = (
        models.BigIntegerField()
    )  # Changed to BigIntegerField for larger values

    class Meta:
        unique_together = ("python_version", "configuration")

    def __str__(self):
        return f"{self.python_version} - {self.configuration} - {self.measurement_date}"

    def get_size_data(self):
        return json.loads(self.size_data)

    def set_size_data(self, data):
        self.size_data = json.dumps(data)


class BloatyOutput(models.Model):
    size_measurement = models.OneToOneField(SizeMeasurement, on_delete=models.CASCADE)
    output = models.TextField()

    def __str__(self):
        return f"Bloaty output for {self.size_measurement}"
