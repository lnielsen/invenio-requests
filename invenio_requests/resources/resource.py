# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests resource."""

# move into invenio_requests.resources.requests.resource
# move into invenio_requests.resources.requests.config


import marshmallow as ma
from flask import g
# import style
from flask_resources import (
    JSONSerializer,
    ResponseHandler,
    resource_requestctx,
    response_handler,
    route,
)
from invenio_records_resources.resources import (
    RecordResource,
    RecordResourceConfig,
    SearchRequestArgsSchema,
)
from invenio_records_resources.resources.records.headers import etag_headers
from invenio_records_resources.resources.records.resource import (
    request_data,
    request_headers,
    request_search_args,
    request_view_args,
)
from invenio_records_resources.resources.records.utils import es_preference


#
# Request args
#
class RequestSearchRequestArgsSchema(SearchRequestArgsSchema):
    """Add parameter to parse tags."""

    # TODO what do we need here?
    pass

    # parse created_by, topic and receiver
    # /api/requests?created_by=user:1,user:2
    # /api/requests?topic=record:124,record:124
    # /api/requests?receiver=community:blr,community:opendata&open=1
    # see VocabulariesResourceConfig and
    # FilterParam.factory(param='tags', field='tags') in records-resources

    # /api/requests?resolution=cancelled or state=cancelled (probably a facet)

    # we will need different facets depending on if we show the dashboard or community requests
    # /api/requests should facet on communities (receiver), status, request type, topic?
    # /api/communities/:blr/requests # status, open/closed, request type, topic?



#
# Resource config
#
class RequestsResourceConfig(RecordResourceConfig):
    """Requests resource configuration."""

    blueprint_name = "requests"
    url_prefix = "/requests"
    routes = {
        "list": "/",
        "item": "/<id>",
        "action": "/<id>/actions/<action>",
    }

    request_view_args = {
        "id": ma.fields.Str(),
        "action": ma.fields.Str(),
    }

    request_search_args = RequestSearchRequestArgsSchema

    response_handlers = {
        "application/json": ResponseHandler(JSONSerializer(), headers=etag_headers),
        # yes (also we should look at i18n....i.e. providing labels for accepted, cancelled, ... if needed, localization of dates and times)
        # also, we might need some permissions related information for the JS app such as : can_comment, can_edit, ....
        # TODO
        # "application/vnd.inveniordm.v1+json": ResponseHandler(
        #     MarshmallowJSONSerializer(
        #         schema_cls=VocabularyL10NItemSchema,
        #         many_schema_cls=VocabularyL10NListSchema,
        #     ),
        #     headers=etag_headers,
        # ),
    }


#
# Resource
#
class RequestsResource(RecordResource):
    """Resource for generic requests."""

    def create_url_rules(self):
        """Create the URL rules for the record resource."""
        routes = self.config.routes
        return [
            route("GET", routes["list"], self.search),
            route("GET", routes["item"], self.read),
            route("PUT", routes["item"], self.update),
            route("DELETE", routes["item"], self.delete),
            route("POST", routes["action"], self.execute_action),
        ]

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search(self):
        """Perform a search over the items."""
        hits = self.service.search(
            identity=g.identity,
            params=resource_requestctx.args,
            es_preference=es_preference(),
        )
        return hits.to_dict(), 200

    @request_view_args
    @response_handler()
    def read(self):
        """Read an item."""
        item = self.service.read(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return item.to_dict(), 200

    @request_headers
    @request_view_args
    @request_data
    @response_handler()
    def update(self):
        """Update an item."""
        # TODO should we allow updating of requests in this general resource?
        # depends on what they can update - title, description yes I woudl say....have to think about the rest.
        item = self.service.update(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
            data=resource_requestctx.data,
        )
        return item.to_dict(), 200

    @request_headers
    @request_view_args
    def delete(self):
        """Delete an item."""
        self.service.delete(
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return "", 204

    @request_headers
    @request_view_args
    def execute_action(self):
        """Execute action."""
        item = self.service.execute_action(
            action=resource_requestctx.view_args["action"],
            id_=resource_requestctx.view_args["id"],
            identity=g.identity,
        )
        return item.to_dict(), 200
