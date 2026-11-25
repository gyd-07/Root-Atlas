import argparse
import csv
import json
import sys
from collections import Counter

from root_analyzer import Analyzer, DATA, EXAMS, OUTPUT, load_json, percentage, write_json

RELIABLE_CONFIDENCE = {"database", "curated", "curated+database", "reviewed"}
MIXED_ETYMOLOGY_FORMS = {
    "relig": "Religion has disputed historical derivations through religare 'bind' and relegere 'read again'; do not select one automatically",
}
ROOT_FORM_ALIASES = {
    "accur": "cur",
    "applicate": "plic",
    "authent": "aut",
    "bacteri": "bac",
    "brevi": "brev",
    "calcul": "calc",
    "chrono": "chron",
    "cognit": "gnosc",
    "compan": "pan",
    "cosmo": "cosm",
    "deleg": "leg",
    "devi": "vi",
    "formul": "form",
    "herit": "her",
    "hesit": "hes",
    "hiero": "hier",
    "litera": "liter",
    "mascul": "mas",
    "myst": "my",
    "neuro": "neur",
    "nucleo": "nuc",
    "orchestr": "orches",
    "ortho": "orth",
    "pacif": "pac",
    "phenomen": "phen",
    "philo": "phil",
    "phys": "physi",
    "plode": "plod",
    "pneum": "pne",
    "pole": "pol",
    "propag": "pact",
    "proto": "prot",
    "prud": "vid",
    "qualit": "qual",
    "redund": "und",
    "sanct": "sanc",
    "satis": "sati",
    "semin": "ser",
    "senti": "sent",
    "separ": "par",
    "simultane": "simul",
    "socio": "soci",
    "spectr": "spect",
    "specul": "spec",
    "sperse": "spers",
    "stitute": "stitu",
    "sume": "sum",
    "summar": "sum",
    "suspici": "spec",
    "ten": "tent",
    "theor": "theori",
    "thermo": "therm",
    "turbul": "turb",
    "toxico": "tox",
    "typo": "typ",
    "tyran": "tyrann",
    "util": "ut",
    "vacu": "vac",
    "vene": "ven",
    "veri": "ver",
    "versy": "vers",
    "vey": "vid",
    "volunt": "vol",
    "volve": "volv",
    "antho": "anth",
    "archaeo": "archae",
    "aristo": "arist",
    "bene": "ben",
    "biblio": "bibl",
    "conting": "ting",
    "dino": "din",
    "electro": "electr",
    "hetero": "heter",
    "horti": "hort",
    "pharma": "pharmac",
    "phylle": "phyll",
    "retic": "tic",
    "sanit": "san",
    "seism": "sei",
    "sono": "son",
    "theo": "the",
    "topo": "top",
    "trude": "trud",
    "visco": "visc",
}
LICENSES = {
    "ECDICT": "MIT",
    "MorphoLex-EN and derived segmentations": "CC BY-NC-SA 4.0; non-commercial use; share adaptations under the same license",
    "Wikipedia Greek and Latin root glosses": "CC BY-SA 4.0; Wikipedia contributors; source page stored per entry; share adaptations of those glosses under the same license",
    "Wiktionary English etymology": "CC BY-SA 4.0; Wiktionary contributors; source page stored per reviewed entry; share adaptations under the same license",
}


def is_reusable(item):
    return item["category"] in {"derived", "compound", "root-derived"} or any(root["rootLearnerId"] for root in item["roots"])


def supplement_root_meanings(grouped_items, glossary):
    occurrences = {}
    for item in grouped_items:
        for root in item["roots"]:
            if not root["meaningEn"]:
                occurrences.setdefault(root["form"], []).append((item, root))
    audit = {}
    for form, pairs in sorted(occurrences.items()):
        words = set(glossary["examRootFamilies"].get(form, []))
        candidates = list(glossary["wikipediaRoots"].get(form, []))
        if form in ROOT_FORM_ALIASES:
            candidates.extend(glossary["wikipediaRoots"].get(ROOT_FORM_ALIASES[form], []))
        meanings = sorted({candidate["meaningEn"] for candidate in candidates})
        entry = None
        matched_examples = []
        reason = ""
        if form in MIXED_ETYMOLOGY_FORMS:
            reason = MIXED_ETYMOLOGY_FORMS[form]
        else:
            matching = [candidate for candidate in candidates if words & set(candidate["exampleWords"])]
            matching_meanings = sorted({candidate["meaningEn"] for candidate in matching})
            if len(matching_meanings) == 1:
                entry = matching[0]
                matched_examples = sorted(words & set(entry["exampleWords"]))
            elif len(matching_meanings) > 1:
                reason = "Multiple sourced meanings match this word family; manual disambiguation required"
            else:
                entry = glossary["freeRootDefinitions"].get(form)
                if entry is None:
                    if candidates:
                        reason = "Sourced root forms exist, but their examples do not safely identify this word family"
                    else:
                        reason = "No exact sourced root gloss or free-root definition"
        if entry is not None:
            for _, root in pairs:
                root.update({
                    "meaningEn": entry["meaningEn"],
                    "meaningKind": entry.get("meaningKind", "etymological root gloss"),
                    "meaningSource": entry["source"],
                    "meaningSourceEntry": entry["sourceEntry"],
                    "meaningSourcePage": entry["sourcePage"],
                    "meaningLicense": entry["license"],
                })
        audit[form] = {
            "status": "filled" if entry is not None else "needs-review",
            "meaningEn": entry["meaningEn"] if entry is not None else "",
            "meaningSource": entry["source"] if entry is not None else "",
            "meaningSourcePage": entry["sourcePage"] if entry is not None else "",
            "matchedExamples": matched_examples,
            "candidateMeanings": meanings,
            "reason": reason,
        }
    return audit


def partition_results(results):
    grouped = []
    independent = []
    review = []
    for item in results:
        if item["needsReview"] or item["confidence"] not in RELIABLE_CONFIDENCE:
            review.append(item)
        elif item["roots"] and is_reusable(item):
            grouped.append(item)
        else:
            independent.append(item)
    return grouped, independent, review


def demote_unresolved_singletons(grouped_items, independent_items, glossary):
    kept = []
    for item in grouped_items:
        unresolved = [root for root in item["roots"] if not root["meaningEn"]]
        singleton_only = unresolved and all(len(glossary["examRootFamilies"].get(root["form"], [])) <= 1 for root in unresolved)
        if not any(root["meaningEn"] for root in item["roots"]) and singleton_only:
            item["category"] = "independent-reviewed"
            item["confidence"] = "reviewed"
            item["reviewNote"] = "No sourced English root gloss and no reusable exam word family; retained as an independent lexical item"
            independent_items.append(item)
        else:
            kept.append(item)
    grouped_items[:] = kept


def build_groups(grouped_items):
    groups = {}
    for item in grouped_items:
        word = {
            "word": item["word"],
            "lemma": item["lemma"],
            "exams": item["exams"],
            "translation": item["translation"],
            "prefixes": item["prefixes"],
            "suffixes": item["suffixes"],
            "segmentation": item.get("segmentation"),
            "confidence": item["confidence"],
        }
        for root in item["roots"]:
            key = (root["form"], root["rootLearnerId"], root["meaningEn"], root.get("meaningSourceEntry", ""))
            if key not in groups:
                groups[key] = {
                    "form": root["form"],
                    "meaningEn": root["meaningEn"],
                    "meaningKind": root.get("meaningKind", "RootLearner curated gloss" if root["rootLearnerId"] else ""),
                    "meaningSource": root.get("meaningSource", "RootLearner" if root["rootLearnerId"] else ""),
                    "meaningSourceEntry": root.get("meaningSourceEntry", ""),
                    "meaningSourcePage": root.get("meaningSourcePage", ""),
                    "meaningLicense": root.get("meaningLicense", ""),
                    "rootLearnerId": root["rootLearnerId"],
                    "matchedForm": root["matchedForm"],
                    "reviewedMatchedExamples": [],
                    "words": [],
                }
            groups[key]["words"].append(word)
            for example in root.get("meaningMatchedExamples", []):
                if example not in groups[key]["reviewedMatchedExamples"]:
                    groups[key]["reviewedMatchedExamples"].append(example)
    result = sorted(groups.values(), key=lambda group: (group["form"], group["rootLearnerId"] or 0, group["meaningEn"] or ""))
    for group in result:
        group["words"].sort(key=lambda item: item["word"])
        group["wordCount"] = len(group["words"])
    return result


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def flat_word_row(item):
    return {
        "word": item["word"],
        "lemma": item["lemma"] or "",
        "exams": " ".join(item["exams"]),
        "roots": " ".join(root["form"] for root in item["roots"]),
        "meaningEn": " | ".join((root["meaningEn"] or "").replace("\n", " / ") for root in item["roots"]),
        "meaningSource": " | ".join(root.get("meaningSource", "RootLearner" if root["rootLearnerId"] else "") for root in item["roots"]),
        "prefixes": " ".join(item["prefixes"]),
        "suffixes": " ".join(item["suffixes"]),
        "category": item["category"],
        "confidence": item["confidence"],
        "needsReview": str(item["needsReview"]).lower(),
        "reason": item.get("reason", ""),
        "translation": item["translation"].replace("\n", " / "),
    }


def generate_exam(exam):
    if exam not in EXAMS:
        raise ValueError(f"Unsupported exam: {exam}")
    prefix = exam.lower()
    analyzer = Analyzer()
    source_words = [item for item in analyzer.exam_data["words"] if exam in item["exams"]]
    results = [analyzer.analyze(item["word"]) for item in source_words]
    grouped, independent, review = partition_results(results)
    glossary = load_json(DATA / "root_meanings.json")
    meaning_audit = supplement_root_meanings(grouped, glossary)
    demote_unresolved_singletons(grouped, independent, glossary)
    active_forms = {root["form"] for item in grouped for root in item["roots"]}
    unresolved_forms = {root["form"] for item in grouped for root in item["roots"] if not root["meaningEn"]}
    meaning_audit = {
        form: audit for form, audit in meaning_audit.items()
        if form in active_forms and (audit["status"] == "filled" or form in unresolved_forms)
    }
    groups = build_groups(grouped)
    output = OUTPUT / prefix
    confidence = Counter(item["confidence"] for item in results)
    categories = Counter(item["category"] for item in results)
    reliable = [item for item in results if item["confidence"] in RELIABLE_CONFIDENCE and item["roots"]]
    new_root_groups = [group for group in groups if not group["meaningEn"]]
    supplemented_groups = [group for group in groups if group["meaningSource"] not in {"", "RootLearner"}]
    supplemented_sources = Counter(group["meaningSource"] for group in supplemented_groups)
    multi_word_groups = [group for group in groups if group["wordCount"] > 1]
    summary = {
        "exam": exam,
        "sourceTagCount": analyzer.exam_data["rawTagCounts"][exam],
        "totalWords": len(results),
        "uniqueWords": len({item["word"] for item in results}),
        "selection": f"All ECDICT entries tagged {prefix}; no sampling",
        "examMembership": {exam: sum(exam in item["exams"] for item in results) for exam in EXAMS},
        "confidenceCounts": dict(sorted(confidence.items())),
        "categoryCounts": dict(sorted(categories.items())),
        "databaseRootSegmented": len(reliable),
        "databaseCoveragePercent": percentage(len(reliable), len(results)),
        "databaseCoverageWarning": "Database coverage includes single-root lexical items and is not reusable-root coverage",
        "rootGroupedWords": len(grouped),
        "rootGroupedPercent": percentage(len(grouped), len(results)),
        "rootGroups": len(groups),
        "multiWordRootGroups": len(multi_word_groups),
        "singletonRootGroups": len(groups) - len(multi_word_groups),
        "wordsInMultiWordGroups": len({item["word"] for group in multi_word_groups for item in group["words"]}),
        "rootGroupMemberships": sum(group["wordCount"] for group in groups),
        "independentWords": len(independent),
        "independentWordPercent": percentage(len(independent), len(results)),
        "reviewWords": len(review),
        "reviewPercent": percentage(len(review), len(results)),
        "curatedConflicts": confidence["conflict"],
        "ambiguousRoots": confidence["ambiguous-root"],
        "partialDatabaseEntries": confidence["database-partial"],
        "ruleCandidates": sum(count for name, count in confidence.items() if name.startswith("rule-")),
        "unresolved": categories["unresolved"],
        "groupedWordsWithRootLearnerMeaning": sum(any(root["rootLearnerId"] for root in item["roots"]) for item in grouped),
        "groupedWordsWithEnglishMeaning": sum(any(root["meaningEn"] for root in item["roots"]) for item in grouped),
        "supplementedRootForms": len(supplemented_groups),
        "supplementedRootFormsBySource": dict(sorted(supplemented_sources.items())),
        "newRootFormsNeedingMeanings": len(new_root_groups),
        "rootMeaningReviewReasons": dict(sorted(Counter(item["reason"] for item in meaning_audit.values() if item["status"] == "needs-review").items())),
        "partitionCheck": len(grouped) + len(independent) + len(review) == len(results),
    }
    if not summary["partitionCheck"] or summary["totalWords"] != summary["sourceTagCount"]:
        raise ValueError(f"{exam} output does not account for every source entry")

    write_json(output / f"{prefix}-full.json", {"summary": summary, "licenses": LICENSES, "rootMeaningAudit": meaning_audit, "results": results})
    write_json(output / f"{prefix}-root-groups.json", {
        "summary": {"rootGroups": len(groups), "groupedWords": len(grouped), "memberships": summary["rootGroupMemberships"]},
        "licenses": LICENSES,
        "groups": groups,
    })
    write_json(output / "summary.json", summary)

    fields = ["word", "lemma", "exams", "roots", "meaningEn", "meaningSource", "prefixes", "suffixes", "category", "confidence", "needsReview", "reason", "translation"]
    write_csv(output / f"{prefix}-full.csv", fields, [flat_word_row(item) for item in results])
    group_rows = []
    for group in groups:
        for item in group["words"]:
            group_rows.append({
                "rootForm": group["form"],
                "meaningEn": (group["meaningEn"] or "").replace("\n", " / "),
                "meaningKind": group["meaningKind"],
                "meaningSource": group["meaningSource"],
                "meaningSourceEntry": group["meaningSourceEntry"],
                "meaningSourcePage": group["meaningSourcePage"],
                "rootLearnerId": group["rootLearnerId"] or "",
                "word": item["word"],
                "exams": " ".join(item["exams"]),
                "prefixes": " ".join(item["prefixes"]),
                "suffixes": " ".join(item["suffixes"]),
                "segmentation": item["segmentation"] or "",
                "confidence": item["confidence"],
                "translation": item["translation"].replace("\n", " / "),
            })
    write_csv(output / f"{prefix}-root-groups.csv", ["rootForm", "meaningEn", "meaningKind", "meaningSource", "meaningSourceEntry", "meaningSourcePage", "rootLearnerId", "word", "exams", "prefixes", "suffixes", "segmentation", "confidence", "translation"], group_rows)
    write_csv(output / f"{prefix}-independent.csv", ["word", "rootForm", "exams", "translation"], [{
        "word": item["word"],
        "rootForm": " ".join(root["form"] for root in item["roots"]),
        "exams": " ".join(item["exams"]),
        "translation": item["translation"].replace("\n", " / "),
    } for item in independent])
    review_rows = []
    for item in review:
        row = flat_word_row(item)
        row["curatedRoots"] = " | ".join(f"{root['form']}={root['meaningEn']}" for root in item.get("curatedRoots", []))
        row["ambiguousRootIds"] = " | ".join(",".join(map(str, root["candidateRootLearnerIds"])) for root in item["roots"] if root["ambiguous"])
        review_rows.append(row)
    write_csv(output / f"{prefix}-review.csv", fields + ["curatedRoots", "ambiguousRootIds"], review_rows)
    write_csv(output / f"{prefix}-new-roots.csv", ["rootForm", "wordCount", "examples", "reviewReason", "candidateMeanings"], [{
        "rootForm": group["form"],
        "wordCount": group["wordCount"],
        "examples": " ".join(item["word"] for item in group["words"][:12]),
        "reviewReason": meaning_audit[group["form"]]["reason"],
        "candidateMeanings": " | ".join(meaning_audit[group["form"]]["candidateMeanings"]),
    } for group in new_root_groups])
    write_csv(output / f"{prefix}-supplemented-roots.csv", ["rootForm", "meaningEn", "meaningKind", "meaningSource", "meaningSourceEntry", "meaningSourcePage", "matchedExamples", "examples"], [{
        "rootForm": group["form"],
        "meaningEn": group["meaningEn"].replace("\n", " / "),
        "meaningKind": group["meaningKind"],
        "meaningSource": group["meaningSource"],
        "meaningSourceEntry": group["meaningSourceEntry"],
        "meaningSourcePage": group["meaningSourcePage"],
        "matchedExamples": " ".join(group["reviewedMatchedExamples"] or meaning_audit.get(group["form"], {}).get("matchedExamples", [])),
        "examples": " ".join(item["word"] for item in group["words"][:12]),
    } for group in supplemented_groups])

    exam_name = {"CET4": "四级", "CET6": "六级", "IELTS": "雅思", "TOEFL": "托福"}[exam]
    lines = [
        f"{exam} {exam_name}词根完整自动整理版",
        f"来源：ECDICT 全部 {prefix} 标签，共 {len(results)} 个词条；无抽样、无遗漏。",
        "",
        f"数据库或现有审核例词可靠覆盖：{len(reliable)}/{len(results)} ({percentage(len(reliable), len(results))}%)",
        f"按可复用词根分组：{len(grouped)}/{len(results)} ({percentage(len(grouped), len(results))}%)，{len(groups)} 个词根组。",
        f"其中含至少 2 词的分组：{len(multi_word_groups)} 个，覆盖 {summary['wordsInMultiWordGroups']} 词；仅 1 词的分组：{len(groups) - len(multi_word_groups)} 个。",
        f"独立或未自动归根词汇项：{len(independent)}/{len(results)} ({percentage(len(independent), len(results))}%)，不强行归根。",
        f"剩余自动切分/归属复核队列：{len(review)}/{len(results)} ({percentage(len(review), len(results))}%)。",
        f"现有 RootLearner 释义可直接用于分组词：{summary['groupedWordsWithRootLearnerMeaning']}/{len(grouped)}。",
        f"本次从外部来源补充英文释义的词根组：{len(supplemented_groups)} 个。",
        "补释义来源：" + json.dumps(summary["supplementedRootFormsBySource"], ensure_ascii=False),
        f"仍未补英文释义的词根组：{len(new_root_groups)} 个。",
        "",
        "复核构成：" + json.dumps({name: count for name, count in sorted(confidence.items()) if name not in RELIABLE_CONFIDENCE}, ensure_ascii=False),
        f"完整逐词表：{prefix}-full.csv；按词根分组表：{prefix}-root-groups.csv。",
        f"独立词：{prefix}-independent.csv；复核项：{prefix}-review.csv；待补根形：{prefix}-new-roots.csv。",
        f"已补释义及逐条来源：{prefix}-supplemented-roots.csv。",
        "注意：自动复核队列为空不等于全部词源已经人工审定；独立词汇项也不等于词源上无根。",
        "许可：ECDICT 为 MIT；MorphoLex 及派生切分数据为 CC BY-NC-SA 4.0，仅限非商业使用并须署名、同许可共享；Wikipedia 与 Wiktionary 释义为 CC BY-SA 4.0，逐条来源页已保存在表内。",
    ]
    (output / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return summary


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Generate a complete root analysis for one exam")
    parser.add_argument("--exam", choices=EXAMS, required=True)
    args = parser.parse_args()
    generate_exam(args.exam)
