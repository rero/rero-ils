# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition api record."""

from abc import ABC

from rero_ils.modules.api import IlsRecord


class AcquisitionIlsRecord(IlsRecord, ABC):
    """Abstract acquisition resource record."""

    def __str__(self):
        """Human-readable record string representation."""
        output = f"[{self.provider.pid_type}#{self.pid}]"
        if "name" in self:
            output += f" {self['name']}"
        return output

    def __repr__(self):
        """Full representation of the record."""
        return super().__repr__()
