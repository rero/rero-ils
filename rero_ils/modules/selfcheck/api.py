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
from invenio_circulation.errors import ItemNotAvailableError

from .models import SelfcheckTerminal
from .utils import authorize_selfckeck_patron, authorize_selfckeck_terminal, \
    check_sip2_module, format_patron_address, get_patron_status, \
    map_item_circulation_status, map_media_type
from ..documents.api import Document
from ..documents.utils import title_format_text_head
from ..items.api import Item
from ..items.models import ItemNoteTypes
from ..libraries.api import Library
from ..loans.api import Loan, LoanAction, LoanState, \
    get_loans_by_item_pid_by_patron_pid, get_loans_by_patron_pid
from ..patron_transactions.api import PatronTransaction
from ..patrons.api import Patron
from ...filter import format_date_filter


def selfcheck_login(name, access_token, **kwargs):
    """Selfcheck login handler.

    Grant access for selfcheck terminal.
    :param name: selfcheck terminal name.
    :param access_token: access token.
    :return: The login object or ``None``.
    """
    terminal = SelfcheckTerminal.find_terminal(name=name)
    user = authorize_selfckeck_terminal(terminal, access_token, **kwargs)
    if terminal and user:
        staffer = Patron.get_librarian_by_user(user)
        if staffer:
            return {
                'authenticated': terminal.active,
                'terminal': terminal.name,
                'transaction_user_id': staffer.pid,
                'institution_id': terminal.organisation_pid,
                'library_name': Library.get_record_by_pid(
                    terminal.library_pid).get('name')
            }


def validate_patron_account(barcode=None, **kwargs):
    """Validate patron account handler.

    Validate patron 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: ``True`` if patron exists or ``False``.
    """
    patron = Patron.get_patron_by_barcode(
        barcode, filter_by_org_pid=kwargs.get('institution_id'))
    return patron and patron.is_patron


def authorize_patron(barcode, password, **kwargs):
    """Authorize patron handler.

    Grant `password` according patron 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :param password: patron password.
    :return: ``True`` if patron is authorized or ``False``.
    """
    patron = Patron.get_patron_by_barcode(
        barcode, filter_by_org_pid=kwargs.get('institution_id'))
    if patron and patron.is_patron:
        return authorize_selfckeck_patron(patron.user.email, password)
    return False


def system_status(terminal, **kwargs):
    """Selfcheck system status handler.

    Get status of automated circulation system.
    :param terminal: selfcheck terminal.
    :return: The status object.
    """
    terminal = SelfcheckTerminal().find_terminal(name=terminal)
    return {
        'authenticated': terminal.active,
        'terminal': terminal.name,
        'institution_id': terminal.library_pid
    }


def enable_patron(barcode, **kwargs):
    """Selfcheck enable patron handler.

    Enable patron 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: ``True`` if patron exists or ``None``.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        patron = Patron.get_patron_by_barcode(
            barcode, filter_by_org_pid=kwargs.get('institution_id'))
        return {
            'patron_status': get_patron_status(patron),
            'language': patron.get('communication_language', 'und'),
            'institution_id': patron.library_pid,
            'patron_id': patron.patron.get('barcode'),
            'patron_name': patron.formatted_name
        }


def patron_status(barcode, **kwargs):
    """Selfcheck patron status handler.

    Get patron status according 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: The SelfcheckPatronInformation object.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckPatronStatus

        patron = Patron.get_patron_by_barcode(
            barcode, filter_by_org_pid=kwargs.get('institution_id'))
        patron_status_response = SelfcheckPatronStatus(
            patron_status=get_patron_status(patron),
            language=patron.get('communication_language', 'und'),
            patron_id=barcode,
            patron_name=patron.formatted_name,
            institution_id=patron.library_pid,
            currency_type=patron.get_organisation().get('default_currency'),
            valid_patron=patron.is_patron
        )

        fee_amount = PatronTransaction \
            .get_transactions_total_amount_for_patron(
                patron.pid, status='open',
                with_subscription=False)
        patron_status_response['fee_amount'] = fee_amount
        return patron_status_response


def patron_information(barcode, **kwargs):
    """Get patron information handler.

    Get patron information according 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: The SelfcheckPatronInformation object.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckPatronInformation

        patron = Patron.get_patron_by_barcode(
            barcode, filter_by_org_pid=kwargs.get('institution_id'))
        patron_account_information = SelfcheckPatronInformation(
            patron_id=barcode,
            patron_name=patron.formatted_name,
            patron_status=get_patron_status(patron),
            institution_id=patron.library_pid,
            language=patron.get('communication_language', 'und'),
            email=patron.get('email'),
            home_phone=patron.get('phone'),
            home_address=format_patron_address(patron),
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
                patron_account_information.get('charged_items', []).append(
                    item.get('pid'))
                if loan.is_loan_overdue():
                    patron_account_information.get('overdue_items', [])\
                        .append(item.get('pid'))
            elif loan['state'] in [
                LoanState.PENDING,
                LoanState.ITEM_AT_DESK,
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
            ]:
                patron_account_information.get('hold_items', []).append(
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
    :param patron_barcode: barcode of the patron.
    :param item_pid: item identifier.
    :return: The SelfcheckItemInformation object.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckFeeType, \
            SelfcheckItemInformation, SelfcheckSecurityMarkerType
        patron = Patron.get_patron_by_barcode(
            patron_barcode,
            filter_by_org_pid=kwargs.get('institution_id'))
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
                document['type'][0]['main_type']
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
                        item_information.get('screen_messages', []).append(
                            _('overdue'))
                elif loan['state'] == LoanState.PENDING:
                    item_information['fee_type'] = SelfcheckFeeType.OTHER
            # public note
            public_note = item.get_note(ItemNoteTypes.PUBLIC)
            if public_note:
                item_information.get('screen_messages', []).append(public_note)

            return item_information


def selfcheck_checkout(transaction_user_pid, library_pid, patron_barcode,
                       item_barcode, **kwargs):
    """SIP2 Handler to perform checkout.

    perform checkout action received from the selfcheck.
    :param transaction_user_pid: identifier of the staff user.
    :param library_pid: library pid of the selfcheck_terminal.
    :param patron_barcode: barcode of the patron.
    :param item_barcode: item identifier.
    :return: The SelfcheckCheckout object.
    """
    if check_sip2_module():
        from invenio_sip2.errors import SelfcheckCirculationError
        from invenio_sip2.models import SelfcheckCheckout

        terminal = SelfcheckTerminal.find_terminal(
            name=kwargs.get('terminal'))
        item = Item.get_item_by_barcode(
            barcode=item_barcode,
            organisation_pid=terminal.organisation_pid
        )
        document = Document.get_record_by_pid(item.document_pid)
        checkout = SelfcheckCheckout(
            title_id=title_format_text_head(document.get('title')),
        )
        try:
            staffer = Patron.get_record_by_pid(transaction_user_pid)
            if staffer.is_librarian:
                patron = Patron.get_patron_by_barcode(
                    patron_barcode,
                    filter_by_org_pid=kwargs.get('institution_id'))
                with current_app.test_request_context() as ctx:
                    language = kwargs.get('language', current_app.config
                                          .get('BABEL_DEFAULT_LANGUAGE'))
                    ctx.babel_locale = language
                    # TODO: check if item is already checked out
                    #  (see sip2 renewal_ok)
                    # do checkout
                    result, data = item.checkout(
                        patron_pid=patron.pid,
                        transaction_user_pid=staffer.pid,
                        transaction_library_pid=library_pid,
                        item_pid=item.pid,
                        selfcheck_terminal_id=str(terminal.id),
                    )
                    loan_pid = data[LoanAction.CHECKOUT].get('pid')
                    loan = Loan.get_record_by_pid(loan_pid)
                    if loan:
                        checkout['checkout'] = True
                        checkout['due_date'] = loan.get_loan_end_date(
                            time_format=None, language=language)
                        # checkout note
                        checkout_note = item.get_note(ItemNoteTypes.CHECKOUT)
                        if checkout_note:
                            checkout.get('screen_messages', [])\
                                .append(checkout_note)
                        # TODO: When is possible, try to return fields:
                        #       magnetic_media, desensitize
        except ItemNotAvailableError:
            checkout.get('screen_messages', []).append(
                _('Checkout impossible: the item is requested by '
                  'another patron'))
        except Exception:
            checkout.get('screen_messages', []).append(
                _('Error encountered: please contact a librarian'))
            raise SelfcheckCirculationError('self checkout failed', checkout)
        return checkout


def selfcheck_checkin(transaction_user_pid, library_pid, patron_barcode,
                      item_barcode, **kwargs):
    """SIP2 Handler to perform checkin.

    perform checkin action received from the selfcheck.
    :param transaction_user_pid: identifier of the staff user.
    :param library_pid: library pid of the selfcheck terminal.
    :param patron_barcode: barcode of the patron.
    :param item_barcode: item identifier.
    :return: The SelfcheckCheckin object.
    """
    if check_sip2_module():
        from invenio_sip2.errors import SelfcheckCirculationError
        from invenio_sip2.models import SelfcheckCheckin
        library = Library.get_record_by_pid(library_pid)
        item = Item.get_item_by_barcode(
            barcode=item_barcode,
            organisation_pid=library.organisation_pid
        )
        checkin = SelfcheckCheckin(
            permanent_location=library.get('name')
        )
        try:
            document = Document.get_record_by_pid(item.document_pid)
            checkin['title_id'] = title_format_text_head(
                document.get('title')
            )
            staffer = Patron.get_record_by_pid(transaction_user_pid)
            if staffer.is_librarian:
                with current_app.test_request_context() as ctx:
                    language = kwargs.get('language', current_app.config
                                          .get('BABEL_DEFAULT_LANGUAGE'))
                    ctx.babel_locale = language

                    # do checkin
                    result, data = item.checkin(
                        transaction_user_pid=staffer.pid,
                        transaction_library_pid=library_pid,
                        item_pid=item.pid,
                    )
                    if data[LoanAction.CHECKIN]:
                        checkin['checkin'] = True
                        # checkin note
                        checkin_note = item.get_note(ItemNoteTypes.CHECKIN)
                        if checkin_note:
                            checkin.get('screen_messages', [])\
                                .append(checkin_note)
                        # TODO: When is possible, try to return fields:
                        #       magnetic_media, resensitize
        except Exception:
            checkin.get('screen_messages', []).append(
                _('Error encountered: please contact a librarian'))
            raise SelfcheckCirculationError('self checkin failed', checkin)
        return checkin
