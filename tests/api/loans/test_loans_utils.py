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

"""Tests loans utils."""
from rero_ils.modules.items.utils import item_pid_to_object
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.utils import (
    loan_build_document_ref,
    loan_build_item_ref,
    loan_build_patron_ref,
)
from rero_ils.modules.utils import get_ref_for_pid


def test_loans_build_refs(item_lib_martigny, patron_martigny, document):
    """Test functions buildings refs."""

    # Create "virtual" Loan (not registered)
    loan = Loan(
        {
            "item_pid": item_pid_to_object(item_lib_martigny.pid),
            "document_pid": document.pid,
            "patron_pid": patron_martigny.pid,
        }
    )

    assert loan_build_item_ref(None, loan) == get_ref_for_pid(
        "items", item_lib_martigny.pid
    )
    assert loan_build_document_ref(None, loan) == get_ref_for_pid("doc", document.pid)
    assert loan_build_patron_ref(None, loan) == get_ref_for_pid(
        "patrons", patron_martigny.pid
    )
