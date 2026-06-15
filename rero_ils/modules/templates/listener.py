# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Template."""

from .api import TemplatesSearch


def prepare_template_data(
    sender,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    arguments=None,
    **dummy_kwargs,
):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The document type of the record.
    """
    if index.split("-")[0] == TemplatesSearch.Meta.index:
        # remove `data` fields from search.
        #   This metadata isn't required for indexing process and cause some
        #   troubles with $ref resolution
        json.pop("data", None)
