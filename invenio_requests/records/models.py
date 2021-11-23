# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Base classes for requests in Invenio."""

import uuid

from invenio_db import db
from invenio_records.models import RecordMetadataBase
from sqlalchemy.dialects import mysql
from sqlalchemy.types import String
from sqlalchemy_utils import UUIDType


class RequestMetadata(db.Model, RecordMetadataBase):
    """Base class for requests of any kind in Invenio."""

    __tablename__ = "request_metadata"

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)

    external_id = db.Column(String(50), unique=True, index=True, nullable=True)

    expires_at = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        default=None,
        nullable=True,
    )

    # TODO later
    # labels: maybe per-community CVs
    # assignees: enables notifications? no impact on permissions


class RequestEventModel(db.Model, RecordMetadataBase):
    """Request Events model."""

    __tablename__ = "request_events"

    type = db.Column(db.String(1), nullable=False)
    request_id = db.Column(
        UUIDType, db.ForeignKey(RequestMetadata.id, ondelete="CASCADE")
    )
    request = db.relationship(RequestMetadata)
