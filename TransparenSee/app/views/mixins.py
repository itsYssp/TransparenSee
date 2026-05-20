from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class RoleRequireMixin(LoginRequiredMixin):
    role_required = None 
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        required_roles = self.role_required
        if isinstance(required_roles, str):
            required_roles = [required_roles]

        if required_roles and request.user.role not in required_roles:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
    
