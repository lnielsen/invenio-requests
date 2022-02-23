# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""

import pytest
from flask_principal import Identity, Need, UserNeed

from invenio_requests.customizations import RequestType
from invenio_requests.proxies import current_requests
from invenio_requests.records.api import (
    RequestEvent,
    RequestEventFormat,
    RequestEventType,
)


@pytest.fixture(scope="module")
def requests_service(app):
    """Request Factory fixture."""
    return current_requests.requests_service


@pytest.fixture(scope="module")
def request_events_service(app):
    """Request Factory fixture."""
    return current_requests.request_events_service


@pytest.fixture()
def create_request(users, request_record_input_data, requests_service):
    """Request Factory fixture."""

    def _create_request(identity, input_data=None, receiver=None, **kwargs):
        """Create a request."""
        input_data = input_data or request_record_input_data
        receiver = receiver or users[1]
        # Need to use the service to get the id
        item = requests_service.create(
            identity, input_data, RequestType, receiver=receiver, **kwargs
        )
        return item._request

    return _create_request


@pytest.fixture()
def submit_request(create_request, requests_service):
    """Opened Request Factory fixture."""

    def _submit_request(identity, data=None):
        """Create and submit a request."""
        request = create_request(identity)
        id_ = request.id
        data = data or {
            "payload": {
                "content": "Can I belong to the community?",
                "format": RequestEventFormat.HTML.value,
            }
        }
        return requests_service.execute_action(identity, id_, "submit", data)._request

    return _submit_request
