# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Ill request JSON schema tests."""

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.ill_requests.api import ILLRequest
from rero_ils.modules.ill_requests.models import ILLRequestNoteStatus


def test_required(ill_request_schema, ill_request_martigny_data_tmp):
    """Test required for ill request jsonschemas."""
    validate(ill_request_martigny_data_tmp, ill_request_schema)

    with pytest.raises(ValidationError):
        validate({}, ill_request_schema)

    # check PID - pid should be a string
    with pytest.raises(ValidationError):
        ill_request_martigny_data_tmp["pid"] = 25
        validate(ill_request_martigny_data_tmp, ill_request_schema)

    # status - check allowed values
    with pytest.raises(ValidationError):
        ill_request_martigny_data_tmp["status"] = "fake"
        validate(ill_request_martigny_data_tmp, ill_request_schema)

    # check document title - length > 2
    with pytest.raises(ValidationError):
        ill_request_martigny_data_tmp["document"]["title"] = "no"
        validate(ill_request_martigny_data_tmp, ill_request_schema)

    # check document year - length > 0
    with pytest.raises(ValidationError):
        ill_request_martigny_data_tmp["document"]["year"] = ""
        validate(ill_request_martigny_data_tmp, ill_request_schema)


def test_extended_validation(app, ill_request_martigny_data_tmp):
    """Test extended validation for ill request."""
    data = copy.deepcopy(ill_request_martigny_data_tmp)

    # pages are required if request is a request copy
    data["copy"] = True
    if "pages" in data:
        del data["pages"]
    with pytest.raises(ValidationError):
        ILLRequest.validate(ILLRequest(data))

    # test on 'notes' field :: have 2 note of the same type is disallowed
    data = copy.deepcopy(ill_request_martigny_data_tmp)
    data["notes"] = [{"type": ILLRequestNoteStatus.PUBLIC_NOTE, "content": "dummy content"}]
    ILLRequest.validate(ILLRequest(data))
    with pytest.raises(ValidationError):
        data["notes"].append({"type": ILLRequestNoteStatus.PUBLIC_NOTE, "content": "second dummy note"})
        ILLRequest.validate(ILLRequest(data))
