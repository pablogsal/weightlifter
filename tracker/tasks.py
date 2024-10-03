import subprocess
import csv
import os
import re
from datetime import datetime
from celery import shared_task
from .models import PythonVersion, Configuration, SizeMeasurement, BloatyOutput
from django.conf import settings
import logging
import git
import json

logger = logging.getLogger(__name__)


def parse_bloaty_output(csv_output):
    reader = csv.DictReader(csv_output.splitlines())
    section_sizes = {}
    total_size = 0

    for row in reader:
        section = row["sections"]
        vmsize = int(row["vmsize"])
        filesize = int(row["filesize"])

        section_sizes[section] = {"vmsize": vmsize, "filesize": filesize}
        total_size += vmsize

    section_sizes["total"] = {
        "vmsize": total_size,
        "filesize": sum(s["filesize"] for s in section_sizes.values()),
    }
    return section_sizes


def get_python_version(python_binary):
    try:
        result = subprocess.run(
            [python_binary, "--version"], capture_output=True, text=True, check=True
        )
        version_string = result.stdout.strip()
        # Extract version number using regex
        match = re.search(r"Python (\d+\.\d+\.\d+)", version_string)
        if match:
            return match.group(1)
        else:
            return f"Unknown-{version_string}"
    except subprocess.CalledProcessError:
        logger.error(f"Failed to get Python version from binary: {python_binary}")
        return "Unknown"


@shared_task
def measure_python_size():
    # Check all commits since the last measurement
    cpython_repo_path = settings.CPYTHON_REPO_PATH
    repo = git.Repo(cpython_repo_path)
    last_measurement = PythonVersion.objects.last()

    if last_measurement:
        last_commit = last_measurement.commit_hash
        commits = repo.iter_commits(f"{last_commit}..HEAD")
    else:
        commits = repo.iter_commits()

    for commit in commits:
        commit_hash = commit.hexsha
        logger.info(f"Processing commit: {commit_hash}")
        _measure_python_size(commit_hash)


def _measure_python_size(commit_hash):
    cpython_repo_path = settings.CPYTHON_REPO_PATH
    repo = git.Repo(cpython_repo_path)

    try:
        commit = repo.commit(commit_hash)
    except git.exc.BadName:
        logger.error(f"Invalid commit hash: {commit_hash}")
        return f"Error: Invalid commit hash {commit_hash}"

    # Checkout the specific commit
    repo.git.checkout(commit_hash)

    configurations = Configuration.objects.all()

    for config in configurations:
        logger.info(f"Processing configuration: {config.name}")

        # Configure and build Python
        # configure_command = ['./configure', '-C'] + config.configure_flags.split()
        # subprocess.run(configure_command, cwd=cpython_repo_path, check=True)
        subprocess.run(["make", "-j8"], cwd=cpython_repo_path, check=True)

        # Get Python version
        python_binary = os.path.join(cpython_repo_path, "python")
        version_string = get_python_version(python_binary)

        # Create or update PythonVersion object
        python_version, created = PythonVersion.objects.update_or_create(
            commit_hash=commit_hash,
            defaults={
                "commit_date": datetime.fromtimestamp(commit.committed_date),
                "version_string": version_string,
            },
        )

        if created:
            logger.info(f"Created new PythonVersion object for commit {commit_hash}")
        else:
            logger.info(
                f"Updated existing PythonVersion object for commit {commit_hash}"
            )

        # Run Bloaty
        bloaty_result = subprocess.run(
            ["bloaty", "--csv", python_binary],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse Bloaty output
        section_sizes = parse_bloaty_output(bloaty_result.stdout)

        # Save the measurement
        measurement, m_created = SizeMeasurement.objects.update_or_create(
            python_version=python_version,
            configuration=config,
            defaults={
                "size_data": json.dumps(section_sizes),
                "total_size": section_sizes["total"]["vmsize"],
            },
        )

        if m_created:
            logger.info(
                f"Created new measurement for {commit_hash} with configuration {config.name}"
            )
        else:
            logger.info(
                f"Updated existing measurement for {commit_hash} with configuration {config.name}"
            )

        # Save or update Bloaty output
        bloaty_output, _ = BloatyOutput.objects.update_or_create(
            size_measurement=measurement, defaults={"output": bloaty_result.stdout}
        )

    return f"Measurements completed for {commit_hash}"


def run_measurement_manually():
    """
    Function to run the measurement task manually without using Celery.
    """
    # Check all commits since the last measurement
    cpython_repo_path = settings.CPYTHON_REPO_PATH
    repo = git.Repo(cpython_repo_path)
    last_measurement = PythonVersion.objects.last()

    if last_measurement:
        last_commit = last_measurement.commit_hash
        commits = repo.iter_commits(f"{last_commit}..main")
    else:
        commits = repo.iter_commits()

    for commit in commits:
        print(commit.hexsha)
        commit_hash = commit.hexsha
        logger.info(f"Processing commit: {commit_hash}")
        _measure_python_size(commit_hash)
