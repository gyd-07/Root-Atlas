import csv
import unittest

from generate_exam import build_groups, demote_unresolved_singletons, partition_results
from root_analyzer import Analyzer, DATA, EXAMS, OUTPUT, RAW, choose_sample, load_json, parse_segmentation, sha256


class AnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = Analyzer()

    def test_nested_segmentation_parser(self):
        self.assertEqual(
            parse_segmentation("{<pre<(dict)}>ion>"),
            {"prefixes": ["pre"], "roots": ["dict"], "suffixes": ["ion"]},
        )

    def test_bound_root_marker(self):
        self.assertEqual(parse_segmentation("{<co<(_here)}>ant>")["roots"], ["here"])
        result = self.analyzer.analyze("coherent")
        self.assertEqual(result["roots"][0]["rootLearnerId"], 163)
        self.assertEqual(result["roots"][0]["matchedForm"], "her")

    def test_inflected_exam_word_uses_lemma(self):
        result = self.analyzer.analyze("keywords")
        self.assertEqual(result["lemma"], "keyword")
        self.assertEqual([root["form"] for root in result["roots"]], ["key", "word"])
        self.assertEqual(result["category"], "compound")
        self.assertEqual(result["confidence"], "reviewed")
        self.assertFalse(result["needsReview"])

    def test_malformed_closing_brace_is_supported(self):
        self.assertEqual(parse_segmentation("{(back}){(board)}")["roots"], ["back", "board"])
        result = self.analyzer.analyze("backboard")
        self.assertEqual(result["confidence"], "database")
        self.assertTrue(result["parseComplete"])
        self.assertEqual([root["form"] for root in result["roots"]], ["back", "board"])

    def test_incomplete_signature_requires_review(self):
        result = self.analyzer.analyze("assonance")
        self.assertEqual(result["confidence"], "database-partial")
        self.assertFalse(result["parseComplete"])
        self.assertTrue(result["needsReview"])
        self.assertIn("PRS signature", result["reason"])

    def test_parse_complete_flags_match_signatures(self):
        for word, entry in self.analyzer.morph["words"].items():
            expected = tuple(map(int, entry["signature"].split(",")))
            actual = (len(entry["prefixes"]), len(entry["roots"]), len(entry["suffixes"]))
            self.assertEqual(entry["parseComplete"], expected == actual, word)

    def test_sample_is_deterministic_and_unique(self):
        first = choose_sample(self.analyzer.exam_data, 300)
        second = choose_sample(self.analyzer.exam_data, 300)
        first_words = [item["word"] for item in first]
        self.assertEqual(first_words, [item["word"] for item in second])
        self.assertEqual(len(first_words), 300)
        self.assertEqual(len(set(first_words)), 300)

    def test_curated_example_disambiguates_homograph_root(self):
        result = self.analyzer.analyze("lecture")
        self.assertEqual(result["confidence"], "curated+database")
        self.assertEqual(result["roots"][0]["rootLearnerId"], 194)
        self.assertEqual(result["roots"][0]["meaningEn"], "to speak, to read")
        self.assertFalse(result["roots"][0]["ambiguous"])

    def test_unresolved_homograph_root_is_flagged(self):
        root = self.analyzer.root_info("lect")
        self.assertTrue(root["ambiguous"])
        self.assertEqual(root["candidateRootLearnerIds"], [193, 194])
        resolved = self.analyzer.root_info("lect", preferred_ids=[194])
        self.assertFalse(resolved["ambiguous"])
        self.assertEqual(resolved["rootLearnerId"], 194)

    def test_exam_partitions_cover_every_word_exactly_once(self):
        expected_counts = {"CET4": 3834, "CET6": 5395, "IELTS": 5007, "TOEFL": 6951}
        for exam in EXAMS:
            with self.subTest(exam=exam):
                words = [item["word"] for item in self.analyzer.exam_data["words"] if exam in item["exams"]]
                results = [self.analyzer.analyze(word) for word in words]
                grouped, independent, review = partition_results(results)
                self.assertEqual(len(results), expected_counts[exam])
                self.assertEqual(len(grouped) + len(independent) + len(review), len(results))
                grouped_words = {item["word"] for item in grouped}
                independent_words = {item["word"] for item in independent}
                review_words = {item["word"] for item in review}
                self.assertFalse(grouped_words & independent_words)
                self.assertFalse(grouped_words & review_words)
                self.assertFalse(independent_words & review_words)
                self.assertEqual(grouped_words | independent_words | review_words, set(words))
                groups = build_groups(grouped)
                self.assertEqual(sum(group["wordCount"] for group in groups), sum(len(item["roots"]) for item in grouped))

    def test_root_meaning_sources_and_hashes(self):
        data = load_json(DATA / "root_meanings.json")
        self.assertEqual(data["summary"]["wikipediaRows"], 1679)
        self.assertEqual(data["summary"]["wikipediaRootForms"], 1885)
        self.assertEqual(data["summary"]["examRootFamilies"], 1888)
        self.assertEqual(data["summary"]["freeRootDefinitions"], len(data["freeRootDefinitions"]))
        self.assertGreaterEqual(data["summary"]["freeRootDefinitions"], 12906)
        self.assertEqual(len(data["sources"]["Wikipedia Greek and Latin roots"]["rawSha256"]), 24)
        for digest in data["sources"]["Wikipedia Greek and Latin roots"]["rawSha256"].values():
            self.assertEqual(len(digest), 64)
        for form in ("able", "aviate", "path", "borne", "ion", "urban"):
            self.assertIn(form, data["freeRootDefinitions"])
        self.assertNotIn("devi", data["freeRootDefinitions"])

    def test_reviewed_root_sources_and_hashes(self):
        data = load_json(DATA / "reviewed_root_meanings.json")
        self.assertEqual(data["source"]["license"], "CC BY-SA 4.0; Wiktionary contributors")
        self.assertEqual(len(data["source"]["rawFiles"]), 4)
        for relative, expected in data["source"]["rawFiles"].items():
            self.assertEqual(sha256(DATA.parent / relative), expected)
        for entry in data["roots"]:
            self.assertTrue(entry["words"])
            self.assertTrue(entry["meaningEn"])
            self.assertTrue(entry["sourceEntry"])
            self.assertTrue(entry["sourcePage"].startswith((
                "https://en.wiktionary.org/wiki/",
                "https://en.wikipedia.org/wiki/List_of_Greek_and_Latin_roots_in_English/",
            )))
            if "source" in entry:
                self.assertEqual(entry["source"], "Wikipedia: List of Greek and Latin roots in English")
                self.assertEqual(entry["license"], "CC BY-SA 4.0")

    def test_supplemented_root_meanings_are_consistent(self):
        for exam in (item.lower() for item in EXAMS):
            full = load_json(OUTPUT / exam / f"{exam}-full.json")
            summary = full["summary"]
            groups = load_json(OUTPUT / exam / f"{exam}-root-groups.json")["groups"]
            with (OUTPUT / exam / f"{exam}-supplemented-roots.csv").open(encoding="utf-8-sig", newline="") as stream:
                supplemented = list(csv.DictReader(stream))
            with (OUTPUT / exam / f"{exam}-new-roots.csv").open(encoding="utf-8-sig", newline="") as stream:
                remaining = list(csv.DictReader(stream))
            with (OUTPUT / exam / f"{exam}-review.csv").open(encoding="utf-8-sig", newline="") as stream:
                review = list(csv.DictReader(stream))
            with (OUTPUT / exam / f"{exam}-full.csv").open(encoding="utf-8-sig", newline="") as stream:
                full_rows = list(csv.DictReader(stream))
            with (OUTPUT / exam / f"{exam}-root-groups.csv").open(encoding="utf-8-sig", newline="") as stream:
                group_rows = list(csv.DictReader(stream))
            with (OUTPUT / exam / f"{exam}-independent.csv").open(encoding="utf-8-sig", newline="") as stream:
                independent_rows = list(csv.DictReader(stream))
            self.assertEqual(len(supplemented), summary["supplementedRootForms"])
            self.assertEqual(remaining, [])
            self.assertEqual(review, [])
            self.assertEqual(len(full_rows), summary["totalWords"])
            self.assertEqual(len(group_rows), summary["rootGroupMemberships"])
            self.assertEqual(len(independent_rows), summary["independentWords"])
            self.assertTrue(summary["partitionCheck"])
            self.assertEqual(summary["supplementedRootForms"], len(supplemented))
            self.assertEqual(summary["newRootFormsNeedingMeanings"], 0)
            self.assertEqual(summary["reviewWords"], 0)
            self.assertTrue(all(group["meaningEn"] for group in groups))
            self.assertTrue(all(audit["status"] == "filled" for audit in full["rootMeaningAudit"].values()))
            for row in supplemented:
                self.assertTrue(row["meaningEn"])
                self.assertTrue(row["meaningSource"])
                self.assertTrue(row["meaningSourcePage"])
                if row["meaningSource"].startswith(("Wikipedia", "Wiktionary")):
                    self.assertTrue(row["matchedExamples"], row["rootForm"])

    def test_homograph_groups_are_separate_and_sourced(self):
        groups = load_json(OUTPUT / "cet6" / "cet6-root-groups.json")["groups"]
        meanings = {(group["form"], word["word"]): group["meaningEn"] for group in groups for word in group["words"]}
        self.assertEqual(meanings["ag", "ambiguous"], "drive, move")
        self.assertEqual(meanings["ag", "strategy"], "lead, conduct")
        self.assertEqual(meanings["pole", "monopoly"], "barter, sell")
        self.assertEqual(meanings["pole", "polar"], "pole")
        self.assertEqual(meanings["crimin", "criminal"], "crime")
        self.assertEqual(meanings["crimin", "discrimination"], "distinguish")
        self.assertEqual(meanings["stat", "static"], "make stand")
        self.assertEqual(meanings["stat", "stationary"], "stand")
        self.assertIn("a way especially designed", meanings["path", "footpath"])
        groups = load_json(OUTPUT / "toefl" / "toefl-root-groups.json")["groups"]
        meanings = {(group["form"], word["word"]): group["meaningEn"] for group in groups for word in group["words"]}
        self.assertEqual(meanings["prodig", "prodigal"], "wasteful, lavish")
        self.assertEqual(meanings["prodig", "prodigy"], "omen, portent, prophetic sign")
        self.assertEqual(meanings["strat", "strategy"], "army")
        self.assertEqual(meanings["strat", "stratum"], "spread, strew")
        self.assertEqual(meanings["man", "emanate"], "to flow")
        self.assertNotEqual(meanings["man", "emanate"], meanings["man", "layman"])
        self.assertEqual(meanings["syllab", "syllable"], "grasp, seize, take")
        groups = load_json(OUTPUT / "ielts" / "ielts-root-groups.json")["groups"]
        meanings = {(group["form"], word["word"]): group["meaningEn"] for group in groups for word in group["words"]}
        self.assertEqual(meanings["syllab", "syllabus"], "parchment label, table of contents")

    def test_reviewed_overrides_and_independent_decisions(self):
        self.assertEqual(self.analyzer.analyze("demography")["confidence"], "reviewed")
        self.assertFalse(self.analyzer.analyze("internet")["needsReview"])
        grandson = self.analyzer.analyze("grandson")
        self.assertEqual(grandson["category"], "independent-reviewed")
        self.assertEqual(grandson["roots"], [])
        for word in ("chemical", "chemist", "chemistry", "religion", "religious"):
            self.assertEqual(self.analyzer.analyze(word)["category"], "independent-reviewed")
        self.assertEqual(self.analyzer.analyze("subsidy")["roots"][0]["form"], "sid")
        self.assertEqual(self.analyzer.analyze("subsidy")["roots"][0]["meaningEn"], "sit")
        self.assertEqual(self.analyzer.analyze("philanthropy")["roots"][1]["rootLearnerId"], 17)
        self.assertEqual(self.analyzer.analyze("pursuit")["roots"][0]["form"], "sequ")
        self.assertEqual(self.analyzer.analyze("extent")["roots"][0]["form"], "tend")
        self.assertEqual(self.analyzer.analyze("retention")["roots"][0]["form"], "ten")
        footpath = self.analyzer.analyze("footpath")
        self.assertEqual([root["form"] for root in footpath["roots"]], ["foot", "path"])
        self.assertIsNone(footpath["roots"][1]["rootLearnerId"])
        self.assertEqual([root["form"] for root in self.analyzer.analyze("allergic")["roots"]], ["all", "erg"])
        self.assertEqual(self.analyzer.analyze("antagonism")["roots"][0]["rootLearnerId"], 6)
        self.assertEqual(self.analyzer.analyze("cosmopolitan")["roots"][1]["rootLearnerId"], 311)
        self.assertEqual([root["form"] for root in self.analyzer.analyze("monopolize")["roots"]], ["mon", "pole"])
        self.assertEqual(self.analyzer.analyze("hypothesize")["roots"][0]["meaningEn"], "put")
        self.assertEqual(self.analyzer.analyze("aesthetical")["roots"][0]["rootLearnerId"], 108)
        for word in ("birmingham", "mackintosh", "matrimony", "knapsack", "friday"):
            self.assertEqual(self.analyzer.analyze(word)["category"], "independent-reviewed")
            self.assertEqual(self.analyzer.analyze(word)["roots"], [])

    def test_unresolved_singleton_is_retained_as_independent(self):
        item = {"category": "derived", "roots": [{"form": "unattested", "meaningEn": None}]}
        grouped = [item]
        independent = []
        glossary = {"examRootFamilies": {"unattested": ["example"]}}
        demote_unresolved_singletons(grouped, independent, glossary)
        self.assertEqual(grouped, [])
        self.assertEqual(independent, [item])
        self.assertEqual(item["category"], "independent-reviewed")
        self.assertEqual(item["confidence"], "reviewed")
        self.assertIn("no reusable exam word family", item["reviewNote"])

    def test_sourced_meanings_do_not_use_unrelated_homographs(self):
        audit4 = load_json(OUTPUT / "cet4" / "cet4-full.json")["rootMeaningAudit"]
        audit6 = load_json(OUTPUT / "cet6" / "cet6-full.json")["rootMeaningAudit"]
        for form in ("struct", "volve"):
            self.assertEqual(audit6[form]["status"], "filled")
            self.assertTrue(audit6[form]["meaningSource"].startswith("Wikipedia"))
        self.assertEqual(audit4["bio"]["status"], "filled")
        self.assertEqual(audit4["bio"]["meaningEn"], "life")
        self.assertEqual(audit6["struct"]["meaningEn"], "to make up, build")
        self.assertEqual(audit6["able"]["meaningSource"], "ECDICT ecdict.csv")

    def test_cross_exam_group_glosses_are_consistent(self):
        seen = {}
        for exam in (item.lower() for item in EXAMS):
            groups = load_json(OUTPUT / exam / f"{exam}-root-groups.json")["groups"]
            for group in groups:
                key = (group["form"], group["rootLearnerId"], group["meaningSourceEntry"])
                value = (group["meaningEn"], group["meaningKind"], group["meaningSource"], group["meaningSourcePage"])
                self.assertEqual(seen.setdefault(key, value), value, key)

    def test_prediction(self):
        result = self.analyzer.analyze("prediction")
        self.assertEqual(result["confidence"], "database")
        self.assertEqual(result["roots"][0]["form"], "dict")
        self.assertEqual(result["roots"][0]["rootLearnerId"], 89)
        self.assertEqual(result["prefixes"], ["pre"])
        self.assertEqual(result["suffixes"], ["ion"])
        self.assertEqual(result["exams"], ["CET6", "TOEFL"])

    def test_free_root_links_back_to_curated_variant(self):
        result = self.analyzer.analyze("augmentation")
        self.assertEqual(result["confidence"], "curated+database")
        self.assertFalse(result["needsReview"])
        self.assertEqual(result["roots"][0]["form"], "augment")
        self.assertEqual(result["roots"][0]["rootLearnerId"], 26)
        self.assertEqual(result["roots"][0]["meaningEn"], "to increase")

    def test_progress_uses_corrected_root(self):
        result = self.analyzer.analyze("progress")
        self.assertEqual(result["confidence"], "curated+database")
        self.assertEqual(result["roots"][0]["rootLearnerId"], 154)
        self.assertEqual(result["roots"][0]["meaningEn"], "to go, to walk")

    def test_unhappy(self):
        result = self.analyzer.analyze(" UnHappy ")
        self.assertEqual(result["roots"][0]["form"], "happy")
        self.assertEqual(result["prefixes"], ["un"])
        self.assertEqual(result["category"], "derived")

    def test_root_outside_current_letter_range_is_retained(self):
        result = self.analyzer.analyze("construction")
        self.assertEqual(result["roots"][0]["form"], "struct")
        self.assertIsNone(result["roots"][0]["rootLearnerId"])
        self.assertIsNone(result["roots"][0]["meaningEn"])
        self.assertEqual(result["confidence"], "database")

    def test_unknown_word_is_not_called_rootless(self):
        result = self.analyzer.analyze("asdfqwer")
        self.assertEqual(result["category"], "unresolved")
        self.assertTrue(result["needsReview"])
        self.assertIn("does not prove", result["reason"])

    def test_invalid_input(self):
        result = self.analyzer.analyze("two words")
        self.assertEqual(result["category"], "invalid")
        self.assertTrue(result["needsReview"])

    def test_real_tag_counts(self):
        data = load_json(DATA / "exam_words.json")
        self.assertEqual(data["uniqueWords"], 10510)
        self.assertEqual(data["rawTagCounts"], {"CET4": 3834, "CET6": 5395, "IELTS": 5007, "TOEFL": 6951})

    def test_source_hashes_and_licenses(self):
        sources = load_json(DATA / "sources.json")
        self.assertEqual(sources["ECDICT"]["license"], "MIT")
        self.assertEqual(sources["MorphoLex-EN"]["license"], "CC BY-NC-SA 4.0")
        self.assertTrue(sources["MorphoLex-EN"]["nonCommercialOnly"])
        self.assertEqual(len(sources["ECDICT"]["sha256"]), 64)
        self.assertEqual(len(sources["MorphoLex-EN"]["sha256"]), 64)

    @unittest.skipUnless(
        (RAW / "ecdict.csv").is_file() and (RAW / "MorphoLEX_en.xlsx").is_file(),
        "optional raw source downloads are not included in the repository",
    )
    def test_raw_files_are_isolated(self):
        self.assertTrue((RAW / "ecdict.csv").is_file())
        self.assertTrue((RAW / "MorphoLEX_en.xlsx").is_file())


if __name__ == "__main__":
    unittest.main()
