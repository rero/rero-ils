# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Rollover on acquisition resource."""

import logging.config
import random
import string
from copy import deepcopy

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccount, \
    AcqAccountsSearch
from rero_ils.modules.acquisition.acq_accounts.utils import \
    sort_accounts_as_tree
from rero_ils.modules.acquisition.acq_order_lines.api import AcqOrderLine, \
    AcqOrderLinesSearch
from rero_ils.modules.acquisition.acq_order_lines.models import \
    AcqOrderLineStatus
from rero_ils.modules.acquisition.acq_orders.api import AcqOrder, \
    AcqOrdersSearch
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.acquisition.budgets.api import Budget
from rero_ils.modules.acquisition.config import ROLLOVER_LOGGING_CONFIG
from rero_ils.modules.acquisition.exceptions import BudgetDoesNotExist, \
    BudgetNotEmptyError, InactiveBudgetError, IncompatibleBudgetError, \
    RolloverError
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.libraries.models import AccountTransferOption
from rero_ils.modules.utils import get_ref_for_pid
from rero_ils.modules.utils import truncate_string as truncate


class AcqRollover:
    """Acquisition rollover class.

    The aim of this class is to proceed to rollover process. A rollover process
    consist of migration of resources related to an acquisition budget to
    another budget. Migrated resources will be acquisition accounts, orders
    and order lines ; acquisition reception and reception lines are NEVER
    migrate by rollover process.

    USAGE :
    -------
       >> rollover_cli = AcqRollover(original_budget, destination_budget)
       >> rollover_cli.run()
    OR
       >> rollover_cli = AcqRollover(original_budget, name='', start_date='',
       ...                           end_date='')
       >> rollover_cli.run()

    During the rollover object creation, some checks will be done to validate
    arguments. If the destination budget doesn't exist, you could omit this
    argument, but it will then be necessary to specify required arguments to
    create the budget (name, start_date and end_date).

    A rollover process could only be operated with some resources related to
    an original budget, and if the destination budget is empty (related to none
    resources).


    ERROR MANAGEMENT :
    ------------------
    Some errors can occurred during the rollover process. If any errors are
    raised during the rollover process, then all possibly created object will
    be deleted ; so the database situation should be restored at the same point
    that before rollover start.

    INTERACTIVE MODE :
    ------------------
    By default, the rollover process will ask user to confirm choices at
    different step of the process. This interactive mode could be skipped using
    the init argument `is_interactive=False` ; In this case, the script will
    not prompt any questions and operations will be chained until end of the
    process or any errors.

    LOGGING:
    --------
    The rollover process has option to log operations to some output streams.
    This configuration is based on Python logging package. If no configuration
    is specified, the default configuration will be used. This configuration
    could be found into ``ROLLOVER_LOGGING_CONFIG`` variable.

    If you want to specify another configuration, you could use this variable
    as default template.

    >> custom_logging_config = deepcopy(ROLLOVER_LOGGING_CONFIG)
    >> custom_logging_config['handlers'] = ...
    >> custom_logging_config['formatters']['my_format'] = {...}
    >> rollover_cli = AcqRollover(..., logging_config=custom_logging_config)
    >> rollover_cli.run()


    """

    def __init__(self, original_budget, destination_budget=None,
                 logging_config=None, is_interactive=True,
                 propagate_errors=False, **kwargs):
        """Initialization.

        :param original_budget: the `Budget` resource related to resources to
            migrate.
        :param destination_budget: the `Budget` resource where the rollovered
            resources will be migrated.
        :param logging_config: (optional) a dictionary containing all necessary
            configuration to log the rollover process result. If not specified
            the configuration comes from `ROLLOVER_LOGGING_CONFIG` setting.
        :param is_interactive: boolean to determine if user confirmation is
            required. True by default.
        :param propagate_errors: Boolean to determine if error will be
            propagated to caller. Default is false
        :param **kwargs: all others named argument useful for rollover process.
        :raises InactiveBudgetException: if ....
        """
        self.cache = {}
        self.stack = []
        self.mapping_table = {}
        self.propagate_errors = propagate_errors

        # Set special logging configuration for rollover process
        logging.config.dictConfig(logging_config or ROLLOVER_LOGGING_CONFIG)
        self.logger = logging.getLogger(__name__)
        self.logger.info('ROLLOVER PROCESS ==================================')

        self.original_budget = original_budget
        if destination_budget is None:
            destination_budget = self._create_new_budget(**kwargs)

        self.destination_budget = destination_budget
        self.is_interactive = is_interactive
        # Why `_validate` is into a try...except.
        #   It's possible that the stack already contains an object if the
        #   destination budget didn't exist and has been created. In this case
        #   this destination budget must be destroyed.
        try:
            self._validate()
        except Exception as e:
            self._abort_rollover(str(e))
            if self.propagate_errors:
                raise e

    def run(self):
        """Run the rollover process."""
        log = self.logger
        try:
            log.info('start running....')
            log.info("parameters ::")
            log.info(f"\torigin      : {self.original_budget}")
            log.info(f"\tdestination : {self.destination_budget}")

            # STEP#1 :: Get account related to original budget
            #   Load acquisition accounts related to the original budget and
            #   sort them to get a hierarchical tree structure (parent -> child
            #   -> grandchild -> ...).
            #   When loaded, log these accounts into a table to visualize which
            #   resources will be migrated according to related library
            #   rollover setting.
            orig_accounts = AcqRollover._get_accounts(self.original_budget.pid)
            if not orig_accounts:
                raise RolloverError('Unable to find any account to rollovered')
            log.info("original accounts ::")
            columns = [
                ('ACCOUNT', 60),  # title, max_length
                ('AMOUNT', 16, 'right'),
                ('ENCUMBRANCE', 16, 'right'),
                ('MIGRATION_SETTING', 30)
            ]
            rows = []
            for account in orig_accounts:
                padding = '  ' * account.depth
                label = f"[#{account.pid}] {account.name}"
                rows.append((
                    padding + label,
                    str(account.get('allocated_amount')),
                    str(account.encumbrance_amount[0]),
                    self._get_rollover_migration_setting(account)
                ))
            self._draw_data_table(columns, rows, padding='  ')

            # STEP#2 :: Get user confirmation
            #   If interactive mode is activated, ask user for a confirmation
            #   to determine if previous table seems correct for it. If user
            #   confirm this table, a random password key will be asked to
            #   avoid bad/quick confirmation click
            if self.is_interactive:
                if not self._confirm('Are you agree ?', default="no"):
                    raise RolloverError("User doesn\'t agree")
                key_confirm = ''.join(random.choices(string.ascii_letters,
                                                     k=10))
                log.info("To continue, please enter the confirmation "
                         f"key [{key_confirm}] :: ")
                key = input()
                if key != key_confirm:
                    raise RolloverError("Confirmation key mismatch")

            # STEP#3 :: Get resources to rollover
            #   * Filter account to keep only account to migrate
            #   * Get orders to migrate :: orders containing some order lines
            #     related to the filtered account list.
            #   * Get orders lines to migrate :: order lines related to same
            #     account list + order list AND with a 'not-closed' status.
            accounts = {
                account.pid: account for account in orig_accounts
                if self._get_rollover_migration_setting(account) !=
                AccountTransferOption.NO_TRANSFER
            }
            orders = {
                order.pid: order
                for order in AcqRollover._get_opened_orders(
                    list(accounts.keys()))
            }
            to_migrate = {
                'accounts': accounts.values(),
                'orders': orders.values(),
                'order_lines': AcqRollover._get_opened_order_lines(
                    list(orders.keys()), list(accounts.keys()))
            }
            log.info('Resources to migrate (according rollover settings) :')
            log.info(f"\t#AcqAccount   : {len(to_migrate['accounts'])}")
            log.info(f"\t#AcqOrder     : {len(to_migrate['orders'])}")
            log.info(f"\t#AcqOrderLine : {len(to_migrate['order_lines'])}")

            # STEP#5 :: Proceed to rollover
            #   TODO: Add more comments.
            log.info('Starting resources migrations ...')
            self._migrate_accounts(to_migrate['accounts'])
            self._migrate_orders(to_migrate['orders'])
            self._migrate_order_lines(to_migrate['order_lines'])

            # STEP#6 :: compare new budget account table with previous version.
            #   TODO :: Add more comments
            log.info("Completed process comparison table ::")
            columns = [
                ('ACCOUNT', 60),  # title, max_length
                ('AMOUNT', 16, 'right'),
                ('ENCUMBRANCE', 16, 'right'),
                ('SUCCESS ?', 11, 'center'),
                ('NEW AMOUNT', 20, 'right'),
                ('NEW ENCUMBRANCE', 20, 'right'),
            ]
            rows = []
            errors = 0
            for account in accounts.values():
                padding = '  ' * account.depth
                label = f"[#{account.pid}] {account.name}"
                n_acc_pid = self.mapping_table['accounts'][account.pid]
                new_acc = AcqAccount.get_record_by_pid(n_acc_pid)

                rollover_status = 'OK'
                if account.encumbrance_amount[0] != \
                   new_acc.encumbrance_amount[0]:
                    rollover_status = '!! ERR !!'
                    errors += 1
                rows.append((
                    padding + label,
                    str(account.get('allocated_amount')),
                    str(account.encumbrance_amount[0]),
                    rollover_status,
                    str(new_acc.get('allocated_amount')),
                    str(new_acc.encumbrance_amount[0]),
                ))
            self._draw_data_table(columns, rows, padding='  ')
            if errors:
                raise RolloverError(f"{errors} detected on completion table.")

            # STEP#7 :: user confirmation that all seems correct for it
            if self.is_interactive:
                if not self._confirm('Are you agree ?', default="no"):
                    raise RolloverError("User doesn\'t agree")
            self._update_budgets(False, True)
            log.info("Rollover complete.... it's time for 🍺🍺🍺🍹 party !")
            # raise RolloverError("Everything works as excepted")

        except RolloverError as re:
            self._abort_rollover(str(re))
            if self.propagate_errors:
                raise re

    # RESOURCE MIGRATION METHODS ==============================================

    def _migrate_accounts(self, accounts):
        """Migrate a list of account to the destination budget.

        :params account (AcqAccount[]): the list of account to migrate.
        :raises RolloverError: If an account migration failed.
        """
        log = self.logger
        log.info("  Migrating accounts ...")
        self.mapping_table['accounts'] = {}
        new_budget_ref = get_ref_for_pid('budg', self.destination_budget.pid)
        for acc in accounts:
            data = deepcopy(acc)
            data['budget']['$ref'] = new_budget_ref
            # Try to find the new parent account (checking the temporary
            # mapping table). This is possible because we sorted the accounts
            # in hierarchical tree, so root/parent account should be migrated
            # before children accounts.
            if old_parent_pid := acc.parent_pid:
                p_pid = self.mapping_table.get('accounts').get(old_parent_pid)
                if not p_pid:
                    raise RolloverError(
                        f'Unable to find new parent account for {str(acc)}'
                        f' : parent pid was {old_parent_pid}'
                    )
                data['parent']['$ref'] = get_ref_for_pid('acac', p_pid)
            # Create the new account.
            #   If create failed :: raise an error.
            #   If success :: fill the mapping table AND the stack of new obj.
            try:
                new_account = AcqAccount.create(
                    data, dbcommit=True, reindex=True, delete_pid=True)
                self.stack.append(new_account)
                self.mapping_table['accounts'][acc.pid] = new_account.pid
                old_label = truncate(str(acc), 55).ljust(57)
                new_label = truncate(str(new_account), 55)
                log.info(f"\t* migrate {old_label} --> {new_label}")
            except Exception as e:
                raise RolloverError(f'Account creation failed :: {str(e)}') \
                    from e

    def _migrate_orders(self, orders):
        """."""
        log = self.logger
        log.info("  Migrating orders ...")
        self.mapping_table['orders'] = {}
        for order in orders:
            data = deepcopy(order)
            # Add a relation between the new order and the previous one.
            # This is useful to navigate in order history.
            data.setdefault('relations', []).append({
                "predicate": "previousVersion",
                "$ref": get_ref_for_pid('acor', order.pid)
            })
            # Create the new order.
            #   If create failed :: raise an error.
            #   If success :: fill the mapping table AND the stack of new obj.
            try:
                new_order = AcqOrder.create(
                    data, dbcommit=True, reindex=True, delete_pid=True)
                self.stack.append(new_order)
                self.mapping_table['orders'][order.pid] = new_order.pid
                old_label = truncate(str(order), 55).ljust(57)
                new_label = truncate(str(new_order), 55)
                log.info(f"\t* migrate {old_label} --> {new_label}")
            except Exception as e:
                raise RolloverError(f'Order creation failed :: {str(e)}') \
                    from e

    def _migrate_order_lines(self, order_lines):
        """."""
        log = self.logger
        log.info("  Migrating order lines ...")
        self.mapping_table['order_lines'] = {}
        for line in order_lines:
            data = deepcopy(line)
            # Try to find the new parent pids (checking the temporary
            # mapping table).
            o_order_pid = line.order_pid
            p_order_pid = self.mapping_table.get('orders').get(o_order_pid)
            if not p_order_pid:
                raise RolloverError(
                    f'Unable to find new parent order for {str(line)}'
                    f' : parent pid was {p_order_pid}'
                )
            o_acc_pid = line.account_pid
            p_acc_pid = self.mapping_table.get('accounts').get(o_acc_pid)
            if not p_acc_pid:
                raise RolloverError(
                    f'Unable to find new parent account for {str(line)}'
                    f' : parent pid was {p_acc_pid}'
                )
            data['acq_order']['$ref'] = get_ref_for_pid('acor', p_order_pid)
            data['acq_account']['$ref'] = get_ref_for_pid('acac', p_acc_pid)
            # Update specific order line fields
            data['quantity'] = data.unreceived_quantity
            del data['total_amount']

            # Create the new order line.
            #   If create failed :: raise an error.
            #   If success :: fill the mapping table AND the stack of new obj.
            try:
                new_line = AcqOrderLine.create(
                    data, dbcommit=True, reindex=True, delete_pid=True)
                self.stack.append(new_line)
                self.mapping_table['order_lines'][line.pid] = new_line.pid
                old_label = truncate(str(line), 55).ljust(57)
                new_label = truncate(str(new_line), 55)
                log.info(f"\t* migrate {old_label} --> {new_label}")
            except Exception as e:
                raise RolloverError(f'Order line creation failed :: {str(e)}')\
                    from e

    def _update_budgets(self, orig_state=False, dest_state=False):
        """Update rollover budgets to activate/deactivate them.

        :param orig_state (boolean): the new state for original budget.
        :param dest_state (boolean): the new state for destination budget.
        """
        self.logger.info("\tUpdating budget resources...")
        orig_data = deepcopy(self.original_budget)
        orig_data['is_active'] = orig_state
        self.original_budget.update(orig_data, dbcommit=True, reindex=True)
        state_str = 'activated' if orig_state else 'deactivated'
        self.logger.info(f"\t* Original budget is now {state_str}")

        dest_data = deepcopy(self.destination_budget)
        dest_data['is_active'] = dest_state
        self.destination_budget.update(dest_data, dbcommit=True, reindex=True)
        state_str = 'activated' if dest_state else 'deactivated'
        self.logger.info(f"\t* Destination budget is now {state_str}")

    # PRIVATE METHODS =========================================================
    #  These methods are used during the rollover process. They shouldn't be
    #  use outside this class

    def _abort_rollover(self, message=None):
        """Aborting the rollover process.

        This will delete all acquisition resources created on the destination
        `Budget` resource in the reverse order of their creation.

        :param message: the message to log.
        """
        if message:
            self.logger.warning(message)
        self.logger.warning('Aborting rollover process !')
        self._update_budgets(True, False)
        if not self.stack:
            return
        self.logger.info('Purging created resources...')
        for obj in reversed(self.stack):
            obj.delete(force=True, dbcommit=True, delindex=True)
            self.logger.info(f"\t* object [{str(obj)}] deleted")

    def _confirm(self, question, default="yes"):
        """Ask a yes/no question via raw_input() and return their answer.

        :param question: is a string that is presented to the user.
        :param default: is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning an answer
            is required of the user).
        :return: The "answer" return value is True for "yes" or False for "no".
        """
        valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            self.logger.info(question + prompt)
            choice = input().lower()
            if default is not None and choice == "":
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                self.logger.warning("Please respond with 'yes' or 'no'.")

    def _create_new_budget(self, **kwargs):
        """Create a new budget to use for rollover setting.

        :param organisation_pid: the organisation pid for the new budget.
        :param **kwargs: all necessary information to create the new budget.
        :return: the new `Budget` resource.
        :raises ValueError: If some required budget parameters are missing.
        """
        org_pid = self.original_budget.organisation_pid
        data = {
            'organisation': {'$ref': get_ref_for_pid('org', org_pid)},
            'is_active': False
        }
        for required_param in ['name', 'start_date', 'end_date']:
            assert required_param in kwargs, f'{required_param} param required'
            data[required_param] = kwargs[required_param]
        if budget := Budget.create(data, dbcommit=True, reindex=True):
            self.stack.append(budget)
        return budget

    def _draw_data_table(self, columns, rows=[], padding=''):
        """Draw data as a table using ASCII characters.

        :param columns: the column headers. Each column is a tuple that must
            define column name, column max length and optionally data alignment
            in this column.
        :param rows: a list of tuple. Each tuple representing a data row and
            must define at most as much data as the number of columns.
        :param padding: the left padding to apply to each table line.
        """

        def table_header():
            column_lengths = [column[1] for column in columns]

            def draw_line(col_lengths, sep='┼'):
                return sep.join(['─' * length for length in col_lengths])

            def draw_column_name(cols, sep='│', pad=' '):
                return sep.join([
                    f'{pad}{truncate(col[0], col[1] - len(pad * 2))}{pad}'
                    .ljust(col[1])
                    for col in cols
                ])

            log.info(f"{padding}┌{draw_line(column_lengths, sep='┬')}┐")
            log.info(f"{padding}│{draw_column_name(columns)}│")
            log.info(f"{padding}├{draw_line(column_lengths)}┤")

        def table_footer():
            log.info(f"{padding}"
                     f"└{'┴'.join(['─' * col[1] for col in columns])}┘")

        def table_rows(sep='│'):
            def draw_row_content(pad=' '):
                parts = []
                for idx, col_content in enumerate(row, 0):
                    column = columns[idx]
                    col_length = columns[idx][1]
                    align = column[2] if len(column) >= 3 else 'left'
                    data = truncate(col_content, col_length - len(pad * 2))
                    if align == 'right':
                        data = f'{pad}{data}{pad}'.rjust(col_length)
                    elif align == 'center':
                        data = f'{pad}{data}{pad}'.center(col_length)
                    else:
                        data = f'{pad}{data}{pad}'.ljust(col_length)
                    parts.append(data)
                return sep.join(parts)

            for row in rows:
                log.info(f"{padding}{sep}{draw_row_content()}{sep}")

        log = self.logger
        table_header()
        table_rows()
        table_footer()

    def _get_rollover_migration_setting(self, account):
        """Get the rollover migration setting from library related to account.

        :param account: the account to analyze.
        :return: the migration setting ; 'ALLOCATED_AMOUNT' by default.
        """
        return self._get_library(account.library_pid) \
            .get('rollover_settings', {}) \
            .get('account_transfer', AccountTransferOption.ALLOCATED_AMOUNT)

    def _get_library(self, library_pid):
        """Get a `Library` resources from cache or load it.

        :param library_pid (string): the library_pid to get/load.
        """
        if library_pid not in self.cache.get('library', {}):
            library = Library.get_record_by_pid(library_pid)
            self.cache.setdefault('library', {})[library_pid] = library
        return self.cache['library'][library_pid]

    def _validate(self):
        """Validate the rollover parameters.

        To be valid, we need to check parameters of a rollover process :
          - origin and destination budget exists
          - both budgets must be related to the same organisation
          - origin budget is an active budget
          - destination budget must be empty (no acquisition account children
            doesn't exist)

        :raises BudgetDoesNotExist: A desired resource doesn't exist.
        :raises IncompatibleBudgetError: If budgets doesn't belong to the same
            organisation
        :raises InactiveBudgetError: If origin budget is inactive.
        :raises NotEmptyBudgetError: If destination budget doesn't empty
        """
        if not self.original_budget or not self.destination_budget:
            raise BudgetDoesNotExist()
        o_org_pid = self.original_budget.organisation_pid
        d_org_pid = self.destination_budget.organisation_pid
        if o_org_pid != d_org_pid:
            raise IncompatibleBudgetError(o_org_pid, d_org_pid)
        elif not self.original_budget.is_active:
            raise InactiveBudgetError(self.original_budget.pid)
        elif self.destination_budget.get_links_to_me():
            raise BudgetNotEmptyError(self.destination_budget.pid)

    # PRIVATE STATIC METHODS ==================================================

    @staticmethod
    def _get_accounts(budget_pid):
        """Get accounts related to a budget sorted as hierarchical tree.

        :param budget_pid (string): the budget pid to filter.
        :return: the sorted list of `AcqAccount`.
        """
        query = AcqAccountsSearch() \
            .filter('term', budget__pid=budget_pid) \
            .params(preserve_order=True) \
            .sort({'depth': {'order': 'asc'}}) \
            .source(False).scan()
        return sort_accounts_as_tree(
            [AcqAccount.get_record(hit.meta.id) for hit in query]
        )

    @staticmethod
    def _get_opened_orders(account_pids):
        """Get opened orders related to a list of accounts.

        An opened order is an order for which the status is still PENDING,
        ORDERED or PARTIALLY_RECEIVED. If an order is CANCELLED or totally
        RECEIVED, it's not necessary to migrate it.

        :param account_pids (string[]): the list of account pids to filter.
        :return: a list of `AcqOrder` related to account pids.
        """
        open_status = [
            AcqOrderStatus.ORDERED,
            AcqOrderStatus.PENDING,
            AcqOrderStatus.PARTIALLY_RECEIVED
        ]
        query = AcqOrdersSearch() \
            .filter('terms', order_lines__account__pid=account_pids) \
            .filter('terms', status=open_status) \
            .source(False).scan()
        return [AcqOrder.get_record(hit.meta.id) for hit in query]

    @staticmethod
    def _get_opened_order_lines(order_pids, account_pids):
        """Get opened order lines related to some orders and some accounts.

        Valid states for opened order lines are APPROVED, ORDERED and PARTIALLY
        RECEIVED. We need to check accounts AND orders, because an order
        contains multiple order lines and these order lines are linked to
        an account (not necessary always the same).

        :param order_pids (string[]): the list of order pids.
        :param account_pids (string[]): the list of account pids.
        :return: a list open `AcqOrderLine` matching criteria.
        """
        open_status = [
            AcqOrderLineStatus.APPROVED,
            AcqOrderLineStatus.ORDERED,
            AcqOrderLineStatus.PARTIALLY_RECEIVED
        ]
        query = AcqOrderLinesSearch() \
            .filter('terms', acq_account__pid=account_pids) \
            .filter('terms', acq_order__pid=order_pids) \
            .filter('terms', status=open_status) \
            .source(False).scan()
        return [AcqOrderLine.get_record(hit.meta.id) for hit in query]
