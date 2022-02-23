# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test the requests record API."""


def test_grant_tokens(example_request):
    """Test if the expired system field works as intended."""
    data = example_request.dumps()
    assert data['grants'] == ['created_by.id.1', 'receiver.id.2']
