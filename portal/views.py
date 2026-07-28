import json
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import RegistrationForm, LoginForm, AdminLoginForm, ProfileForm
from .models import *
from .telegram_auth import verify_init_data
from .notifications import send_telegram

XORAZM_DISTRICTS = [
    "Bog‘ot tumani", "Gurlan tumani", "Shovot tumani", "Tuproqqala tumani",
    "Urganch shahri", "Urganch tumani", "Xazorasp tumani", "Xiva shahri",
    "Xiva tumani", "Xonqa tumani", "Yangiariq tumani", "Yangibozor tumani",
]

def client_ip(request): return request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0]
def audit(request, action, target="", details=None):
    AuditLog.objects.create(actor=request.user if request.user.is_authenticated else None, action=action, target=target, details=details or {}, ip_address=client_ip(request) or None)

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        telegram = verify_init_data(request.POST.get("telegram_init_data"))
        if telegram and not CitizenAccount.objects.filter(telegram_id=telegram["id"]).exclude(pk=user.pk).exists():
            user.telegram_id = telegram["id"]; user.save(update_fields=["telegram_id"])
        login(request, user, backend="portal.backends.PhoneBackend")
        audit(request, "REGISTER"); messages.success(request, "Hisobingiz muvaffaqiyatli yaratildi.")
        return redirect("home")
    return render(request, "portal/auth.html", {"form":form, "mode":"register", "title":"Ro‘yxatdan o‘tish"})

def user_login(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        key = f"login:{client_ip(request)}:{form.cleaned_data['phone']}"
        attempts = cache.get(key, 0)
        if attempts >= 5:
            form.add_error(None, "Ko‘p urinish. 15 daqiqadan keyin qayta urinib ko‘ring.")
        else:
            user = authenticate(request, phone=form.cleaned_data["phone"], password=form.cleaned_data["password"])
            if user and not user.is_staff:
                login(request, user); cache.delete(key); audit(request, "LOGIN")
                telegram = verify_init_data(request.POST.get("telegram_init_data"))
                if telegram and not CitizenAccount.objects.filter(telegram_id=telegram["id"]).exclude(pk=user.pk).exists():
                    user.telegram_id = telegram["id"]; user.save(update_fields=["telegram_id"])
                return redirect("home")
            cache.set(key, attempts + 1, 900); audit(request, "LOGIN_FAILED", details={"phone":form.cleaned_data["phone"]})
            form.add_error(None, "Telefon raqami yoki parol noto‘g‘ri.")
    return render(request, "portal/auth.html", {"form":form, "mode":"login", "title":"Tizimga kirish"})

def admin_login(request):
    form = AdminLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(request, username=form.cleaned_data["login"], password=form.cleaned_data["password"])
        if user and user.is_staff:
            login(request, user); audit(request, "ADMIN_LOGIN"); return redirect("admin_dashboard")
        form.add_error(None, "Login yoki parol noto‘g‘ri."); audit(request, "ADMIN_LOGIN_FAILED")
    return render(request, "portal/auth.html", {"form":form, "mode":"admin", "title":"Admin sifatida kirish"})

def password_reset(request):
    sent=False
    if request.method=="POST":
        sent=True; audit(request,"PASSWORD_RESET_REQUEST")
    return render(request,"portal/password_reset.html",{"sent":sent})

def logout_view(request):
    audit(request, "LOGOUT"); logout(request); return redirect("login")

@login_required
def home(request):
    if request.user.is_staff: return redirect("admin_dashboard")
    stats = request.user.applications.aggregate(total=Count("id"), progress=Count("id", filter=Q(status="IN_PROGRESS")), resolved=Count("id", filter=Q(status="RESOLVED")), rejected=Count("id", filter=Q(status="REJECTED")))
    return render(request, "portal/home.html", {"stats":stats, "drafts":request.user.drafts.all()[:3]})

@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Profil yangilandi."); return redirect("profile")
    return render(request, "portal/profile.html", {"form":form})

@login_required
def wizard(request, draft_id=None, step=1):
    if request.user.is_staff: raise Http404
    draft = get_object_or_404(ApplicationDraft, pk=draft_id, citizen=request.user) if draft_id else ApplicationDraft.objects.create(citizen=request.user)
    step = max(1, min(6, int(step)))
    if draft.current_step < step: draft.current_step = step; draft.save(update_fields=["current_step","updated_at"])
    return render(request, "portal/wizard.html", {
        "draft":draft, "step":step,
        "primary_categories":MainCategory.objects.filter(is_primary=True,is_active=True).prefetch_related("subcategories"),
        "other_categories":MainCategory.objects.filter(is_primary=False,is_active=True).prefetch_related("subcategories"),
        "regions":Region.objects.filter(name="Xorazm viloyati"), "contact_choices":CitizenAccount.Contact.choices,
    })

@login_required
@require_POST
def save_draft(request, pk):
    draft = get_object_or_404(ApplicationDraft, pk=pk, citizen=request.user)
    try: payload = json.loads(request.body)
    except json.JSONDecodeError: return JsonResponse({"error":"Noto‘g‘ri ma’lumot"}, status=400)
    draft.form_data = payload.get("form_data", {})
    draft.current_step = max(draft.current_step, max(1, min(6, int(payload.get("current_step", 1)))))
    draft.save()
    return JsonResponse({"saved":True, "updated_at":draft.updated_at.isoformat()})

def merge_wizard_post(draft, post, step):
    data = dict(draft.form_data)
    step_fields = {
        1: ["region","district","neighborhood_name","street","house","landmark","latitude","longitude"],
        2: ["main_category","subcategory"],
        3: ["title","description","urgency"],
        4: [],
        5: ["preferred_contact_method"],
        6: [],
    }
    for key in step_fields.get(step, []):
        if key in post:
            data[key] = post.get(key, "").strip()
    if step == 3:
        data["is_repeated"] = post.get("is_repeated") == "on"
    if step == 5:
        data["consent"] = post.get("consent") == "on"
    if step == 6:
        data["confirm"] = post.get("confirm") == "on"
    if data.get("neighborhood_name"):
        data["neighborhood_name"] = " ".join(data["neighborhood_name"].split())
    draft.form_data = data
    return data

def wizard_step_error(data, step):
    if step == 1:
        if not all(data.get(k) for k in ["region","district","neighborhood_name","street","house"]):
            return "Joylashuvdagi barcha majburiy maydonlarni to‘ldiring."
        if not 2 <= len(data["neighborhood_name"]) <= 150:
            return "Mahalla / MFY nomi 2–150 ta belgidan iborat bo‘lishi kerak."
    elif step == 2 and not all(data.get(k) for k in ["main_category","subcategory"]):
        return "Asosiy va kichik kategoriyani tanlang."
    elif step == 3:
        if len(data.get("title","").strip()) < 5:
            return "Murojaat sarlavhasi kamida 5 ta belgidan iborat bo‘lishi kerak."
        if len(data.get("description","").strip()) < 20:
            return "Murojaat matni kamida 20 ta belgidan iborat bo‘lishi kerak."
    elif step == 5 and not data.get("consent"):
        return "Shaxsiy ma’lumotlarni qayta ishlashga rozilik berish majburiy."
    elif step == 6 and not data.get("confirm"):
        return "Kiritilgan ma’lumotlar to‘g‘riligini tasdiqlang."
    return None

@login_required
@require_POST
def advance_draft(request, pk):
    draft = get_object_or_404(ApplicationDraft, pk=pk, citizen=request.user)
    step = max(1, min(5, int(request.POST.get("current_step", 1))))
    data = merge_wizard_post(draft, request.POST, step)
    error = wizard_step_error(data, step)
    draft.current_step = max(draft.current_step, step if error else step + 1)
    draft.save()
    if error:
        messages.error(request, error)
        return redirect("wizard", draft_id=draft.id, step=step)
    return redirect("wizard", draft_id=draft.id, step=step + 1)

@login_required
@require_POST
def upload_draft(request, pk):
    draft=get_object_or_404(ApplicationDraft,pk=pk,citizen=request.user); f=request.FILES.get("file")
    if not f: return JsonResponse({"error":"Fayl topilmadi."},status=400)
    images={"image/jpeg","image/png","image/webp"}; videos={"video/mp4","video/quicktime"}
    if f.content_type not in images|videos: return JsonResponse({"error":"Fayl turi qo‘llab-quvvatlanmaydi."},status=400)
    if f.content_type in images and (draft.attachments.filter(mime_type__startswith="image/").count()>=5 or f.size>10*1024*1024): return JsonResponse({"error":"Rasm limiti oshdi."},status=400)
    if f.content_type in videos and (draft.attachments.filter(mime_type__startswith="video/").exists() or f.size>50*1024*1024): return JsonResponse({"error":"Video limiti oshdi."},status=400)
    item=DraftAttachment.objects.create(draft=draft,file=f,mime_type=f.content_type,size=f.size)
    return JsonResponse({"id":item.id,"name":f.name,"url":item.file.url})

@login_required
@require_POST
def delete_draft_file(request, pk, file_id):
    item=get_object_or_404(DraftAttachment,pk=file_id,draft_id=pk,draft__citizen=request.user)
    item.file.delete(save=False);item.delete();return JsonResponse({"deleted":True})

@login_required
@require_POST
def delete_draft(request, pk):
    get_object_or_404(ApplicationDraft, pk=pk, citizen=request.user).delete()
    messages.success(request, "Xomaki o‘chirildi."); return redirect("home")

@login_required
def location_options(request):
    if request.GET.get("region"):
        items = District.objects.filter(
            region_id=request.GET["region"],
            region__name="Xorazm viloyati",
            name__in=XORAZM_DISTRICTS,
        )
    else: items = []
    if request.GET.get("region"):
        order = {name:index for index,name in enumerate(XORAZM_DISTRICTS)}
        items = sorted(items, key=lambda item:order[item.name])
    return JsonResponse({"items":[{"id":x.id,"name":x.name} for x in items]})

def select_id(data, key, model):
    try: return model.objects.get(pk=int(data.get(key)))
    except (model.DoesNotExist, TypeError, ValueError): raise ValueError(key)

def choose_department(main, sub, region, district):
    rules = RoutingRule.objects.filter(
        is_active=True, main_category=main, department__is_active=True,
        neighborhood__isnull=True,
    ).filter(Q(subcategory=sub)|Q(subcategory=None))
    rules = rules.filter(Q(region=region)|Q(region=None)).filter(Q(district=district)|Q(district=None))
    return rules.order_by("-priority", "-district_id", "-region_id", "-subcategory_id").values_list("department", flat=True).first()

@login_required
@require_POST
def submit_application(request, pk):
    with transaction.atomic():
        draft = get_object_or_404(ApplicationDraft.objects.select_for_update(), pk=pk, citizen=request.user)
        is_html_post = bool(request.POST)
        d = merge_wizard_post(draft, request.POST, 6) if is_html_post else draft.form_data
        def invalid(message):
            if is_html_post:
                draft.save()
                messages.error(request, message)
                return redirect("wizard", draft_id=draft.id, step=6)
            return JsonResponse({"error":message}, status=400)
        required = ["region","district","neighborhood_name","street","house","main_category","subcategory","title","description","urgency","preferred_contact_method"]
        if any(not d.get(k) for k in required) or not d.get("consent") or not d.get("confirm"):
            return invalid("Barcha majburiy maydonlarni to‘ldiring va tasdiqlang.")
        neighborhood_name = " ".join(str(d["neighborhood_name"]).split())
        if len(neighborhood_name) < 2:
            return invalid("Mahalla / MFY nomi kamida 2 ta belgidan iborat bo‘lishi kerak.")
        if len(neighborhood_name) > 150:
            return invalid("Mahalla / MFY nomi 150 ta belgidan oshmasligi kerak.")
        if len(d["title"].strip()) < 5 or not 20 <= len(d["description"].strip()) <= 5000:
            return invalid("Sarlavha yoki murojaat matni talabga mos emas.")
        try:
            region=select_id(d,"region",Region); district=select_id(d,"district",District)
            main=select_id(d,"main_category",MainCategory); sub=select_id(d,"subcategory",SubCategory)
            if region.name != "Xorazm viloyati" or district.region_id != region.id or sub.main_category_id != main.id: raise ValueError
        except ValueError:
            return invalid("Tanlangan ma’lumotlar mos emas.")
        department_id = choose_department(main,sub,region,district)
        app = Application.objects.create(
            citizen=request.user, region=region,district=district,neighborhood_name=neighborhood_name,street=d["street"].strip(),
            house=d["house"].strip(),landmark=d.get("landmark","").strip(),latitude=d.get("latitude") or None,longitude=d.get("longitude") or None,
            main_category=main,subcategory=sub,title=d["title"].strip(),description=d["description"].strip(),urgency=d["urgency"],
            is_repeated=bool(d.get("is_repeated")),preferred_contact_method=d["preferred_contact_method"],assigned_department_id=department_id,consent_accepted=True)
        app.application_number = f"ARZ-{timezone.now():%Y}-{app.pk:06d}"; app.save(update_fields=["application_number"])
        for item in draft.attachments.all():
            Attachment.objects.create(application=app,file=item.file.name,mime_type=item.mime_type,size=item.size)
        audit(request,"APPLICATION_SUBMITTED",app.application_number,{"department_id":department_id}); draft.delete()
        transaction.on_commit(lambda:send_telegram(request.user,f"✅ Murojaatingiz qabul qilindi: {app.application_number}\nHolat: Yangi"))
    if is_html_post:
        return redirect("success", pk=app.pk)
    return JsonResponse({"ok":True,"url":f"/applications/{app.pk}/success/"})

@login_required
def success(request, pk):
    app = get_object_or_404(Application, pk=pk, citizen=request.user)
    return render(request,"portal/success.html",{"application":app})
@login_required
def application_list(request):
    apps = request.user.applications.all().order_by("-submitted_at") if not request.user.is_staff else Application.objects.none()
    return render(request,"portal/applications.html",{"applications":apps})
@login_required
def application_detail(request, pk):
    qs = Application.objects.all() if request.user.is_superuser else (request.user.department and Application.objects.filter(assigned_department=request.user.department) if request.user.is_staff else request.user.applications.all())
    return render(request,"portal/application_detail.html",{"application":get_object_or_404(qs,pk=pk),"status_choices":Application.Status.choices})

@login_required
@user_passes_test(lambda u:u.is_staff)
def admin_dashboard(request):
    qs = Application.objects.all() if request.user.is_superuser else Application.objects.filter(assigned_department=request.user.department)
    return render(request,"portal/admin_dashboard.html",{"applications":qs.select_related("citizen","main_category","assigned_department").order_by("-submitted_at")[:30],"counts":qs.aggregate(total=Count("id"),new=Count("id",filter=Q(status="SUBMITTED")),progress=Count("id",filter=Q(status="IN_PROGRESS")),resolved=Count("id",filter=Q(status="RESOLVED")))})

@login_required
@user_passes_test(lambda u:u.is_staff)
def admin_citizens(request):
    citizens = CitizenAccount.objects.filter(is_staff=False)
    if not request.user.is_superuser:
        citizens = citizens.filter(applications__assigned_department=request.user.department)
    query = request.GET.get("q", "").strip()
    if query:
        citizens = citizens.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) |
            Q(middle_name__icontains=query) | Q(normalized_phone__icontains=query) |
            Q(telegram_username__icontains=query)
        )
    citizens = citizens.annotate(
        application_count=Count("applications", distinct=True)
    ).distinct().order_by("last_name", "first_name")
    return render(request, "portal/admin_citizens.html", {"citizens":citizens, "query":query})

@login_required
@user_passes_test(lambda u:u.is_staff)
@require_POST
def admin_status(request, pk):
    qs=Application.objects.all() if request.user.is_superuser else Application.objects.filter(assigned_department=request.user.department)
    app=get_object_or_404(qs,pk=pk); status=request.POST.get("status")
    if status not in Application.Status.values: return JsonResponse({"error":"Status noto‘g‘ri"},status=400)
    app.status=status; app.assigned_admin=request.user; app.save(update_fields=["status","assigned_admin","updated_at"])
    audit(request,"STATUS_CHANGED",app.application_number,{"status":status}); messages.success(request,"Status yangilandi.")
    transaction.on_commit(lambda:send_telegram(app.citizen,f"{app.application_number} murojaati holati: {app.get_status_display()}"))
    return redirect("application_detail",pk=pk)
