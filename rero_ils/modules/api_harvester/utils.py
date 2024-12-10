# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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

"""ApiHarvester utils."""

from __future__ import absolute_import, print_function

from flask import current_app
from invenio_db import db
from invenio_oaiserver.models import OAISet
from sqlalchemy.exc import OperationalError

from .errors import ApiHarvesterConfigNotFound
from .models import ApiHarvestConfig


def add_set(spec, name, pattern, description="..."):
    """Add OAI set.

    :param spec: set identifier
    :param name: human readable name of the set
    :param pattern: search pattern to get records
    :param description: human readable description
    """
    try:
        oaiset = OAISet(
            spec=spec, name=name, description=description, system_created=False
        )
        oaiset.search_pattern = pattern
        db.session.add(oaiset)
        db.session.commit()
        msg = f"OAIset added: {name}"
    except Exception as err:
        db.session.rollback()
        msg = f"OAIset exist: {name} {err}"
    return msg


def api_source(name, url="", classname=None, code="", update=False):
    """Add ApiHarvestConfig do DB.

    :param name: name for the configuration
    :param url: harvesting url
    :param classname: Class responsible for getting record_serializers
    :param code: code added to electronic_location['nonpublic_note']
    :param update: update configuration if exist
    :returns: update message string
    """
    with current_app.app_context():
        msg = "No Update"
        source = ApiHarvestConfig.query.filter_by(name=name).first()
        if not source:
            source = ApiHarvestConfig(
                name=name, url=url, classname=classname, code=code
            )
            source.save()
            db.session.commit()
            msg = "Add"
        elif update:
            source.name = name
            msgs = []
            if url != "":
                source.url = url
                msgs.append(f"url:{url}")
                source.classname = classname
                msgs.append(f"classname:{classname}")
            if code != "":
                source.code = code
                msgs.append(f"code:{code}")
            db.session.commit()
            msg = f'Update {", ".join(msgs)}'
        return msg


def get_apiharvest_object(name):
    """Query and returns an ApiHarvestConfig object based on its name.

    :param name: The name of the ApiHarvestConfig object.
    :returns: The ApiHarvestConfig object.
    """
    get_config_error_count = 0
    get_config_ok = False
    while not get_config_ok and get_config_error_count < 5:
        try:
            obj = ApiHarvestConfig.query.filter_by(name=name).first()
            get_config_ok = True
        except OperationalError:
            get_config_error_count += 1
            current_app.logger.error(
                "ApiHarvestConfig OperationalError: " f"{get_config_error_count} {name}"
            )

    if not obj:
        raise ApiHarvesterConfigNotFound(
            f"Unable to find ApiHarvesterConfig obj with name {name}."
        )

    return obj
