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

from invenio_requests.errors import CannotExecuteActionError
from invenio_requests.records.api import RequestEventFormat


@pytest.fixture()
def requests_service_action_input_data():
    return {
        "payload": {
            "content": "Can I belong to the community?",
            "format": RequestEventFormat.HTML.value,
        }
    }


def test_only_creator_can_submit(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, create_request):
    request = create_request(identity_simple)
    request_id = request.id
    data = requests_service_action_input_data

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_stranger, request_id, "submit", data)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_simple_2, request_id, "submit", data)
    # Creator
    assert (
        requests_service.execute_action(identity_simple, request_id, "submit", data)
    )


def test_only_receiver_can_accept(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id
    data = copy.deepcopy(requests_service_action_input_data)
    data["payload"]["content"] = "You are in."

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_stranger, request_id, "accept", data)
    # Creator
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_simple, request_id, "accept", data)
    # Receiver
    assert (
        requests_service.execute_action(identity_simple_2, request_id, "accept", data)
    )


def test_only_receiver_can_decline(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id
    data = copy.deepcopy(requests_service_action_input_data)
    data["payload"]["content"] = "You are NOT in."

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_stranger, request_id, "decline", data)
    # Creator
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_simple, request_id, "decline", data)
    # Receiver
    assert (
        requests_service.execute_action(identity_simple_2, request_id, "decline", data)
    )


def test_only_creator_can_cancel(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_stranger, request_id, "cancel")
    # Receiver
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_simple_2, request_id, "cancel")
    # Creator
    assert (
        requests_service.execute_action(identity_simple, request_id, "cancel")
    )


def test_only_creator_can_read_draft_request(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, create_request):
    request = create_request(identity_simple)
    request_id = request.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.read(identity_stranger, request_id)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        requests_service.read(identity_simple_2, request_id)
    # Creator
    assert requests_service.read(identity_simple, request_id)


def test_creator_and_receiver_can_read_open_request(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.read(identity_stranger, request_id)
    # Receiver
    assert requests_service.read(identity_simple_2, request_id)
    # Creator
    assert requests_service.read(identity_simple, request_id)


def test_creator_and_receiver_can_read_expired_request(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id
    requests_service.execute_action(system_identity, request_id, "expire")

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.read(identity_stranger, request_id)
    # Receiver
    assert requests_service.read(identity_simple_2, request_id)
    # Creator
    assert requests_service.read(identity_simple, request_id)


def update_input(request):
    """Prepare a palatable data entry."""
    data = request.dumps()
    del data["version_id"]
    del data["uuid"]
    del data["$schema"]
    del data["grants"]
    data["title"] = "Updated title"
    return data


def test_only_creator_can_update_draft_request(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, create_request, submit_request):
    request = create_request(identity_simple)  # receiver is user #2
    request_id = request.id
    data = update_input(request)

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.update(identity_stranger, request_id, data)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        requests_service.update(identity_simple_2, request_id, data)
    # Creator
    assert requests_service.update(identity_simple, request_id, data)


def test_creator_and_receiver_can_update_open_request(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id
    data = update_input(request)

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.update(identity_stranger, request_id, data)
    # Receiver
    assert requests_service.update(identity_simple_2, request_id, data)
    # Creator
    assert requests_service.update(identity_simple, request_id, data)


def test_only_system_can_update_closed_request(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id
    result = requests_service.execute_action(system_identity, request_id, "decline")
    data = result.to_dict()

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.update(identity_stranger, request_id, data)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        requests_service.update(identity_simple_2, request_id, data)
    # Creator
    with pytest.raises(PermissionDeniedError):
        requests_service.update(identity_simple, request_id, data)
    # System
    assert requests_service.update(system_identity, request_id, data)


def test_only_authenticated_user_can_create_request(
        app, identity_simple, identity_stranger,
        requests_service, create_request):
    # Stranger
    with pytest.raises(PermissionDeniedError):
        create_request(identity_stranger)
    # Creator
    assert create_request(identity_simple)


def test_only_system_and_creator_can_delete_request(
        app, identity_simple, identity_stranger, submit_request,
        requests_service, create_request):
    request = create_request(identity_simple)
    request_id = request.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.delete(identity_stranger, request_id)

    # Creator CAN delete draft
    assert requests_service.delete(identity_simple, request_id)

    request = submit_request(identity_simple)
    request_id = request.id

    # Creator CANNOT delete open/closed
    with pytest.raises(PermissionDeniedError):
        requests_service.delete(identity_stranger, request_id)

    # System CAN, but action doesn't allow
    with pytest.raises(CannotExecuteActionError):
        assert requests_service.delete(system_identity, request_id)
