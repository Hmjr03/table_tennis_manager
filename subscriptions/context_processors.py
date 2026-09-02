def subscription_access(request):
    if not request.user.is_authenticated:
        return {"account_subscription": None}
    try:
        subscription = request.user.subscription
    except AttributeError:
        subscription = None
    return {"account_subscription": subscription}
