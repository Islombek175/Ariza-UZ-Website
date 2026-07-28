from django.contrib.auth.backends import ModelBackend
from .models import CitizenAccount, normalize_phone

class PhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, phone=None, **kwargs):
        identifier = phone or username
        if not identifier: return None
        try: normalized = normalize_phone(identifier)
        except ValueError: return None
        try: user = CitizenAccount.objects.get(normalized_phone=normalized)
        except CitizenAccount.DoesNotExist: return None
        if user.check_password(password) and self.user_can_authenticate(user): return user

class StaffUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username: return None
        try: user=CitizenAccount.objects.get(username=username,is_staff=True)
        except CitizenAccount.DoesNotExist: return None
        if user.check_password(password) and self.user_can_authenticate(user): return user
