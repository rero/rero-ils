# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
# Copyright (C) 2019-2024 UCLouvain
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

from datetime import datetime, timezone

from flask import current_app
from flask_babel import force_locale
from flask_babel import gettext as _
from invenio_circulation.errors import CirculationException, \
    ItemNotAvailableError

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.extensions import TitleExtension
from rero_ils.modules.errors import ItemBarcodeNotFound, NoCirculationAction, \
    PatronBarcodeNotFound
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemNoteTypes
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan, \
    get_loans_by_item_pid_by_patron_pid, get_loans_by_patron_pid
from rero_ils.modules.loans.models import LoanAction, LoanState
from rero_ils.modules.patron_transactions.api import PatronTransaction
from rero_ils.modules.patron_transactions.utils import \
    get_last_transaction_by_loan_pid, get_transactions_pids_for_patron, \
    get_transactions_total_amount_for_patron
from rero_ils.modules.patrons.api import Patron

from .models import SelfcheckTerminal
from .utils import authorize_selfckeck_terminal, authorize_selfckeck_user, \
    check_sip2_module, format_patron_address, get_patron_status, \
    map_item_circulation_status, map_media_type


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
            library = Library.get_record_by_pid(terminal.library_pid)
            return {
                'authenticated': terminal.active,
                'terminal': terminal.name,
                'transaction_user_id': staffer.pid,
                'institution_id': terminal.organisation_pid,
                'library_name': library.get('name'),
                'library_language': library.get('communication_language')
            }


def validate_patron_account(barcode=None, **kwargs):
    """Validate patron account handler.

    Validate patron 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: ``True`` if patron exists or ``False``.
    """
    patron = Patron.get_patron_by_barcode(
        barcode=barcode, org_pid=kwargs.get('institution_id'))
    return patron and patron.is_patron


def authorize_patron(barcode, password, **kwargs):
    """Authorize patron handler.

    Grant `password` according patron 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :param password: patron password.
    :return: ``True`` if patron is authorized or ``False``.
    """
    patron = Patron.get_patron_by_barcode(
        barcode=barcode, org_pid=kwargs.get('institution_id'))
    if patron and patron.is_patron:
        # User email is an optional field. When User hasn't email address,
        # we take his username as login.
        user_login = patron.user.email or patron.user.username
        return authorize_selfckeck_user(user_login, password)
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
        from invenio_sip2.models import SelfcheckEnablePatron
        institution_id = kwargs.get('institution_id')
        patron = Patron.get_patron_by_barcode(
            barcode=barcode, org_pid=institution_id)
        if patron:
            return SelfcheckEnablePatron(
                patron_status=get_patron_status(patron),
                language=patron.patron.get('communication_language', 'und'),
                institution_id=patron.organisation_pid,
                patron_id=patron.patron.get('barcode'),
                patron_name=patron.formatted_name
            )
        else:
            return SelfcheckEnablePatron(
                patron_id=barcode,
                institution_id=institution_id,
                screen_messages=[_('Error encountered: patron not found')]
            )


def patron_status(barcode, **kwargs):
    """Selfcheck patron status handler.

    Get patron status according 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: The SelfcheckPatronInformation object.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckPatronStatus
        institution_id = kwargs.get('institution_id')
        language = kwargs.get('language', current_app.config
                              .get('BABEL_DEFAULT_LANGUAGE'))
        # Temporarily overrides the currently selected locale.
        # force_locale is allowed to work outside of application context
        with force_locale(language):
            patron = Patron.get_patron_by_barcode(
                barcode=barcode, org_pid=institution_id)
            if patron:
                patron_status_response = SelfcheckPatronStatus(
                    patron_status=get_patron_status(patron),
                    language=patron.get('communication_language', 'und'),
                    patron_id=barcode,
                    patron_name=patron.formatted_name,
                    institution_id=patron.organisation_pid,
                    currency_type=patron.organisation.get('default_currency'),
                    valid_patron=patron.is_patron
                )

                fee_amount = get_transactions_total_amount_for_patron(
                        patron.pid, status='open', with_subscription=False)
                patron_status_response['fee_amount'] = '%.2f' % fee_amount
                return patron_status_response
            else:
                return SelfcheckPatronStatus(
                    patron_id=barcode,
                    institution_id=institution_id,
                    screen_messages=[_('Error encountered: patron not found')]
                )


def patron_information(barcode, **kwargs):
    """Get patron information handler.

    Get patron information according 'barcode' from selfcheck user.
    :param barcode: patron barcode.
    :return: The SelfcheckPatronInformation object.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckPatronInformation
        institution_id = kwargs.get('institution_id')
        language = kwargs.get('language', current_app.config
                              .get('BABEL_DEFAULT_LANGUAGE'))
        # Temporarily overrides the currently selected locale.
        # force_locale is allowed to work outside of application context
        with force_locale(language):
            patron = Patron.get_patron_by_barcode(
                barcode=barcode, org_pid=institution_id)
            if patron:
                patron_dumps = patron.dumps()
                patron_account_information = SelfcheckPatronInformation(
                    patron_id=barcode,
                    patron_name=patron.formatted_name,
                    patron_status=get_patron_status(patron),
                    institution_id=patron.organisation_pid,
                    language=patron.get(
                        'patron', {}).get('communication_language', 'und'),
                    email=patron.get('patron', {}).get(
                            'additional_communication_email',
                            patron_dumps.get('email')),
                    home_phone=patron_dumps.get('home_phone'),
                    home_address=format_patron_address(patron),
                    currency_type=patron.organisation.get('default_currency'),
                    valid_patron=patron.is_patron
                )

                filter_states = [
                    LoanState.PENDING,
                    LoanState.ITEM_AT_DESK,
                    LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
                    LoanState.ITEM_ON_LOAN
                ]
                sip2_summary_fields = current_app.config \
                    .get('SIP2_SUMMARY_FIELDS')
                for loan in get_loans_by_patron_pid(patron.pid, filter_states):
                    item = Item.get_record_by_pid(loan.item_pid)
                    if field := sip2_summary_fields.get(loan['state']):
                        patron_account_information.setdefault(field, []) \
                            .append(item.get('barcode'))
                    if loan['state'] == LoanState.ITEM_ON_LOAN \
                            and loan.is_loan_overdue():
                        patron_account_information\
                            .setdefault('overdue_items', [])\
                            .append(item.get('barcode'))

                fee_amount = get_transactions_total_amount_for_patron(
                        patron.pid, status='open', with_subscription=False)
                patron_account_information['fee_amount'] = '%.2f' % fee_amount
                # check for fine items
                if fee_amount > 0:
                    # Check if fine items exist
                    transaction_pids = get_transactions_pids_for_patron(
                            patron.pid, status='open')
                    for transaction_pid in transaction_pids:
                        # TODO: return screen message to notify patron if there
                        #  are other open transactions
                        transaction = PatronTransaction \
                            .get_record_by_pid(transaction_pid)
                        if transaction.loan_pid:
                            loan = Loan.get_record_by_pid(transaction.loan_pid)
                            item = Item.get_record_by_pid(loan.item_pid)
                            patron_account_information\
                                .setdefault('fine_items', []) \
                                .append(item.get('barcode'))
                return patron_account_information
            else:
                return SelfcheckPatronInformation(
                    patron_id=barcode,
                    institution_id=institution_id,
                    screen_messages=[_('Error encountered: patron not found')]
                )


def item_information(item_barcode, **kwargs):
    """Get item information handler.

    get item information according 'item_identifier' from selfcheck user.
    :param patron_barcode: barcode of the patron.
    :param item_barcode: item identifier.
    :return: The SelfcheckItemInformation object.
    """
    # check if invenio_sip2 module is present
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckFeeType, \
            SelfcheckItemInformation, SelfcheckSecurityMarkerType
        org_pid = kwargs.get('institution_id')
        item = Item.get_item_by_barcode(item_barcode, org_pid)
        language = kwargs.get('language', current_app.config
                              .get('BABEL_DEFAULT_LANGUAGE'))
        # Temporarily overrides the currently selected locale.
        # force_locale is allowed to work outside of application context
        with force_locale(language):
            if item:
                document = Document.get_record_by_pid(item.document_pid)
                location = item.get_location()

                item_information = SelfcheckItemInformation(
                    item_id=item.get('barcode'),
                    title_id=TitleExtension.format_text(document.get('title')),
                    circulation_status=map_item_circulation_status(
                        item.status),
                    fee_type=SelfcheckFeeType.OTHER,
                    security_marker=SelfcheckSecurityMarkerType.OTHER
                )
                item_information['media_type'] = map_media_type(
                    document['type'][0]['main_type']
                )
                item_information['hold_queue_length'] = \
                    item.number_of_requests()
                item_information['owner'] = location.get_library().get('name')
                item_information['permanent_location'] = location.get('name')
                item_information['current_location'] = \
                    item.get_last_location().get('name')
                item_information['fee_type'] = SelfcheckFeeType.OVERDUE
                # get loan for item
                loan_pid = Item.get_loan_pid_with_item_on_loan(item.pid)
                if loan_pid:
                    loan = Loan.get_record_by_pid(loan_pid)
                    if loan:
                        # format the end date according selfcheck language
                        item_information['due_date'] = loan['end_date']
                        transaction = get_last_transaction_by_loan_pid(
                                loan_pid=loan.pid, status='open')
                        if transaction:
                            item_information['fee_amount'] = \
                                '%.2f' % transaction.total_amount
                            item_information['currency_type'] = \
                                transaction.currency
                            item_information.get('screen_messages', []) \
                                .append(_('overdue'))
                # public note
                public_note = item.get_note(ItemNoteTypes.PUBLIC)
                if public_note:
                    item_information.get('screen_messages', []) \
                        .append(public_note)

                return item_information
            else:
                return SelfcheckItemInformation(
                    item_id=item_barcode,
                    screen_messages=[_('Error encountered: item not found')]
                )


def selfcheck_checkout(transaction_user_pid, item_barcode, patron_barcode,
                       **kwargs):
    """SIP2 Handler to perform checkout.

    perform checkout action received from the selfcheck.
    :param transaction_user_pid: identifier of the staff user.
    :param patron_barcode: barcode of the patron.
    :param item_barcode: item identifier.
    :return: The SelfcheckCheckout object.
    """
    if check_sip2_module():
        from invenio_sip2.errors import SelfcheckCirculationError
        from invenio_sip2.models import SelfcheckCheckout

        language = kwargs.get('language', current_app.config
                              .get('BABEL_DEFAULT_LANGUAGE'))
        # Temporarily overrides the currently selected locale.
        # force_locale is allowed to work outside of application context
        with force_locale(language):
            try:
                terminal = SelfcheckTerminal.find_terminal(
                    name=kwargs.get('terminal'))
                item = Item.get_item_by_barcode(
                    barcode=item_barcode,
                    organisation_pid=terminal.organisation_pid
                )
                if not item:
                    raise ItemBarcodeNotFound
                document = Document.get_record_by_pid(item.document_pid)
                checkout = SelfcheckCheckout(
                    title_id=TitleExtension.format_text(document.get('title')),
                )

                staffer = Patron.get_record_by_pid(transaction_user_pid)
                if staffer.is_professional_user:
                    patron = Patron.get_patron_by_barcode(
                        barcode=patron_barcode,
                        org_pid=terminal.organisation_pid)
                    if not patron:
                        raise PatronBarcodeNotFound
                    # do checkout
                    result, data = item.checkout(
                        patron_pid=patron.pid,
                        transaction_user_pid=staffer.pid,
                        transaction_library_pid=terminal.library_pid,
                        item_pid=item.pid,
                        selfcheck_terminal_id=str(terminal.id),
                    )
                    if LoanAction.CHECKOUT in data:
                        loan = data[LoanAction.CHECKOUT]
                        checkout['checkout'] = True
                        checkout['desensitize'] = True
                        checkout['due_date'] = loan['end_date']
                        # checkout note
                        checkout_note = item.get_note(
                            ItemNoteTypes.CHECKOUT)
                        if checkout_note:
                            checkout.get('screen_messages', []) \
                                .append(checkout_note)
                        # TODO: When is possible, try to return fields:
                        #       magnetic_media
            except ItemBarcodeNotFound:
                checkout = SelfcheckCheckout(
                    title_id='',
                    due_date=datetime.now(timezone.utc)
                )
                checkout.get('screen_messages', []).append(
                    _('Error encountered: item not found'))
                checkout.get('screen_messages', []).append(
                    _('Error encountered: please contact a librarian'))
            except ItemNotAvailableError:
                # the due date is a required field from sip2
                checkout['due_date'] = datetime.now(timezone.utc)

                # check if item is already checked out by the current
                # patron
                loan = get_loans_by_item_pid_by_patron_pid(
                    item_pid=item.pid, patron_pid=patron.pid,
                    filter_states=[LoanState.ITEM_ON_LOAN])
                if loan:
                    checkout['renewal'] = True
                    checkout['desensitize'] = True
                    checkout['due_date'] = loan['end_date']
                else:
                    checkout.get('screen_messages', []).append(
                        _('Item is already checked-out or '
                          'requested by patron.'))
            except PatronBarcodeNotFound:
                checkout = SelfcheckCheckout(
                    title_id='',
                    due_date=datetime.now(timezone.utc)
                )
                checkout.get('screen_messages', []).append(
                    _('Error encountered: patron not found'))
                checkout.get('screen_messages', []).append(
                    _('Error encountered: please contact a librarian'))
            except NoCirculationAction:
                checkout.get('screen_messages', []).append(
                    _('No circulation action is possible'))
            except CirculationException as circ_err:
                checkout.get('screen_messages', []).append(
                    _(circ_err.description))
            except Exception:
                checkout.get('screen_messages', []).append(
                    _('Error encountered: please contact a librarian'))
                raise SelfcheckCirculationError('self checkout failed',
                                                checkout)
            return checkout


def selfcheck_checkin(transaction_user_pid, item_barcode, **kwargs):
    """SIP2 Handler to perform checkin.

    perform checkin action received from the selfcheck.
    :param transaction_user_pid: identifier of the staff user.
    :param item_barcode: item identifier.
    :return: The SelfcheckCheckin object.
    """
    if check_sip2_module():
        from invenio_sip2.models import SelfcheckCheckin

        language = kwargs.get('language', current_app.config
                              .get('BABEL_DEFAULT_LANGUAGE'))
        # Temporarily overrides the currently selected locale.
        # force_locale is allowed to work outside of application context
        with force_locale(language):
            try:
                terminal = SelfcheckTerminal.find_terminal(
                    name=kwargs.get('terminal'))
                library = Library.get_record_by_pid(terminal.library_pid)
                checkin = SelfcheckCheckin(
                    permanent_location=library.get('name')
                )
                item = Item.get_item_by_barcode(
                    barcode=item_barcode,
                    organisation_pid=terminal.organisation_pid
                )
                if not item:
                    raise ItemBarcodeNotFound

                document = Document.get_record_by_pid(item.document_pid)
                checkin['title_id'] = TitleExtension.format_text(
                    document.get('title')
                )
                staffer = Patron.get_record_by_pid(transaction_user_pid)
                if staffer.is_professional_user:
                    # do checkin
                    result, data = item.checkin(
                        transaction_user_pid=staffer.pid,
                        transaction_library_pid=terminal.library_pid,
                        item_pid=item.pid,
                        selfcheck_terminal_id=str(terminal.id),
                    )
                    if LoanAction.CHECKIN in data:
                        checkin['checkin'] = True
                        checkin['resensitize'] = True
                        if item.get_requests(output='count') > 0:
                            checkin['alert'] = True
                        # checkin note
                        checkin_note = item.get_note(ItemNoteTypes.CHECKIN)
                        if checkin_note:
                            checkin.get('screen_messages', []) \
                                .append(checkin_note)
                        # TODO: When is possible, try to return fields:
                        #       magnetic_media
                        # TODO: implements `print_line`
            except ItemBarcodeNotFound:
                checkin.get('screen_messages', []).append(
                    _('Error encountered: item not found'))
                checkin.get('screen_messages', []).append(
                    _('Error encountered: please contact a librarian'))
            except NoCirculationAction:
                checkin.get('screen_messages', []).append(
                    _('No circulation action is possible'))
            except CirculationException as circ_err:
                checkin.get('screen_messages', []).append(
                    _(circ_err.description))
            except Exception:
                current_app.logger.error('self checkin failed')
                checkin.get('screen_messages', []).append(
                    _('Error encountered: please contact a librarian'))
        return checkin


def selfcheck_renew(transaction_user_pid, item_barcode, **kwargs):
    """SIP2 handler to perform renew.

    Perform renew action received from the selfcheck.
    :param transaction_user_pid: identifier of the staff user.
    :param item_barcode: item identifier.from
    :return: The SelfcheckRenew object.
    """
    if check_sip2_module():
        from invenio_sip2.errors import SelfcheckCirculationError
        from invenio_sip2.models import SelfcheckFeeType, SelfcheckRenew
        language = kwargs.get('language', current_app.config
                              .get('BABEL_DEFAULT_LANGUAGE'))
        # Temporarily overrides the currently selected locale.
        # force_locale is allowed to work outside of application context
        with force_locale(language):
            try:
                terminal = SelfcheckTerminal.find_terminal(
                    name=kwargs.get('terminal'))
                item = Item.get_item_by_barcode(
                    barcode=item_barcode,
                    organisation_pid=terminal.organisation_pid
                )
                if not item:
                    raise ItemBarcodeNotFound

                document = Document.get_record_by_pid(item.document_pid)
                renew = SelfcheckRenew(
                    title_id=TitleExtension.format_text(document.get('title'))
                )

                staffer = Patron.get_record_by_pid(transaction_user_pid)
                if staffer.is_professional_user:
                    # do extend loan
                    result, data = item.extend_loan(
                        transaction_user_pid=staffer.pid,
                        transaction_library_pid=terminal.library_pid,
                        item_pid=item.pid,
                        selfcheck_terminal_id=str(terminal.id),
                    )
                    if LoanAction.EXTEND in data:
                        loan = data[LoanAction.EXTEND]
                        renew['success'] = True
                        renew['renewal'] = True
                        renew['desensitize'] = True
                        renew['due_date'] = loan['end_date']
                        transaction = get_last_transaction_by_loan_pid(
                                loan_pid=loan.pid, status='open')
                        if transaction:
                            # TODO: map transaction type
                            renew['fee_type'] = SelfcheckFeeType.OVERDUE
                            renew['fee_amount'] = \
                                '%.2f' % transaction.total_amount
                            renew['currency_type'] = transaction.currency
                        # TODO: When is possible, try to return fields:
                        #       magnetic_media

            except ItemBarcodeNotFound:
                renew = SelfcheckRenew(title_id='')
                renew.get('screen_messages', []).append(
                    _('Error encountered: item not found'))
                renew.get('screen_messages', []).append(
                    _('Error encountered: please contact a librarian'))
            except NoCirculationAction:
                renew.get('screen_messages', []).append(
                    _('No circulation action is possible'))
            except CirculationException as circ_err:
                renew.get('screen_messages', []).append(
                    _(circ_err.description))
            except Exception:
                renew.get('screen_messages', []).append(
                    _('Error encountered: please contact a librarian'))
                raise SelfcheckCirculationError(
                    'self renewal failed',
                    renew
                )
            return renew
