# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests service."""

from invenio_db import db
from invenio_records_resources.services import RecordService, ServiceSchemaWrapper

from ...customizations.base import RequestActions
from ...errors import CannotExecuteActionError
from ...proxies import current_registry
from ...resolvers import reference_entity, reference_identity
from .links import RequestLinksTemplate


class RequestsService(RecordService):
    """Requests service."""

    @property
    def links_item_tpl(self):
        """Item links template."""
        return RequestLinksTemplate(self.config.links_item, self.config.action_link)

    @property
    def request_type_registry(self):
        """Request_type_registry."""
        return current_registry

    def _wrap_schema(self, schema):
        """Wrap schema."""
        return ServiceSchemaWrapper(self, schema)


    # needs unit of work
    #@unit_of_work
    def create(self, identity, data, request_type, receiver, creator=None, topic=None, uow=None):
        """Create a record."""
        self.require_permission(identity, "create")

        # add comment why we're not using "self.schema" - because of request type depend schemas
        schema = self._wrap_schema(request_type.marshmallow_schema)
        data, errors = schema.load(
            data,
            context={"identity": identity},
        )

        # parts of the data are initialized here, parts of it via the components
        creator = reference_entity(creator) if creator else reference_identity(identity)
        request = self.record_cls.create(
            {},
            request_type=request_type,
            created_by=creator,
            topic=reference_entity(topic),
            receiver=reference_entity(receiver),
        )

        # run components
        # instead: self.run_components('create', ..args..)
        for component in self.components:
            if hasattr(component, "create"):
                component.create(
                    identity,
                    data=data,
                    record=request,
                    errors=errors,
                )

        # persist record (DB and index)
        # needs unit of work: uow.register(RecordCommit(request))
        request.commit()
        db.session.commit()
        if self.indexer:
            self.indexer.index(request)

        return self.result_item(
            self,
            identity,
            request,
            schema=schema,
            links_tpl=self.links_item_tpl,
            errors=errors,
        )

    def read(self, id_, identity):
        """Retrieve a request."""
        # resolve and require permission
        request = self.record_cls.get_record(id_)
        self.require_permission(identity, "read", record=request)

        # run components
        # ditto
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, record=request)

        return self.result_item(
            self,
            identity,
            request,
            schema=self._wrap_schema(request.request_type.marshmallow_schema),
            links_tpl=self.links_item_tpl,
        )

    def read_all(self, identity, fields, max_records=150, **kwargs):
        """Search for records matching the querystring."""
        # TODO check later
        return super().read_all(identity, fields, max_records=max_records, **kwargs)

    def read_many(self, identity, ids, fields=None, **kwargs):
        """Search for requests matching the ids."""
        # TODO check later
        return super().read_many(identity, ids, fields=fields, **kwargs)

    def scan(self, identity, params=None, es_preference=None, **kwargs):
        """Scan for requests matching the querystring."""
        # TODO check later
        return super().scan(identity, params=None, es_preference=None, **kwargs)

    def search(self, identity, params=None, es_preference=None, **kwargs):
        """Search for records matching the querystring."""
        # TODO check later
        return super().search(identity, es_preference=None, **kwargs)

    # unit of work
    def update(self, id_, identity, data):
        """Replace a request."""
        request = self.record_cls.get_record(id_)

        # TODO do we need revisions for requests?
        # self.check_revision_id(request, revision_id)

        # check permissions
        self.require_permission(identity, "update", record=request)

        schema = self._wrap_schema(request.request_type.marshmallow_schema)
        data, _ = schema.load(
            data,
            context={
                "identity": identity,
                "record": request,
            },
        )

        # run components
        for component in self.components:
            if hasattr(component, "update"):
                component.update(identity, data=data, record=request)

        request.commit()
        db.session.commit()

        if self.indexer:
            self.indexer.index(request)

        return self.result_item(
            self,
            identity,
            request,
            schema=schema,
            links_tpl=self.links_item_tpl,
        )

    # unit of work
    def delete(self, id_, identity):
        """Delete a request from database and search indexes."""
        request = self.record_cls.get_record(id_)

        # TODO do we need revisions for requests?
        # self.check_revision_id(request, revision_id)

        # check permissions
        self.require_permission(identity, "delete", record=request)

        # run components
        for component in self.components:
            if hasattr(component, "delete"):
                component.delete(identity, record=request)

        request.delete()
        db.session.commit()

        if self.indexer:
            self.indexer.delete(request, refresh=True)

        return True

    def reindex(self, identity, params=None, es_preference=None, **kwargs):
        """Reindex records matching the query parameters."""
        # TODO check later
        return super().reindex(identity, params=None, es_preference=None, **kwargs)

    def rebuild_index(self, identity):
        """Reindex all records managed by this service."""
        for req_meta in self.record_cls.model_cls.query.all():
            request = self._request_from_model(req_meta)

            if not request.is_deleted:
                self.indexer.index(request)

    # unit of work
    def execute_action(self, identity, id_, action, data):
        """Execute the given action for the request, if possible.

        For instance, it would be not possible to execute the specified
        action on the request, if the latter has the wrong status.
        """
        request = self.record_cls.get_record(id_)

        # TODO permission checks

        # check if the action *can* be executed
        # (i.e. the request has the right status, etc.)
        if not RequestActions.can_execute(identity, request, action, data):
            raise CannotExecuteActionError(action)

        # uow should be passed in here as well.
        RequestActions.execute(identity, request, action, data)

        return self.result_item(
            self,
            identity,
            request,
            schema=self._wrap_schema(request.request_type.marshmallow_schema),
            links_tpl=self.links_item_tpl,
        )
