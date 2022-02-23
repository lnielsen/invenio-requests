# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permission tests."""
import copy

import pytest
from invenio_access.permissions import system_identity
from invenio_records_resources.services.errors import PermissionDeniedError

from invenio_requests.records.api import RequestEventFormat


@pytest.fixture()
def requests_service_action_input_data():
    return {
        "payload": {
            "content": "Can I belong to the community?",
            "format": RequestEventFormat.HTML.value,
        }
    }


def test_relevant_identities_can_search_requests(
        app, identity_simple, identity_simple_2, identity_stranger, requests_service,
        users, create_request):
    u1, u2, u3 = users
    u1_request = create_request(identity_simple, receiver=u2, creator=u1)
    create_request(identity_simple, receiver=u3, creator=u1)
    request = create_request(identity_simple_2, receiver=u3, creator=u2)
    request.index.refresh()

    # user #1 can see their created requests
    results = requests_service.search(identity_simple)
    assert 2 == len(list(results.hits))

    # user #2 can see their created requests but not the received one yet
    results = requests_service.search(identity_simple_2)
    assert 1 == len(list(results.hits))

    # user #1 submits, so now user #2 can see the received request.
    requests_service.execute_action(identity_simple, u1_request.id, "submit")
    request.index.refresh()
    results = requests_service.search(identity_simple_2)
    assert 2 == len(list(results.hits))

    # unauthenticated user can't search for requests
    with pytest.raises(PermissionDeniedError):
        requests_service.search(identity_stranger)
