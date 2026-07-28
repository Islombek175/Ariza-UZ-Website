import re
from django import forms
from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError
from .models import CitizenAccount, normalize_phone

class StyledForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field")

class RegistrationForm(StyledForm, forms.ModelForm):
    password1 = forms.CharField(label="Parol", widget=forms.PasswordInput(attrs={"placeholder":"Kamida 8 belgi, kichik va katta harf, raqam"}))
    password2 = forms.CharField(label="Parolni tasdiqlash", widget=forms.PasswordInput)
    agreement = forms.BooleanField(label="Maxfiylik siyosati va foydalanish shartlariga roziman")
    class Meta:
        model = CitizenAccount
        fields = ["first_name","last_name","middle_name","phone","telegram_username"]
        labels = {"first_name":"Ism","last_name":"Familiya","middle_name":"Sharif","phone":"Telefon raqami","telegram_username":"Telegram username"}
        widgets = {"phone": forms.TextInput(attrs={"placeholder":"+998 90 123 45 67"}), "telegram_username":forms.TextInput(attrs={"placeholder":"@username"})}
    def clean_phone(self):
        try: return normalize_phone(self.cleaned_data["phone"])
        except ValueError as e: raise ValidationError(str(e))
    def clean_telegram_username(self):
        value = self.cleaned_data["telegram_username"].strip().lstrip("@").lower()
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{4,31}", value):
            raise ValidationError("Telegram username noto‘g‘ri.")
        return "@" + value
    def clean(self):
        data = super().clean()
        p = data.get("password1", "")
        if p:
            if not re.search(r"[A-Z]", p) or not re.search(r"[a-z]", p) or not re.search(r"\d", p):
                self.add_error("password1", "Parolda katta harf, kichik harf va raqam bo‘lishi kerak.")
            try: password_validation.validate_password(p)
            except ValidationError as e: self.add_error("password1", e)
        if p != data.get("password2"): self.add_error("password2", "Parollar mos emas.")
        return data
    def save(self, commit=True):
        user = super().save(False)
        user.username = user.phone
        user.set_password(self.cleaned_data["password1"])
        if commit: user.save()
        return user

class LoginForm(StyledForm):
    phone = forms.CharField(label="Telefon raqami", widget=forms.TextInput(attrs={"placeholder":"+998 90 123 45 67"}))
    password = forms.CharField(label="Parol", widget=forms.PasswordInput)
    def clean_phone(self):
        try: return normalize_phone(self.cleaned_data["phone"])
        except ValueError as e: raise ValidationError(str(e))

class AdminLoginForm(StyledForm):
    login = forms.CharField(label="Login")
    password = forms.CharField(label="Parol", widget=forms.PasswordInput)

class ProfileForm(StyledForm, forms.ModelForm):
    class Meta:
        model = CitizenAccount
        fields = ["first_name","last_name","middle_name","telegram_username","preferred_contact_method"]
        labels = {"first_name":"Ism","last_name":"Familiya","middle_name":"Sharif","telegram_username":"Telegram username","preferred_contact_method":"Javob olish usuli"}
