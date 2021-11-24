# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 CERN.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Type registry for looking up registered types per id/name.

The interface requires that the registered type have at least the property
``type_id`` defined:

.. code-block:: python

    class MyType(BaseType):
        type_id = "invenio-requests.my-id"
        type_name = "my-name"  # optional

Afterwards you can lookup types:

.. code-block:: python

    registry.lookup("invenio-request.my-id")
    registry.lookup_by_name("my_name")
    for t in registry:
        # do something
"""


class TypeRegistry:
    """Registry for looking up registered types per id/name."""

    def __init__(self, types):
        """Constructor."""
        self._registered_types = {}
        self._registered_names = {}
        for t in types:
            self.register_type(t)

    def register_type(self, type_, force=False):
        """Register the specified request_type."""
        type_id = type_.type_id
        type_name = getattr(type_, 'name', type_id)

        if force:
            self._registered_types[type_id] = type_
            self._registered_names[type_name] = type_id
        else:
            self._registered_types.setdefault(type_id, type_)
            self._registered_names.setdefault(type_name, type_id)

    def lookup(self, type_id, quiet=False, default=None):
        """Look up a registered type by its id."""
        if not quiet:
            return self._registered_types[type_id]

        return self._registered_types.get(type_id, default)

    def lookup_by_name(self, type_name, quiet=False, default=None):
        """Lookup a registered type by name."""
        if not quiet:
            self.lookup(
                self._registered_names[type_name],
                quiet=quiet,
                default=default
            )
        return self.lookup(
            self._registered_names.get(type_name, None),
            quiet=quiet,
            default=default
        )

    def __iter__(self):
        """Iterate over all types."""
        for t in self._registered_types.values():
            yield t
