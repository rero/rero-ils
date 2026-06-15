# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest fixtures and plugins."""

import pytest
from flask_security.utils import hash_password
from invenio_accounts.models import User
from invenio_search import current_search_client


@pytest.fixture(scope="function")
def user_with_profile(db, default_user_password):
    """Create a simple invenio user with a profile."""
    with db.session.begin_nested():
        profile = {
            "birth_date": "1990-01-01",
            "first_name": "User",
            "last_name": "With Profile",
            "city": "Nowhere",
        }
        user = User(
            email="user_with_profile@test.com",
            username="user_with_profile",
            password=hash_password(default_user_password),
            user_profile=profile,
            active=True,
        )
        db.session.add(user)
    db.session.commit()
    user.password_plaintext = default_user_password
    return user


@pytest.fixture(scope="function")
def user_without_name_email(db, default_user_password):
    """Create a simple invenio user without email."""
    with db.session.begin_nested():
        profile = {
            "birth_date": "1990-01-01",
            "city": "Nowhere",
        }
        user = User(
            password=hash_password(default_user_password),
            user_profile=profile,
            username="user_without_name_email",
            active=True,
        )
        db.session.add(user)
    db.session.commit()
    user.password_plaintext = default_user_password
    return user


@pytest.fixture(scope="function")
def user_without_name(db, default_user_password):
    """Create a simple invenio user without nmae."""
    with db.session.begin_nested():
        profile = {
            "birth_date": "1990-01-01",
            "city": "Nowhere",
        }
        user = User(
            password=hash_password(default_user_password),
            user_profile=profile,
            username="user_without_name",
            email="user_without_name@test.com",
            active=True,
        )
        db.session.add(user)
    db.session.commit()
    user.password_plaintext = default_user_password
    return user


@pytest.fixture(scope="module")
def create_app():
    """Create test app."""
    from invenio_app.factory import create_ui

    return create_ui


@pytest.fixture()
def ils_record():
    """Ils Record test record."""
    yield {"pid": "ilsrecord_pid", "name": "IlsRecord Name"}


@pytest.fixture()
def ils_record_2():
    """Ils Record test record 2."""
    yield {"pid": "ilsrecord_pid_2", "name": "IlsRecord Name 2"}


@pytest.fixture(scope="module")
def search_default_index(search):
    """Search default index."""
    index_name = list(current_search_client.indices.get_alias("records-record-v1.0.0").keys()).pop()
    current_search_client.indices.delete(index=index_name)
    current_search_client.indices.create(
        index="records-record-v1.0.0",
        body={"mappings": {"record-v1.0.0": {"properties": {"pid": {"type": "keyword"}}}}},
        ignore=[400],
    )
    yield search
    current_search_client.indices.delete(index="records-record-v1.0.0", ignore=[400, 404])
