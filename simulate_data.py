# simulate_data.py

import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weightlifter.settings")
django.setup()

from tracker.models import PythonVersion, Configuration, SizeMeasurement


def simulate_data():
    # Create or get configurations
    configs = [
        Configuration.objects.get_or_create(
            name="Default", defaults={"configure_flags": ""}
        )[0],
        Configuration.objects.get_or_create(
            name="Debug", defaults={"configure_flags": "--with-pydebug"}
        )[0],
        Configuration.objects.get_or_create(
            name="Optimized", defaults={"configure_flags": "--enable-optimizations"}
        )[0],
    ]

    # Create Python versions and size measurements
    start_date = datetime(2023, 1, 1)
    for i in range(100):
        commit_date = start_date + timedelta(days=i)
        version, created = PythonVersion.objects.get_or_create(
            commit_hash=f"commit_{i:04d}",
            defaults={
                "commit_date": commit_date,
                "version_string": f"3.{10 + i // 30}.{i % 30}",
            },
        )

        for config in configs:
            SizeMeasurement.objects.get_or_create(
                python_version=version,
                configuration=config,
                defaults={
                    "total_size": random.randint(10000000, 12000000),
                    "text_section_size": random.randint(5000000, 6000000),
                    "data_section_size": random.randint(3000000, 4000000),
                    "bss_section_size": random.randint(1000000, 2000000),
                },
            )

    print("Simulation completed successfully.")


if __name__ == "__main__":
    simulate_data()
