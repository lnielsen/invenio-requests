# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for the provided customization mechanisms."""

import pytest
from invenio_access.permissions import system_identity
from invenio_records_permissions.generators import AnyUser, SystemProcess

from invenio_requests.customizations import RequestState
from invenio_requests.customizations.base import RequestAction
from invenio_requests.customizations.default import DefaultRequestType
from invenio_requests.errors import NoSuchActionError
from invenio_requests.records.api import Request
from invenio_requests.services.permissions import PermissionPolicy

variable = False


class TestAction(RequestAction):
    """Test action."""

    def can_execute(self, identity):
        """Check if the action can be executed."""
        return True

    def execute(self, identity, uow):
        """Execute the action."""
        global variable
        variable = True


class CustomizedReferenceRequestType(DefaultRequestType):
    """Custom request type with different set of allowed reference types."""

    type_id = "customized-reference-request"

    available_actions = {"test": TestAction}
    available_statuses = {
        "not_closed": RequestState.OPEN,
        "closed": RequestState.CLOSED,
    }
    default_status = "not_closed"

    creator_can_be_none = True
    allowed_creator_ref_types = ["community"]
    allowed_receiver_ref_types = ["role", "user"]
    allowed_topic_ref_types = ["record"]


class CustomPermissionPolicy(PermissionPolicy):
    """Customized permission policy allowing the test action."""

    can_action_test = [AnyUser(), SystemProcess()]


def assert_nested_field_allows_type_key(schema, field_name, type_key, negated=False):
    """Assert that the nested field allows a type key."""
    is_in = type_key in schema._declared_fields[field_name].nested._declared_fields
    return negated != is_in


@pytest.fixture(scope="module")
def app_config(app_config):
    """Customized App Config."""
    app_config["REQUESTS_PERMISSION_POLICY"] = CustomPermissionPolicy
    return app_config


@pytest.fixture
def customized_app(app):
    """App with registered test request types."""
    # we need to register the custom type, otherwise it won't be available
    requests_ext = app.extensions["invenio-requests"]
    registry = requests_ext.request_type_registry
    registry.register_type(CustomizedReferenceRequestType)
    registry.register_type(DefaultRequestType)
    return app


def test_customized_reference_types(customized_app):
    """Test if the marshmallow schema customization for entity refs works."""
    example_request_data = {
        "created_by": {"user": "1"},
        "receiver": {"user": "2"},
        "topic": None,
    }
    example_request_data_2 = {
        "created_by": {"community": "blr"},
        "receiver": {"role": "admin"},
        "topic": {"record": "1234-abcd"},
    }

    # check if the default schema accepts the first dataset but rejects the second
    schema = DefaultRequestType.marshmallow_schema()
    assert_nested_field_allows_type_key(schema, "created_by", "community", negated=True)
    assert_nested_field_allows_type_key(schema, "receiver", "role", negated=True)
    assert_nested_field_allows_type_key(schema, "topic", "record", negated=True)
    errors = schema().validate(example_request_data)
    assert not errors
    errors = schema().validate(example_request_data_2)
    assert errors

    # check if the customized schema accepts the second dataset but rejects the first
    schema = CustomizedReferenceRequestType.marshmallow_schema()
    assert_nested_field_allows_type_key(schema, "created_by", "community")
    assert_nested_field_allows_type_key(schema, "receiver", "role")
    assert_nested_field_allows_type_key(schema, "receiver", "user")
    assert_nested_field_allows_type_key(schema, "topic", "record")
    errors = schema().validate(example_request_data)
    assert errors
    errors = schema().validate(example_request_data_2)
    assert not errors


def test_customized_request_actions(customized_app, users):
    """Test if the action customization mechanism works."""
    service = customized_app.extensions["invenio-requests"].requests_service
    request = service.create(
        system_identity,
        {},
        CustomizedReferenceRequestType,
        receiver=users[0],
        creator=None,
    )

    # after executing the customized action, the global variable should be True
    assert not variable
    service.execute_action(system_identity, request.id, "test")
    assert variable

    # check that none of the other actions are available
    for action in DefaultRequestType.available_actions:
        with pytest.raises(NoSuchActionError):
            service.execute_action(system_identity, request.id, action)


def test_customized_statuses(customized_app):
    """Test if the set of available statuses can be customized properly."""
    default_req = Request.create({}, type=DefaultRequestType)
    custom_req = Request.create({}, type=CustomizedReferenceRequestType)

    # check that there's no overlap
    default_statuses = set(default_req.type.available_statuses)
    custom_statuses = set(custom_req.type.available_statuses)
    assert not default_statuses.intersection(custom_statuses)

    def _is_open(status, request_type):
        return RequestState.OPEN == request_type.available_statuses[status]

    def _is_closed(status, request_type):
        return RequestState.CLOSED == request_type.available_statuses[status]

    # check if the status systemfields do their jobs
    for status in default_statuses:
        default_req.status = status
        assert default_req.status == status
        assert default_req.is_open == _is_open(status, default_req.type)
        assert default_req.is_closed == _is_closed(status, default_req.type)

        with pytest.raises(ValueError):
            # the default statuses aren't available in the custom request type
            custom_req.status = status

    for status in custom_statuses:
        custom_req.status = status
        assert custom_req.status == status
        assert custom_req.is_open == _is_open(status, custom_req.type)
        assert custom_req.is_closed == _is_closed(status, custom_req.type)

        with pytest.raises(ValueError):
            # same as above, but the other way around
            default_req.status = status
