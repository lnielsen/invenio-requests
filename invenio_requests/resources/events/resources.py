# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests resource."""

from copy import deepcopy

from flask import g
from flask_resources import (
    JSONDeserializer,
    JSONSerializer,
    RequestBodyParser,
    ResponseHandler,
    from_conf,
    request_body_parser,
    request_parser,
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
from invenio_records_resources.resources.records.resource import request_headers
from invenio_records_resources.resources.records.utils import es_preference
from marshmallow import fields

from ...records.api import RequestEventType

# split configs from resources into two separate models:
# - events.resources
# - events.config

#
# Resource config
#
# shorter name: CommentsResourceConfig
class RequestCommentsResourceConfig(RecordResourceConfig):
    """Request Events resource configuration."""

    blueprint_name = "request_events"
    url_prefix = "/requests"
    routes = {
        "list": "/<request_id>/comments",
        "item": "/<request_id>/comments/<comment_id>",
        "timeline": "/<request_id>/timeline",
    }

    # Input
    # WARNING: These "request_*" values have nothing to do with the
    #          "Request" of "RequestEvent". They are related to the Flask
    #          request.
    # this request_list_view_args and request_list_view_args can be merged into
    # request_view_args, since non of them are defined as required. main point
    # here is to parse the values so the are avilabe on the resource_requestctx
    request_list_view_args = {
        "request_id": fields.Str(),
    }
    request_list_view_args = {
        "request_id": fields.Str(),
        "comment_id": fields.Str(),
    }
    request_search_args = SearchRequestArgsSchema
    # the default in invenio-records-resources so no need to override
    request_body_parsers = {"application/json": RequestBodyParser(JSONDeserializer())}

    # Ouput
    # the default in invenio-records-resources so no need to override
    response_handlers = {
        "application/json": ResponseHandler(JSONSerializer(), headers=etag_headers),
    }


#
# Resource
#
# shorter name: CommentsResource
class RequestCommentsResource(RecordResource):
    """Resource for Request comments for now."""

    list_view_args_parser = request_parser(
        from_conf("request_list_view_args"), location="view_args"
    )
    item_view_args_parser = request_parser(
        from_conf("request_item_view_args"), location="view_args"
    )
    search_args_parser = request_parser(
        from_conf("request_search_args"), location="args"
    )
    data_parser = request_body_parser(
        parsers=from_conf("request_body_parsers"),
        default_content_type=from_conf("default_content_type"),
    )

    def create_url_rules(self):
        """Create the URL rules for the record resource."""
        # Aassignment of routes should be part of the
        # Config class
        routes = self.config.routes
        return [
            route("POST", routes["list"], self.create),
            route("GET", routes["item"], self.read),
            route("PUT", routes["item"], self.update),
            route("DELETE", routes["item"], self.delete),
            route("GET", routes["timeline"], self.search),
        ]

    @list_view_args_parser
    @data_parser
    @response_handler()
    def create(self):
        """Create an event."""
        data = deepcopy(resource_requestctx.data)
        data["type"] = RequestEventType.COMMENT.value
        item = self.service.create(
            identity=g.identity,
            request_id=resource_requestctx.view_args["request_id"],
            data=data,
        )
        return item.to_dict(), 201

    @item_view_args_parser
    @response_handler()
    def read(self):
        """Read an event.

        Because each event has a unique id, we can disregard the request_id
        for now.
        """
        item = self.service.read(
            identity=g.identity,
            id_=resource_requestctx.view_args["comment_id"],
        )
        return item.to_dict(), 200

    @item_view_args_parser
    @request_headers
    @data_parser
    @response_handler()
    def update(self):
        """Update a comment."""
        data = deepcopy(resource_requestctx.data)
        data["type"] = RequestEventType.COMMENT.value
        item = self.service.update(
            identity=g.identity,
            id_=resource_requestctx.view_args["comment_id"],
            data=data,
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return item.to_dict(), 200

    @item_view_args_parser
    @request_headers
    def delete(self):
        """Delete a comment."""
        self.service.delete(
            identity=g.identity,
            id_=resource_requestctx.view_args["comment_id"],
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return "", 204

    @list_view_args_parser
    @search_args_parser
    @response_handler(many=True)
    def search(self):
        """Perform a search over EVENTS.

        Its primary purpose is as a batch read of events i.e. the timeline.
        """
        params = deepcopy(resource_requestctx.args)
        params["request_id"] = resource_requestctx.view_args["request_id"]
        # shouldn't defaults be set by the service instead of the resource.
        params.setdefault("sort", "oldest")
        hits = self.service.search(
            identity=g.identity,
            params=params,
            es_preference=es_preference(),
        )
        return hits.to_dict(), 200
