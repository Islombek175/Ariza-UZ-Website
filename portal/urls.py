from django.urls import path
from . import views
urlpatterns = [
 path("health/",views.health,name="health"),
 path("",views.home,name="home"), path("register/",views.register,name="register"), path("login/",views.user_login,name="login"),
 path("admin-login/",views.admin_login,name="admin_login"), path("logout/",views.logout_view,name="logout"),
 path("password-reset/",views.password_reset,name="password_reset"),
 path("profile/",views.profile,name="profile"), path("applications/",views.application_list,name="application_list"),
 path("applications/new/",views.wizard,name="wizard_new"), path("drafts/<int:draft_id>/step/<int:step>/",views.wizard,name="wizard"),
 path("api/drafts/<int:pk>/save/",views.save_draft,name="save_draft"), path("drafts/<int:pk>/delete/",views.delete_draft,name="delete_draft"),
 path("drafts/<int:pk>/advance/",views.advance_draft,name="advance_draft"),
 path("api/drafts/<int:pk>/upload/",views.upload_draft,name="upload_draft"),path("api/drafts/<int:pk>/files/<int:file_id>/delete/",views.delete_draft_file,name="delete_draft_file"),
 path("api/location-options/",views.location_options,name="location_options"), path("api/drafts/<int:pk>/submit/",views.submit_application,name="submit_application"),
 path("applications/<int:pk>/success/",views.success,name="success"), path("applications/<int:pk>/",views.application_detail,name="application_detail"),
 path("staff/",views.admin_dashboard,name="admin_dashboard"), path("staff/citizens/",views.admin_citizens,name="admin_citizens"),
 path("staff/applications/<int:pk>/status/",views.admin_status,name="admin_status"),
]
