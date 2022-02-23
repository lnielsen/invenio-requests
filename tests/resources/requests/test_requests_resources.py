# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request resource tests."""

import copy


def assert_api_response_json(expected_json, received_json):
    """Assert the REST API response's json."""
    # We don't compare dynamic times at this point
    received_json.pop("created")
    received_json.pop("updated")
    received_json.pop("revision_id")
    assert expected_json == received_json


def assert_api_response(response, code, json):
    """Assert the REST API response."""
    assert code == response.status_code
    assert_api_response_json(json, response.json)


def check_reference_search_filter_results(response, expected_hits, expected_req_nums):
    """Check if all expected results are there."""
    hits = response.json["hits"]["hits"]
    reported_hits = int(response.json["hits"]["total"])
    req_numbers = [r["number"] for r in response.json["hits"]["hits"]]

    assert len(req_numbers) == len(expected_req_nums)
    for num in expected_req_nums:
        assert num in req_numbers

    assert reported_hits == len(hits) == expected_hits


def test_reference_search_filters(app, client_logged_as, headers, example_requests):
    """Test if the reference search filters (e.g. receiver=user:1) work as intended."""
    # use the admin with superuser-access to evade potential permission issues
    client = client_logged_as("admin@example.org")
    req1, req2, req3 = example_requests

    # get unfiltered responses
    response = client.get(
        "/requests/",
        headers=headers,
    )
    check_reference_search_filter_results(
        response, 3, [req1.number, req2.number, req3.number]
    )

    # get requests where user #1 is the receiver (should be the first two)
    response = client.get(
        "/requests/?receiver=user:1",
        headers=headers,
    )
    check_reference_search_filter_results(response, 2, [req1.number, req2.number])

    # get requests where user #2 is the receiver (should be the last one)
    response = client.get(
        "/requests/?receiver=user:2",
        headers=headers,
    )
    check_reference_search_filter_results(response, 1, [req3.number])

    # get requests where user #3 is the receiver (none)
    response = client.get(
        "/requests/?receiver=user:3",
        headers=headers,
    )
    check_reference_search_filter_results(response, 0, [])

    # check what happens when there's an invalid reference
    # (the filter should get dropped)
    response = client.get(
        "/requests/?receiver=nosuchthing:1",
        headers=headers,
    )
    check_reference_search_filter_results(
        response, 3, [req1.number, req2.number, req3.number]
    )


def test_empty_comment(
    app, client_logged_as, headers, example_requests, request_action_resource_data
):
    client = client_logged_as("admin@example.org")
    r1, r2, r3 = example_requests
    for r in [r1, r2, r3]:
        r.status = "submitted"
        r.commit()

    # Accept (valid for other actions too) no payload is Ok
    response = client.post(f"/requests/{r1.id}/actions/accept", headers=headers)
    assert 200 == response.status_code
    assert "accepted" == response.json["status"]

    # Accept {} is Ok
    response = client.post(
        f"/requests/{r2.id}/actions/accept", headers=headers, json={}
    )
    assert 200 == response.status_code
    assert "accepted" == response.json["status"]

    # Accept empty content is an error
    data = copy.deepcopy(request_action_resource_data)
    data["payload"]["content"] = ""
    response = client.post(
        f"/requests/{r3.id}/actions/accept", headers=headers, json=data
    )
    assert 400 == response.status_code

    response = client.get(f"/requests/{r3.id}", headers=headers)
    assert "submitted" == response.json["status"]


def test_create_is_disallowed(app, client_logged_as, headers, request_resource_data):
    """Test if the user cannot create a new generic request."""
    client = client_logged_as("user1@example.org")

    # try to create a request, should fail
    response = client.post("/requests/", headers=headers, json=request_resource_data)
    assert response.status_code == 405


def test_simple_request_flow(app, client_logged_as, headers, example_request):
    client = client_logged_as("user1@example.org")
    id_ = str(example_request.id)
    number = str(example_request.number)

    # test read
    response = client.get(f"/requests/{id_}", headers=headers)
    expected_data = {
        "id": id_,
        "number": example_request.number,
        "title": "Foo bar",
        "type": "base-request",
        "created_by": {"user": "1"},
        "receiver": {"user": "2"},
        "topic": None,
        "status": "created",
        "is_open": False,
        "is_closed": False,
        "expires_at": None,
        "is_expired": False,
        "links": {
            "self": f"https://127.0.0.1:5000/api/requests/{id_}",
            "timeline": f"https://127.0.0.1:5000/api/requests/{id_}/timeline",
            "comments": f"https://127.0.0.1:5000/api/requests/{id_}/comments",
            "actions": {
                "submit": f"https://127.0.0.1:5000/api/requests/{id_}/actions/submit",
            },
        },
    }
    assert_api_response(response, 200, expected_data)

    # submit the request
    url = response.json["links"]["actions"]["submit"]
    response = client.post(url[len("https://127.0.0.1:5000/api") :], headers=headers)
    expected_data.update(
        {
            "status": "submitted",
            "is_open": True,
            "links": {
                "self": f"https://127.0.0.1:5000/api/requests/{id_}",
                "timeline": f"https://127.0.0.1:5000/api/requests/{id_}/timeline",
                "comments": f"https://127.0.0.1:5000/api/requests/{id_}/comments",
                "actions": {
                    "cancel": f"https://127.0.0.1:5000/api/requests/{id_}/actions/cancel",  # noqa
                },
            },
        }
    )
    assert_api_response(response, 200, expected_data)

    # cancel the request
    url = response.json["links"]["actions"]["cancel"]
    response = client.post(url[len("https://127.0.0.1:5000/api") :], headers=headers)
    expected_data.update(
        {
            "status": "cancelled",
            "is_closed": True,
            "is_open": False,
            "links": {
                "self": f"https://127.0.0.1:5000/api/requests/{id_}",
                "timeline": f"https://127.0.0.1:5000/api/requests/{id_}/timeline",
                "comments": f"https://127.0.0.1:5000/api/requests/{id_}/comments",
                "actions": {},
            },
        }
    )
    assert_api_response(response, 200, expected_data)
