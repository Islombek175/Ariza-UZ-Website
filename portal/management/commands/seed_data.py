import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from portal.models import *

PRIMARY = {
"Kommunal to‘lovlar":["Elektr energiyasi to‘lovi","Tabiiy gaz to‘lovi","Ichimlik suvi to‘lovi","Issiqlik ta’minoti to‘lovi","Chiqindi xizmati to‘lovi","Noto‘g‘ri hisoblangan qarzdorlik","Hisoblagich muammosi","To‘lov tizimi ishlamayapti","Boshqa kommunal to‘lov masalasi"],
"Uy-joy va qurilish":["Ko‘p qavatli uy","Qurilish sifati","Noqonuniy qurilish","Boshqa"],
"Yo‘llar va transport":["Yo‘l ta’miri","Jamoat transporti","Yo‘l belgilari","Boshqa"],
"Obodonlashtirish":["Ko‘cha yoritish","Chiqindi","Ko‘kalamzorlashtirish","Boshqa"],
"Internet va aloqa":["Optik internet","Mobil aloqa sifati","Pochta xizmatlari","Internet narxi","Aloqa uzilishi","Boshqa"],
"Bandlik va mehnat":["Ish qidirish","Mehnat huquqi","Ish haqi","Boshqa"],
"Ta’lim":["Maktab","Bog‘cha","Oliy ta’lim","Boshqa"],
"Sog‘liqni saqlash":["Poliklinika","Shifoxona","Dori vositalari","Boshqa"],
"Davlat xizmatlari":["Davlat xizmatlari markazi","Elektron xizmat","Hujjat olish","Boshqa"],
"Huquqiy masalalar":["Huquqiy maslahat","Sud masalasi","Notariat","Boshqa"],
}
OTHER=["Ijtimoiy himoya","Pensiya va nafaqa","Yer va kadastr","Majburiy ijro","Ekologiya","Tadbirkorlik","Soliq masalalari","Bank va moliya xizmatlari","Jamoat xavfsizligi","Davlat idoralari faoliyati","Madaniyat va sport","Boshqa masala"]

def env_value(name, default=""):
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else value

def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default

class Command(BaseCommand):
    help="Ariza.uz development and catalog data"
    def add_arguments(self,p):
        p.add_argument("--reset-admin-password",action="store_true")
        p.add_argument("--demo-users",action="store_true")
    def handle(self,*args,**opts):
        cats=[]
        for i,(name,subs) in enumerate(PRIMARY.items(),1):
            c,_=MainCategory.objects.update_or_create(slug=f"primary-{i}",defaults={"name":name,"display_order":i,"is_primary":True,"icon":["▣","⌂","▰","♧","⌁","♙","▤","♡","▦","⚖"][i-1]});cats.append(c)
            for j,s in enumerate(subs,1): SubCategory.objects.update_or_create(main_category=c,slug=f"sub-{j}",defaults={"name":s,"display_order":j})
        for i,name in enumerate(OTHER,1):
            c,_=MainCategory.objects.update_or_create(slug=f"other-{i}",defaults={"name":name,"display_order":i,"is_primary":False,"icon":"◉"});SubCategory.objects.update_or_create(main_category=c,slug="general",defaults={"name":"Boshqa","display_order":1})
        region,_=Region.objects.get_or_create(name="Xorazm viloyati")
        district_names=["Bog‘ot tumani","Gurlan tumani","Shovot tumani","Tuproqqala tumani","Urganch shahri","Urganch tumani","Xazorasp tumani","Xiva shahri","Xiva tumani","Xonqa tumani","Yangiariq tumani","Yangibozor tumani"]
        districts={name:District.objects.get_or_create(region=region,name=name)[0] for name in district_names}
        district=districts["Xiva shahri"]
        dep,_=Department.objects.get_or_create(name="Xiva shahar murojaatlar markazi",region=region,district=district)
        for c in cats: RoutingRule.objects.get_or_create(main_category=c,region=region,district=district,department=dep,defaults={"priority":10})
        username=env_value("DEFAULT_ADMIN_USERNAME","admin");password=env_value("DEFAULT_ADMIN_PASSWORD","admin123")
        admin=CitizenAccount.objects.filter(username=username).first()
        if not admin:
            admin=CitizenAccount.objects.create_superuser(username=username,password=password,phone="+998000000001",first_name="Administrator")
        elif opts["reset_admin_password"]: admin.set_password(password);admin.save(update_fields=["password"])
        create_demo_users = opts["demo_users"] or env_bool("CREATE_DEMO_USERS", settings.DEBUG)
        if create_demo_users:
            staff,_=CitizenAccount.objects.get_or_create(phone="+998901111111",defaults={"normalized_phone":"+998901111111","username":"xiva_admin","first_name":"Xiva","last_name":"Operator","is_staff":True,"department":dep})
            if not staff.has_usable_password(): staff.set_password("Operator123");staff.save()
            citizen,_=CitizenAccount.objects.get_or_create(phone="+998901234567",defaults={"normalized_phone":"+998901234567","username":"+998901234567","first_name":"Anvar","last_name":"Karimov","middle_name":"Olimovich","telegram_username":"@anvar_sample"})
            if not citizen.has_usable_password(): citizen.set_password("Citizen123");citizen.save()
        self.stdout.write(self.style.SUCCESS("Kategoriyalar, joylashuvlar, tashkilotlar va foydalanuvchilar yaratildi."))
        if create_demo_users:
            self.stdout.write(self.style.WARNING("DEVELOPMENT ONLY: admin/admin123. Ishlab chiqarishdan oldin parolni almashtiring!"))
