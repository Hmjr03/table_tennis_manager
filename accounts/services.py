from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import override


def send_account_activation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_path = reverse(
        "accounts:activate",
        kwargs={"uidb64": uid, "token": token},
    )
    activation_url = request.build_absolute_uri(activation_path)
    language = getattr(request, "LANGUAGE_CODE", settings.LANGUAGE_CODE)

    with override(language):
        subject = render_to_string(
            "accounts/account_activation_subject.txt"
        ).strip()
        message = render_to_string(
            "accounts/account_activation_email.txt",
            {
                "activation_url": activation_url,
                "user": user,
            },
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
