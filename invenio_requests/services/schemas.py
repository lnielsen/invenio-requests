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
from marshmallow import (
    RAISE,
    Schema,
    ValidationError,
    fields,
    missing,
    validate,
    validates_schema,
)
from marshmallow_oneofschema import OneOfSchema
from marshmallow_utils import fields as utils_fields

from ..records.api import Request, RequestEventFormat, RequestEventType


class EntityReferenceBaseSchema(Schema):
    """Base schema for entity references, allowing only a single key.

    It will be populated dynamically by the ``RequestType``, based on the allowed
    reference types registered there.
    """

    class Meta:
        """Schema meta."""

        unknown = RAISE

    @validates_schema
    def there_can_be_only_one(self, data, **kwargs):
        """Only allow a single key."""
        if len(data) != 1:
            raise ValidationError("Entity references may only have one key")

    @classmethod
    def create_from_dict(cls, allowed_types, special_fields=None):
        """Create an entity reference schema based on the allowed reference types.

        Per default, a ``fields.String()`` field is registered for each of the type
        names in the ``allowed_types`` list.
        The field type can be customized by providing an entry in the
        ``special_fields`` dict, with the type name as key and the field type as value
         (e.g. ``{"user": fields.Integer()}``).
        """
        field_types = special_fields or {}
        for ref_type in allowed_types:
            # each type would be a String field per default
            field_types.setdefault(ref_type, fields.String())

        return cls.from_dict(
            {ref_type: field_types[ref_type] for ref_type in allowed_types}
        )


class RequestSchema(BaseRecordSchema):
    """Schema for requests.

    Note that the payload schema and the entity reference schemas (i.e. creator,
    receiver, and topic) are dynamically constructed and injected into this schema.
    """

    number = fields.String(dump_only=True)
    type = fields.String()
    title = utils_fields.SanitizedUnicode(default="")
    description = utils_fields.SanitizedUnicode()

    # status information is also likely set by the service
    status = fields.String(dump_only=True)
    is_open = fields.Boolean(dump_only=True)
    expires_at = utils_fields.TZDateTime(
        timezone=timezone.utc, format="iso", dump_only=True
    )
    is_expired = fields.Boolean(dump_only=True)

    class Meta:
        """Schema meta."""

        unknown = RAISE


class GenericRequestSchema(RequestSchema):
    """Generic request schema.

    CAUTION: This schema should not be used for the final validation of input
    data. Use the request type's own defined schema instead.

    This schema can be used in situations where you need to do basic validation
    or dumping of a request without the payload.

    This is used e.g. in Invenio-RDM-Records for dumping a request without
    having to know the specific request type.
    """

    created_by = fields.Dict()
    receiver = fields.Dict()
    topic = fields.Dict()


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
