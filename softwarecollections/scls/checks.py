"""Liveness/readiness checks for supervisor"""

from django.core.cache import cache, InvalidCacheBackendError
from django.db import DatabaseError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

from .models import SoftwareCollection

SUCCESS = "OK"  # sentinel value indicating successful query


def database_check(model=SoftwareCollection):
    """Check that the database responds to queries.

    Arguments:
        model: The model/table to run the ping query against.

    Returns:
        SUCCESS if the database responds, error message in case of errors.
    """

    try:
        model.objects.count()
        return SUCCESS
    except DatabaseError as err:
        return str(err)


def cache_check(key="scls-ping-test", value=42):
    """Check that the cache can be interacted with.

    Arguments:
        key: The key to set in the cache.
        value: The value to set the key to.

    Returns:
        SUCCESS if the cache works, error message in case of errors.
    """

    try:
        cache.set(key, value)
        cache.get(key)
        cache.delete(key)
        return SUCCESS
    except InvalidCacheBackendError as err:
        return str(err)


@never_cache
def report_liveness(_request):
    """The application is live and serving requests."""

    return JsonResponse({"live": True})


@never_cache
def report_readiness(_request):
    """The app is ready and has access to all resources."""

    report = {"database": database_check(), "cache": cache_check()}
    response = JsonResponse(report)

    if any(status is not SUCCESS for status in report.values()):
        response.status_code = 503  # Service Unavailable
        response["Retry-After"] = 10  # seconds

    return response
