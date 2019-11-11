# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Utilities functions for rero-ils."""

from elasticsearch.exceptions import NotFoundError
from flask import render_template
from flask_mail import Message
from flask_security.utils import config_value
from invenio_mail.tasks import send_email as _send_mail
from invenio_records_rest.errors import PIDDoesNotExistRESTError, \
    PIDMissingObjectRESTError
from invenio_records_rest.utils import LazyPIDValue, PathConverter, \
    PIDConverter, obj_or_import_string
from werkzeug.routing import BaseConverter
from werkzeug.utils import cached_property

from .modules.api import ElasticsearchRecord
from .resolver import ElasticsearchResolver


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

    if config_value('EMAIL_PLAINTEXT'):
        msg.body = render_template(
            'email/{template}_{language}.txt'.format(
                template=template,
                language=language
            ),
            **context
        )
        # msg.html = render_template(
        #     'email/{template}_{language}.html'.format(
        #         template=template,
        #         language=language
        #     ),
        #     **context
        # )

    _send_mail.delay(msg.__dict__)


def unique_list(data):
    """Unicity of list."""
    return list(dict.fromkeys(data))


def get_agg_config(index_name, field):
    """Get Elasticsearch aggregation term configuration.

    This function allows to configure aggregation size per index name using
    environnement variables.

    :param index_name: name of Elasticsearch index
    :param field: field name for the aggregation
    :return: dict of Elasticsearch DSL aggregation configuration
    """
    from flask import current_app
    return dict(terms=dict(
        field=field,
        size=current_app.config.get(
            'RERO_ILS_AGGREGATION_SIZE', {}
        ).get(
            index_name,
            current_app.config.get('RERO_ILS_DEFAULT_AGGREGATION_SIZE')
        )
    ))


class LazyESPIDValue(object):
    """Lazy ESPID resolver.

    The ESPID will not be resolved until the `data` property is accessed.
    """

    def __init__(self, resolver, value):
        """Initialize with resolver object and the PID value.

        :params resolver: Resolves for PID,
                          see :class:`rero-ils.resolver.ElasticsearchResolver`.
        :params value: PID value.
        :type value: str
        """
        self.resolver = resolver
        self.value = value

    @cached_property
    def data(self):
        """Resolve PID from a value and return a tuple with PID and the record.

        :returns: A tuple with the PID and the record resolved.
        """
        try:
            return self.resolver.resolve(self.value)
        except NotFoundError as pid_error:
            raise PIDDoesNotExistRESTError(pid_error=pid_error)


class ElasticsearchPIDConverter(BaseConverter):
    """Converter for elasticsearch PID values.

    This class is a custom routing converter defining the 'ESPID' type.
    """

    def __init__(self, url_map, pid_type, getter=None, record_class=None):
        """Initialize the converter."""
        super(ElasticsearchPIDConverter, self).__init__(url_map)

        getter = obj_or_import_string(
                record_class,
                default=ElasticsearchRecord).get_record_by_pid
        self.resolver = ElasticsearchResolver(
            pid_type=pid_type,
            object_type='rec',
            getter=getter)

    def to_python(self, value):
        """Resolve PID value."""
        return LazyESPIDValue(self.resolver, value)
