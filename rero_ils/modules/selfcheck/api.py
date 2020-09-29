# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

"""Selfcheck API."""

from flask import current_app
from flask_babelex import gettext as _

from .utils import authorize_selfckeck_user, check_sip2_module, \
    format_patron_address, get_patron_status, map_item_circulation_status, \
    map_media_type
from ..documents.api import Document
from ..documents.utils import title_format_text_head
from ..items.api import Item
from ..items.models import ItemNoteTypes
from ..libraries.api import Library
from ..loans.api import Loan, LoanState, get_loans_by_item_pid_by_patron_pid, \
    get_loans_by_patron_pid, is_overdue_loan
from ..patron_transactions.api import PatronTransaction
from ..patrons.api import Patron
from ...filter import format_date_filter


def selfcheck_login(login, password):
    """Selfcheck login handler.

    Grant 'password' for selfcheck client.
    :param login: selfcheck client login.
    :param password: Password.
    :return: The login object or ``None``.
    """
    if authorize_selfckeck_user(login, password):
        staffer = Patron.get_patron_by_email(login)
        return {
            'authenticated': staffer.is_librarian,
            'user_id': staffer.get('pid'),
            'institution_id': staffer.get_organisation().get('code'),
            'library_name': Library.get_record_by_pid(
                staffer.library_pid).get('name')
        }


def validate_patron_account(barcode=None):
    """Validate patron account handler.

    Validate patron 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: ``True`` if patron exists or ``False``.
    """
    patron = Patron.get_patron_by_barcode(barcode)
    return patron and patron.is_patron


def authorize_patron(barcode, password):
    """Authorize patron handler.

    Grant `password` according patron 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: ``True`` if patron is authorized or ``False``.
    """
    patron = Patron.get_patron_by_barcode(barcode)
    if patron and patron.is_patron:
        return authorize_selfckeck_user(patron.get('email'), password)
    return False


def system_status(login, *kwargs):
    """Selfcheck system status handler.

    Get status of automated circulation system.
    :param login: selfcheck client login.
    :return: The status object.
    """
    staffer = Patron.get_patron_by_email(login)
    return {
        'institution_id': staffer.get_organisation().get('code')
    }


def enable_patron(barcode, **kwargs):
    """Selfcheck enable patron handler.

    Enable patron 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: ``True`` if patron exists or ``None``.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        patron = Patron.get_patron_by_barcode(barcode)
        return {
            'patron_status': get_patron_status(patron),
            'language': patron.get('communication_language', 'und'),
            'institution_id': patron.get_organisation().get('code'),
            'patron_id': patron.patron.get('barcode'),
            'patron_name': patron.formatted_name
        }


def patron_information(barcode, **kwargs):
    """Get patron information handler.

    Get patron information according 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: The SelfcheckPatronInformation object.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckPatronInformation

        patron = Patron.get_patron_by_barcode(barcode)

        # TODO: add PatronStatusType according account
        #  e.g.:
        #   patron_status.add_patron_status_type(
        #   SelfcheckPatronStatusTypes.CARD_REPORTED_LOST)
        patron_account_information = SelfcheckPatronInformation(
            patron_id=barcode,
            patron_name=patron.formatted_name,
            email=patron.get('email'),
            home_phone=patron.get('phone'),
            home_address=format_patron_address(patron),
            institution_id=patron.get_organisation().get('code'),
            language=patron.get('communication_language', 'und'),
            currency_type=patron.get_organisation().get('default_currency'),
            valid_patron=patron.is_patron
        )

        filter_states = [
            LoanState.PENDING,
            LoanState.ITEM_AT_DESK,
            LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
            LoanState.ITEM_ON_LOAN
        ]
        loans = get_loans_by_patron_pid(patron.pid, filter_states)
        for loan in loans:
            item = Item.get_record_by_pid(loan.item_pid)
            if loan['state'] == LoanState.ITEM_ON_LOAN:
                patron_account_information.get('charged_items').append(
                    item.get('pid'))
                if is_overdue_loan(loan):
                    patron_account_information.get('overdue_items')\
                        .append(item.get('pid'))
            elif loan['state'] in [
                LoanState.PENDING,
                LoanState.ITEM_AT_DESK,
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
            ]:
                patron_account_information.get('hold_items').append(
                    item.get('pid')
                )

        fee_amount = PatronTransaction \
            .get_transactions_total_amount_for_patron(
                patron.pid, status='open',
                with_subscription=False)
        patron_account_information['fee_amount'] = fee_amount
        # check for fine items
        if fee_amount > 0:
            # Check if fine items exist
            transaction_pids = PatronTransaction\
                .get_transactions_pids_for_patron(
                    patron.pid, status='open')
            for transaction_pid in transaction_pids:
                # TODO: return screen message to notify patron if there are
                #  other open transactions
                transaction = PatronTransaction\
                    .get_record_by_pid(transaction_pid)
                if transaction.loan_pid:
                    loan = Loan.get_record_by_pid(transaction.loan_pid)
                    item = Item.get_record_by_pid(loan.item_pid)
                    patron_account_information.get('fine_items', []).append(
                        item.get('pid')
                    )
        return patron_account_information


def item_information(patron_barcode, item_pid, **kwargs):
    """Get item information handler.

    get item information according 'item_identifier' from selfcheck user.
    :param barcode: barcode of the patron.
    :param item_pid: item identifier.
    :return: The SelfcheckItemInformation object.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckFeeType, \
            SelfcheckItemInformation, SelfcheckSecurityMarkerType
        patron = Patron.get_patron_by_barcode(patron_barcode)
        item = Item.get_record_by_pid(item_pid)
        document = Document.get_record_by_pid(item.document_pid)
        location = item.get_location()
        language = kwargs.get('language', current_app.config
                              .get('BABEL_DEFAULT_LANGUAGE'))
        with current_app.test_request_context() as ctx:
            ctx.babel_locale = language
            item_information = SelfcheckItemInformation(
                item_id=item.get('barcode'),
                title_id=title_format_text_head(document.get('title')),
                circulation_status=map_item_circulation_status(item.status),
                fee_type=SelfcheckFeeType.OTHER,
                security_marker=SelfcheckSecurityMarkerType.OTHER
            )
            item_information['media_type'] = map_media_type(
                document.get('type')
            )
            item_information['hold_queue_length'] = item.number_of_requests()
            item_information['owner'] = location.get_library().get('name')
            item_information['permanent_location'] = location.get('name')
            item_information['current_location'] = \
                item.get_last_location().get('name')
            # get loan for item
            filter_states = [
                LoanState.PENDING,
                LoanState.ITEM_ON_LOAN
            ]
            loan = get_loans_by_item_pid_by_patron_pid(item_pid, patron.pid,
                                                       filter_states)
            if loan:
                if loan['state'] == LoanState.ITEM_ON_LOAN:
                    # format the end date according selfcheck language
                    item_information['due_date'] = format_date_filter(
                        loan['end_date'],
                        date_format='short',
                        time_format=None,
                        locale=language,
                    )

                    transaction = PatronTransaction.\
                        get_last_transaction_by_loan_pid(
                            loan_pid=loan.pid,
                            status='open')
                    if transaction:
                        # TODO: map transaction type
                        item_information['fee_type'] = SelfcheckFeeType.OVERDUE
                        item_information['fee_amount'] = \
                            transaction.total_amount
                        item_information['currency_type'] = \
                            transaction.currency
                        item_information.get('screen_messages').append(
                            _('overdue'))
                elif loan['state'] == LoanState.PENDING:
                    item_information['fee_type'] = SelfcheckFeeType.OTHER
            # public note
            public_note = item.get_note(ItemNoteTypes.PUBLIC)
            if public_note:
                item_information.get('screen_messages').append(public_note)

            return item_information
