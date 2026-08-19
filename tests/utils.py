# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Utils."""

import csv
import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, Mock
from xml.etree import ElementTree
from zipfile import ZipFile

import jsonref
import xmltodict
from flask import url_for
from importlib_resources import files
from invenio_accounts.testutils import login_user_via_session, login_user_via_view
from invenio_circulation.api import get_loan_for_item
from invenio_db import db
from invenio_oauth2server.models import Client, Token
from invenio_search import current_search
from six import StringIO
from six.moves.urllib.parse import parse_qs, urlparse

from rero_ils.modules.circ_policies.api import CircPolicy
from rero_ils.modules.documents.api import Document
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.item_types.api import ItemType
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.items.utils import item_pid_to_object
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan, LoansSearch
from rero_ils.modules.loans.models import LoanAction, LoanState
from rero_ils.modules.locations.api import Location
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patron_types.api import PatronType
from rero_ils.modules.patrons.api import Patron, PatronsSearch
from rero_ils.modules.patrons.utils import create_patron_from_data
from rero_ils.modules.selfcheck.models import SelfcheckTerminal


class VerifyRecordPermissionPatch:
    """Verify record permissions."""

    status_code = 200


def check_permission(permission_policy, actions, record):
    """Check permission.

    :param permission_policy: Permission policy used to do check.
    :param actions: dictionnary contains actions to check.
    :param record: Record against which to check permission.
    """
    for action_name, action_result in actions.items():
        result = permission_policy(action_name, record=record).can()
        assert result == action_result, f"{action_name} :: return {result} but should {action_result}"


def login_user(client, user):
    """Sign in user."""
    login_user_via_session(client, user=user.user)


def login_user_for_view(client, user, default_user_password):
    """Sign in user for view."""
    invenio_user = user.user
    invenio_user.password_plaintext = default_user_password
    login_user_via_view(client, user=invenio_user)


def get_json(response):
    """Get JSON from response."""
    return json.loads(response.get_data(as_text=True))


def get_xml_dict(response, ordered=False):
    """Get XML from response."""
    if ordered:
        return xmltodict.parse(response.get_data(as_text=True))
    return json.loads(json.dumps(xmltodict.parse(response.get_data(as_text=True))))


def get_csv(response):
    """Get CSV from response."""
    return response.get_data(as_text=True)


def parse_csv(raw_data):
    """Parse CSV raw data into a iterable raw file."""
    content = StringIO(raw_data)
    return csv.reader(content)


XLSX_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "xl/workbook.xml",
    "xl/_rels/workbook.xml.rels",
    "xl/styles.xml",
    "xl/worksheets/sheet1.xml",
}

XLSX_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_NAMESPACES = {"xlsx": XLSX_NAMESPACE}
XLSX_RELATIONSHIP_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_RELATIONSHIP_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/content-types"
XLSX_EXCEL_EPOCH = datetime(1899, 12, 30)
XLSX_BUILTIN_DATE_FORMAT_IDS = {str(identifier) for identifier in range(14, 23)}


def _xlsx_parts(raw_data):
    """Return the parsed XML parts of a structurally valid XLSX package."""
    with ZipFile(BytesIO(raw_data)) as archive:
        assert archive.testzip() is None
        assert XLSX_PARTS.issubset(archive.namelist())
        return {part: ElementTree.fromstring(archive.read(part)) for part in XLSX_PARTS}


def assert_xlsx_structure(raw_data):
    """Assert that an XLSX package contains valid required parts."""
    parts = _xlsx_parts(raw_data)

    content_types = parts["[Content_Types].xml"]
    overrides = {element.get("PartName") for element in content_types.findall(f"{{{CONTENT_TYPES_NAMESPACE}}}Override")}
    assert {
        "/xl/workbook.xml",
        "/xl/styles.xml",
        "/xl/worksheets/sheet1.xml",
    }.issubset(overrides)

    root_relationships = parts["_rels/.rels"]
    assert "xl/workbook.xml" in {
        element.get("Target")
        for element in root_relationships.findall(f"{{{PACKAGE_RELATIONSHIP_NAMESPACE}}}Relationship")
    }

    workbook_relationships = parts["xl/_rels/workbook.xml.rels"]
    relationships = {
        element.get("Id"): element.get("Target")
        for element in workbook_relationships.findall(f"{{{PACKAGE_RELATIONSHIP_NAMESPACE}}}Relationship")
    }
    assert {"worksheets/sheet1.xml", "styles.xml"}.issubset(relationships.values())

    workbook = parts["xl/workbook.xml"]
    worksheet = workbook.find("xlsx:sheets/xlsx:sheet", XLSX_NAMESPACES)
    assert worksheet is not None
    relationship_id = worksheet.get(f"{{{XLSX_RELATIONSHIP_NAMESPACE}}}id")
    assert relationships[relationship_id] == "worksheets/sheet1.xml"
    return parts


def _xlsx_style_ids(styles, *, bold=False, date=False):
    """Return style indexes matching the requested formatting."""
    font_ids = set()
    if bold:
        fonts = styles.findall("xlsx:fonts/xlsx:font", XLSX_NAMESPACES)
        font_ids = {str(index) for index, font in enumerate(fonts) if font.find("xlsx:b", XLSX_NAMESPACES) is not None}

    number_format_ids = set(XLSX_BUILTIN_DATE_FORMAT_IDS)
    if date:
        for number_format in styles.findall("xlsx:numFmts/xlsx:numFmt", XLSX_NAMESPACES):
            code = number_format.get("formatCode", "").lower().replace("\\", "")
            if any(token in code for token in ("yy", "dd", "hh", "ss")):
                number_format_ids.add(number_format.get("numFmtId"))

    style_ids = set()
    for index, style in enumerate(styles.findall("xlsx:cellXfs/xlsx:xf", XLSX_NAMESPACES)):
        if bold and style.get("fontId", "0") not in font_ids:
            continue
        if date and style.get("numFmtId", "0") not in number_format_ids:
            continue
        style_ids.add(str(index))
    return style_ids


def inspect_xlsx(raw_data):
    """Return worksheet metadata and cells parsed directly from OOXML."""
    parts = assert_xlsx_structure(raw_data)
    workbook = parts["xl/workbook.xml"]
    worksheet = parts["xl/worksheets/sheet1.xml"]
    styles = parts["xl/styles.xml"]
    bold_style_ids = _xlsx_style_ids(styles, bold=True)
    date_style_ids = _xlsx_style_ids(styles, date=True)

    sheet = workbook.find("xlsx:sheets/xlsx:sheet", XLSX_NAMESPACES)
    pane = worksheet.find("xlsx:sheetViews/xlsx:sheetView/xlsx:pane", XLSX_NAMESPACES)
    auto_filter = worksheet.find("xlsx:autoFilter", XLSX_NAMESPACES)
    widths = [float(column.get("width")) for column in worksheet.findall("xlsx:cols/xlsx:col", XLSX_NAMESPACES)]

    rows = []
    for row in worksheet.findall("xlsx:sheetData/xlsx:row", XLSX_NAMESPACES):
        cells = []
        for cell in row.findall("xlsx:c", XLSX_NAMESPACES):
            cell_type = cell.get("t")
            style_id = cell.get("s", "0")
            if cell_type == "inlineStr":
                value = "".join(text.text or "" for text in cell.findall("xlsx:is//xlsx:t", XLSX_NAMESPACES))
                data_type = "s"
            else:
                raw_value = cell.find("xlsx:v", XLSX_NAMESPACES)
                value = (raw_value.text or "") if raw_value is not None else ""
                if cell_type == "b":
                    data_type = "b"
                elif style_id in date_style_ids:
                    data_type = "d"
                else:
                    data_type = "n"
            cells.append(
                {
                    "reference": cell.get("r"),
                    "type": data_type,
                    "style": style_id,
                    "bold": style_id in bold_style_ids,
                    "value": value,
                }
            )
        rows.append(cells)

    return {
        "worksheet_name": sheet.get("name"),
        "freeze_pane": pane.get("topLeftCell") if pane is not None else None,
        "pane_state": pane.get("state") if pane is not None else None,
        "auto_filter": auto_filter.get("ref") if auto_filter is not None else None,
        "widths": widths,
        "rows": rows,
    }


def _xlsx_datetime(value):
    """Convert an Excel serial number to a Python datetime."""
    serial = Decimal(value)
    days = int(serial)
    microseconds = int(((serial - days) * Decimal(86_400_000_000)).to_integral_value())
    return XLSX_EXCEL_EPOCH + timedelta(days=days, microseconds=microseconds)


def parse_xlsx(raw_data, csv_compatible=False):
    """Parse rows from an XLSX workbook.

    :param csv_compatible: Convert typed dates and booleans back to the text
        produced by the CSV serializer.
    """
    workbook = inspect_xlsx(raw_data)
    rows = []
    for row in workbook["rows"]:
        values = []
        for cell in row:
            value = cell["value"]
            if value and cell["type"] == "d":
                parsed = _xlsx_datetime(value)
                value = parsed.isoformat()
                if csv_compatible and parsed.time().isoformat() == "00:00:00":
                    value = parsed.date().isoformat()
            elif csv_compatible and cell["type"] == "b":
                value = "True" if value == "1" else "False"
            values.append(value)
        rows.append(values)
    return rows


def postdata(client, endpoint, data=None, headers=None, url_data=None, force_data_as_json=True):
    """Build URL from given endpoint and send given data to it.

    :param force_data_as_json: the data sent forced json.
    :return: returns result and JSON from result.
    """
    if data is None:
        data = {}
    if headers is None:
        headers = [("Accept", "application/json"), ("Content-Type", "application/json")]
    if url_data is None:
        url_data = {}
    if force_data_as_json:
        data = json.dumps(data)
    res = client.post(url_for(endpoint, **url_data), data=data, headers=headers)
    output = get_json(res)
    return res, output


def to_relative_url(url):
    """Build relative URL from external URL.

    This is needed because the test client discards query parameters on
    external urls.
    """
    parsed = urlparse(url)
    return parsed.path + "?" + "&".join([f"{param}={val[0]}" for param, val in parse_qs(parsed.query).items()])


def get_mapping(name):
    """Returns es mapping."""
    return current_search.client.indices.get_mapping(name)


def loaded_resources_report():
    """For debug only: returns a list or count of loaded objects."""
    objects = {
        "organisations": Organisation,
        "libraries": Library,
        "locations": Location,
        "circ_policies": CircPolicy,
        "item_types": ItemType,
        "patron_types": PatronType,
        "patrons": Patron,
        "documents": Document,
        "items": Item,
        "holdings": Holding,
    }
    report = {}
    for name, record_class in objects.items():
        object_pids = record_class.get_all_pids()
        report[name] = len(list(object_pids))
        item_details = []
        if name == "items":
            for item in object_pids:
                item_details.append(
                    {
                        "item_pid": item,
                        "item_status": record_class.get_record_by_pid(item).status,
                        "requests": record_class.get_record_by_pid(item).number_of_requests(),
                        "loans": get_loan_for_item(item_pid_to_object(item)),
                    }
                )
        report["item_details"] = item_details
    return report


def mock_response(status=200, content="CONTENT", headers=None, json_data=None, raise_for_status=None):
    """Mock a request response."""
    headers = headers or {"Content-Type": "text/plain"}
    mock_resp = Mock()
    # mock raise_for_status call w/optional error
    mock_resp.raise_for_status = Mock()
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    # set status code and content
    mock_resp.status_code = status
    mock_resp.content = content
    mock_resp.headers = headers
    mock_resp.text = content
    # add json data if provided
    if json_data:
        mock_resp.headers["Content-Type"] = "application/json"
        mock_resp.json = MagicMock(return_value=json_data)
        mock_resp.text = json.dumps(json_data)
        mock_resp.content = json.dumps(json_data)
    return mock_resp


def get_timezone_difference(timezone, date):
    """Get timezone offset difference, in hours."""
    if date.tzinfo is not None:
        date = date.replace(tzinfo=None)
    return int(timezone.utcoffset(date).total_seconds() / 3600)


def check_timezone_date(timezone, date, expected=None):
    """Check hour and minute of given date regarding given timezone."""
    difference = get_timezone_difference(timezone, date)
    # In case the difference is positive, the result hour could be greater
    # or equal to 24.
    # A day doesn't contain more than 24 hours.
    # We so use modulo to always have less than 24.
    hour = (date.hour + difference) % 24
    # Prepare date
    tocheck_date = date.astimezone(timezone)
    error_msg = f"Date: {tocheck_date}. Expected: {date}. Minutes should be: {date.minute}. Hour: {hour}"
    # Expected list defines accepted hours for tests
    if expected:
        assert hour in expected, error_msg
    assert tocheck_date.minute == date.minute, error_msg
    assert tocheck_date.hour == hour, error_msg


def jsonloader(uri, **kwargs):
    """This method will be used by the mock to replace requests.get."""
    ref_split = uri.split("/")
    # TODO: find a better way to determine name and path.
    if ref_split[-2] == "common":
        path = "rero_ils.jsonschemas"
        name = f"common/{ref_split[-1]}"
    else:
        if ref_split[-2] in ["remote_entities", "local_entities"]:
            path = f"rero_ils.modules.entities.{ref_split[-2]}.jsonschemas"
        else:
            path = f"rero_ils.modules.{ref_split[-2]}.jsonschemas"
        name = f"{ref_split[-2]}/{ref_split[-1]}"

    schema_in_bytes = files(path).joinpath(name).read_bytes()
    return json.loads(schema_in_bytes.decode("utf8"))


def get_schema(schema_in_bytes):
    """Get json schema and replace $refs.

    For the resolving of the $ref we have to catch the request.get and
    get the referenced json schema directly from the resource.

    :schema_in_bytes: schema in bytes.
    :returns: resolved json schema.
    """
    schema = jsonref.loads(schema_in_bytes.decode("utf8"), loader=jsonloader)

    # Replace all remaining $refs
    while schema != jsonref.loads(jsonref.dumps(schema), loader=jsonloader):
        schema = jsonref.loads(jsonref.dumps(schema), loader=jsonloader)
    return schema


def create_new_item_from_existing_item(item=None):
    """Create a new item as a copy of a given existing item.

    :param item: the item record

    :return: the newly created item
    """
    data = deepcopy(item)
    data.pop("barcode")
    data["status"] = ItemStatus.ON_SHELF
    new_item = Item.create(data=data, dbcommit=True, reindex=True, delete_pid=True)
    ItemsSearch.flush_and_refresh()
    assert new_item.status == ItemStatus.ON_SHELF
    assert new_item.number_of_requests() == 0
    return new_item


def item_record_to_a_specific_loan_state(item=None, loan_state=None, params=None, copy_item=True):
    """Put an item into a specific circulation loan state.

    :param item: the item record
    :param loan_state: the desired loan state and attached to the given item
    :param params: the required parameters to perform the circ transactions
    :param copy_item: an option to perform transaction on a copy of the item

    :return: the item and its loan
    """
    if copy_item:
        item = create_new_item_from_existing_item(item=item)

    # complete missing parameters
    if params is None:
        params = {}
    params.setdefault("transaction_date", datetime.now(UTC).isoformat())
    params.setdefault("document_pid", item.document_pid)

    # a parameter to allow in_transit returns
    checkin_transaction_location_pid = params.pop("checkin_transaction_location_pid", None)
    patron = Patron.get_record_by_pid(params.get("patron_pid"))
    # perform circulation actions
    if loan_state in [
        LoanState.PENDING,
        LoanState.ITEM_AT_DESK,
        LoanState.ITEM_ON_LOAN,
        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
        LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
    ]:
        item, actions = item.request(**params)
        loan = Loan.get_record_by_pid(actions[LoanAction.REQUEST].get("pid"))
        assert item.number_of_requests() >= 1
        assert item.is_requested_by_patron(patron.get("patron", {}).get("barcode")[0])
    if loan_state in [
        LoanState.ITEM_AT_DESK,
        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
        LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
    ]:
        item, actions = item.validate_request(**params, pid=loan.pid)
        loan = Loan.get_record_by_pid(actions[LoanAction.VALIDATE].get("pid"))
    if loan_state in [LoanState.ITEM_ON_LOAN, LoanState.ITEM_IN_TRANSIT_TO_HOUSE]:
        item, actions = item.checkout(**params, pid=loan.pid)
        loan = Loan.get_record_by_pid(actions[LoanAction.CHECKOUT].get("pid"))
    if loan_state == LoanState.ITEM_IN_TRANSIT_TO_HOUSE:
        if checkin_transaction_location_pid:
            params["transaction_location_pid"] = checkin_transaction_location_pid
        item, actions = item.checkin(**params, pid=loan.pid)
        loan = Loan.get_record_by_pid(actions[LoanAction.CHECKIN].get("pid"))

    ItemsSearch.flush_and_refresh()
    LoansSearch.flush_and_refresh()

    assert loan["state"] == loan_state
    return item, loan


def create_patron(data):
    """Create a patron with his related user for text fixtures.

    :param data: - A dict containing a mix of user and patron data.
    :returns: - A freshly created Patron instance.
    """
    ptrn = create_patron_from_data(data=data)
    PatronsSearch.flush_and_refresh()
    return ptrn


def create_user_token(client_name, user, access_token):
    """Create a token for the given user."""
    # Create token for user
    with db.session.begin_nested():
        client = Client(
            name=client_name,
            user_id=user.id,
            is_internal=True,
            is_confidential=False,
            _default_scopes="",
        )
        client.gen_salt()
        token = Token(
            client_id=client.client_id,
            user_id=user.id,
            access_token=access_token,
            expires=None,
            is_personal=True,
            is_internal=True,
            _scopes="",
        )
        db.session.add(client)
        db.session.add(token)
    return token


def create_selfcheck_terminal(data):
    """Create a selfcheck terminal.

    :param data: - A dict containing selfcheck user data.
    :returns: - A freshly created SelfcheckUser instance.
    """
    selfcheck_terminal = SelfcheckTerminal(**data)
    db.session.add(selfcheck_terminal)
    return selfcheck_terminal


def patch_expiration_date(data):
    """Patch expiration date for patrons."""
    if data.get("patron", {}).get("expiration_date"):
        # expiration date in one year
        data["patron"]["expiration_date"] = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    return data


def clean_text(data):
    """Delete all _text from data."""
    if isinstance(data, list):
        data = [clean_text(val) for val in data]
    elif isinstance(data, dict):
        if "_text" in data:
            del data["_text"]
        data = {key: clean_text(val) for key, val in data.items()}
    return data
