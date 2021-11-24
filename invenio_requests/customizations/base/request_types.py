# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Base class for creating custom types of requests.

The `RequestType` classes are the most important part in the customization/extension
mechanism for custom types of requests.
TODO explain what can be done here, and how!
"""


from uuid import uuid4

import marshmallow as ma


class RequestType:
    """Base class for custom request types."""

    type_id = "invenio-requests.request"
    """The unique and constant identifier for this type of requests.

    Since this property is used to map generic chunks of data from the database
    (i.e. the request model entries) to their correct `RequestType`, this should
    be a globally unique value.
    By convention, this would be the name of the package in which the custom
    `RequestType` is defined as prefix, together with a suffix related to the
    `RequestType`.
    Further, it should be constant after the first release of the package
    (otherwise, requests created with the old value will no longer be able to be
    mapped to their `RequestType`).
    """

    name = "Generic Request"
    """The human-readable name for this type of requests."""

    available_statuses = {
        "draft": True,
        "open": True,
        "cancelled": False,
        "declined": False,
        "accepted": False,
        "expired": False,
    }
    """Available statuses for the Request.

    The keys in this dictionary is the set of available statuses, and their
    values are indicators whether this Request is still considered to be
    "open" in this state.
    """

    available_actions = {}
    """Available actions for this Request.

    The keys are the internal identifiers for the actions, the values are
    the actual RequestAction classes (not objects).
    Whenever an action is looked up, a new object of the registered
    RequestAction class is instantiated with the current Request object as
    argument.
    """

    payload_schema = None
    """Schema for supported fields.

    A dictionary of fields mappings is expected:

    .. code-block:: python

        payload_schema = {
            "content": fields.String(),
        }
    """

    def _create_marshmallow_schema(self):
        """Create a marshmallow schema for this request type."""
        from invenio_requests.services.schemas import RequestSchema

        # Use a bare schema if no payload
        if self.payload_schema is None:
            return RequestSchema

        # Raise on invalid payload keys
        class PayloadBaseSchema(ma.Schema):
            class Meta:
                unknown = ma.RAISE

        return RequestSchema.from_dict({
            "payload": ma.fields.Nested(
                # Dynamically create a schema from the fields defined
                # by the payload schema dict.
                PayloadBaseSchema.from_dict(self.payload_schema),
            ),
        })


    @property
    def marshmallow_schema(self):
        """Create a schema for the entire request including payload."""
        if not hasattr(self, '_marshmallow_schema'):
            self._marshmallow_schema = self._create_marshmallow_schema()
        return self._marshmallow_schema


    def generate_external_id(self, request, **kwargs):
        """Generate a new external identifier.

        This method can be overridden in subclasses to create external identifiers
        according to a custom schema, using the information associated with the request
        (e.g. topic, receiver, creator).
        """
        return str(uuid4())

    def __str__(self):
        """Return str(self)."""
        return self.name

    def __repr__(self):
        """Return repr(self)."""
        return f"<RequestType '{self.name}'>"
