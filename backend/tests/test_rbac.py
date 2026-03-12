"""RBAC and security tests"""

import pytest
from fastapi import HTTPException, status
from unittest.mock import Mock, patch
from src.middleware.rbac import (
    ROLE_PERMISSIONS,
    require_permission,
    require_role,
    get_user_permissions,
    check_permission,
)


class TestRolePermissions:
    """Test role-based permission matrix"""

    def test_admin_has_all_permissions(self):
        """Test that admin role has all permissions"""
        admin_perms = get_user_permissions("admin")

        assert "view_anomalies" in admin_perms
        assert "manage_models" in admin_perms
        assert "manage_users" in admin_perms
        assert len(admin_perms) > 5

    def test_analyst_has_limited_permissions(self):
        """Test that analyst has limited permissions"""
        analyst_perms = get_user_permissions("analyst")

        assert "view_anomalies" in analyst_perms
        assert "configure_thresholds" in analyst_perms
        # Analyst should not have these:
        assert "manage_users" not in analyst_perms
        assert "manage_models" not in analyst_perms

    def test_auditor_has_read_only_permissions(self):
        """Test that auditor has read-only access"""
        auditor_perms = get_user_permissions("auditor")

        assert "view_audit_logs" in auditor_perms
        assert "view_anomalies" in auditor_perms
        # Auditor should not modify:
        assert "export_anomalies" not in auditor_perms
        assert "configure_thresholds" not in auditor_perms

    def test_guest_minimal_permissions(self):
        """Test that guest has minimal permissions"""
        guest_perms = get_user_permissions("guest")

        assert len(guest_perms) == 1
        assert "view_anomalies" in guest_perms

    def test_unknown_role_no_permissions(self):
        """Test unknown role gets no permissions"""
        perms = get_user_permissions("unknown_role")

        assert len(perms) == 0


class TestPermissionCheck:
    """Test permission checking functionality"""

    def test_admin_can_manage_users(self):
        """Test admin can perform user management"""
        can_manage = check_permission("admin", "manage_users")
        assert can_manage is True

    def test_analyst_cannot_manage_users(self):
        """Test analyst cannot manage users"""
        can_manage = check_permission("analyst", "manage_users")
        assert can_manage is False

    def test_analyst_can_view_anomalies(self):
        """Test analyst can view anomalies"""
        can_view = check_permission("analyst", "view_anomalies")
        assert can_view is True

    def test_auditor_cannot_export(self):
        """Test auditor has read-only access"""
        can_export = check_permission("auditor", "export_anomalies")
        assert can_export is False


class TestRBACDecorators:
    """Test RBAC enforcement decorators"""

    @pytest.mark.asyncio
    async def test_require_permission_granted(self):
        """Test decorator allows access when permission is granted"""
        # Create mock request with authenticated user
        mock_request = Mock()
        mock_user = Mock()
        mock_user.user_id = "user123"
        mock_user.role = "admin"
        mock_request.state = Mock()
        mock_request.state.user = mock_user

        # Create decorated function
        @require_permission("manage_users")
        async def protected_route(request):
            return {"status": "success"}

        # Should not raise exception
        result = await protected_route(request=mock_request)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_require_permission_denied(self):
        """Test decorator denies access when permission is missing"""
        mock_request = Mock()
        mock_user = Mock()
        mock_user.user_id = "user123"
        mock_user.role = "analyst"
        mock_request.state = Mock()
        mock_request.state.user = mock_user

        @require_permission("manage_users")
        async def protected_route(request):
            return {"status": "success"}

        # Should raise HTTPException with 403
        with pytest.raises(HTTPException) as exc_info:
            await protected_route(request=mock_request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_permission_no_auth(self):
        """Test decorator rejects unauthenticated requests"""
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.user = None

        @require_permission("manage_users")
        async def protected_route(request):
            return {"status": "success"}

        # Should raise HTTPException with 401
        with pytest.raises(HTTPException) as exc_info:
            await protected_route(request=mock_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_require_role_granted(self):
        """Test role-based decorator allows access"""
        mock_request = Mock()
        mock_user = Mock()
        mock_user.user_id = "user123"
        mock_user.role = "admin"
        mock_request.state = Mock()
        mock_request.state.user = mock_user

        @require_role(["admin", "analyst"])
        async def protected_route(request):
            return {"status": "success"}

        result = await protected_route(request=mock_request)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_require_role_denied(self):
        """Test role-based decorator denies access"""
        mock_request = Mock()
        mock_user = Mock()
        mock_user.user_id = "user123"
        mock_user.role = "guest"
        mock_request.state = Mock()
        mock_request.state.user = mock_user

        @require_role(["admin", "analyst"])
        async def protected_route(request):
            return {"status": "success"}

        with pytest.raises(HTTPException) as exc_info:
            await protected_route(request=mock_request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
