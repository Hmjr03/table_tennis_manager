from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "activation/sent/",
        views.activation_sent,
        name="activation_sent",
    ),
    path(
        "activate/<uidb64>/<token>/",
        views.activate,
        name="activate",
    ),
    path(
        "activation/resend/",
        views.resend_activation,
        name="resend_activation",
    ),
    path(
        "activation/resent/",
        views.activation_resent,
        name="activation_resent",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "privacy/",
        views.privacy_center,
        name="privacy_center",
    ),
    path(
        "privacy/export/",
        views.export_account_data,
        name="export_account_data",
    ),
    path(
        "delete/",
        views.delete_account,
        name="delete_account",
    ),
    path(
        "delete-request/",
        views.request_account_deletion,
        name="request_account_deletion",
    ),
    path(
        "delete-request/sent/",
        views.deletion_requested,
        name="deletion_requested",
    ),
    path(
        "delete-confirm/<uidb64>/<token>/",
        views.delete_via_email,
        name="delete_via_email",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy(
                "accounts:password_reset_done"
            ),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy(
                "accounts:password_reset_complete"
            ),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
