# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test the calculated systemfields."""

from datetime import datetime, timedelta

import pytest

from invenio_requests.customizations import RequestState


def test_expired_systemfield(example_request):
    """Test if the expired system field works as intended."""
    now = datetime.utcnow()
    example_request.expires_at = None
    example_request.commit()

    # if the expiration date is set to None, the request never expires
    assert example_request.expires_at is None
    assert not example_request.is_expired

    # date in the future: not expired
    next_week = now + timedelta(days=7)
    example_request.expires_at = next_week
    example_request.commit()
    assert example_request.expires_at == next_week
    assert not example_request.is_expired

    # date in the past: expired
    last_week = now - timedelta(days=7)
    example_request.expires_at = last_week
    example_request.commit()
    assert example_request.expires_at == last_week
    assert example_request.is_expired

    # we shouldn't be able to set the value of the calculated field
    with pytest.raises(AttributeError):
        example_request.is_expired = False


def test_open_systemfield(example_request):
    """Test if the is_open system field works as intended."""
    for status, state in example_request.type.available_statuses.items():
        example_request.status = status
        example_request.commit()

        should_be_open = RequestState.OPEN == state
        should_be_closed = RequestState.CLOSED == state
        assert example_request.is_open is should_be_open
        assert example_request.is_closed is should_be_closed
