from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import FileExtensionValidator
from django.db import models

def normalize_phone(value):
    digits = "".join(filter(str.isdigit, value or ""))
    if len(digits) == 9:
        digits = "998" + digits
    if len(digits) != 12 or not digits.startswith("998"):
        raise ValueError("Telefon raqami O‘zbekiston formatida bo‘lishi kerak.")
    return "+" + digits

class CitizenManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra):
        phone = normalize_phone(phone)
        user = self.model(phone=phone, normalized_phone=phone, username=extra.pop("username", phone), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, username, password, **extra):
        extra.update(is_staff=True, is_superuser=True)
        phone = extra.pop("phone", "+998000000001")
        return self.create_user(phone, password, username=username, **extra)

class CitizenAccount(AbstractUser):
    class Contact(models.TextChoices):
        TELEGRAM = "telegram", "Telegram bot"
        PHONE = "phone", "Telefon qo‘ng‘irog‘i"
        SMS = "sms", "SMS xabar"
    middle_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, unique=True)
    normalized_phone = models.CharField(max_length=13, unique=True)
    telegram_username = models.CharField(max_length=64, unique=True, null=True, blank=True)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    preferred_contact_method = models.CharField(max_length=16, choices=Contact.choices, default=Contact.TELEGRAM)
    is_phone_verified = models.BooleanField(default=False)
    department = models.ForeignKey("Department", null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["username"]
    objects = CitizenManager()
    def save(self, *args, **kwargs):
        self.normalized_phone = normalize_phone(self.phone)
        self.phone = self.normalized_phone
        if self.telegram_username:
            self.telegram_username = "@" + self.telegram_username.lstrip("@").lower()
        super().save(*args, **kwargs)
    @property
    def full_fio(self):
        return " ".join(filter(None, [self.last_name, self.first_name, self.middle_name]))

class MainCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=32, default="◉")
    display_order = models.PositiveSmallIntegerField(default=0)
    is_primary = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    class Meta: ordering = ["display_order", "name"]
    def __str__(self): return self.name

class SubCategory(models.Model):
    main_category = models.ForeignKey(MainCategory, related_name="subcategories", on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    slug = models.SlugField()
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ["display_order", "name"]
        constraints = [models.UniqueConstraint(fields=["main_category", "slug"], name="unique_sub_slug")]
    def __str__(self): return self.name

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name
class District(models.Model):
    region = models.ForeignKey(Region, related_name="districts", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta: unique_together = ("region", "name")
    def __str__(self): return self.name
class Neighborhood(models.Model):
    district = models.ForeignKey(District, related_name="neighborhoods", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    class Meta: unique_together = ("district", "name")
    def __str__(self): return self.name

class Department(models.Model):
    name = models.CharField(max_length=180)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    district = models.ForeignKey(District, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class RoutingRule(models.Model):
    main_category = models.ForeignKey(MainCategory, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, null=True, blank=True, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.CASCADE)
    district = models.ForeignKey(District, null=True, blank=True, on_delete=models.CASCADE)
    neighborhood = models.ForeignKey(Neighborhood, null=True, blank=True, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    priority = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

class ApplicationDraft(models.Model):
    citizen = models.ForeignKey(CitizenAccount, related_name="drafts", on_delete=models.CASCADE)
    current_step = models.PositiveSmallIntegerField(default=1)
    form_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DraftAttachment(models.Model):
    draft = models.ForeignKey(ApplicationDraft, related_name="attachments", on_delete=models.CASCADE)
    file = models.FileField(upload_to="drafts/%Y/%m/")
    mime_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Yangi"
        IN_PROGRESS = "IN_PROGRESS", "Ko‘rib chiqilmoqda"
        RESOLVED = "RESOLVED", "Hal qilindi"
        REJECTED = "REJECTED", "Rad etildi"
        NEEDS_INFO = "NEEDS_INFO", "Qo‘shimcha ma’lumot kerak"
    class Urgency(models.TextChoices):
        NORMAL = "normal", "Oddiy"
        IMPORTANT = "important", "Muhim"
        URGENT = "urgent", "Shoshilinch"
    application_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    citizen = models.ForeignKey(CitizenAccount, related_name="applications", on_delete=models.PROTECT)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    district = models.ForeignKey(District, on_delete=models.PROTECT)
    # Legacy relation retained as nullable so old application records remain valid.
    neighborhood = models.ForeignKey(Neighborhood, null=True, blank=True, on_delete=models.PROTECT)
    neighborhood_name = models.CharField(max_length=150, blank=True)
    street = models.CharField(max_length=180)
    house = models.CharField(max_length=80)
    landmark = models.CharField(max_length=250, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    main_category = models.ForeignKey(MainCategory, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.PROTECT)
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=5000)
    urgency = models.CharField(max_length=16, choices=Urgency.choices, default=Urgency.NORMAL)
    is_repeated = models.BooleanField(default=False)
    preferred_contact_method = models.CharField(max_length=16, choices=CitizenAccount.Contact.choices)
    assigned_department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    assigned_admin = models.ForeignKey(CitizenAccount, null=True, blank=True, related_name="assigned_applications", on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    consent_accepted = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.application_number or self.title

class Attachment(models.Model):
    application = models.ForeignKey(Application, related_name="attachments", on_delete=models.CASCADE)
    file = models.FileField(upload_to="attachments/%Y/%m/", validators=[FileExtensionValidator(["jpg","jpeg","png","webp","mp4","mov","pdf"])])
    mime_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()

class AuditLog(models.Model):
    actor = models.ForeignKey(CitizenAccount, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    target = models.CharField(max_length=180, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
