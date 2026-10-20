import os
import tempfile
import unittest


class SiteRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        previous = os.environ.get("VOCAB_DB_PATH")
        os.environ["VOCAB_DB_PATH"] = os.path.join(cls.tmp.name, "test.db")
        try:
            import app as site
            import database
        finally:
            if previous is None:
                os.environ.pop("VOCAB_DB_PATH", None)
            else:
                os.environ["VOCAB_DB_PATH"] = previous
        cls.site = site
        cls.database = database
        cls.site.app.testing = True

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        with self.database.get_conn() as conn:
            conn.execute("DELETE FROM words")
            conn.execute("DELETE FROM daily_log")
            conn.execute("DELETE FROM settings")
        self.database.add_word("Alpha", ["first meaning"], "", [], "A")
        self.database.add_word("Beta%", ["percent sign"], "", [], "B")
        self.database.add_word("Gamma", ["third meaning"], "", [], "A")
        self.client = self.site.app.test_client()

    def test_search_is_literal_and_keeps_group_filter(self):
        self.assertEqual([w["word"] for w in self.database.get_all_words(search="%")], ["Beta%"])
        self.assertEqual([w["word"] for w in self.database.get_all_words("recent")],
                         ["Gamma", "Beta%", "Alpha"])
        response = self.client.get("/words?category=A&q=first")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Alpha", page)
        self.assertNotIn("Gamma", page)
        self.assertIn('name="category" value="A"', page)

    def test_review_sort_and_search_remain_in_review(self):
        alpha_id = self.database.find_word_by_name("Alpha")["id"]
        gamma_id = self.database.find_word_by_name("Gamma")["id"]
        self.database.record_result(alpha_id, False)
        self.database.record_result(gamma_id, False)
        self.database.record_result(gamma_id, False)
        self.assertEqual([w["word"] for w in self.database.get_unfamiliar_words()],
                         ["Gamma", "Alpha"])
        self.assertEqual([w["word"] for w in self.database.get_unfamiliar_words("az")],
                         ["Alpha", "Gamma"])
        response = self.client.get("/words?review=1&sort=az&q=Alpha")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="review" value="1"', page)
        self.assertIn("Alpha", page)
        self.assertNotIn("Gamma", page)

    def test_group_summary_counts_reviews_and_groups(self):
        alpha_id = self.database.find_word_by_name("Alpha")["id"]
        self.database.record_result(alpha_id, False)
        summary = self.database.get_group_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["unfamiliar"], 1)
        self.assertEqual(summary["ungrouped"], 0)
        self.assertEqual(summary["groups"], [
            {"name": "A", "count": 2}, {"name": "B", "count": 1},
        ])

    def test_word_list_search_and_empty_state(self):
        self.assertIn("Beta%", self.client.get("/list?q=percent").get_data(as_text=True))
        page = self.client.get("/list?q=missing").get_data(as_text=True)
        self.assertIn("No words match your search.", page)
        self.assertIn('name="q" value="missing"', page)

    def test_study_result_requires_boolean_and_counts_once(self):
        alpha_id = self.database.find_word_by_name("Alpha")["id"]
        bad = self.client.post("/api/result", json={"id": alpha_id, "known": "false"})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.database.get_today_count(), 0)
        good = self.client.post("/api/result", json={"id": alpha_id, "known": False})
        self.assertEqual(good.status_code, 200)
        self.assertEqual(good.get_json()["familiarity"], -1)
        self.assertEqual(good.get_json()["today"], 1)

    def test_study_data_is_safe_inside_script(self):
        self.database.add_word("</script><script>alert(1)</script>", ["example"], "", [], "")
        page = self.client.get("/learn").get_data(as_text=True)
        self.assertNotIn("</script><script>alert(1)</script>", page)
        self.assertIn("\\u003c/script\\u003e", page)
        self.assertNotIn("created_at", page)

    def test_missing_or_blank_word_does_not_change_data(self):
        self.assertEqual(self.client.get("/edit/999999").status_code, 404)
        response = self.client.post("/add", data={"word": "  ", "english_def": "kept meaning"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("kept meaning", response.get_data(as_text=True))
        alpha_id = self.database.find_word_by_name("Alpha")["id"]
        response = self.client.post(f"/edit/{alpha_id}", data={"word": "  "})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.database.get_word(alpha_id)["word"], "Alpha")

    def test_delete_ignores_external_referrer(self):
        alpha_id = self.database.find_word_by_name("Alpha")["id"]
        response = self.client.post(f"/delete/{alpha_id}", headers={"Referer": "https://example.com/elsewhere"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")


if __name__ == "__main__":
    unittest.main()
