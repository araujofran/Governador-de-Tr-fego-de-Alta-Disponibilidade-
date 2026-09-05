import os
import pytest
from database import AuditDatabase

@pytest.fixture
def test_db(tmp_path):
    db_file = os.path.join(tmp_path, "test_rbac.db")
    return AuditDatabase(db_file)

def test_rbac_authentication(test_db):
    # Test admin auth
    admin_user = test_db.authenticate_user("admin", "admin1")
    assert admin_user is not None
    assert admin_user["role"] == "admin"
    assert admin_user["can_access_infra"] is True
    assert admin_user["can_access_executive"] is True

    # Test usuario auth
    regular_user = test_db.authenticate_user("usuario", "usuario1")
    assert regular_user is not None
    assert regular_user["role"] == "usuario"
    assert regular_user["can_access_infra"] is False
    assert regular_user["can_access_executive"] is True

    # Test invalid password
    invalid_user = test_db.authenticate_user("admin", "wrongpassword")
    assert invalid_user is None

def test_rbac_permissions_update(test_db):
    # Admin grants infra access to regular user
    success = test_db.update_user_permissions("usuario", can_access_infra=True, can_access_executive=True)
    assert success is True

    updated_user = test_db.authenticate_user("usuario", "usuario1")
    assert updated_user["can_access_infra"] is True

    # Admin revokes executive access
    test_db.update_user_permissions("usuario", can_access_infra=False, can_access_executive=False)
    revoked_user = test_db.authenticate_user("usuario", "usuario1")
    assert revoked_user["can_access_infra"] is False
    assert revoked_user["can_access_executive"] is False
