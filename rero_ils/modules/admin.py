# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Admin views and actions."""


from json import loads

from flask import abort, current_app, flash, jsonify, redirect, \
    render_template, request, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from invenio_admin.permissions import \
    admin_permission_factory as default_admin_permission_factory
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_rest.utils import obj_or_import_string
from pkg_resources import resource_string

from ..permissions import can_edit
from ..utils import resolve_relations
from .babel_extractors import translate
from .utils import delete_record, get_schema, get_schema_url, remove_pid, \
    save_record


class ResourceView(BaseView):
    """Resource Admin View."""

    @property
    def can_create(self):
        """Is model creation allowed."""
        app_config = current_app.config
        cfg = app_config.get('RERO_ILS_RESOURCES_ADMIN_OPTIONS')
        cfg = cfg.get(self.endpoint)
        return cfg.get('can_create', lambda: True)()

    @property
    def can_edit(self):
        """Is model creation allowed."""
        return True

    @property
    def can_delete(self):
        """Is model creation allowed."""
        return True

    def is_accessible(self):
        """Access control."""
        return (can_edit() or default_admin_permission_factory(self).can())

    def is_visible(self):
        """Dynamically hide or show administrative views."""
        app_config = current_app.config
        cfg = app_config.get('RERO_ILS_RESOURCES_ADMIN_OPTIONS')
        cfg = cfg.get(self.endpoint)
        if not cfg.get('api'):
            return False
        return True

    @expose('/')
    def index_view(self):
        """Search list view."""
        app_config = current_app.config
        cfg = app_config.get('RERO_ILS_RESOURCES_ADMIN_OPTIONS')
        cfg = cfg.get(self.endpoint)
        if not cfg or not cfg.get('api'):
            abort(404)
        api = cfg.get('api')
        search_template = cfg.get(
            'results_template',
            app_config.get('SEARCH_UI_JSTEMPLATE_RESULTS')
        )
        search_index = app_config.get('RECORDS_REST_ENDPOINTS', {}) \
            .get(self.endpoint, {}) \
            .get('search_index', app_config.get('SEARCH_UI_SEARCH_INDEX'))
        return render_template(
            'rero_ils/search.html', search_api=api,
            search_results_template=search_template,
            search_index=search_index,
            record_type=self.endpoint
        )

    @expose('/new', methods=('GET', 'POST'))
    def create_view(self):
        """Create model view."""
        parent_pid = request.args.get('parent_pid')
        app_config = current_app.config
        cfg = app_config.get('RERO_ILS_RESOURCES_ADMIN_OPTIONS')
        cfg = cfg.get(self.endpoint)
        default_template = app_config[
            'RERO_ILS_EDITOR_TEMPLATE'
        ]
        template = cfg.get('editor_template', default_template)
        schema = cfg.get('schema')
        if not cfg or not schema:
            abort(404)

        form_options = cfg.get('form_options')
        schema_url = get_schema_url(schema)

        if form_options:
            options_in_bytes = resource_string(*form_options)
            form_options = loads(options_in_bytes.decode('utf8'))

            for key_to_remove in cfg.get('form_options_create_exclude', []):
                remove_pid(form_options, key_to_remove)

            form_options = resolve_relations(form_options)

            keys = current_app.config['RERO_ILS_BABEL_TRANSLATE_JSON_KEYS']
            form_options = translate(form_options, keys=keys)

        return render_template(
            template,
            form=form_options or ['*'],
            model={'$schema': schema_url},
            schema=get_schema(schema),
            api_save_url=url_for('%s.ajax_update' % self.endpoint),
            record_type=self.endpoint,
            parent_pid=parent_pid
        )

    @expose('/edit/<pid>', methods=('GET', 'POST'))
    def edit_view(self, pid):
        """Edit model view."""
        app_config = current_app.config
        cfg = app_config.get('RERO_ILS_RESOURCES_ADMIN_OPTIONS')
        cfg = cfg.get(self.endpoint)
        record_type = self.endpoint
        record_class = cfg.get('record_class')
        if not record_class:
            flash(
                _('Record class configuration does not exists for %s.' %
                  record_type),
                'danger')
            abort(500)
        default_template = current_app.config[
            'RERO_ILS_EDITOR_TEMPLATE'
        ]
        template = cfg.get('editor_template', default_template)
        schema = cfg.get('schema')
        if not cfg or not schema:
            abort(404)

        form_options = cfg.get('form_options')

        if form_options:
            options_in_bytes = resource_string(*form_options)
            form_options = loads(options_in_bytes.decode('utf8'))

            form_options = resolve_relations(form_options)

            keys = current_app.config['RERO_ILS_BABEL_TRANSLATE_JSON_KEYS']
            form_options = translate(form_options, keys=keys)

        try:
            rec = record_class.get_record_by_pid(pid)
        except PIDDoesNotExistError:
            flash(_('The record %s does not exists.' % pid), 'danger')
            abort(404)

        return render_template(
            template,
            form=form_options or ['*'],
            model=rec,
            schema=get_schema(schema),
            api_save_url=url_for('%s.ajax_update' % self.endpoint),
            record_type=record_type
        )

    @expose('/delete/<pid>', methods=('POST', 'GET'))
    def delete_view(self, pid):
        """Delete model view."""
        app_config = current_app.config
        cfg = app_config.get('RERO_ILS_RESOURCES_ADMIN_OPTIONS')
        cfg = cfg.get(self.endpoint)
        record_type = self.endpoint
        record_class = cfg.get('record_class')

        if not record_class:
            flash(
                _('Record class configuration does not exists for %s.' %
                  record_type),
                'danger')
            abort(500)
        _delete_record = obj_or_import_string(cfg.get('delete_record')) \
            or delete_record
        try:
            _next, pid = _delete_record(record_type, record_class, pid)
        except PIDDoesNotExistError:
            flash(
                _('The record %s does not exists.' % pid),
                'danger')
            abort(404)
        except Exception as e:
            raise(e)
            flash(_('An error occured on the server.'), 'danger')
            abort(500)

        flash(_('The record %s has been deleted.' % pid), 'success')

        return redirect(_next)

    @expose('/ajax/update/', methods=('POST',))
    def ajax_update(self):
        """Create or update api service."""
        app_config = current_app.config
        cfg = app_config.get('RERO_ILS_RESOURCES_ADMIN_OPTIONS')
        cfg = cfg.get(self.endpoint)
        record_type = self.endpoint
        record_class = cfg.get('record_class')
        parent_pid = request.args.get('parent_pid')
        if not record_class:
            flash(
                _('Record class configuration does not exists for %s.' %
                  record_type),
                'danger')
            abort(500)

        _save_record = obj_or_import_string(
            cfg.get('save_record', save_record))
        try:
            _next, pid = _save_record(
                request.get_json(), record_type, record_class, parent_pid)
            message = {
                'pid': pid,
                'next': _next
            }

            flash(
                _('The record has been saved (%s, pid: %s).'
                  % (_(record_type), pid)), 'success')
            return jsonify(message)
        except PIDDoesNotExistError:
            msg = _('Cannot retrieve the record (%s).' % record_type)
            response = {
                'content': msg
            }
            return jsonify(response), 404

        except Exception as e:
            raise(e)
            msg = _('An error occured on the server.')
            response = {
                'content': msg
            }
            return jsonify(response), 500


class ILSManager(BaseView):
    """Flask-Admin Ils view."""

    @expose('/')
    @expose('/<path:path>')
    def index(self, path=None):
        """Angular Circulation view."""
        return self.render('rero_ils/admin/page.html')

    def is_accessible(self):
        """Access control."""
        return (can_edit() or default_admin_permission_factory(self).can())


class LibraryManager(BaseView):
    """Flask-Admin Library view."""

    @expose('/')
    @expose('/<path:path>')
    def index(self, path=None):
        """Index."""
        return self.render('rero_ils/admin/page.html')

    def is_visible(self):
        """Visible control."""
        return False

    def is_accessible(self):
        """Access control."""
        return (can_edit() or default_admin_permission_factory(self).can())


circulation_settings = {
    'view_class': ILSManager,
    'kwargs': dict(name='Circulation Settings',
                   endpoint='circulation_settings',
                   menu_icon_type='fa',
                   menu_icon_value='fa-barcode')
}

my_library = {
    'view_class': ILSManager,
    'kwargs': dict(
        name='My Library',
        endpoint='mylibrary',
        menu_icon_type='fa',
        menu_icon_value='fa-university'
    )
}

library = {
    'view_class': LibraryManager,
    'kwargs': dict(
        name='Libraries',
        endpoint='libraries',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}
