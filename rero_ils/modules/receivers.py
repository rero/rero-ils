# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Query factories for REST API."""

import json
import re

from invenio_search import current_search


def process_boosting(index_name, config):
    """Expand the '*' using the mapping file.

    :param config: array of es fields.
    :returns: the expanded version of *.
    """
    config = config.copy()
    try:
        config.remove("*")
    except ValueError:
        # nothing to replace
        return config
    # list of existing fields without the boosting factor
    existing_fields = [re.sub(r"\^\d+$", "", field) for field in config]
    doc_mappings = list(current_search.aliases[index_name].values())
    assert len(doc_mappings) == 1
    mapping_path = doc_mappings.pop()
    with open(mapping_path) as body:
        mapping = json.load(body)
    fields = []
    for prop, conf in mapping["mappings"]["properties"].items():
        field = prop
        # fields for multiple mapping configurations
        if conf.get("fields"):
            tmp_fields = [field, f"{field}.*"]
            for tmp_f in tmp_fields:
                if tmp_f not in existing_fields:
                    fields.append(tmp_f)
            continue
        # add .* for field with children
        if conf.get("properties"):
            field = f"{field}.*"
        # do nothing for existing fields
        if field in existing_fields:
            continue
        fields.append(field)
    return config + fields


def set_boosting_query_fields(sender, app=None, **kwargs):
    """Expand '*' in the boosting configuration.

    :param sender: sender of the signal
    :param app: the flask app
    """
    # required to access to the flask extension
    with app.app_context():
        for key, value in app.config["RERO_ILS_QUERY_BOOSTING"].items():
            app.config["RERO_ILS_QUERY_BOOSTING"][key] = process_boosting(key, value)
