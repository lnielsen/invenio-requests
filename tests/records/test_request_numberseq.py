# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Request number identifier model tests."""

from invenio_requests.records.models import RequestNumber


def test_request_number(app, db):
    """Test sequence generator."""
    assert RequestNumber.next() == 1
    assert RequestNumber.next() == 2
    assert RequestNumber.max() == 2

    # Mess up the sequence
    with db.session.begin_nested():
        obj = RequestNumber(value=3)
        db.session.add(obj)

    assert RequestNumber.max() == 3

    # This tests a particular problem on PostgreSQL which is using
    # sequences to generate auto incrementing columns and doesn't deal
    # nicely with having values inserted in the table.
    assert RequestNumber.next() == 4

    # Jump in the sequence
    RequestNumber.insert(10)
    assert RequestNumber.next() == 11
    assert RequestNumber.max() == 11

    # 7 was never inserted, because we jumped the sequence above.
    RequestNumber.insert(7)
    assert RequestNumber.max() == 11
    assert RequestNumber.next() == 12
