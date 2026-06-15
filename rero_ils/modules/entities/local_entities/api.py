# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating local entities."""

from functools import partial

from rero_ils.modules.api import IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.operation_logs.extensions import OperationLogObserverExtension
from rero_ils.modules.providers import Provider

from ..api import Entity
from ..dumpers import replace_refs_dumper
from ..models import EntityResourceType
from .extensions import AuthorizedAccessPointExtension, LocalEntityFactoryExtension
from .models import LocalEntityIdentifier, LocalEntityMetadata

# provider
LocalEntityProvider = type(
    "LocalEntityProvider",
    (Provider,),
    {"identifier": LocalEntityIdentifier, "pid_type": "locent"},
)
# minter
local_entity_id_minter = partial(id_minter, provider=LocalEntityProvider)
# fetcher
local_entity_id_fetcher = partial(id_fetcher, provider=LocalEntityProvider)


class LocalEntitiesSearch(IlsRecordsSearch):
    """Local entities search."""

    class Meta:
        """Meta class."""

        index = "local_entities"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class LocalEntity(Entity):
    """Local entity class."""

    minter = local_entity_id_minter
    fetcher = local_entity_id_fetcher
    provider = LocalEntityProvider
    model_cls = LocalEntityMetadata
    # disable legacy replace refs
    enable_jsonref = False

    _extensions = [
        LocalEntityFactoryExtension(),
        AuthorizedAccessPointExtension(),
        OperationLogObserverExtension(),
    ]

    @property
    def resource_type(self):
        """Get entity type."""
        return EntityResourceType.LOCAL

    @property
    def type(self):
        """Shortcut for local entity type."""
        return self.get("type")

    def get_authorized_access_point(self, language):
        """Get localized authorized_access_point.

        For a local entity, no matters `language` parameter, the authorized
        access point is always the `authorized_access_point` field content.

        :param language: language for authorized access point.
        :returns: authorized access point in given language.
        """
        return self.get("authorized_access_point")

    def resolve(self):
        """Resolve references data.

        Uses the dumper to do the job.
        Mainly used by the `resolve=1` URL parameter.

        :returns: a fresh copy of the resolved data.
        """
        # DEV NOTES :: Why using `replace_refs_dumper`
        #   Not really required now (because no $ref relation exists into an
        #   entity resource) but in next development, links between entity will
        #   be implemented.
        #   The links will be stored as a `$ref` and `replace_refs_dumper`
        #   will be used.
        return self.dumps(replace_refs_dumper)
