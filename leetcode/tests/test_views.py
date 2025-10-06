from django.test import TestCase
from django.urls import reverse


class TestLeetCodeViews(TestCase):
    def test_home_renders(self):
        resp = self.client.get(reverse('leetcode:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'LeetCode', resp.content)

    def test_daily_question_renders(self):
        # Does not assert content of API; just checks the view renders (may use fallback)
        resp = self.client.get(reverse('leetcode:daily_question'))
        self.assertEqual(resp.status_code, 200)

    def test_question_selection_renders(self):
        resp = self.client.get(reverse('leetcode:question_selection'))
        self.assertEqual(resp.status_code, 200)

    def test_fetch_cpp_template_endpoint(self):
        resp = self.client.post(reverse('leetcode:fetch_cpp_template'), data='{}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/json', resp['Content-Type'])

