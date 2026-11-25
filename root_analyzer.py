from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parent
RAW = BASE / "data" / "raw"
DATA = BASE / "data"
OUTPUT = BASE / "output"
DEFAULT_VOCAB = BASE.parent / "root-learner" / "src" / "vocab.json"
EXAMS = ("CET4", "CET6", "IELTS", "TOEFL")
TAGS = {"cet4": "CET4", "cet6": "CET6", "ielts": "IELTS", "toefl": "TOEFL"}
WORD_RE = re.compile(r"^[a-z]+$")
SHEET_RE = re.compile(r"^\d+-\d+-\d+$")
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

REVIEWED_ROOT_VARIANTS = {
    "accident": (36, "cid"),
    "adequ": (105, "equ"),
    "aggress": (154, "gress"),
    "altern": (10, "alter"),
    "alti": (9, "alt"),
    "anthropo": (17, "anthrop"),
    "amble": (12, "ambul"),
    "apart": (281, "part"),
    "apolog": (208, "log"),
    "appar": (279, "par"),
    "aqua": (19, "aqu"),
    "articul": (23, "art"),
    "audio": (25, "audi"),
    "baro": (32, "bar"),
    "capacit": (39, "cap"),
    "capit": (40, "cap"),
    "certain": (47, "cert"),
    "charit": (61, "char"),
    "chrono": (48, "chron"),
    "circle": (50, "circ"),
    "cognize": (70, "cogn"),
    "communic": (244, "mun"),
    "confer": (117, "fer"),
    "concile": (67, "cil"),
    "critic": (72, "crit"),
    "cultiv": (77, "cult"),
    "delic": (199, "lic"),
    "demic": (83, "dem"),
    "elevate": (196, "lev"),
    "empire": (104, "imper"),
    "energ": (106, "erg"),
    "ference": (117, "fer"),
    "fici": (114, "fic"),
    "formul": (133, "form"),
    "gener": (142, "gen"),
    "geni": (142, "gen"),
    "horr": (166, "hor"),
    "hospital": (167, "hospit"),
    "illus": (214, "lus"),
    "import": (314, "port"),
    "incid": (36, "cid"),
    "incide": (36, "cid"),
    "initi": (177, "it"),
    "innoc": (256, "noc"),
    "innovate": (263, "nov"),
    "integer": (176, "integr"),
    "intellig": (194, "leg"),
    "legislate": (195, "legis"),
    "legitim": (195, "leg"),
    "litera": (205, "liter"),
    "majest": (217, "maj"),
    "mani": (218, "man"),
    "motive": (242, "mot"),
    "nation": (248, "nat"),
    "negect": (193, "lect"),
    "notori": (261, "not"),
    "novel": (263, "nov"),
    "nym": (268, "onym"),
    "orient": (274, "ori"),
    "origin": (274, "orig"),
    "patho": (283, "pathy"),
    "penal": (287, "pen"),
    "percent": (45, "cent"),
    "perman": (219, "man"),
    "petrol": (292, "petr"),
    "philo": (294, "phil"),
    "picto": (299, "pict"),
    "plement": (306, "ple"),
    "podo": (285, "ped"),
    "precipit": (40, "cipit"),
    "pregn": (248, "nat"),
    "prehend": (319, "prehen"),
    "profess": (119, "fess"),
    "profici": (114, "fic"),
    "promin": (232, "min"),
    "relev": (196, "lev"),
    "repetit": (291, "pet"),
    "suffici": (114, "fic"),
    "choreo": (65, "chor"),
    "cosmo": (71, "cosm(o)"),
    "expense": (289, "pens"),
    "indemn": (82, "demn"),
    "lateral": (190, "later"),
    "monish": (238, "mon"),
    "nostalg": (260, "nost"),
    "orate": (272, "ora"),
    "pater": (284, "patri"),
    "pedagogue": (285, "ped"),
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_ecdict():
    entries = {}
    lemmas = {}
    tag_counts = Counter()
    with (RAW / "ecdict.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            word = row["word"].strip().lower()
            if len(word) < 3 or not WORD_RE.fullmatch(word):
                continue
            lemma = next((part[2:].lower() for part in row["exchange"].split("/") if part.startswith("0:")), "")
            if len(lemma) >= 3 and WORD_RE.fullmatch(lemma) and lemma != word:
                lemmas[word] = lemma
            exams = sorted({TAGS[tag] for tag in row["tag"].split() if tag in TAGS})
            if not exams:
                continue
            for exam in exams:
                tag_counts[exam] += 1
            item = {
                "word": word,
                "lemma": lemma or None,
                "exams": exams,
                "translation": row["translation"].strip().replace("\\n", "\n"),
                "definition": row["definition"].strip().replace("\\n", "\n"),
                "collins": int(row["collins"] or 0),
                "oxford": row["oxford"] == "1",
                "bnc": int(row["bnc"] or 0),
                "frq": int(row["frq"] or 0),
            }
            old = entries.get(word)
            if old is None:
                entries[word] = item
            else:
                old["exams"] = sorted(set(old["exams"]) | set(exams))
                if not old["translation"] and item["translation"]:
                    old["translation"] = item["translation"]
    result = {
        "source": "ECDICT ecdict.csv",
        "license": "MIT",
        "rawTagCounts": dict(tag_counts),
        "uniqueWords": len(entries),
        "lemmaMappings": len(lemmas),
        "lemmas": dict(sorted(lemmas.items())),
        "words": sorted(entries.values(), key=lambda item: item["word"]),
    }
    write_json(DATA / "exam_words.json", result)
    return result


def column_name(reference):
    return re.match(r"[A-Z]+", reference).group(0)


def workbook_sheets(archive):
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.get("Id"): rel.get("Target")
        for rel in relationships.findall(f"{{{PKG_REL_NS}}}Relationship")
    }
    for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
        target = targets[sheet.get(f"{{{DOC_REL_NS}}}id")]
        if target.startswith("/"):
            path = target.lstrip("/")
        else:
            path = str(Path("xl") / target).replace("\\", "/")
        yield sheet.get("name"), path


def iter_sheet_rows(archive, path, shared_strings):
    headers = None
    with archive.open(path) as stream:
        for _, elem in ET.iterparse(stream, events=("end",)):
            if elem.tag != f"{{{MAIN_NS}}}row":
                continue
            values = {}
            for cell in elem.findall(f"{{{MAIN_NS}}}c"):
                value_node = cell.find(f"{{{MAIN_NS}}}v")
                if value_node is None or value_node.text is None:
                    value = ""
                else:
                    value = value_node.text
                    if cell.get("t") == "s":
                        value = shared_strings[int(value)]
                values[column_name(cell.get("r"))] = value
            if headers is None:
                headers = {column: value for column, value in values.items() if value}
            else:
                row = {headers[column]: value for column, value in values.items() if column in headers}
                if row:
                    yield row
            elem.clear()


def parse_segmentation(segmentation):
    clean = lambda form: form.strip("_")
    return {
        "prefixes": [clean(form) for form in re.findall(r"<([a-z_]+)<", segmentation)],
        "roots": [clean(form) for form in re.findall(r"\(([a-z_]+)[)}]", segmentation)],
        "suffixes": [clean(form) for form in re.findall(r">([a-z_]+)>", segmentation)],
    }


def prepare_morpholex():
    words = {}
    roots = set()
    prefixes = set()
    suffixes = set()
    with zipfile.ZipFile(RAW / "MorphoLEX_en.xlsx") as archive:
        shared_strings = [
            "".join(node.itertext())
            for node in ET.fromstring(archive.read("xl/sharedStrings.xml"))
        ]
        for sheet_name, path in workbook_sheets(archive):
            if SHEET_RE.fullmatch(sheet_name):
                for row in iter_sheet_rows(archive, path, shared_strings):
                    word = row.get("Word", "").lower()
                    segmentation = row.get("MorphoLexSegm", "")
                    if not WORD_RE.fullmatch(word) or not segmentation:
                        continue
                    parts = parse_segmentation(segmentation)
                    signature = row.get("PRS_signature", sheet_name.replace("-", ","))
                    expected_counts = tuple(map(int, signature.split(",")))
                    actual_counts = (len(parts["prefixes"]), len(parts["roots"]), len(parts["suffixes"]))
                    words[word] = {
                        "segmentation": segmentation,
                        "signature": signature,
                        "parseComplete": expected_counts == actual_counts,
                        **parts,
                    }
            elif sheet_name in {"All roots", "All prefixes", "All suffixes"}:
                destination = {"All roots": roots, "All prefixes": prefixes, "All suffixes": suffixes}[sheet_name]
                for row in iter_sheet_rows(archive, path, shared_strings):
                    morpheme = row.get("morpheme", "")
                    match = re.search(r"[a-z]+", morpheme)
                    if match:
                        destination.add(match.group(0))
    result = {
        "source": "MorphoLex-EN",
        "license": "CC BY-NC-SA 4.0",
        "citation": "Sánchez-Gutiérrez et al. (2017), doi:10.3758/s13428-017-0981-8",
        "uniqueWords": len(words),
        "partialWords": sum(not entry["parseComplete"] for entry in words.values()),
        "words": dict(sorted(words.items())),
        "roots": sorted(roots),
        "prefixes": sorted(prefixes),
        "suffixes": sorted(suffixes),
    }
    write_json(DATA / "morpholex.json", result)
    return result


def prepare_root_index(vocab_path):
    vocab = load_json(vocab_path)
    roots = []
    examples = {}
    for root in vocab["roots"]:
        item = {
            "id": root["id"],
            "forms": sorted({form.lower() for form in root["forms"]}),
            "meaningEn": root["meaningEn"],
        }
        roots.append(item)
        for word in root["words"]:
            examples.setdefault(word["w"].lower(), set()).add(root["id"])
    result = {
        "source": str(vocab_path),
        "roots": roots,
        "examples": {word: sorted(ids) for word, ids in sorted(examples.items())},
    }
    write_json(DATA / "root_index.json", result)
    return result


def prepare_sources(vocab_path):
    files = {
        "ECDICT": {
            "url": "https://github.com/skywind3000/ECDICT",
            "file": "ecdict.csv",
            "license": "MIT",
        },
        "MorphoLex-EN": {
            "url": "https://github.com/hugomailhot/MorphoLex-en",
            "file": "MorphoLEX_en.xlsx",
            "license": "CC BY-NC-SA 4.0",
            "nonCommercialOnly": True,
            "shareAlike": True,
            "citation": "Sánchez-Gutiérrez et al. (2017), doi:10.3758/s13428-017-0981-8",
        },
        "RootLearner": {
            "path": str(vocab_path),
            "usage": "read-only root meanings and curated examples",
        },
    }
    for name, filename in (("ECDICT", "ecdict.csv"), ("MorphoLex-EN", "MorphoLEX_en.xlsx")):
        files[name]["sha256"] = sha256(RAW / filename)
    write_json(DATA / "sources.json", files)


def prepare(vocab_path):
    exam = prepare_ecdict()
    morph = prepare_morpholex()
    roots = prepare_root_index(vocab_path)
    prepare_sources(vocab_path)
    print(f"ECDICT: {exam['uniqueWords']} unique exam words; tags={exam['rawTagCounts']}")
    print(f"MorphoLex: {morph['uniqueWords']} segmented words, {len(morph['roots'])} roots, {morph['partialWords']} partial")
    print(f"RootLearner: {len(roots['roots'])} roots, {len(roots['examples'])} curated examples")


class Analyzer:
    def __init__(self, data_dir=DATA):
        self.exam_data = load_json(data_dir / "exam_words.json")
        self.exam_words = {item["word"]: item for item in self.exam_data["words"]}
        self.lemmas = self.exam_data["lemmas"]
        self.morph = load_json(data_dir / "morpholex.json")
        self.root_data = load_json(data_dir / "root_index.json")
        self.reviewed_words = load_json(data_dir / "reviewed_words.json")
        reviewed_meanings = load_json(data_dir / "reviewed_root_meanings.json")
        self.reviewed_meaning_source = reviewed_meanings["source"]
        self.reviewed_root_meanings = {}
        for entry in reviewed_meanings["roots"]:
            self.reviewed_root_meanings.setdefault(entry["form"], []).append(entry)
        self.roots_by_id = {root["id"]: root for root in self.root_data["roots"]}
        self.form_index = {}
        for root in self.root_data["roots"]:
            for form in root["forms"]:
                self.form_index.setdefault(form, []).append(root["id"])
        self.prefixes = tuple(sorted(self.morph["prefixes"], key=len, reverse=True))
        self.suffixes = tuple(sorted(self.morph["suffixes"], key=len, reverse=True))
        self.free_roots = {
            word for word, entry in self.morph["words"].items()
            if entry["parseComplete"] and entry["roots"] == [word] and not entry["prefixes"] and not entry["suffixes"]
        }

    def root_info(self, form, root_id=None, preferred_ids=()):
        variant = REVIEWED_ROOT_VARIANTS.get(form)
        if variant is not None and (root_id is None or root_id == variant[0]):
            root_id, matched_variant = variant
        else:
            matched_variant = None
        ids = [root_id] if root_id is not None else self.form_index.get(form, []) or self.root_data["examples"].get(form, [])
        if not ids and root_id is None:
            ids = [root["id"] for root in self.root_data["roots"] for candidate in root["forms"] if form == candidate + "e"]
        if ids:
            preferred = any(candidate in ids for candidate in preferred_ids) or variant is not None
            selected_id = next((candidate for candidate in preferred_ids if candidate in ids), ids[0])
            root = self.roots_by_id[selected_id]
            matched = matched_variant or next((candidate for candidate in root["forms"] if candidate == form or form == candidate + "e"), form)
            return {
                "form": form,
                "meaningEn": root["meaningEn"],
                "rootLearnerId": root["id"],
                "matchedForm": matched,
                "candidateRootLearnerIds": ids,
                "ambiguous": len(ids) > 1 and not preferred,
            }
        return {"form": form, "meaningEn": None, "rootLearnerId": None, "matchedForm": None, "candidateRootLearnerIds": [], "ambiguous": False}

    def reviewed_root(self, spec):
        if spec.get("useRootLearner", True):
            root = self.root_info(spec["form"], spec.get("rootLearnerId"))
        else:
            root = {"form": spec["form"], "meaningEn": None, "rootLearnerId": None, "matchedForm": None, "candidateRootLearnerIds": [], "ambiguous": False}
        for key in ("meaningEn", "meaningKind", "meaningSource", "meaningSourceEntry", "meaningSourcePage", "meaningLicense", "matchedForm"):
            if key in spec:
                root[key] = spec[key]
        return root

    def apply_reviewed_root_meanings(self, word, result):
        for root in result["roots"]:
            for entry in self.reviewed_root_meanings.get(root["form"], []):
                if word not in entry["words"]:
                    continue
                root.update({
                    "meaningEn": entry["meaningEn"],
                    "meaningKind": "etymological root gloss",
                    "meaningSource": entry.get("source", self.reviewed_meaning_source["name"]),
                    "meaningSourceEntry": entry["sourceEntry"],
                    "meaningSourcePage": entry["sourcePage"],
                    "meaningLicense": entry.get("license", self.reviewed_meaning_source["license"]),
                    "meaningMatchedExamples": [word],
                })
                break
        return result

    def apply_reviewed_override(self, result, override, morph):
        result.update({
            "category": override["category"],
            "confidence": "reviewed",
            "roots": [self.reviewed_root(root) for root in override.get("roots", [])],
            "prefixes": override.get("prefixes", []),
            "suffixes": override.get("suffixes", []),
            "needsReview": False,
            "reviewNote": override["note"],
            "sources": override.get("sources", ["Reviewed lexical analysis"]),
        })
        if morph:
            result.update({
                "segmentation": morph["segmentation"],
                "signature": morph["signature"],
                "parseComplete": morph["parseComplete"],
            })
        return self.apply_reviewed_root_meanings(result["word"], result)

    def curated_root_info(self, word, root_id):
        root = self.roots_by_id[root_id]
        form = next((form for form in sorted(root["forms"], key=len, reverse=True) if form in word), root["forms"][0])
        return self.root_info(form, root_id)

    @staticmethod
    @lru_cache(maxsize=None)
    def split_parts(text, parts, maximum=3):
        if not text:
            return ()
        if maximum == 0:
            return None
        for part in parts:
            if text.startswith(part):
                rest = Analyzer.split_parts(text[len(part):], parts, maximum - 1)
                if rest is not None:
                    return (part,) + rest
        return None

    def compound_candidate(self, word):
        for split in range(2, len(word) - 1):
            left, right = word[:split], word[split:]
            if left in self.free_roots and right in self.free_roots:
                return [left, right]
        return None

    def rule_candidates(self, word):
        candidates = []
        for form, root_ids in self.form_index.items():
            if len(form) < 3:
                continue
            start = word.find(form)
            while start >= 0:
                left = self.split_parts(word[:start], self.prefixes)
                right = self.split_parts(word[start + len(form):], self.suffixes)
                complete = left is not None and right is not None
                candidates.append({
                    "form": form,
                    "rootIds": root_ids,
                    "start": start,
                    "prefixes": list(left or ()),
                    "suffixes": list(right or ()),
                    "complete": complete,
                    "score": (complete, len(form), -start),
                })
                start = word.find(form, start + 1)
        candidates.sort(key=lambda item: item["score"], reverse=True)
        return candidates

    def analyze(self, raw_word):
        word = raw_word.strip().lower()
        if not WORD_RE.fullmatch(word):
            return {
                "word": raw_word,
                "category": "invalid",
                "confidence": "none",
                "roots": [],
                "prefixes": [],
                "suffixes": [],
                "needsReview": True,
                "reason": "Only one ASCII alphabetic word is supported",
            }
        exam = self.exam_words.get(word)
        lemma = self.lemmas.get(word)
        analysis_word = lemma or word
        curated_ids = self.root_data["examples"].get(analysis_word, [])
        morph = self.morph["words"].get(analysis_word)
        result = {
            "word": word,
            "lemma": lemma,
            "exams": exam["exams"] if exam else [],
            "translation": exam["translation"] if exam else "",
            "frequency": {"bnc": exam["bnc"], "frq": exam["frq"]} if exam else None,
            "roots": [],
            "prefixes": [],
            "suffixes": [],
            "needsReview": False,
            "sources": [],
        }
        if word in self.reviewed_words:
            return self.apply_reviewed_override(result, self.reviewed_words[word], morph)
        if morph:
            parse_complete = morph["parseComplete"]
            result.update({
                "category": "compound" if len(morph["roots"]) > 1 else ("single-root" if not morph["prefixes"] and not morph["suffixes"] else "derived"),
                "confidence": "database" if parse_complete else "database-partial",
                "roots": [self.root_info(form, preferred_ids=curated_ids) for form in morph["roots"]],
                "prefixes": morph["prefixes"],
                "suffixes": morph["suffixes"],
                "segmentation": morph["segmentation"],
                "signature": morph["signature"],
                "parseComplete": parse_complete,
                "needsReview": not parse_complete,
                "sources": ["MorphoLex-EN"] + (["ECDICT lemma"] if lemma else []),
            })
            if not parse_complete:
                result["reason"] = "MorphoLex PRS signature and parsed morpheme counts disagree; manual review required"
            if not morph["roots"]:
                expected_roots = int(morph["signature"].split(",")[1])
                result["category"] = "no-root-in-database" if expected_roots == 0 else "needs-review"
            ambiguous_forms = [root["form"] for root in result["roots"] if root["ambiguous"]]
            if ambiguous_forms:
                if parse_complete:
                    result["confidence"] = "ambiguous-root"
                result["needsReview"] = True
                result["reason"] = "Root form has multiple RootLearner meanings and no curated example disambiguates it: " + ", ".join(ambiguous_forms)
            if curated_ids:
                result["sources"].append("RootLearner curated example")
                matched = any(root["rootLearnerId"] in curated_ids for root in result["roots"])
                if matched:
                    if parse_complete and not ambiguous_forms:
                        result["confidence"] = "curated+database"
                else:
                    result["confidence"] = "conflict"
                    result["needsReview"] = True
                    result["curatedRoots"] = [self.curated_root_info(analysis_word, root_id) for root_id in curated_ids]
                    result["reason"] = "Curated example and MorphoLex segmentation disagree"
            return self.apply_reviewed_root_meanings(word, result)
        if curated_ids:
            result.update({
                "category": "root-derived",
                "confidence": "curated",
                "roots": [self.curated_root_info(analysis_word, root_id) for root_id in curated_ids],
                "sources": ["RootLearner curated example"] + (["ECDICT lemma"] if lemma else []),
            })
            return result
        compound = self.compound_candidate(analysis_word)
        if compound:
            result.update({
                "category": "compound-candidate",
                "confidence": "rule-medium",
                "roots": [self.root_info(form) for form in compound],
                "needsReview": True,
                "sources": ["MorphoLex free-root inventory"] + (["ECDICT lemma"] if lemma else []),
                "reason": "Compound boundary inferred from two database lexical roots; review required",
            })
            return result
        candidates = self.rule_candidates(analysis_word)
        if candidates:
            best = candidates[0]
            confidence = "rule-medium" if best["complete"] else "rule-low"
            result.update({
                "category": "derived-candidate" if best["complete"] else "needs-review",
                "confidence": confidence,
                "roots": [self.root_info(best["form"])],
                "prefixes": best["prefixes"],
                "suffixes": best["suffixes"],
                "needsReview": True,
                "sources": ["RootLearner form matching", "MorphoLex affix inventory"] + (["ECDICT lemma"] if lemma else []),
                "reason": "String-boundary rule only; etymology not verified",
                "alternativeCandidateCount": len(candidates) - 1,
            })
            return result
        result.update({
            "category": "unresolved",
            "confidence": "none",
            "needsReview": True,
            "sources": [],
            "reason": "No database entry or safe rule candidate; this does not prove the word has no root",
        })
        return result


def choose_sample(exam_data, size):
    lists = {}
    for exam in EXAMS:
        words = [item for item in exam_data["words"] if exam in item["exams"]]
        words.sort(key=lambda item: (hashlib.sha256(f"{exam}:{item['word']}".encode()).hexdigest(), item["word"]))
        lists[exam] = iter(words)
    selected = []
    seen = set()
    while len(selected) < size:
        added = False
        for exam in EXAMS:
            for item in lists[exam]:
                if item["word"] not in seen:
                    selected.append(item)
                    seen.add(item["word"])
                    added = True
                    break
            if len(selected) >= size:
                break
        if not added:
            break
    if len(selected) != size:
        raise ValueError(f"Only {len(selected)} unique words available, requested {size}")
    return selected


def percentage(count, total):
    return round(count * 100 / total, 1) if total else 0


def generate_sample(analyzer, size):
    sample = choose_sample(analyzer.exam_data, size)
    results = []
    for item in sample:
        result = analyzer.analyze(item["word"])
        result["sampleExams"] = item["exams"]
        results.append(result)
    confidence = Counter(item["confidence"] for item in results)
    categories = Counter(item["category"] for item in results)
    reliable_items = [item for item in results if item["confidence"] in {"database", "curated", "curated+database"} and item["roots"]]
    reusable_items = [item for item in reliable_items if item["category"] in {"derived", "compound", "root-derived"} or any(root["rootLearnerId"] for root in item["roots"])]
    rule_candidates = sum(item["confidence"].startswith("rule-") for item in results)
    unresolved = sum(item["category"] == "unresolved" for item in results)
    conflicts = sum(item["confidence"] == "conflict" for item in results)
    with_meaning = sum(any(root["meaningEn"] for root in item["roots"]) for item in results)
    new_root_forms = sorted({root["form"] for item in reusable_items for root in item["roots"] if not root["meaningEn"]})
    summary = {
        "sampleSize": len(results),
        "selection": "Deterministic SHA-256 random ordering; round-robin unique selection from " + "/".join(EXAMS),
        "examMembership": {exam: sum(exam in item["exams"] for item in results) for exam in EXAMS},
        "confidenceCounts": dict(sorted(confidence.items())),
        "categoryCounts": dict(sorted(categories.items())),
        "databaseRootSegmented": len(reliable_items),
        "databaseCoveragePercent": percentage(len(reliable_items), len(results)),
        "databaseCoverageWarning": "MorphoLex treats an unsegmented lexical item as a root; database coverage is not reusable-root coverage",
        "reusableRootCandidates": len(reusable_items),
        "reusableRootCandidatePercent": percentage(len(reusable_items), len(results)),
        "singleRootLexemes": categories["single-root"],
        "singleRootLexemePercent": percentage(categories["single-root"], len(results)),
        "ruleCandidates": rule_candidates,
        "ruleCandidatePercent": percentage(rule_candidates, len(results)),
        "unresolved": unresolved,
        "unresolvedPercent": percentage(unresolved, len(results)),
        "unresolvedWarning": "Unresolved means not identified by this prototype, not etymologically rootless",
        "curatedConflicts": conflicts,
        "withRootLearnerMeaning": with_meaning,
        "newRootCurationNeeded": sum(not any(root["meaningEn"] for root in item["roots"]) for item in reusable_items),
        "newRootFormsNeedingMeanings": len(new_root_forms),
        "needsReview": sum(item["needsReview"] for item in results),
    }
    write_json(OUTPUT / f"sample-{size}.json", {
        "summary": summary,
        "licenses": {
            "ECDICT": "MIT",
            "MorphoLex-EN and derived segmentations": "CC BY-NC-SA 4.0; non-commercial use; share adaptations under the same license",
        },
        "results": results,
    })
    write_json(OUTPUT / "summary.json", summary)
    with (OUTPUT / f"sample-{size}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["word", "lemma", "exams", "roots", "meaningEn", "prefixes", "suffixes", "category", "confidence", "needsReview", "translation"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in results:
            writer.writerow({
                "word": item["word"],
                "lemma": item["lemma"] or "",
                "exams": " ".join(item["exams"]),
                "roots": " ".join(root["form"] for root in item["roots"]),
                "meaningEn": " | ".join(root["meaningEn"] or "" for root in item["roots"]),
                "prefixes": " ".join(item["prefixes"]),
                "suffixes": " ".join(item["suffixes"]),
                "category": item["category"],
                "confidence": item["confidence"],
                "needsReview": str(item["needsReview"]).lower(),
                "translation": item["translation"].replace("\n", " / "),
            })
    lines = [
        "词根分析隔离原型：样本报告",
        f"样本：{len(results)} 个不重复单词；各考试标签可重叠。",
        "抽样：按 SHA-256 确定性随机排序，从 " + "/".join(EXAMS) + " 轮流抽取未选单词。",
        "",
        f"MorphoLex 有词根切分：{len(reliable_items)}/{len(results)} ({percentage(len(reliable_items), len(results))}%)",
        "注意：数据库把未再切分的独立词也记为一个词根，所以上项不是可复用词根覆盖率。",
        f"派生/复合或能衔接现有词根表的候选：{len(reusable_items)}/{len(results)} ({percentage(len(reusable_items), len(results))}%)",
        f"单根独立词（不等于无根词）：{categories['single-root']}/{len(results)} ({percentage(categories['single-root'], len(results))}%)",
        f"规则候选（必须复核）：{rule_candidates}/{len(results)} ({percentage(rule_candidates, len(results))}%)",
        f"未识别（不等于无根词）：{unresolved}/{len(results)} ({percentage(unresolved, len(results))}%)",
        f"现有 RootLearner 词根释义可直接衔接：{with_meaning}/{len(results)}",
        f"需要补释义的新根形：{summary['newRootFormsNeedingMeanings']} 种",
        f"需要人工复核：{summary['needsReview']}/{len(results)}",
        f"现有例词与 MorphoLex 冲突：{conflicts}",
        "",
        "置信度：" + json.dumps(summary["confidenceCounts"], ensure_ascii=False),
        "分类：" + json.dumps(summary["categoryCounts"], ensure_ascii=False),
        "考试标签：" + json.dumps(summary["examMembership"], ensure_ascii=False),
        "",
        "许可：ECDICT 为 MIT；MorphoLex 及其派生切分数据为 CC BY-NC-SA 4.0，仅限非商业使用，改编数据须同许可共享并署名。",
        "详细结果见 sample-300.json；便于表格检查的版本见 sample-300.csv。",
    ]
    (OUTPUT / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Offline root analysis prototype using ECDICT and MorphoLex")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--vocab", type=Path, default=DEFAULT_VOCAB)
    sample_parser = subparsers.add_parser("sample")
    sample_parser.add_argument("--size", type=int, default=300)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("words", nargs="+")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.vocab.resolve())
        return
    analyzer = Analyzer()
    if args.command == "sample":
        generate_sample(analyzer, args.size)
    elif args.command == "analyze":
        results = [analyzer.analyze(word) for word in args.words]
        print(json.dumps(results[0] if len(results) == 1 else results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
