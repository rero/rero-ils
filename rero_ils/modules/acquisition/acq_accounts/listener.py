# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Acquisition account."""

from .api import AcqAccount, AcqAccountsSearch
from .models import AcqAccountExceedanceType


def enrich_acq_account_data(
    sender,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    arguments=None,
    **dummy_kwargs,
):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split("-")[0] != AcqAccountsSearch.Meta.index:
        return
    account = record
    if not isinstance(record, AcqAccount):
        account = AcqAccount.get_record_by_pid(record.get("pid"))

    if amount := account.get("allocated_amount", 0):
        if "encumbrance_exceedance" in account:
            json["encumbrance_exceedance"] = {
                "value": account.get("encumbrance_exceedance"),
                "amount": account.get_exceedance(AcqAccountExceedanceType.ENCUMBRANCE),
            }
        if "expenditure_exceedance" in account:
            json["expenditure_exceedance"] = {
                "value": account.get("expenditure_exceedance"),
                "amount": account.get_exceedance(AcqAccountExceedanceType.EXPENDITURE),
            }
    else:
        json.pop("encumbrance_exceedance", None)
        json.pop("expenditure_exceedance", None)

    # encumbrance, expenditure and balance amounts
    (self_amount, children_amount) = account.encumbrance_amount
    json["encumbrance_amount"] = {
        "self": self_amount,
        "children": children_amount,
        "total": round(self_amount + children_amount, 2),
    }
    (self_amount, children_amount) = account.expenditure_amount
    json["expenditure_amount"] = {
        "self": self_amount,
        "children": children_amount,
        "total": round(self_amount + children_amount, 2),
    }
    (self_amount, total_amount) = account.remaining_balance
    json["remaining_balance"] = {"self": self_amount, "total": total_amount}

    # additional fields for search
    json["is_active"] = account.is_active
    json["depth"] = account.depth
    json["distribution"] = account.distribution
    json["organisation"] = {"pid": account.organisation_pid, "type": "org"}
