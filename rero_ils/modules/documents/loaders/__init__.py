# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document loaders."""

from .marcxml import marcxml_marshmallow_loader

marcxml_loader = marcxml_marshmallow_loader
