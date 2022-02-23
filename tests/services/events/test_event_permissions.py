# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permission tests."""

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError

from invenio_requests.records.api import RequestEvent


def test_creator_and_receiver_can_comment(
        app, identity_simple, identity_simple_2, identity_stranger,
        request_events_service, events_service_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id

    # Creator
    assert (
        request_events_service.create(identity_simple, request_id, events_service_data)
    )
    # Receiver
    assert (
        request_events_service.create(
            identity_simple_2, request_id, events_service_data
        )
    )
    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.create(
            identity_stranger, request_id, events_service_data
        )


def test_only_commenter_can_update_comment(
        app, identity_simple, identity_simple_2, identity_stranger,
        request_events_service, events_service_data, example_request):
    request_id = example_request.id
    item = request_events_service.create(
        identity_simple, request_id, events_service_data
    )
    comment_id = item.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.update(
            identity_stranger, comment_id, events_service_data
        )
    # Receiver
    with pytest.raises(PermissionDeniedError):
        request_events_service.update(
            identity_simple_2, comment_id, events_service_data
        )
    # Commenter
    assert request_events_service.update(
        identity_simple, comment_id, events_service_data
    )


def test_only_commenter_can_delete_comment(
        app, identity_simple, identity_simple_2, identity_stranger,
        request_events_service, events_service_data, example_request):
    request_id = example_request.id
    item_1 = request_events_service.create(
        identity_simple, request_id, events_service_data
    )
    comment_id_1 = item_1.id
    item_2 = request_events_service.create(
        identity_simple, request_id, events_service_data
    )
    comment_id_2 = item_2.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.delete(identity_stranger, comment_id_1)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        request_events_service.delete(identity_simple_2, comment_id_1)
    # Commenter
    assert request_events_service.delete(identity_simple, comment_id_2)


def test_creator_can_see_timeline(
        app, identity_simple, identity_simple_2, identity_stranger,
        request_events_service, events_service_data, example_request):
    request_id = example_request.id
    request_events_service.create(
        identity_simple, request_id, events_service_data
    )
    RequestEvent.index.refresh()

    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.search(identity_stranger, request_id)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        request_events_service.search(identity_simple_2, request_id)
    # Creator
    assert list(request_events_service.search(identity_simple, request_id))


def test_receiver_can_see_timeline_of_open_request(
        app, identity_simple, identity_simple_2, identity_stranger,
        request_events_service, events_service_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id
    request_events_service.create(
        identity_simple, request_id, events_service_data
    )
    RequestEvent.index.refresh()

    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.search(identity_stranger, request_id)
    # Receiver
    assert list(request_events_service.search(identity_simple_2, request_id))
