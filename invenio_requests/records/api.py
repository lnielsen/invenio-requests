# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""API classes for requests in Invenio."""

from enum import Enum

from invenio_records.dumpers import ElasticsearchDumper
from invenio_records.systemfields import ConstantField, DictField, ModelField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from .dumpers import CalculatedFieldDumperExt
from .models import RequestEventModel, RequestMetadata
from .systemfields import (
    ExpiredStateCalculatedField,
    IdentityField,
    OpenStateCalculatedField,
    ReferencedEntityField,
    RequestStatusField,
    RequestTypeField,
)
from .systemfields.entity_reference import (
    check_allowed_creators,
    check_allowed_receivers,
    check_allowed_topics,
)


class Request(Record):
    """A generic request record."""

    model_cls = RequestMetadata
    """The model class for the request."""

    dumper = ElasticsearchDumper(
        extensions=[
            CalculatedFieldDumperExt("is_open"),
        ]
    )
    """Elasticsearch dumper with configured extensions."""

    number = IdentityField("number")
    """The request's number (i.e. external identifier)."""

    metadata = None
    """Disabled metadata field from the base class."""

    index = IndexField("requests-request-v1.0.0", search_alias="requests")
    """The Elasticsearch index to use for the request."""

    schema = ConstantField("$schema", "local://requests/request-v1.0.0.json")
    """The JSON Schema to use for validation."""

    type = RequestTypeField("type")
    """System field for management of the request type.

    This field manages loading of the correct RequestType classes associated with
    `Requests`, based on their `request_type_id` field.
    This is important because the `RequestType` classes are the place where the
    custom request actions are registered.
    """

    topic = ReferencedEntityField("topic", check_allowed_topics)
    """Topic (associated object) of the request."""

    created_by = ReferencedEntityField("created_by", check_allowed_creators)
    """The entity that created the request."""

    receiver = ReferencedEntityField("receiver", check_allowed_receivers)
    """The entity that will receive the request."""

    status = RequestStatusField("status")
    """The current status of the request."""

    is_open = OpenStateCalculatedField("status")
    """Whether or not the current status can be seen as an 'open' state."""

    expires_at = ModelField("expires_at")
    """Expiration date of the request."""

    is_expired = ExpiredStateCalculatedField("expires_at")
    """Whether or not the request is already expired."""

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Retrieve the request by id.

        :param id_: The record's number or internal ID.
        :param with_deleted: If `True`, then it includes deleted requests.
        :returns: The :class:`Request` instance.
        """
        # note: in case of concurrency errors, `with db.session.no_autoflush` might help
        try:
            query = cls.model_cls.query.filter_by(number=str(id_))
            if not with_deleted:
                query = query.filter(cls.model_cls.is_deleted != True)  # noqa

            model = query.one()

        except (MultipleResultsFound, NoResultFound):
            # either no results or ambiguous results
            # (e.g. if number is None)
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

    COMMENT = "C"
    REMOVED = "R"
    ACCEPTED = "A"
    DECLINED = "D"
    CANCELLED = "X"
    EXPIRED = "E"


class RequestEventFormat(Enum):
    """Comment/content format enum."""

    HTML = "html"


class RequestEvent(Record):
    """A Request Event."""

    model_cls = RequestEventModel

    # Systemfields
    metadata = None

    schema = ConstantField("$schema", "local://request_events/event-v1.0.0.json")
    """The JSON Schema to use for validation."""

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
