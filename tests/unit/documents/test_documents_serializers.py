# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document serializers tests."""

from rero_ils.modules.documents.serializers.json import _rewrite_nested_terms


def test_rewrite_nested_terms():
    """Test the holdings-to-documents facet terms rewrite.

    The nested aggregation counts holdings; the `record_count`
    (reverse_nested) sub-aggregation gives the document count. The rewrite
    must expose it as `doc_count` and drop empty buckets, preserve the order
    returned by Elasticsearch (the query orders terms by `record_count`, so
    the rewrite must not reorder the buckets), and drop the stale
    holdings-based terms metadata.
    """
    terms = {
        "buckets": [
            {"key": "lib1", "doc_count": 5, "record_count": {"doc_count": 2}},
            {"key": "lib2", "doc_count": 3, "record_count": {"doc_count": 4}},
            {"key": "lib3", "doc_count": 0, "record_count": {"doc_count": 0}},
        ],
        # holdings-based metadata: no longer matches the document counts
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 7,
    }

    # `doc_count` becomes the document count, `lib3` is pruned, the incoming
    # order is kept (a document-count sort would move `lib2` first) and the
    # stale (non-zero) holdings metadata is dropped.
    assert _rewrite_nested_terms(terms) == {
        "buckets": [
            {"key": "lib1", "doc_count": 2},
            {"key": "lib2", "doc_count": 4},
        ],
    }
