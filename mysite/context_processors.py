from django.conf import settings


def leetcode_flags(request):
    return {
        "LEETCODE_ENABLED": getattr(settings, "LEETCODE_ENABLED", True),
    }


