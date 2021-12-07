"""Util functions that are leveraged by the managed commands."""
# pylint: disable=too-many-branches,bad-option-value
import time
import uuid

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.test.client import RequestFactory

from nautobot.extras.choices import JobResultStatusChoices
from nautobot.extras.models import JobResult
from nautobot.extras.jobs import run_job
from nautobot.dcim.models import Device
from nautobot.users.models import User


# Largely based on nautobot core run_job command, which does not allow variables to be sent
# so copied instead of used directly.
def job_runner(handle_class, job_class, device=None, user=None):
    """Function to make management command code more DRY."""
    data = {}

    if device:
        data["device"] = Device.objects.get(name=device)

    request = RequestFactory().request(SERVER_NAME="WebRequestContext")
    request.id = uuid.uuid4()
    request.user = User.objects.get(username=user)

    job_content_type = ContentType.objects.get(app_label="extras", model="job")

    # Run the job and create a new JobResult
    handle_class.stdout.write(f"[{timezone.now():%H:%M:%S}] Running {job_class.class_path}...")

    job_result = JobResult.enqueue_job(
        run_job,
        job_class.class_path,
        job_content_type,
        request.user,
        data=data,
        request=request,
        commit=True,
    )

    # Wait on the job to finish
    while job_result.status not in JobResultStatusChoices.TERMINAL_STATE_CHOICES:
        time.sleep(1)
        job_result = JobResult.objects.get(pk=job_result.pk)

    # Report on success/failure
    for test_name, attrs in job_result.data.items():

        if test_name in ["total", "output"]:
            continue

        handle_class.stdout.write(
            f"\t{test_name}: {attrs['success']} success, {attrs['info']} info, {attrs['warning']} warning, {attrs['failure']} failure"
        )

        for log_entry in attrs["log"]:
            status = log_entry[1]
            if status == "success":
                status = handle_class.style.SUCCESS(status)
            elif status == "info":
                status = status  # pylint: disable=self-assigning-variable
            elif status == "warning":
                status = handle_class.style.WARNING(status)
            elif status == "failure":
                status = handle_class.style.NOTICE(status)

            if log_entry[2]:  # object associated with log entry
                handle_class.stdout.write(f"\t\t{status}: {log_entry[2]}: {log_entry[-1]}")
            else:
                handle_class.stdout.write(f"\t\t{status}: {log_entry[-1]}")

    if job_result.data["output"]:
        handle_class.stdout.write(job_result.data["output"])

    if job_result.status == JobResultStatusChoices.STATUS_FAILED:
        status = handle_class.style.ERROR("FAILED")
    elif job_result.status == JobResultStatusChoices.STATUS_ERRORED:
        status = handle_class.style.ERROR("ERRORED")
    else:
        status = handle_class.style.SUCCESS("SUCCESS")
    handle_class.stdout.write(f"[{timezone.now():%H:%M:%S}] {job_class.class_path}: {status}")

    # Wrap things up
    handle_class.stdout.write(f"[{timezone.now():%H:%M:%S}] {job_class.class_path}: Duration {job_result.duration}")
    handle_class.stdout.write(f"[{timezone.now():%H:%M:%S}] Finished")
