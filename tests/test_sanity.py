"""Basic functionality sanity tests"""
import pytest


@pytest.mark.django_db
def test_scl_page(client):
    """Selected SCL page contains expected content"""

    response = client.get("/en/scls/hhorak/rpmquality/")

    assert b"check-content-instructions" in response.content
    assert b"check-content-description" in response.content
    assert b"yum install centos-release-scl" in response.content
