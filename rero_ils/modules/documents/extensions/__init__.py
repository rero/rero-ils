# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document record extensions."""

from .add_cover_url import AddCoverUrlExtension
from .add_mef_pid import AddMEFPidExtension
from .edition_statement import EditionStatementExtension
from .provision_activities import ProvisionActivitiesExtension
from .series_statement import SeriesStatementExtension
from .title import TitleExtension

__all__ = (
    "AddCoverUrlExtension",
    "AddMEFPidExtension",
    "EditionStatementExtension",
    "ProvisionActivitiesExtension",
    "SeriesStatementExtension",
    "TitleExtension",
)
