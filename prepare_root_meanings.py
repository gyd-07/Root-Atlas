import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from generate_exam import partition_results
from root_analyzer import Analyzer, DATA, EXAMS, RAW, WORD_RE, load_json, write_json

WIKI_RAW = RAW / "wikipedia-roots"
WIKI_BASE = "https://en.wikipedia.org/wiki/List_of_Greek_and_Latin_roots_in_English/"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVXZ"
ADDITIONAL_FREE_FORMS = {
    "analog",
    "archive",
    "aviate",
    "borne",
    "burse",
    "catastrophe",
    "cognize",
    "contaminant",
    "contain",
    "elect",
    "evitable",
    "fitting",
    "frequence",
    "galvanize",
    "gravitate",
    "history",
    "incandesce",
    "ion",
    "jeopard",
    "journal",
    "loco",
    "magister",
    "palatable",
    "path",
    "pollinate",
    "reck",
    "rigor",
    "semble",
    "skeptic",
    "substantiate",
    "true",
    "urban",
    "venge",
    "virus",
    "whelm",
}


def clean_text(value):
    value = re.sub(r"<!--.*?-->", "", value)
    value = re.sub(r"<ref\b[^>]*/>", "", value)
    value = re.sub(r"<ref\b[^>]*>.*?</ref>", "", value)
    value = re.sub(r"<br\s*/?>", ", ", value, flags=re.I)
    previous = None
    while previous != value:
        previous = value
        value = re.sub(r"\[\[([^\[\]]+)\]\]", lambda match: match.group(1).split("|")[-1], value)
        value = re.sub(r"\{\{([^{}]+)\}\}", lambda match: match.group(1).split("|")[-1], value)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip(" ,\n")


def normalize_root(value):
    value = re.sub(r"\([^)]*\)", "", value).strip().lower().strip("-–— ")
    return value if WORD_RE.fullmatch(value) else None


def parse_wikipedia_page(letter, wikitext):
    entries = []
    for line in wikitext.splitlines():
        if not line.startswith("|") or line.startswith("|-") or line.startswith("|}") or "||" not in line:
            continue
        cells = [cell.strip() for cell in line[1:].split("||")]
        if len(cells) < 5:
            continue
        raw_forms = clean_text(cells[0])
        forms = {normalize_root(part) for part in raw_forms.split(",")}
        forms.discard(None)
        if not forms:
            continue
        meaning = clean_text(cells[1])
        if not meaning:
            continue
        examples_text = clean_text(cells[4])
        entry = {
            "forms": sorted(forms),
            "meaningEn": meaning,
            "originLanguage": clean_text(cells[2]),
            "etymology": clean_text(cells[3]),
            "examples": examples_text,
            "exampleWords": sorted(set(re.findall(r"[a-z]+", examples_text.lower()))),
            "sourceEntry": raw_forms,
            "sourcePage": f"{WIKI_BASE}{letter}",
            "source": "Wikipedia: List of Greek and Latin roots in English",
            "license": "CC BY-SA 4.0",
        }
        for form in sorted(forms):
            entries.append((form, entry))
    return entries


def download_wikipedia(proxy=None, delay=3.0):
    WIKI_RAW.mkdir(parents=True, exist_ok=True)
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    opener = urllib.request.build_opener(*handlers)
    for letter in LETTERS:
        path = WIKI_RAW / f"{letter}.json"
        if path.is_file():
            print(f"Kept existing Wikipedia roots {letter}")
            continue
        page = f"List of Greek and Latin roots in English/{letter}"
        params = urllib.parse.urlencode({"action": "parse", "format": "json", "formatversion": "2", "page": page, "prop": "wikitext"})
        request = urllib.request.Request(
            "https://en.wikipedia.org/w/api.php?" + params,
            headers={"User-Agent": "RootLearnerResearch/1.0 (educational offline prototype)"},
        )
        with opener.open(request, timeout=45) as response:
            payload = json.load(response)
        if "error" in payload:
            raise RuntimeError(f"Wikipedia {letter}: {payload['error']}")
        document = {
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "sourceApi": "https://en.wikipedia.org/w/api.php",
            "sourcePage": f"{WIKI_BASE}{letter}",
            "license": "CC BY-SA 4.0",
            "response": payload,
        }
        write_json(path, document)
        print(f"Downloaded Wikipedia roots {letter}")
        time.sleep(delay)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_wikipedia():
    roots = {}
    row_count = 0
    raw_hashes = {}
    for letter in LETTERS:
        path = WIKI_RAW / f"{letter}.json"
        document = load_json(path)
        raw_hashes[f"{letter}.json"] = sha256(path)
        entries = parse_wikipedia_page(letter, document["response"]["parse"]["wikitext"])
        row_count += len({id(entry) for _, entry in entries})
        for form, entry in entries:
            candidates = roots.setdefault(form, [])
            if not any(old == entry for old in candidates):
                candidates.append(entry)
    for candidates in roots.values():
        candidates.sort(key=lambda item: (item["meaningEn"], item["sourceEntry"], item["sourcePage"]))
    return roots, row_count, raw_hashes


def prepare_free_definitions():
    morph = load_json(DATA / "morpholex.json")
    free_roots = {
        word for word, entry in morph["words"].items()
        if entry["parseComplete"] and entry["roots"] == [word] and not entry["prefixes"] and not entry["suffixes"]
    }
    definitions = {}
    with (RAW / "ecdict.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            form = row["word"].strip().lower()
            definition = row["definition"].strip().replace("\\n", "\n")
            if len(form) < 2 or (form not in free_roots and form not in ADDITIONAL_FREE_FORMS) or not definition:
                continue
            definitions[form] = {
                "meaningEn": definition,
                "meaningKind": "free-root lexical definition",
                "source": "ECDICT ecdict.csv",
                "sourceEntry": form,
                "sourcePage": "https://github.com/skywind3000/ECDICT",
                "license": "MIT",
            }
    return definitions


def prepare_exam_root_families():
    analyzer = Analyzer()
    families = {}
    for exam in EXAMS:
        source_words = [item["word"] for item in analyzer.exam_data["words"] if exam in item["exams"]]
        results = [analyzer.analyze(word) for word in source_words]
        grouped, _, _ = partition_results(results)
        for item in grouped:
            for root in item["roots"]:
                if not root["meaningEn"]:
                    values = families.setdefault(root["form"], set())
                    values.add(item["word"])
                    if item["lemma"]:
                        values.add(item["lemma"])
    return {form: sorted(words) for form, words in sorted(families.items())}


def prepare():
    wikipedia, row_count, raw_hashes = prepare_wikipedia()
    free_definitions = prepare_free_definitions()
    exam_root_families = prepare_exam_root_families()
    result = {
        "sources": {
            "Wikipedia Greek and Latin roots": {
                "index": "https://en.wikipedia.org/wiki/List_of_Greek_and_Latin_roots_in_English",
                "license": "CC BY-SA 4.0",
                "attribution": "Wikipedia contributors, List of Greek and Latin roots in English",
                "rawSha256": raw_hashes,
            },
            "ECDICT": {
                "url": "https://github.com/skywind3000/ECDICT",
                "license": "MIT",
                "usage": "English definitions for forms attested as free roots in MorphoLex, plus explicitly reviewed standalone forms in ADDITIONAL_FREE_FORMS",
            },
        },
        "summary": {
            "wikipediaRows": row_count,
            "wikipediaRootForms": len(wikipedia),
            "wikipediaHomographForms": sum(len({candidate["meaningEn"] for candidate in candidates}) > 1 for candidates in wikipedia.values()),
            "freeRootDefinitions": len(free_definitions),
            "examRootFamilies": len(exam_root_families),
        },
        "wikipediaRoots": dict(sorted(wikipedia.items())),
        "freeRootDefinitions": dict(sorted(free_definitions.items())),
        "examRootFamilies": exam_root_families,
    }
    write_json(DATA / "root_meanings.json", result)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Prepare sourced English meanings for root forms")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--proxy")
    parser.add_argument("--delay", type=float, default=3.0)
    args = parser.parse_args()
    if args.download:
        download_wikipedia(args.proxy, args.delay)
    prepare()
