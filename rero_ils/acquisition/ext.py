# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Invenio module declaration for RERO ILS acquisitions."""


from . import config


class _ReroIlsAcquisitionState:
    """RERO ILS acquisition app state."""

    def __init__(self, app, resources_config):
        """Initialize state."""
        self.app = app
        self.resources_config = resources_config

    @property
    def resources(self):
        """Get the registered resources.

        :returns: Dictionary of registered resources.
        """
        return self.resources_config

    def get_service(self, resource_type):
        """Return the service corresponding to resource.

        :param resource_type: Type of resource.
        :returns: A service instance
        """
        if not self.resources.get(resource_type):
            raise Exception(
                f'No service configured for resource "{resource_type}"')

        return self.resources[resource_type].service


class ReroIlsAcquisition:
    """RERO ILS Acquisition app."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.app = app
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.init_resources(app)
        app.extensions['rero-ils-acquisition'] = _ReroIlsAcquisitionState(
            app, resources_config=self.resources_config)

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('ACQ_'):
                app.config.setdefault(k, getattr(config, k))

    def init_resources(self, app):
        """Initialize resources."""
        self.resources_config = getattr(config, "ACQ_RECORDS_RESOURCES")

        for key, resource in self.resources_config.items():
            app.register_blueprint(resource.as_blueprint())
