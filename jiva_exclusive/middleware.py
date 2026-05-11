class NoIndexMiddleware:
    """Add crawler no-index directives to every Django response."""

    robots_header = "noindex, nofollow, noarchive, nosnippet, noimageindex"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Robots-Tag"] = self.robots_header
        return response
