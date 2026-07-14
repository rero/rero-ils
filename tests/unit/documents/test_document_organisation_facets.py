# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document organisation facet tests."""

from rero_ils.modules.documents.serializers.json import DocumentJSONSerializer


def test_build_organisation_aggregation_from_location_paths():
    """Build organisation aggregation without creating invalid children."""
    aggregation = {
        "organisation": {
            "buckets": [
                {"key": "org1", "doc_count": 2},
                {"key": "org2", "doc_count": 1},
            ]
        },
        "library": {
            "buckets": [
                {"key": "org1|lib1", "doc_count": 2},
                {"key": "org1|lib2", "doc_count": 1},
                {"key": "org2|lib3", "doc_count": 1},
            ]
        },
        "location": {
            "buckets": [
                {"key": "org1|lib1|loc1", "doc_count": 2},
                {"key": "org1|lib2|loc2", "doc_count": 1},
                {"key": "org2|lib3|loc3", "doc_count": 1},
            ]
        },
    }

    result = DocumentJSONSerializer._build_organisation_aggregation(aggregation)

    assert result["buckets"] == [
        {
            "key": "org1",
            "doc_count": 2,
            "library": {
                "buckets": [
                    {
                        "key": "lib1",
                        "doc_count": 2,
                        "location": {
                            "buckets": [{"key": "loc1", "doc_count": 2}],
                            "doc_count_error_upper_bound": 0,
                            "sum_other_doc_count": 0,
                        },
                    },
                    {
                        "key": "lib2",
                        "doc_count": 1,
                        "location": {
                            "buckets": [{"key": "loc2", "doc_count": 1}],
                            "doc_count_error_upper_bound": 0,
                            "sum_other_doc_count": 0,
                        },
                    },
                ],
                "doc_count_error_upper_bound": 0,
                "sum_other_doc_count": 0,
            },
        },
        {
            "key": "org2",
            "doc_count": 1,
            "library": {
                "buckets": [
                    {
                        "key": "lib3",
                        "doc_count": 1,
                        "location": {
                            "buckets": [{"key": "loc3", "doc_count": 1}],
                            "doc_count_error_upper_bound": 0,
                            "sum_other_doc_count": 0,
                        },
                    }
                ],
                "doc_count_error_upper_bound": 0,
                "sum_other_doc_count": 0,
            },
        },
    ]
