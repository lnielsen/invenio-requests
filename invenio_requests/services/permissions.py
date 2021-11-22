# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request permissions."""

from elasticsearch_dsl import Q
from invenio_access.permissions import any_user
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, Generator, SystemProcess


class Requester(Generator):
    """Allows request makers."""

    def needs(self, request=None, **kwargs):
        """Enabling Needs.

        record is a request here
        """
        # TODO when request is more fleshed out
        return [any_user]
        # return [
        #     UserNeed(owner.owner_id) for owner in record.access.owners
        # ]
        # even above could be optimized without caching by using raw ids

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        # TODO when request is more fleshed out
        return []


class Reviewers(Generator):
    """Allows request reviewers."""

    def needs(self, request=None, **kwargs):
        """Enabling Needs.

        record is a request here
        """
        # TODO when request is more fleshed out
        return [any_user]
        # return [
        #     UserNeed(owner.owner_id) for owner in record.access.owners
        # ]
        # even above could be optimized without caching by using raw ids

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        # TODO when request is more fleshed out
        return []


class Commenter(Generator):
    """Allows request event commenter."""

    def needs(self, event=None, **kwargs):
        """Enabling Needs."""
        # TODO: postponed until we have a common owner/creator since it is
        #       used in multiple places
        return [any_user]
        # return [UserNeed(event.created_by.owner_id)] if event else []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as creator."""
        users = [n.value for n in identity.provides if n.method == "id"]
        if users:
            return Q("terms", **{"created_by.user": users})


class PermissionPolicy(RecordPermissionPolicy):
    """Permission policy."""

    can_search = [SystemProcess(), AnyUser()]
    can_read = [SystemProcess(), AnyUser()]
    can_create = [SystemProcess(), AnyUser()]
    can_update = [SystemProcess(), AnyUser()]
    can_delete = [SystemProcess(), AnyUser()]

    # **Request Events Permission policy.**
    # Comments need special cases for some service methods
    # shorter: can_create_comment
    can_create_event_comment = [Requester(), Reviewers(), SystemProcess()]
    can_update_event_comment = [Commenter(), SystemProcess()]
    # Reviewers too for moderation
    can_delete_event_comment = [Commenter(), Reviewers(), SystemProcess()]

    # Accept/Decline/Cancel need special permissions
    can_accept = [Reviewers(), SystemProcess()]
    can_decline = [Reviewers(), SystemProcess()]
    can_cancel = [Requester(), SystemProcess()]

    # Other events are all the same
    can_create_event = [SystemProcess()]
    can_read_event = [Requester(), Reviewers(), SystemProcess()]
    can_update_event = [SystemProcess()]
    can_delete_event = [SystemProcess()]
    can_search_event = [Requester(), Reviewers(), SystemProcess()]
