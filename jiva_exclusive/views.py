from django.http import HttpResponse


def robots_txt(request):
    content = "\n".join([
        "User-agent: *",
        "Allow: /",
        "# Pages stay crawlable so search engines can see the noindex directives.",
        "",
    ])
    return HttpResponse(content, content_type="text/plain")
