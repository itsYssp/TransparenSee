from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class RoleRequireMixin(LoginRequiredMixin):
    role_required = None 
    login_url = '/login/'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.role_required and request.user.role not in self.role_required:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
    