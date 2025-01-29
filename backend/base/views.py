from django.shortcuts import get_object_or_404, redirect


def redirect_short_link(request, short_code):
    short_link = get_object_or_404(ShortLink, short_code=short_code)
    return redirect(short_link.original_url)
