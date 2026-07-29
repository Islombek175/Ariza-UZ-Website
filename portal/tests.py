import json
from django.test import RequestFactory, TestCase
from django.urls import reverse
from .models import *
from .views import client_ip

class PortalFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region=Region.objects.create(name="Xorazm viloyati");cls.district=District.objects.create(region=cls.region,name="Xiva shahri")
        cls.category=MainCategory.objects.create(name="Kommunal to‘lovlar",slug="utility");cls.sub=SubCategory.objects.create(main_category=cls.category,name="Elektr energiyasi to‘lovi",slug="electric")
        cls.dep=Department.objects.create(name="Elektr tarmog‘i",region=cls.region,district=cls.district);RoutingRule.objects.create(main_category=cls.category,subcategory=cls.sub,region=cls.region,district=cls.district,department=cls.dep,priority=20)
        cls.user=CitizenAccount.objects.create_user("+998901234567","Citizen123",first_name="Anvar",username="+998901234567")
    def test_phone_normalization_and_login(self):
        self.assertTrue(self.client.login(phone="90 123 45 67",password="Citizen123"))
    def test_client_ip_skips_malformed_forwarded_values(self):
        request=RequestFactory().get("/",HTTP_X_FORWARDED_FOR="unknown, 203.0.113.44:1234",REMOTE_ADDR="10.0.0.1")
        self.assertEqual(client_ip(request),"203.0.113.44")
        request=RequestFactory().get("/",HTTP_X_FORWARDED_FOR="not-an-ip",REMOTE_ADDR="10.0.0.1")
        self.assertEqual(client_ip(request),"10.0.0.1")
    def test_registration_logs_citizen_in(self):
        response=self.client.post(reverse("register"),{
            "first_name":"Dilshod","last_name":"Rustamov","middle_name":"Akmalovich",
            "phone":"+998 93 765 43 21","telegram_username":"@dilshod_test",
            "password1":"StrongPass1","password2":"StrongPass1","agreement":"on",
        })
        self.assertRedirects(response,reverse("home"))
        user=CitizenAccount.objects.get(normalized_phone="+998937654321")
        self.assertEqual(int(self.client.session["_auth_user_id"]),user.pk)
        self.assertEqual(self.client.session["_auth_user_backend"],"portal.backends.PhoneBackend")
    def test_draft_is_private(self):
        other=CitizenAccount.objects.create_user("+998909999999","Citizen123",username="+998909999999");draft=ApplicationDraft.objects.create(citizen=other)
        self.client.force_login(self.user);self.assertEqual(self.client.post(reverse("save_draft",args=[draft.id]),data="{}",content_type="application/json").status_code,404)
    def test_submission_routes_and_numbers(self):
        self.client.force_login(self.user);data={"region":str(self.region.id),"district":str(self.district.id),"neighborhood_name":"  Mevaston   mahallasi  ","street":"R. Jumaniyazov","house":"6","main_category":str(self.category.id),"subcategory":str(self.sub.id),"title":"Elektr hisobi","description":"Elektr to‘lovi noto‘g‘ri hisoblangan.","urgency":"normal","preferred_contact_method":"telegram","consent":True,"confirm":True}
        draft=ApplicationDraft.objects.create(citizen=self.user,current_step=6,form_data=data);r=self.client.post(reverse("submit_application",args=[draft.id]))
        self.assertEqual(r.status_code,200);app=Application.objects.get();self.assertEqual(app.assigned_department,self.dep);self.assertEqual(app.neighborhood_name,"Mevaston mahallasi");self.assertIsNone(app.neighborhood);self.assertRegex(app.application_number,r"ARZ-\d{4}-\d{6}")
        self.assertEqual(self.client.post(reverse("submit_application",args=[draft.id])).status_code,404)
    def test_department_isolation(self):
        staff=CitizenAccount.objects.create_user("+998901111111","Operator123",username="operator",is_staff=True,department=self.dep)
        other_dep=Department.objects.create(name="Other");region2=Region.objects.create(name="Other region");district2=District.objects.create(region=region2,name="Other")
        app=Application.objects.create(application_number="ARZ-2026-000001",citizen=self.user,region=region2,district=district2,neighborhood_name="Other mahalla",street="A",house="1",main_category=self.category,subcategory=self.sub,title="Valid title",description="A sufficiently long description.",preferred_contact_method="telegram",assigned_department=other_dep,consent_accepted=True)
        self.client.force_login(staff);self.assertEqual(self.client.get(reverse("application_detail",args=[app.id])).status_code,404)
    def test_neighborhood_name_validation(self):
        self.client.force_login(self.user)
        base={"region":str(self.region.id),"district":str(self.district.id),"neighborhood_name":"A","street":"A","house":"1","main_category":str(self.category.id),"subcategory":str(self.sub.id),"title":"Valid title","description":"A sufficiently long description.","urgency":"normal","preferred_contact_method":"telegram","consent":True,"confirm":True}
        draft=ApplicationDraft.objects.create(citizen=self.user,current_step=6,form_data=base)
        response=self.client.post(reverse("submit_application",args=[draft.id]))
        self.assertEqual(response.status_code,400)
        self.assertIn("kamida 2",response.json()["error"])
    def test_department_admin_sees_citizen_contacts(self):
        staff=CitizenAccount.objects.create_user("+998901111112","Operator123",username="contact_operator",is_staff=True,department=self.dep)
        app=Application.objects.create(application_number="ARZ-2026-000099",citizen=self.user,region=self.region,district=self.district,neighborhood_name="Mevaston mahallasi",street="A",house="1",main_category=self.category,subcategory=self.sub,title="Valid title",description="A sufficiently long description.",preferred_contact_method="telegram",assigned_department=self.dep,consent_accepted=True)
        self.client.force_login(staff)
        citizens=self.client.get(reverse("admin_citizens"))
        self.assertContains(citizens,self.user.phone)
        detail=self.client.get(reverse("application_detail",args=[app.id]))
        self.assertContains(detail,self.user.full_fio)
        self.assertContains(detail,self.user.phone)
    def test_full_wizard_works_without_javascript(self):
        self.client.force_login(self.user)
        draft=ApplicationDraft.objects.create(citizen=self.user)
        steps=[
            (1,{"region":self.region.id,"district":self.district.id,"neighborhood_name":"Mevaston mahallasi","street":"R. Jumaniyazov","house":"6"}),
            (2,{"main_category":self.category.id,"subcategory":self.sub.id}),
            (3,{"title":"Elektr hisobi","description":"Elektr to‘lovi noto‘g‘ri hisoblangan.","urgency":"normal"}),
            (4,{}),
            (5,{"preferred_contact_method":"telegram","consent":"on"}),
        ]
        for step,payload in steps:
            payload["current_step"]=step
            response=self.client.post(reverse("advance_draft",args=[draft.id]),payload)
            self.assertRedirects(response,reverse("wizard",args=[draft.id,step+1]))
        response=self.client.post(reverse("submit_application",args=[draft.id]),{"current_step":6,"confirm":"on"})
        app=Application.objects.get(citizen=self.user)
        self.assertRedirects(response,reverse("success",args=[app.id]))
        self.assertFalse(ApplicationDraft.objects.filter(pk=draft.id).exists())
    def test_back_then_next_does_not_erase_other_steps(self):
        self.client.force_login(self.user)
        original={"region":str(self.region.id),"district":str(self.district.id),"neighborhood_name":"Mevaston mahallasi","street":"A","house":"1","main_category":str(self.category.id),"subcategory":str(self.sub.id),"title":"Valid title","description":"A sufficiently long description.","urgency":"normal"}
        draft=ApplicationDraft.objects.create(citizen=self.user,current_step=4,form_data=original)
        response=self.client.post(reverse("advance_draft",args=[draft.id]),{"current_step":2,"main_category":self.category.id,"subcategory":self.sub.id})
        self.assertRedirects(response,reverse("wizard",args=[draft.id,3]))
        draft.refresh_from_db()
        self.assertEqual(draft.form_data["district"],str(self.district.id))
        self.assertEqual(draft.form_data["title"],"Valid title")
        self.assertEqual(draft.current_step,4)
