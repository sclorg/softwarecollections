"""Basic functionality sanity tests"""
from urllib.parse import urljoin

import pytest

# Various sub-urls for the main page
PAGE_URL_LIST = ["", "about/", "docs/", "scls/"]
# Various sub-urls for a collection
SCL_URL_LIST = ["", "edit/", "coprs/", "repos/", "acl/", "review_req/"]


@pytest.mark.django_db
def test_scl_page(client):
    """Selected SCL page contains expected content"""

    response = client.get("/en/scls/hhorak/rpmquality/")

    assert b"check-content-instructions" in response.content
    assert b"check-content-description" in response.content
    assert b"yum install centos-release-scl" in response.content


@pytest.mark.parametrize("url_tail", PAGE_URL_LIST)
@pytest.mark.django_db
def test_top_page_accessible(client, url_tail):
    """Top-level sub-page is accessible."""

    url = urljoin("/en/", url_tail)

    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.parametrize("url_tail", SCL_URL_LIST)
@pytest.mark.django_db
def test_scl_page_accessible(admin_client, url_tail):
    """SCL-level sub-page is accessible."""

    url = urljoin("/en/scls/hhorak/rpmquality/", url_tail)

    response = admin_client.get(url)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param("/scls/-/live"),
        pytest.param("/scls/-/ready", marks=pytest.mark.django_db),
    ],
)
def test_scl_health_checks_is_never_cached(client, endpoint):
    """The health check indicator instructs clients to never cache the results"""

    response = client.get(endpoint, follow=True)
    assert 200 <= response.status_code < 300
    assert "no-cache" in response["Cache-Control"]
