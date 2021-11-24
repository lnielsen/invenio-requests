# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Request Event Schemas."""

from datetime import timezone

from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow import RAISE, Schema, fields, missing, validate
from marshmallow_oneofschema import OneOfSchema
from marshmallow_utils import fields as utils_fields

from ..records.api import RequestEventFormat, RequestEventType


class EntityReferenceSchema(Schema):
    """Schema for a referenced entity."""

    # straight out of RDM-Records!
    # TODO will need to accomodate for communities (as receivers), records (as
    #      topic/associated objects) and probably a few more
    #      - but only for one of them at a time!
    # TODO: should come from registered entity types
    user = fields.String(required=True)
    community = fields.String()


class RequestSchema(BaseRecordSchema):
    """Schema for requests.

    Note that the payload schema is dynamically constructed and injected into
    this schema.
    """

    number = fields.String(dump_only=True)
    request_type = fields.String()
    title = utils_fields.SanitizedUnicode(default='')
    description = utils_fields.SanitizedUnicode()

    # routing information can likely be inferred during creation
    created_by = fields.Nested(EntityReferenceSchema)
    receiver = fields.Nested(EntityReferenceSchema)
    topic = fields.Nested(EntityReferenceSchema, dump_only=True)

    # status information is also likely set by the service
    status = fields.String(dump_only=True)
    is_open = fields.Boolean(dump_only=True)
    expires_at = utils_fields.TZDateTime(
        timezone=timezone.utc, format="iso", dump_only=True)
    is_expired = fields.Boolean(dump_only=True)

    class Meta:
        """Schema meta."""

        unknown = RAISE


class ModelFieldStr(fields.Str):
    """Marshmallow field for serializing by attribute before item."""

    def get_value(self, obj, attr, **kwargs):
        """Return obj.attr or obj[attr] in this precedence order."""
        return getattr(obj, attr, obj.get(attr, missing))


class BaseEventSchema(BaseRecordSchema):
    """Base Event schema that other schemas should inherit from."""

    type = ModelFieldStr(required=True)


class CommentSchema(BaseEventSchema):
    """Comment schema."""

    class CommentExtra(Schema):
        """Comment extras schema."""

        content = utils_fields.SanitizedHTML()
        format = fields.Str(
            validate=validate.OneOf(choices=[e.value for e in RequestEventFormat]),
            load_default=RequestEventFormat.HTML.value,
        )

    payload = fields.Nested(CommentExtra)


class NoExtrasSchema(BaseEventSchema):
    """No extras schema."""


class RequestEventSchema(BaseRecordSchema, OneOfSchema):
    """Schema."""

    # TODO: Make this schema hookable? how?

    type_schemas = {
        RequestEventType.COMMENT.value: CommentSchema,
        RequestEventType.ACCEPTED.value: NoExtrasSchema,
        RequestEventType.DECLINED.value: NoExtrasSchema,
        RequestEventType.CANCELLED.value: NoExtrasSchema,
        RequestEventType.REMOVED.value: NoExtrasSchema,
        RequestEventType.EXPIRED.value: NoExtrasSchema,
    }
    type_field_remove = False

    def get_obj_type(self, obj):
        """Return key of type_schemas to use given object to dump."""
        return obj.type
