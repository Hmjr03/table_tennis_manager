from django.conf import settings
from django.shortcuts import render


def legal_context():
    return {
        "document_version": settings.LEGAL_DOCUMENTS_VERSION,
        "effective_date": settings.LEGAL_EFFECTIVE_DATE,
        "controller_name": settings.LEGAL_CONTROLLER_NAME,
        "contact_email": settings.LEGAL_CONTACT_EMAIL,
        "country": settings.LEGAL_COUNTRY,
    }


def privacy_policy(request):
    return render(
        request,
        "legal/privacy_policy.html",
        legal_context(),
    )


def terms_of_use(request):
    return render(
        request,
        "legal/terms_of_use.html",
        legal_context(),
    )
