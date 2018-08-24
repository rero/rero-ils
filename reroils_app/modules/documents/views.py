# -*- coding: utf-8 -*-
#
# This file is part of organisations.
# Copyright (C) 2018 RERO.
#

"""Blueprint used for loading templates.

The sole purpose of this blueprint is to ensure that Invenio can find the
templates and static files located in the folders of the same names next to
this file.
"""

from __future__ import absolute_import, print_function

from urllib.request import urlopen

import six
from dojson.contrib.marc21.utils import create_record, split_stream
from flask import Blueprint, abort, current_app, jsonify
from flask_babelex import gettext as _
from reroils_record_editor.permissions import record_edit_permission

from .dojson.contrib.unimarctojson import unimarctojson

blueprint = Blueprint(
    'documents',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/editor/import/bnf/ean/<int:ean>")
@record_edit_permission.require()
def import_bnf_ean(ean):
    """Import record from BNFr given a isbn 13 without dashes."""
    bnf_url = current_app.config['REROILS_APP_IMPORT_BNF_EAN']
    try:
        with urlopen(bnf_url % ean) as response:
            if response.status != 200:
                abort(500)
            # read the xml date from the HTTP response
            xml_data = response.read()

            # create a xml file in memory
            xml_file = six.BytesIO()
            xml_file.write(xml_data)
            xml_file.seek(0)

            # get the record in xml if exists
            # note: the request should returns one record max
            xml_record = next(split_stream(xml_file))

            # convert xml in marc json
            json_data = create_record(xml_record)

            # convert marc json to local json format
            record = unimarctojson.do(json_data)
            response = {
                'record': record,
                'type': 'success',
                'content': _('The record has been imported.'),
                'title': _('Success:')
            }
            return jsonify(response)
    # no record found!
    except StopIteration:
        response = {
                'record': {},
                'type': 'warning',
                'content': _('EAN (%(ean)s) not found on the BNF server.',
                             ean=ean),
                'title': _('Warning:')
            }
        return jsonify(response), 404
    # other errors
    except Exception as e:
        import sys
        print(e)
        sys.stdout.flush()
        response = {
                'record': {},
                'type': 'danger',
                'content': _('An error occured on the BNF server.'),
                'title': _('Error:')
            }
        return jsonify(response), 500
