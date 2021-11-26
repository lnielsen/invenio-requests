# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from invenio_records.api import Record
from invenio_records.systemfields import SystemFieldsMixin

from invenio_requests.records.api import Request
from invenio_requests.records.systemfields.relatedrecord import RelatedRecord


@pytest.fixture()
def MockRecord(app, db):
    class MockRecord_(Record, SystemFieldsMixin):
        request = RelatedRecord(Request)
    return MockRecord_


@pytest.fixture()
def MockRecord2(MockRecord):
    class MockRecord2_(MockRecord):
        request = RelatedRecord(Request, keys=['type'], attrs=['is_open'])
    return MockRecord2_


#
# Test assignments
#
def test_no_assignment(MockRecord, example_request):
    r = MockRecord.create({})
    r.commit()
    assert 'request' not in r


def test_record_assignment(MockRecord, example_request):
    r = MockRecord.create({})
    r.request = example_request
    r.commit()
    assert 'request' in r
    assert r['request']['id'] == str(example_request.id)
    assert r['request']['@v'] == f'{example_request.id}::{example_request.revision_id}'


def test_id_assignment(MockRecord, example_request):
    r = MockRecord.create({})
    r.request = str(example_request.id)
    r.commit()
    assert 'request' in r
    assert r['request']['id'] == str(example_request.id)
    assert r['request']['@v'] == f'{example_request.id}::{example_request.revision_id}'


def test_remove_assignment(MockRecord, example_request):
    r = MockRecord.create({}, request=example_request)
    r.commit()
    assert 'request' in r
    r.request = None
    r.commit()
    assert 'request' not in r
    assert r.request is None


def test_dump_created_by(MockRecord2, example_request):
    r = MockRecord2.create({}, request=example_request)
    r.commit()
    assert r['request']['is_open'] == example_request.is_open
    # We are dumping the key, not the attr (which key/attr is different for
    # type)
    assert r['request']['type'] == example_request['type']
    assert r['request']['type'] != example_request.type
