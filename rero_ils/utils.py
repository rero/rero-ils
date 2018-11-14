# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Utilities functions for rero-ils."""

from flask import current_app, render_template
from flask_mail import Message
from flask_security.utils import config_value


def send_mail(subject, recipients, template, language, **context):
    """Send an email via the Flask-Mail extension.

    :param subject: Email subject
    :param recipients: List of email recipients
    :param template: The name of the email template
    :param context: The context to render the template with
    """
    sender = config_value('EMAIL_SENDER')
    msg = Message(subject,
                  sender=sender,
                  recipients=recipients)

    ctx = ('email', template, language)

    if config_value('EMAIL_PLAINTEXT'):
        msg.body = render_template('%s/%s_%s.txt' % ctx, **context)
    # if config_value('EMAIL_HTML'):
    #     msg.html = render_template('%s/%s.html' % ctx, **context)

    mail = current_app.extensions.get('mail')
    mail.send(msg)


def i18n_to_str(language):
    """Transform i18n languages to string."""
    i18n_languages = current_app.config['I18N_LANGUAGES']
    for i18n_language in i18n_languages:
        if language in i18n_language:
            return i18n_language[1]
    return 'English'


def resolve_function(function_name):
    """Execute resolve function."""
    result = []
    if function_name == 'libraries_pids_names':
        from rero_ils.modules.libraries_locations.api import Library
        for id in Library.get_all_ids():
            library = Library.get_record_by_id(id)
            result.append({
                'name': '{library}'.format(
                    library=library.get('name')
                ),
                'value': library.pid
            })
    if function_name == 'locations_pids_names':
        from rero_ils.modules.locations.api import Location
        from rero_ils.modules.libraries_locations.api import \
            LibraryWithLocations
        for id in Location.get_all_ids():
            location = Location.get_record_by_id(id)
            library = LibraryWithLocations.get_library_by_locationid(id)
            result.append({
                'name': '{library}: {location}'.format(
                    library=library.get('name'),
                    location=location.get('name')
                ),
                'value': location.pid
            })
    if function_name == 'item_types_names_descriptions':
        from rero_ils.modules.items_types.api import ItemType
        for id in ItemType.get_all_ids():
            item_type = ItemType.get_record_by_id(id)
            result.append({
                'name': item_type.get('name'),
                'value': item_type.get('pid')
            })
    if function_name == 'patron_names_descriptions':
        from rero_ils.modules.patrons_types.api import PatronType
        for id in PatronType.get_all_ids():
            patron_type = PatronType.get_record_by_id(id)
            result.append({
                'name': patron_type.get('name'),
                'value': patron_type.get('pid')
            })
    # sort the rsult
    result = sorted(result, key=lambda k: k['name'])
    return result


def resolve_relations(form_options):
    """Resolve relations."""
    resolved_form_options = []
    for form_option in form_options:
        form_option = resolve_relation(form_option)
        resolved_form_options.append(form_option)
    return resolved_form_options


def resolve_relation(form_option):
    """Resolve relation."""
    if 'items' in form_option:
        for item in form_option['items']:
            item = resolve_relation(item)
            # form_option['items'] = items
    elif 'populate' in form_option:
        populate = form_option['populate']
        form_option['titleMap'] = resolve_function(populate)
        del(form_option['populate'])
    return form_option
