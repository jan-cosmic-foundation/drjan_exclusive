from django.test import SimpleTestCase
from django.urls import reverse


class SearchIndexingControlsTests(SimpleTestCase):
    def test_every_response_has_noindex_header(self):
        response = self.client.get(reverse("robots_txt"))

        self.assertEqual(
            response.headers["X-Robots-Tag"],
            "noindex, nofollow, noarchive, nosnippet, noimageindex",
        )

    def test_robots_txt_allows_crawlers_to_see_noindex_directives(self):
        response = self.client.get(reverse("robots_txt"))

        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "User-agent: *", content_type="text/plain")
        self.assertContains(response, "Allow: /", content_type="text/plain")
