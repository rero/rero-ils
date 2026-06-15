# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SRU (Search/Retrieve via URL) and CQL (Contextual Query Language) support.

Implements the SRU 1.1 protocol for searching documents via standard CQL queries,
including query parsing, Elasticsearch translation, and result set management.

See Also:
    - SRU Standard: http://www.loc.gov/standards/sru/
    - CQL Specification: http://www.loc.gov/standards/sru/cql/
"""
