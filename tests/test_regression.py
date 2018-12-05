"""Tests for issues found and fixed in general usage.

Should be moved in case of refactoring the respective parts.
"""

import pytest


@pytest.mark.django_db
def test_new_scl_form_is_displayed(admin_client):
    """The form for insertion of new collection is properly rendered."""

    response = admin_client.get("/en/scls/new/", follow=False)

    assert response.status_code == 200
    assert "maintainer" in response.context["form"].fields
