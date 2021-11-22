# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""API classes for requests in Invenio."""

from datetime import datetime
from enum import Enum

import pytz
from invenio_records.dumpers import ElasticsearchDumper
from invenio_records.systemfields import ConstantField, DictField, ModelField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from .dumpers import CalculatedFieldDumperExt, RequestTypeDumperExt
from .models import RequestEventModel, RequestMetadata
# import style
from .systemfields import (
    IdentityField,
    OpenStateCalculatedField,
    ReferencedEntityField,
    RequestStatusField,
    RequestTypeField,
)


class Request(Record):
    """A generic request record."""

    model_cls = RequestMetadata
    """The model class for the request."""

    dumper = ElasticsearchDumper(
        extensions=[
            CalculatedFieldDumperExt("is_open"),
            # Do we need to dump? is_expired? at some point the calculated value will not be correct ?
            CalculatedFieldDumperExt("is_expired"),
            RequestTypeDumperExt("request_type"),
        ]
    )
    """Elasticsearch dumper with configured extensions."""

    # should we rename external_id to number in model?
    number = IdentityField("external_id")
    """The request's external identity."""

    metadata = None
    """Disabled metadata field from the base class."""

    index = IndexField("requests-request-v1.0.0", search_alias="requests")
    """The Elasticsearch index to use for the request."""

    schema = ConstantField("$schema", "local://requests/request-v1.0.0.json")
    """The JSON Schema to use for validation."""

    # rename to type? implicit that it's for a request: request.type vs request.request_type
    request_type = RequestTypeField("request_type_id")
    """System field for management of the request type.

    This field manages loading of the correct RequestType classes associated with
    `Requests`, based on their `request_type_id` field.
    This is important because the `RequestType` classes are the place where the
    custom request actions are registered.
    """

    topic = ReferencedEntityField("topic")
    """Topic (associated object) of the request."""

    created_by = ReferencedEntityField("created_by")
    """The entity that created the request."""

    receiver = ReferencedEntityField("receiver")
    """The entity that will receive the request."""

    status = RequestStatusField("status")
    """The current status of the request."""

    is_open = OpenStateCalculatedField("is_open")
    """Whether or not the current status can be seen as an 'open' state."""

    expires_at = ModelField("expires_at")
    """Expiration date of the request."""

    # could be put on a system field instead:
    # expires_at = ExpiresAtField("expires_at")
    # usage: record.expires_at.is_expired() or Record.expired_at.is_expired.(record)
    @property
    def is_expired(self):
        """Check if the Request is expired."""
        if self.expires_at is None:
            return False

        # comparing timezone-aware and naive datetimes results in an error
        # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive # noqa
        now = datetime.utcnow()
        d = self.expires_at
        if d.tzinfo and d.tzinfo.utcoffset(d) is not None:
            now = now.replace(tzinfo=pytz.utc)

        return d < now

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Retrieve the request by id.

        :param id_: The record ID (external or internal).
        :param with_deleted: If `True`, then it includes deleted requests.
        :returns: The :class:`Request` instance.
        """
        # note: in case of concurrency errors, `with db.session.no_autoflush` might help
        try:
            query = cls.model_cls.query.filter_by(external_id=str(id_))
            if not with_deleted:
                query = query.filter(cls.model_cls.is_deleted != True)  # noqa

            model = query.one()

        except (MultipleResultsFound, NoResultFound):
            # either no results or ambiguous results
            # (e.g. if external_id is None)
            # NOTE: if 'id_' is None, this will return None!
            query = cls.model_cls.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter(cls.model_cls.is_deleted != True)  # noqa

            model = query.one()

        if model is None:
            # TODO maybe some kind of `NullRequest`?
            return None

        return cls(model.data, model=model)


class RequestEventType(Enum):
    """Request Event type enum."""

    # How do we extend with other event types?
    COMMENT = "C"
    REMOVED = "R"
    ACCEPTED = "A"
    DECLINED = "D"
    CANCELLED = "X"


class RequestEventFormat(Enum):
    """Comment/content format enum."""

    HTML = "html"


class RequestEvent(Record):
    """A Request Event."""

    model_cls = RequestEventModel

    # Systemfields
    metadata = None

    request = ModelField(dump=False)
    """The request."""

    request_id = DictField("request_id")
    """The data-layer id of the related Request."""

    type = ModelField("type")
    """The human-readable event type."""

    index = IndexField("request_events-event-v1.0.0", search_alias="request_events")
    """The ES index used."""

    id = ModelField("id")
    """The data-layer id."""

    # TODO: Revisit when dealing with ownership
    created_by = DictField("created_by")
    """Who created the event."""
