from django.test import SimpleTestCase
from django.urls import reverse, resolve


class TestLeetCodeURLs(SimpleTestCase):
    def test_home_url(self):
        url = reverse('leetcode:home')
        self.assertTrue(url.endswith('/leetcode-home/'))
        match = resolve(url)
        self.assertEqual(match.namespace, 'leetcode')

    def test_question_selection_url(self):
        url = reverse('leetcode:question_selection')
        match = resolve(url)
        self.assertEqual(match.namespace, 'leetcode')

    def test_daily_question_url(self):
        url = reverse('leetcode:daily_question')
        match = resolve(url)
        self.assertEqual(match.namespace, 'leetcode')

    def test_editor_url(self):
        url = reverse('leetcode:question_editor')
        match = resolve(url)
        self.assertEqual(match.namespace, 'leetcode')

