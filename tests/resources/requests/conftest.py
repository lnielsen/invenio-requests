# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request resource conftest."""

import pytest
from invenio_access.permissions import system_identity as sys_id

from invenio_requests.customizations import RequestType
from invenio_requests.records.api import RequestEventFormat


@pytest.fixture()
def request_resource_data(users):
    """Example data for sending to the REST API."""
    user = users[0]

    return {
        "title": "Example Request",
        "receiver": {"user": str(user.id)},
    }


@pytest.fixture()
def example_requests(app, users):
    """A few example requests."""
    svc = app.extensions["invenio-requests"].requests_service

    u1, u2, u3 = users
    req1 = svc.create(
        sys_id, {"title": "first"}, RequestType, receiver=u1, creator=u3
    )._obj
    req2 = svc.create(
        sys_id, {"title": "second"}, RequestType, receiver=u1, creator=u3
    )._obj
    req3 = svc.create(
        sys_id, {"title": "third"}, RequestType, receiver=u2, creator=u3
    )._obj

    # this is needed to make sure that the requests are indexed in time,
    # before the tests are run
    req1.index.refresh()

    return [req1, req2, req3]


@pytest.fixture()
def request_action_resource_data():
    """REST API input fixture."""
    return {
        "payload": {
            "content": "Action comment.",
            "format": RequestEventFormat.HTML.value
        }
    }
