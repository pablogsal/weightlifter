from django.contrib import admin
from .models import PythonVersion, Configuration, SizeMeasurement

admin.site.register(PythonVersion)
admin.site.register(Configuration)
admin.site.register(SizeMeasurement)
