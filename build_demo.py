from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "output"
DESTINATION = BASE / "demo" / "index.html"
EXAMS = ("CET4", "CET6", "IELTS", "TOEFL")
PHONETICS = json.loads((BASE / "data" / "phonetics.json").read_text(encoding="utf-8"))["words"]


def phonetic(word):
    value = PHONETICS.get(word, "").strip()
    if not value:
        raise ValueError(f"Missing phonetic transcription: {word}")
    return value


def load_exam(exam):
    slug = exam.lower()
    directory = OUTPUT / slug
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    document = json.loads((directory / f"{slug}-root-groups.json").read_text(encoding="utf-8"))
    if not summary["partitionCheck"] or summary["reviewWords"] or summary["newRootFormsNeedingMeanings"]:
        raise ValueError(f"{exam} has not passed the final output checks")
    groups = []
    for group in document["groups"]:
        if not group["meaningEn"]:
            raise ValueError(f"{exam} contains an empty root meaning: {group['form']}")
        groups.append({
            "form": group["form"],
            "meaning": group["meaningEn"],
            "kind": group["meaningKind"],
            "source": group["meaningSource"],
            "sourceEntry": group["meaningSourceEntry"],
            "sourcePage": group["meaningSourcePage"],
            "license": group["meaningLicense"],
            "rootLearnerId": group["rootLearnerId"],
            "words": [{
                "w": word["word"],
                "t": word["translation"],
                "ph": phonetic(word["word"]),
                "p": word["prefixes"],
                "s": word["suffixes"],
                "l": word["lemma"],
                "c": word["confidence"],
            } for word in group["words"]],
        })
    with (directory / f"{slug}-independent.csv").open(encoding="utf-8-sig", newline="") as stream:
        independent = [{"w": row["word"], "t": row["translation"], "ph": phonetic(row["word"])} for row in csv.DictReader(stream)]
    if len(groups) != summary["rootGroups"] or len(independent) != summary["independentWords"]:
        raise ValueError(f"{exam} demo data does not match its summary")
    return {"summary": summary, "groups": groups, "independent": independent}


def build():
    data = {
        "generated": date.today().isoformat(),
        "exams": {exam: load_exam(exam) for exam in EXAMS},
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    page = PAGE.replace("/*__DEMO_DATA__*/null", payload)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(page, encoding="utf-8")
    print(f"Built {DESTINATION} ({DESTINATION.stat().st_size / 1024 / 1024:.1f} MiB)")
    for exam in EXAMS:
        item = data["exams"][exam]
        print(f"{exam}: {len(item['groups'])} root groups, {len(item['independent'])} independent words")


PAGE = r'''<!doctype html>
<html lang="zh-CN" data-theme="elegant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>Root Atlas · 四考试词根图谱</title>
<style>
:root{--paper:#f4f2ec;--card:#fffefa;--ink:#18352d;--muted:#6b7771;--line:#dedfd7;--green:#173f35;--green-2:#285c4c;--accent:#dd714d;--accent-soft:#f8e8df;--sage:#e5ece5;--shadow:0 14px 40px rgba(24,53,45,.07);--radius:18px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}button,input,select{font:inherit}button{color:inherit}button,a{-webkit-tap-highlight-color:transparent}a{color:inherit}.shell{width:min(1180px,calc(100% - 40px));margin:0 auto}.topbar{height:76px;display:flex;align-items:center;justify-content:space-between}.brand{display:flex;align-items:center;gap:12px;font-weight:700;letter-spacing:.02em}.brand-mark{width:36px;height:36px;border-radius:11px;background:var(--green);display:grid;place-items:center;color:#fff}.brand-mark svg{width:23px;height:23px}.brand small{display:block;font-size:10px;line-height:1.1;color:var(--muted);font-weight:600;letter-spacing:.16em;text-transform:uppercase}.text-button{border:0;background:transparent;padding:8px 0;color:var(--green-2);font-size:14px;font-weight:600;cursor:pointer}.text-button:hover{text-decoration:underline;text-underline-offset:4px}.hero{background:var(--green);color:#fff;border-radius:26px;padding:52px 56px;display:grid;grid-template-columns:1.25fr .75fr;gap:48px;position:relative;overflow:hidden}.hero:before{content:"";position:absolute;width:420px;height:420px;border:1px solid rgba(255,255,255,.09);border-radius:50%;right:-110px;top:-200px;box-shadow:0 0 0 70px rgba(255,255,255,.025),0 0 0 140px rgba(255,255,255,.02)}.eyebrow{margin:0 0 14px;color:#b8cfc3;font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}.hero h1{font-family:Georgia,"Songti SC",serif;font-weight:500;font-size:clamp(32px,4vw,50px);line-height:1.22;letter-spacing:-.025em;margin:0 0 18px;max-width:610px}.hero-copy{margin:0;color:#cedbd5;max-width:590px;font-size:15px}.hero-note{display:flex;align-items:center;gap:8px;margin-top:26px;color:#a9c2b5;font-size:12px}.status-dot{width:7px;height:7px;border-radius:50%;background:#e8a685;box-shadow:0 0 0 4px rgba(232,166,133,.12)}.specimen{align-self:center;position:relative;z-index:1;background:#f8f4e9;color:var(--ink);padding:26px;border-radius:4px 22px 4px 22px;transform:rotate(1.5deg);box-shadow:0 24px 50px rgba(0,0,0,.18)}.specimen-label{font-size:10px;color:#7c827a;letter-spacing:.16em;text-transform:uppercase}.specimen-root{display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid #d8d5c9;padding:8px 0 14px;margin-bottom:12px}.specimen-root strong{font-family:Georgia,serif;font-size:46px;font-weight:500;line-height:1}.specimen-root span{font-size:13px;color:#57665f}.specimen-words{display:flex;flex-wrap:wrap;gap:8px}.specimen-words span{font-size:12px;padding:4px 9px;border:1px solid #d4d8cd;border-radius:20px}.specimen-caption{font-size:11px;color:#7c827a;margin:14px 0 0}.exam-wrap{position:relative;z-index:2;margin-top:-1px;padding:18px 0 0}.exam-tabs{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.exam-tab{border:1px solid var(--line);background:rgba(255,254,250,.7);border-radius:14px;padding:14px 18px;text-align:left;cursor:pointer;transition:.18s ease}.exam-tab:hover{background:var(--card);border-color:#b8c3ba}.exam-tab[aria-selected="true"]{background:var(--card);border-color:var(--green-2);box-shadow:var(--shadow)}.exam-tab strong{display:block;font-size:15px;letter-spacing:.04em}.exam-tab span{display:block;color:var(--muted);font-size:12px;margin-top:2px}.exam-tab[aria-selected="true"] strong{color:var(--green-2)}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin:28px 0 34px;background:var(--line);border:1px solid var(--line);border-radius:14px;overflow:hidden}.stat{background:var(--paper);padding:18px 22px}.stat strong{display:block;font-family:Georgia,serif;font-size:28px;font-weight:500;line-height:1.2}.stat span{font-size:12px;color:var(--muted)}.workspace{background:var(--card);border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:28px}.workspace-head{padding:26px 28px 0}.view-row{display:flex;align-items:center;justify-content:space-between;gap:20px}.view-tabs{display:flex;gap:26px}.view-tab{border:0;background:transparent;padding:0 0 16px;cursor:pointer;color:var(--muted);font-size:15px;font-weight:600;position:relative}.view-tab[aria-selected="true"]{color:var(--ink)}.view-tab[aria-selected="true"]:after{content:"";height:3px;border-radius:2px;background:var(--accent);position:absolute;left:0;right:0;bottom:0}.data-note{font-size:11px;color:var(--muted);padding-bottom:16px}.search-box{display:flex;align-items:center;gap:12px;background:#f5f5f0;border:1px solid #e2e4dc;border-radius:13px;padding:0 15px;margin-top:20px;transition:.15s}.search-box:focus-within{border-color:var(--green-2);box-shadow:0 0 0 3px rgba(40,92,76,.08);background:#fff}.search-box svg{width:19px;height:19px;color:#758079;flex:none}.search-box input{width:100%;border:0;outline:0;background:transparent;padding:14px 0;color:var(--ink);min-width:0}.search-box input::placeholder{color:#919a94}.key-hint{border:1px solid #d6dad2;border-radius:5px;color:#87918a;font-size:11px;line-height:20px;width:22px;text-align:center;flex:none}.clear-search{display:none;border:0;background:transparent;color:var(--muted);cursor:pointer;padding:5px}.clear-search.visible{display:block}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:16px 0 20px}.filters{display:flex;gap:7px;flex-wrap:wrap}.filter{border:1px solid transparent;background:transparent;border-radius:20px;padding:6px 12px;color:var(--muted);font-size:12px;cursor:pointer}.filter:hover{background:#f2f3ed}.filter.active{background:var(--sage);color:var(--green-2);font-weight:600}.sort-wrap{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:12px;flex:none}.sort-wrap select{border:0;background:transparent;color:var(--ink);outline:0;cursor:pointer;padding:5px 0}.results-head{display:flex;justify-content:space-between;gap:20px;padding:15px 28px;background:#f7f7f2;border-top:1px solid #eceee7;border-bottom:1px solid #e7e9e2;font-size:12px;color:var(--muted)}.results-head strong{color:var(--ink);font-weight:600}.root-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;padding:20px 28px 28px}.root-card{border:1px solid var(--line);border-radius:15px;background:#fff;min-width:0;transition:border-color .15s,box-shadow .15s;height:max-content}.root-card:hover{border-color:#b9c6bc;box-shadow:0 8px 22px rgba(24,53,45,.05)}.root-card.is-open{grid-column:1/-1;border-color:#9db4a6}.group-summary{display:block;width:100%;border:0;background:transparent;text-align:left;padding:21px 22px 17px;cursor:pointer;border-radius:15px}.root-top{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.root-identity{display:flex;align-items:baseline;gap:10px;min-width:0}.root-form{font-family:Georgia,"Times New Roman",serif;font-size:32px;line-height:1.05;font-weight:500;letter-spacing:-.02em;overflow-wrap:anywhere}.homograph{font-size:10px;color:var(--accent);border:1px solid #edcfc1;padding:1px 6px;border-radius:10px;white-space:nowrap}.word-count{font-size:11px;color:var(--muted);background:#f1f3ed;border-radius:20px;padding:3px 9px;white-space:nowrap}.root-meaning{color:#455d54;font-size:14px;margin:11px 0 13px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}.badges{display:flex;gap:6px;flex-wrap:wrap}.badge{display:inline-flex;align-items:center;border-radius:5px;padding:2px 7px;background:var(--sage);color:#3d6456;font-size:10px;line-height:1.7}.badge.warm{background:var(--accent-soft);color:#9a4d33}.badge.neutral{background:#f0f0eb;color:#707a73}.word-preview{display:flex;gap:6px;flex-wrap:wrap;margin-top:16px}.word-preview span{font-size:12px;color:#56675f}.word-preview span:not(:last-child):after{content:"·";color:#bdc4bd;margin-left:6px}.card-footer{display:flex;justify-content:space-between;gap:12px;align-items:center;border-top:1px solid #eff0eb;margin-top:16px;padding-top:12px;font-size:10px;color:#89918b}.expand-label{color:var(--green-2);font-size:11px;font-weight:600}.group-detail{border-top:1px solid var(--line);padding:22px;background:#fbfcf8;border-radius:0 0 15px 15px}.detail-meaning{display:grid;grid-template-columns:120px 1fr;gap:20px;margin-bottom:16px}.detail-label{font-size:11px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;padding-top:3px}.detail-meaning p{margin:0;font-size:13px;white-space:pre-line;overflow-wrap:anywhere}.source-detail{display:grid;grid-template-columns:120px 1fr;gap:20px;padding-bottom:20px;border-bottom:1px solid #e4e8df;font-size:12px}.source-detail p{margin:0;color:#52645c}.source-detail a{display:inline-block;margin-top:6px;color:var(--green-2);font-weight:600;text-underline-offset:3px}.detail-words-title{font-size:11px;color:var(--muted);margin:20px 0 10px;letter-spacing:.08em;text-transform:uppercase}.detail-word{display:grid;grid-template-columns:minmax(130px,.65fr) minmax(210px,1fr) minmax(240px,1.6fr);gap:20px;padding:15px 0;border-top:1px solid #eceee7;align-items:start}.detail-word:first-of-type{border-top:0}.detail-word-name{font-size:15px;font-weight:650;overflow-wrap:anywhere}.lemma{display:block;color:var(--muted);font-size:10px;font-weight:400;margin-top:3px}.assembly{display:flex;align-items:center;gap:5px;flex-wrap:wrap;font-family:"Segoe UI",sans-serif;font-size:12px}.morpheme{background:#eef1eb;border-radius:5px;padding:2px 6px;color:#5a6a62}.morpheme.root{background:#dfeee5;color:#1f5b46;font-weight:700}.morpheme.current{outline:1px solid #7da58f}.plus{color:#9ca79f}.translation{font-size:12px;color:#5d6963;white-space:pre-line;margin:0;overflow-wrap:anywhere}.reviewed-tag{font-size:9px;color:#9b563c;display:block;margin-top:4px}.word-list{padding:0 28px 20px}.word-row{display:grid;grid-template-columns:minmax(160px,.65fr) minmax(280px,1.8fr) minmax(150px,.8fr);gap:24px;align-items:start;padding:20px 0;border-bottom:1px solid #eceee7}.word-row h3{font-family:Georgia,"Times New Roman",serif;font-size:23px;font-weight:500;margin:0;overflow-wrap:anywhere}.word-row .translation{padding-top:3px}.word-roots{display:flex;justify-content:flex-end;gap:6px;flex-wrap:wrap}.root-link{border:1px solid #cdd9cf;background:#f3f7f1;border-radius:7px;color:#32614f;font-size:11px;padding:4px 9px;cursor:pointer}.root-link:hover{background:#e3eee4;border-color:#9cb6a4}.independent-label{font-size:11px;color:var(--muted);background:#f1f1ec;padding:4px 9px;border-radius:7px}.load-wrap{padding:0 28px 28px;text-align:center}.load-more{border:1px solid #b9c8bc;background:#fff;color:var(--green-2);border-radius:10px;padding:10px 22px;font-size:13px;font-weight:600;cursor:pointer}.load-more:hover{background:#f0f5ef}.empty{text-align:center;padding:70px 24px;color:var(--muted)}.empty strong{display:block;color:var(--ink);font-family:Georgia,"Songti SC",serif;font-size:24px;font-weight:500;margin-bottom:8px}.empty p{font-size:13px;margin:0}.footer{display:flex;justify-content:space-between;gap:24px;padding:4px 0 40px;color:var(--muted);font-size:11px}.footer p{margin:0;max-width:780px}.footer button{flex:none;font-size:11px}.dialog{border:0;border-radius:20px;padding:0;width:min(620px,calc(100% - 32px));color:var(--ink);box-shadow:0 30px 90px rgba(0,0,0,.25)}.dialog::backdrop{background:rgba(15,36,30,.55);backdrop-filter:blur(3px)}.dialog-inner{padding:30px}.dialog-head{display:flex;justify-content:space-between;align-items:start;gap:20px}.dialog h2{font-family:Georgia,"Songti SC",serif;font-weight:500;font-size:26px;margin:0}.dialog-close{border:0;background:#eef0e9;border-radius:50%;width:32px;height:32px;cursor:pointer;font-size:20px;line-height:1}.dialog h3{font-size:13px;margin:22px 0 6px}.dialog p,.dialog li{font-size:12px;color:#5b6962}.dialog ul{padding-left:20px}.dialog .warning{background:#f7eee6;border-radius:10px;padding:12px 14px;color:#81503a}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}button:focus-visible,a:focus-visible,select:focus-visible{outline:3px solid rgba(221,113,77,.35);outline-offset:3px}
.header-actions{display:flex;align-items:center;gap:22px}.theme-picker{display:flex;align-items:center;gap:3px;padding:3px;background:#e9ebe4;border-radius:10px}.theme-picker>span{font-size:10px;color:var(--muted);padding:0 7px}.theme-choice{border:0;background:transparent;border-radius:7px;padding:5px 10px;font-size:11px;color:var(--muted);cursor:pointer;white-space:nowrap}.theme-choice:hover{color:var(--ink)}.theme-choice[aria-pressed="true"]{background:var(--card);color:var(--ink);font-weight:700;box-shadow:0 1px 5px rgba(24,53,45,.09)}body,.hero,.workspace,.root-card,.exam-tab{transition:background-color .2s,color .2s,border-color .2s,box-shadow .2s}
html[data-theme="minimal"]{--paper:#fafaf8;--card:#ffffff;--ink:#242927;--muted:#747b77;--line:#e3e6e2;--green:#29312e;--green-2:#476158;--accent:#4f7569;--accent-soft:#edf2ef;--sage:#edf1ee;--shadow:none;--radius:10px}html[data-theme="minimal"] .topbar{border-bottom:1px solid var(--line);margin-bottom:34px}html[data-theme="minimal"] .brand-mark{border-radius:5px;background:var(--ink)}html[data-theme="minimal"] .hero{background:transparent;color:var(--ink);border-radius:0;border-bottom:1px solid var(--line);padding:34px 0 38px;grid-template-columns:1fr;overflow:visible}html[data-theme="minimal"] .hero:before,html[data-theme="minimal"] .specimen{display:none}html[data-theme="minimal"] .hero h1{font-family:"Segoe UI","PingFang SC",sans-serif;font-size:42px;font-weight:550;letter-spacing:-.045em;max-width:760px}html[data-theme="minimal"] .hero h1 br{display:none}html[data-theme="minimal"] .eyebrow,html[data-theme="minimal"] .hero-note{color:var(--muted)}html[data-theme="minimal"] .hero-copy{color:#66716b;max-width:680px}html[data-theme="minimal"] .status-dot{background:var(--green-2);box-shadow:none}html[data-theme="minimal"] .exam-wrap{padding-top:22px}html[data-theme="minimal"] .exam-tabs{gap:0;border-bottom:1px solid var(--line)}html[data-theme="minimal"] .exam-tab,html[data-theme="minimal"] .exam-tab[aria-selected="true"]{border:0;border-bottom:2px solid transparent;border-radius:0;background:transparent;box-shadow:none;padding:12px 16px}html[data-theme="minimal"] .exam-tab[aria-selected="true"]{border-bottom-color:var(--ink)}html[data-theme="minimal"] .stats{border:0;background:transparent;gap:20px;margin:26px 0}html[data-theme="minimal"] .stat{background:transparent;padding:4px 16px;border-left:1px solid var(--line)}html[data-theme="minimal"] .stat strong{font-family:"Segoe UI",sans-serif;font-size:26px;font-weight:550}html[data-theme="minimal"] .workspace{border:0;background:transparent;box-shadow:none;border-radius:0}html[data-theme="minimal"] .workspace-head{background:var(--card);border:1px solid var(--line);border-radius:12px 12px 0 0}html[data-theme="minimal"] .results-head{border:1px solid var(--line);border-top:0}html[data-theme="minimal"] .root-grid{padding:18px 0;gap:10px}html[data-theme="minimal"] .root-card,html[data-theme="minimal"] .root-card:hover,html[data-theme="minimal"] .root-card.is-open{border:1px solid var(--line);border-radius:9px;box-shadow:none}html[data-theme="minimal"] .group-summary{border-radius:8px}html[data-theme="minimal"] .group-detail{border-radius:0 0 8px 8px}html[data-theme="minimal"] .root-form{font-family:"Segoe UI",sans-serif;font-size:27px;font-weight:600;letter-spacing:-.035em}html[data-theme="minimal"] .word-list{padding:0;background:var(--card);border:1px solid var(--line);border-top:0}html[data-theme="minimal"] .word-row{margin:0 24px}html[data-theme="minimal"] .load-wrap{padding-top:4px}html[data-theme="minimal"] .load-more{border-color:var(--line);border-radius:7px}html[data-theme="minimal"] .filter.active{background:#e9eeeb;color:var(--ink)}html[data-theme="minimal"] .view-tab[aria-selected="true"]:after{background:var(--ink);height:2px}
html[data-theme="classical"]{--paper:#f0e7d4;--card:#fffaf0;--ink:#3c2d24;--muted:#7d6d5d;--line:#d5c3a2;--green:#59372f;--green-2:#774a3d;--accent:#a07035;--accent-soft:#efe0c4;--sage:#e9ddc6;--shadow:0 12px 30px rgba(76,53,33,.08);--radius:4px}html[data-theme="classical"] body{font-family:Georgia,"Songti SC","SimSun",serif;background-image:radial-gradient(rgba(112,82,45,.045) .7px,transparent .7px);background-size:7px 7px}html[data-theme="classical"] .brand-mark{border-radius:2px;background:#59372f}html[data-theme="classical"] .hero{background:#57382f;border:1px solid #a78a5c;outline:1px solid rgba(235,213,167,.32);outline-offset:-8px;border-radius:3px;box-shadow:0 15px 35px rgba(69,44,30,.16)}html[data-theme="classical"] .hero:before{border-color:rgba(235,213,167,.12);box-shadow:0 0 0 70px rgba(235,213,167,.025),0 0 0 140px rgba(235,213,167,.018)}html[data-theme="classical"] .hero h1{font-family:Georgia,"Songti SC","SimSun",serif;letter-spacing:.02em}html[data-theme="classical"] .eyebrow{color:#d7bd8c}html[data-theme="classical"] .hero-copy{color:#e2d4bd}html[data-theme="classical"] .hero-note{color:#cbb894}html[data-theme="classical"] .status-dot{background:#d3ac64;box-shadow:none}html[data-theme="classical"] .specimen{background:#f6edda;border:1px solid #b99d6d;border-radius:2px;transform:rotate(0);box-shadow:7px 8px 0 rgba(32,19,13,.22)}html[data-theme="classical"] .specimen-root strong{color:#6b382e}html[data-theme="classical"] .exam-tab,html[data-theme="classical"] .exam-tab[aria-selected="true"]{border-radius:2px;background:#f7efdf;border-color:#cdb992;box-shadow:none}html[data-theme="classical"] .exam-tab[aria-selected="true"]{background:#fff9ec;border-color:#7d5739;box-shadow:inset 0 0 0 2px #fff9ec,inset 0 0 0 3px #b69b6d}html[data-theme="classical"] .stats{border-color:#cbb792;background:#cbb792}html[data-theme="classical"] .stat{background:rgba(255,250,240,.45)}html[data-theme="classical"] .stat strong{color:#6d3f32}html[data-theme="classical"] .workspace{border:3px double #a88c60;border-radius:3px;box-shadow:var(--shadow)}html[data-theme="classical"] .results-head{background:#f2e8d5;border-color:#dac8a8}html[data-theme="classical"] .root-card,html[data-theme="classical"] .root-card.is-open{border-radius:2px;border-color:#cdbb9d;box-shadow:none}html[data-theme="classical"] .root-card:hover{border-color:#967c55;box-shadow:3px 4px 0 #e6dac3}html[data-theme="classical"] .group-summary{border-radius:1px}html[data-theme="classical"] .group-detail{background:#f8f0e0;border-radius:0;border-color:#d5c3a2}html[data-theme="classical"] .root-form{color:#6e3b30;font-size:34px}html[data-theme="classical"] .root-meaning{color:#665448}html[data-theme="classical"] .word-count,html[data-theme="classical"] .badge,html[data-theme="classical"] .morpheme,html[data-theme="classical"] .independent-label{border-radius:2px}html[data-theme="classical"] .filter.active{background:#e4d5b8;color:#673f30}html[data-theme="classical"] .search-box{background:#faf3e5;border-color:#d7c5a5;border-radius:3px}html[data-theme="classical"] .load-more,html[data-theme="classical"] .root-link,html[data-theme="classical"] .dialog{border-radius:3px}html[data-theme="classical"] .view-tab[aria-selected="true"]:after{background:#9c6a32;height:2px}
html[data-theme="joyful"]{--paper:#fff6e6;--card:#fffefd;--ink:#263f49;--muted:#687980;--line:#e7d8c5;--green:#11656a;--green-2:#11656a;--accent:#ef7355;--accent-soft:#ffe3d9;--sage:#dff2e6;--shadow:0 6px 0 #e7d6bf;--radius:20px}html[data-theme="joyful"] body{background-image:radial-gradient(#ecd9bb 1px,transparent 1px);background-size:24px 24px}html[data-theme="joyful"] .brand-mark{background:#f47d61;color:#263f49;border:2px solid #263f49;border-radius:12px;transform:rotate(-5deg)}html[data-theme="joyful"] .hero{background:#ffcf67;color:#263f49;border:2px solid #263f49;border-radius:28px;box-shadow:0 8px 0 #263f49}html[data-theme="joyful"] .hero:before{border-color:rgba(38,63,73,.13);box-shadow:0 0 0 70px rgba(255,255,255,.12),0 0 0 140px rgba(255,255,255,.09)}html[data-theme="joyful"] .hero h1{font-family:"Trebuchet MS","PingFang SC",sans-serif;font-weight:800;letter-spacing:-.045em}html[data-theme="joyful"] .eyebrow{color:#72542a}html[data-theme="joyful"] .hero-copy{color:#4b5960}html[data-theme="joyful"] .hero-note{color:#5a584d}html[data-theme="joyful"] .status-dot{background:#e95f48;box-shadow:0 0 0 4px rgba(233,95,72,.15)}html[data-theme="joyful"] .specimen{background:#fff;border:2px solid #263f49;border-radius:24px 8px 24px 8px;transform:rotate(2deg);box-shadow:7px 7px 0 #263f49}html[data-theme="joyful"] .specimen-root strong{font-family:"Trebuchet MS",sans-serif;font-weight:800;color:#e86147}html[data-theme="joyful"] .specimen-words span{border-color:#9fb7b4;border-radius:12px}html[data-theme="joyful"] .exam-wrap{padding-top:26px}html[data-theme="joyful"] .exam-tabs{gap:12px}html[data-theme="joyful"] .exam-tab{border:2px solid #263f49;border-radius:16px;background:#fff;box-shadow:0 3px 0 #d5c3aa}html[data-theme="joyful"] .exam-tab:nth-child(1){background:#ffe5d9}html[data-theme="joyful"] .exam-tab:nth-child(2){background:#e1f1e5}html[data-theme="joyful"] .exam-tab:nth-child(3){background:#e5edff}html[data-theme="joyful"] .exam-tab:nth-child(4){background:#fff0b9}html[data-theme="joyful"] .exam-tab:hover{border-color:#263f49;background:#fff;transform:translateY(-2px)}html[data-theme="joyful"] .exam-tab[aria-selected="true"]{border:2px solid #263f49;box-shadow:0 5px 0 #263f49;transform:translateY(-2px)}html[data-theme="joyful"] .exam-tab[aria-selected="true"] strong{color:#263f49}html[data-theme="joyful"] .stats{background:transparent;border:0;gap:12px;overflow:visible}html[data-theme="joyful"] .stat{background:#fff;border:2px solid #263f49;border-radius:16px}html[data-theme="joyful"] .stat:nth-child(2){background:#e3f3e7}html[data-theme="joyful"] .stat:nth-child(3){background:#e8efff}html[data-theme="joyful"] .stat:nth-child(4){background:#ffe8dd}html[data-theme="joyful"] .stat strong{font-family:"Trebuchet MS",sans-serif;font-weight:800}html[data-theme="joyful"] .workspace{border:2px solid #263f49;border-radius:24px;box-shadow:0 6px 0 #d9c4a7}html[data-theme="joyful"] .search-box{background:#fff;border:2px solid #b9c8c4;border-radius:14px}html[data-theme="joyful"] .results-head{background:#fff3d8;border-color:#e6d5bc}html[data-theme="joyful"] .root-card{border:2px solid #263f49;border-radius:19px;box-shadow:0 3px 0 #dbc8ae}html[data-theme="joyful"] .root-card:nth-child(4n+1){background:#fff1e8}html[data-theme="joyful"] .root-card:nth-child(4n+2){background:#eff8ef}html[data-theme="joyful"] .root-card:nth-child(4n+3){background:#f0f3ff}html[data-theme="joyful"] .root-card:nth-child(4n+4){background:#fff9df}html[data-theme="joyful"] .root-card:hover{border-color:#263f49;box-shadow:0 6px 0 #dbc8ae;transform:translateY(-2px)}html[data-theme="joyful"] .root-card.is-open{border-color:#263f49;box-shadow:0 5px 0 #263f49;transform:none}html[data-theme="joyful"] .group-summary{border-radius:17px}html[data-theme="joyful"] .group-detail{background:#fff;border-radius:0 0 17px 17px;border-top:2px solid #263f49}html[data-theme="joyful"] .root-form{font-family:"Trebuchet MS",sans-serif;font-weight:800;color:#145f65}html[data-theme="joyful"] .word-count{background:#fff;border:1px solid #c9d3cf;border-radius:12px}html[data-theme="joyful"] .badge{border-radius:9px}html[data-theme="joyful"] .filter.active{background:#ffcf67;color:#263f49}html[data-theme="joyful"] .view-tab[aria-selected="true"]:after{height:4px;background:#ef7355}html[data-theme="joyful"] .word-row h3{font-family:"Trebuchet MS",sans-serif;font-weight:800;color:#145f65}html[data-theme="joyful"] .root-link{border:2px solid #9fb7b4;background:#e3f3e7;border-radius:10px;color:#244d51}html[data-theme="joyful"] .load-more{border:2px solid #263f49;border-radius:12px;background:#ffcf67;color:#263f49;box-shadow:0 3px 0 #263f49}html[data-theme="joyful"] .morpheme.root{background:#ffdc72;color:#263f49}
.detail-phonetic,.word-phonetic{display:block;margin-top:4px;color:var(--muted);font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:12px;font-weight:400;line-height:1.5;letter-spacing:.01em;overflow-wrap:anywhere}.word-phonetic{font-size:13px}
@media(max-width:900px){.hero{padding:40px;grid-template-columns:1fr}.specimen{display:none}.stats{grid-template-columns:repeat(2,1fr)}.detail-word{grid-template-columns:130px 1fr}.detail-word .translation{grid-column:1/-1}.word-row{grid-template-columns:150px 1fr}.word-roots{grid-column:1/-1;justify-content:flex-start}.data-note{display:none}.theme-picker>span{display:none}.header-actions{gap:12px}html[data-theme="minimal"] .hero{padding:32px 0}}
@media(max-width:640px){.shell{width:min(100% - 24px,1180px)}.topbar{height:64px}.hero{padding:30px 24px;border-radius:20px}.hero h1{font-size:32px}.hero-copy{font-size:13px}.exam-tabs{gap:6px}.exam-tab{padding:11px 10px}.exam-tab strong{font-size:12px}.exam-tab span{font-size:10px}.stats{margin:20px 0}.stat{padding:14px 16px}.stat strong{font-size:24px}.workspace-head{padding:20px 18px 0}.view-tabs{gap:20px}.view-tab{font-size:14px}.search-box{margin-top:16px}.key-hint{display:none}.toolbar{align-items:flex-start;padding-bottom:16px}.sort-wrap span{display:none}.filters{gap:3px}.filter{padding:5px 8px}.results-head{padding:13px 18px}.root-grid{grid-template-columns:1fr;padding:14px 14px 20px;gap:10px}.root-card.is-open{grid-column:auto}.group-summary{padding:18px}.root-form{font-size:29px}.group-detail{padding:18px}.detail-meaning,.source-detail{grid-template-columns:1fr;gap:5px}.detail-word{grid-template-columns:1fr;gap:8px;padding:14px 0}.detail-word .translation{grid-column:auto}.word-list{padding:0 18px 16px}.word-row{grid-template-columns:1fr;gap:8px;padding:17px 0}.word-row .translation{padding-top:0}.word-roots{grid-column:auto}.footer{display:block;padding:0 4px 28px}.footer button{margin-top:12px}.dialog-inner{padding:24px}.results-head span:last-child{display:none}}
@media(max-width:640px){.topbar{height:auto;min-height:64px;flex-wrap:wrap;padding:12px 0;gap:12px}.header-actions{width:100%;justify-content:space-between;gap:10px}.theme-picker{flex:1;justify-content:space-between}.theme-choice{flex:1;padding:5px 7px}.about-button{font-size:11px;white-space:nowrap}html[data-theme="minimal"] .topbar{margin-bottom:20px}html[data-theme="minimal"] .hero{padding:24px 0 28px}html[data-theme="minimal"] .hero h1{font-size:31px}html[data-theme="minimal"] .exam-tab,html[data-theme="minimal"] .exam-tab[aria-selected="true"]{padding:10px 7px}html[data-theme="minimal"] .stats{gap:8px}html[data-theme="minimal"] .stat{padding:6px 10px}html[data-theme="joyful"] .exam-tabs{gap:7px}html[data-theme="joyful"] .exam-tab{padding:10px 6px}html[data-theme="joyful"] .stats{gap:7px}html[data-theme="joyful"] .stat{padding:12px 10px}html[data-theme="classical"] .hero{outline-offset:-6px}}
</style>
</head>
<body>
<div class="shell">
<header class="topbar">
  <div class="brand"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 20V9M12 13 6 7M12 11l6-6M6 7V3M6 7H2M18 5V2M18 5h4"/></svg></span><span>Root Atlas<small>Vocabulary, connected</small></span></div>
  <div class="header-actions"><div class="theme-picker" role="group" aria-label="版面风格"><span>版面</span><button class="theme-choice" data-theme-choice="minimal" aria-pressed="false">简约</button><button class="theme-choice" data-theme-choice="classical" aria-pressed="false">古典</button><button class="theme-choice" data-theme-choice="elegant" aria-pressed="true">优雅</button><button class="theme-choice" data-theme-choice="joyful" aria-pressed="false">欢乐</button></div><button class="text-button about-button" data-action="about">数据与许可</button></div>
</header>
<section class="hero">
  <div><p class="eyebrow">四考试词根图谱 · 离线研究演示</p><h1>从一个词根，<br>看见一整片词族。</h1><p class="hero-copy">汇集四级、六级、雅思与托福的完整分析结果。搜索一个单词，或从一个词根出发，查看构词结构、中文释义与英文词根来源。</p><div class="hero-note"><span class="status-dot"></span>研究预览 · 自动分析与逐项复核结合 · 非最终人工审定版</div></div>
  <div class="specimen" aria-hidden="true"><span class="specimen-label">Root specimen / 089</span><div class="specimen-root"><strong>dict</strong><span>to say, to assert</span></div><div class="specimen-words"><span>predict</span><span>diction</span><span>dictate</span><span>contradict</span></div><p class="specimen-caption">一个核心，多种表达。点击下方的真实词族即可展开。</p></div>
</section>
<nav class="exam-wrap" aria-label="选择考试"><div class="exam-tabs" id="examTabs" role="tablist"></div></nav>
<section class="stats" aria-label="当前考试统计">
  <div class="stat"><strong id="statWords">—</strong><span>考试词条</span></div>
  <div class="stat"><strong id="statGroups">—</strong><span>词根词族</span></div>
  <div class="stat"><strong id="statGrouped">—</strong><span>按词根分组的单词</span></div>
  <div class="stat"><strong id="statIndependent">—</strong><span>独立或未自动归根词</span></div>
</section>
<main class="workspace">
  <div class="workspace-head">
    <div class="view-row"><div class="view-tabs" role="tablist" aria-label="浏览模式"><button class="view-tab" role="tab" data-view="roots" aria-selected="true">词根词族</button><button class="view-tab" role="tab" data-view="words" aria-selected="false">全部单词</button></div><span class="data-note">全部单词均有音标与英文释义 · 复核队列 0</span></div>
    <label class="search-box" for="searchInput"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg><input id="searchInput" type="search" autocomplete="off" spellcheck="false" placeholder="搜索词根、英文释义或单词，例如 dict / predict"><button class="clear-search" id="clearSearch" aria-label="清空搜索">×</button><span class="key-hint" aria-hidden="true">/</span></label>
    <div class="toolbar" id="toolbar"><div class="filters" aria-label="词族筛选"><button class="filter active" data-filter="all">全部词族</button><button class="filter" data-filter="multi">多词词族</button><button class="filter" data-filter="learner">RootLearner 已衔接</button><button class="filter" data-filter="external">外部补释义</button></div><label class="sort-wrap"><span>排序</span><select id="sortSelect"><option value="size">词族规模</option><option value="alpha">字母顺序</option></select></label></div>
  </div>
  <div class="results-head"><strong id="resultTitle"></strong><span id="resultMeta" aria-live="polite"></span><span>点击词族查看构词与来源</span></div>
  <div id="results"></div>
  <div class="load-wrap" id="loadWrap" hidden><button class="load-more" id="loadMore">加载更多</button></div>
</main>
<footer class="footer"><p>释义类型严格区分“词源词根释义”和“自由词现代词典释义”。“独立词汇项”不等于词源上无根；“复核队列 0”也不等于全部词源判断已经人工审定。</p><button class="text-button" data-action="about">查看数据来源与许可</button></footer>
</div>
<dialog class="dialog" id="aboutDialog"><div class="dialog-inner"><div class="dialog-head"><h2>数据、许可与阅读方式</h2><button class="dialog-close" id="closeDialog" aria-label="关闭">×</button></div><p class="warning">这是基于现有分析产物制作的独立浏览 demo，尚未接入 RootLearner 主项目，也不应直接替换主词库。</p><h3>数据来源</h3><ul><li>ECDICT（MIT）：考试标签、中文翻译、自由词英文词典释义和大部分音标。</li><li>CMUdict（BSD）：构建时经 eng_to_ipa 0.0.2 转换为 IPA，补齐缺失或格式异常的音标；其余 16 个词条逐项补充。音标全部静态嵌入，页面运行时不访问网络。</li><li>MorphoLex-EN（CC BY-NC-SA 4.0）：英文构词切分；仅限非商业使用，派生内容须同许可共享。</li><li>RootLearner：现有 342 个词根组的释义与审核例词，只读衔接。</li><li>Wikipedia 希腊语和拉丁语词根表（CC BY-SA 4.0）：部分词源释义。</li><li>Wiktionary 英文词源（CC BY-SA 4.0）：逐词族复核释义。</li></ul><h3>如何理解页面</h3><p>词族卡片展示当前分组所使用的英文释义。ECDICT 的“自由词词典释义”是现代词汇定义，不是古典词源本义。带外部链接的释义可回到原始来源核查；同形但不同词源的词根会按释义和来源分别展示。</p><h3>覆盖范围</h3><p>四个考试分别使用 ECDICT 的全部对应标签词条，考试之间允许重叠；全部单词均附音标。本演示不包含学习、复习或拼写测试功能。</p></div></dialog>
<noscript>此离线演示需要浏览器启用 JavaScript。</noscript>
<script>
const DATA = /*__DEMO_DATA__*/null;
const EXAMS = Object.keys(DATA.exams);
const ROOT_PAGE_SIZE = 18;
const WORD_PAGE_SIZE = 40;
const state = {exam:"CET4",view:"roots",query:"",filter:"all",sort:"size",shown:ROOT_PAGE_SIZE,open:null};
const THEMES = ["minimal","classical","elegant","joyful"];
function setTheme(theme,save=true){
  if(!THEMES.includes(theme))theme="elegant";
  document.documentElement.dataset.theme=theme;
  document.querySelectorAll("[data-theme-choice]").forEach(button=>button.setAttribute("aria-pressed",button.dataset.themeChoice===theme));
  if(save)try{localStorage.setItem("rootAtlas.theme",theme);}catch{}
}
const el = {
  examTabs:document.getElementById("examTabs"),search:document.getElementById("searchInput"),clear:document.getElementById("clearSearch"),
  toolbar:document.getElementById("toolbar"),sort:document.getElementById("sortSelect"),results:document.getElementById("results"),
  resultTitle:document.getElementById("resultTitle"),resultMeta:document.getElementById("resultMeta"),loadWrap:document.getElementById("loadWrap"),
  loadMore:document.getElementById("loadMore"),dialog:document.getElementById("aboutDialog")
};
const number = new Intl.NumberFormat("zh-CN");
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const shortText = (value,length=150) => {const text=String(value||"").replace(/\s+/g," ").trim();return text.length>length?text.slice(0,length)+"…":text;};
function prepareExam(exam){
  const data=DATA.exams[exam];
  if(data.prepared)return data;
  const wordMap=new Map();
  const getWord=(word,translation,phonetic)=>{
    if(!wordMap.has(word))wordMap.set(word,{w:word,t:translation,ph:phonetic,roots:[],independent:true});
    return wordMap.get(word);
  };
  data.groups.forEach((group,index)=>{
    group.id=`${exam}-${index}`;
    group._search=[group.form,group.meaning,group.sourceEntry,...group.words.map(word=>word.w)].join(" ").toLowerCase();
    group.words.forEach(word=>{
      const entry=getWord(word.w,word.t,word.ph);
      entry.independent=false;
      entry.roots.push({id:group.id,form:group.form,meaning:group.meaning});
    });
  });
  data.independent.forEach(word=>getWord(word.w,word.t,word.ph));
  data.wordMap=wordMap;
  data.wordList=[...wordMap.values()].sort((a,b)=>a.w.localeCompare(b.w));
  data.wordList.forEach(word=>word._search=[word.w,word.t,...word.roots.flatMap(root=>[root.form,root.meaning])].join(" ").toLowerCase());
  data.prepared=true;
  return data;
}
function sourceShort(source){
  if(source==="RootLearner")return "RootLearner";
  if(source.startsWith("ECDICT"))return "ECDICT";
  if(source.startsWith("Wikipedia"))return "Wikipedia";
  if(source.startsWith("Wiktionary"))return "Wiktionary";
  return source;
}
function kindLabel(group){return group.kind==="free-root lexical definition"?"自由词词典释义":group.source==="RootLearner"?"现有词根释义":"词源词根释义";}
function safeSourceLink(group){
  if(!group.sourcePage)return "";
  try{
    const url=new URL(group.sourcePage);
    if(url.protocol!=="https:"&&url.protocol!=="http:")return "";
    return `<a href="${escapeHtml(url.href)}" target="_blank" rel="noopener noreferrer">查看原始来源</a>`;
  }catch{return "";}
}
function init(){
  let initialTheme="elegant";
  try{const saved=localStorage.getItem("rootAtlas.theme");if(THEMES.includes(saved))initialTheme=saved;}catch{}
  setTheme(initialTheme,false);
  document.querySelectorAll("[data-theme-choice]").forEach(button=>button.addEventListener("click",()=>setTheme(button.dataset.themeChoice)));
  el.examTabs.innerHTML=EXAMS.map(exam=>{
    const summary=DATA.exams[exam].summary;
    return `<button class="exam-tab" role="tab" data-exam="${exam}" aria-selected="${exam===state.exam}"><strong>${exam}</strong><span>${number.format(summary.totalWords)} 词 · ${number.format(summary.rootGroups)} 词族</span></button>`;
  }).join("");
  el.examTabs.addEventListener("click",event=>{
    const button=event.target.closest("[data-exam]");
    if(!button||button.dataset.exam===state.exam)return;
    state.exam=button.dataset.exam;state.shown=state.view==="roots"?ROOT_PAGE_SIZE:WORD_PAGE_SIZE;state.open=null;
    prepareExam(state.exam);render();
  });
  document.querySelectorAll("[data-view]").forEach(button=>button.addEventListener("click",()=>{
    if(state.view===button.dataset.view)return;
    state.view=button.dataset.view;state.shown=state.view==="roots"?ROOT_PAGE_SIZE:WORD_PAGE_SIZE;render();
  }));
  el.search.addEventListener("input",()=>{state.query=el.search.value.trim().toLowerCase();state.shown=state.view==="roots"?ROOT_PAGE_SIZE:WORD_PAGE_SIZE;state.open=null;renderResults();});
  el.clear.addEventListener("click",()=>{el.search.value="";state.query="";state.open=null;renderResults();el.search.focus();});
  document.querySelectorAll("[data-filter]").forEach(button=>button.addEventListener("click",()=>{state.filter=button.dataset.filter;state.shown=ROOT_PAGE_SIZE;state.open=null;renderResults();}));
  el.sort.addEventListener("change",()=>{state.sort=el.sort.value;state.shown=ROOT_PAGE_SIZE;renderResults();});
  el.results.addEventListener("click",event=>{
    const toggle=event.target.closest("[data-toggle]");
    if(toggle){state.open=state.open===toggle.dataset.toggle?null:toggle.dataset.toggle;renderResults();return;}
    const rootLink=event.target.closest("[data-group]");
    if(rootLink)openGroup(rootLink.dataset.group);
  });
  el.loadMore.addEventListener("click",()=>{state.shown+=state.view==="roots"?ROOT_PAGE_SIZE:WORD_PAGE_SIZE;renderResults();});
  document.querySelectorAll("[data-action='about']").forEach(button=>button.addEventListener("click",()=>el.dialog.showModal()));
  document.getElementById("closeDialog").addEventListener("click",()=>el.dialog.close());
  el.dialog.addEventListener("click",event=>{if(event.target===el.dialog)el.dialog.close();});
  document.addEventListener("keydown",event=>{
    if(event.key==="/"&&document.activeElement!==el.search&&!el.dialog.open){event.preventDefault();el.search.focus();}
    if(event.key==="Escape"&&document.activeElement===el.search&&el.search.value){el.search.value="";state.query="";state.open=null;renderResults();}
  });
  prepareExam(state.exam);render();
}
function render(){
  const data=DATA.exams[state.exam],summary=data.summary;
  el.examTabs.querySelectorAll("[data-exam]").forEach(button=>button.setAttribute("aria-selected",button.dataset.exam===state.exam));
  document.getElementById("statWords").textContent=number.format(summary.totalWords);
  document.getElementById("statGroups").textContent=number.format(summary.rootGroups);
  document.getElementById("statGrouped").textContent=number.format(summary.rootGroupedWords);
  document.getElementById("statIndependent").textContent=number.format(summary.independentWords);
  document.querySelectorAll("[data-view]").forEach(button=>button.setAttribute("aria-selected",button.dataset.view===state.view));
  el.search.placeholder=state.view==="roots"?"搜索词根、英文释义或单词，例如 dict / predict":"搜索全部单词、中文释义或词根";
  el.toolbar.hidden=state.view!=="roots";
  el.sort.value=state.sort;
  renderResults();
}
function filteredGroups(data){
  let groups=data.groups.filter(group=>{
    if(state.query&&!group._search.includes(state.query))return false;
    if(state.filter==="multi"&&group.words.length<2)return false;
    if(state.filter==="learner"&&group.rootLearnerId===null)return false;
    if(state.filter==="external"&&group.source==="RootLearner")return false;
    return true;
  });
  const rank=group=>{
    if(!state.query)return 0;
    if(group.form===state.query)return 0;
    if(group.words.some(word=>word.w===state.query))return 1;
    if(group.form.startsWith(state.query))return 2;
    return 3;
  };
  groups.sort((a,b)=>rank(a)-rank(b)||(state.sort==="alpha"?a.form.localeCompare(b.form)||a.meaning.localeCompare(b.meaning):b.words.length-a.words.length||a.form.localeCompare(b.form)||a.meaning.localeCompare(b.meaning)));
  return groups;
}
function renderResults(){
  const data=DATA.exams[state.exam];
  el.clear.classList.toggle("visible",Boolean(el.search.value));
  document.querySelectorAll("[data-filter]").forEach(button=>button.classList.toggle("active",button.dataset.filter===state.filter));
  if(state.view==="roots")renderGroups(data);else renderWords(data);
}
function groupCard(group,data){
  const open=state.open===group.id;
  const duplicate=data.groups.some(other=>other!==group&&other.form===group.form);
  const badges=`<span class="badge ${group.source==="RootLearner"?"":"warm"}">${escapeHtml(kindLabel(group))}</span>${group.rootLearnerId!==null?`<span class="badge neutral">RootLearner #${group.rootLearnerId}</span>`:""}`;
  const preview=group.words.slice(0,6).map(word=>`<span>${escapeHtml(word.w)}</span>`).join("")+(group.words.length>6?`<span>+${group.words.length-6}</span>`:"");
  const detail=open?groupDetail(group,data):"";
  return `<article class="root-card ${open?"is-open":""}" id="group-${group.id}"><button class="group-summary" data-toggle="${group.id}" aria-expanded="${open}" aria-controls="detail-${group.id}"><div class="root-top"><div class="root-identity"><span class="root-form">${escapeHtml(group.form)}</span>${duplicate?'<span class="homograph">同形异源</span>':""}</div><span class="word-count">${group.words.length} 个词</span></div><p class="root-meaning">${escapeHtml(shortText(group.meaning))}</p><div class="badges">${badges}</div><div class="word-preview">${preview}</div><div class="card-footer"><span>${escapeHtml(sourceShort(group.source))}</span><span class="expand-label">${open?"收起词族":"展开词族"} ${open?"−":"+"}</span></div></button>${detail}</article>`;
}
function groupDetail(group,data){
  const source=group.sourceEntry?`${group.source} · 条目 ${group.sourceEntry}`:group.source;
  const words=group.words.map(word=>{
    const entry=data.wordMap.get(word.w);
    const roots=entry?entry.roots:[{id:group.id,form:group.form}];
    const parts=[...(word.p||[]).map(form=>({form,type:"affix"})),...roots.map(root=>({form:root.form,type:"root",id:root.id})),...(word.s||[]).map(form=>({form,type:"affix"}))];
    const assembly=parts.length?parts.map(part=>`<span class="morpheme ${part.type==="root"?"root":""} ${part.id===group.id?"current":""}">${escapeHtml(part.form)}</span>`).join('<span class="plus">+</span>'):'<span class="morpheme">未自动切分</span>';
    return `<div class="detail-word"><div class="detail-word-name">${escapeHtml(word.w)}<span class="detail-phonetic">/${escapeHtml(word.ph)}/</span>${word.l&&word.l!==word.w?`<span class="lemma">原形：${escapeHtml(word.l)}</span>`:""}${word.c==="reviewed"?'<span class="reviewed-tag">逐项复核</span>':""}</div><div class="assembly" aria-label="构词结构">${assembly}</div><p class="translation">${escapeHtml(word.t)}</p></div>`;
  }).join("");
  return `<div class="group-detail" id="detail-${group.id}"><div class="detail-meaning"><span class="detail-label">英文释义</span><p>${escapeHtml(group.meaning)}</p></div><div class="source-detail"><span class="detail-label">释义来源</span><div><p>${escapeHtml(source)}</p>${group.license?`<p>${escapeHtml(group.license)}</p>`:""}${safeSourceLink(group)}</div></div><div class="detail-words-title">词族成员 · ${group.words.length}</div>${words}</div>`;
}
function renderGroups(data){
  const groups=filteredGroups(data),visible=groups.slice(0,state.shown);
  el.resultTitle.textContent="词根词族";
  el.resultMeta.textContent=`${number.format(groups.length)} 个结果${state.query?` · “${state.query}”`:""}`;
  el.results.className="root-grid";
  el.results.innerHTML=visible.length?visible.map(group=>groupCard(group,data)).join(""):emptyState("没有匹配的词根词族","试试更短的拼写、英文释义，或切换到“全部单词”。");
  updateLoad(groups.length,visible.length);
}
function renderWords(data){
  const words=state.query?data.wordList.filter(word=>word._search.includes(state.query)):data.wordList;
  const visible=words.slice(0,state.shown);
  el.resultTitle.textContent="全部单词";
  el.resultMeta.textContent=`${number.format(words.length)} 个结果${state.query?` · “${state.query}”`:""}`;
  el.results.className="word-list";
  el.results.innerHTML=visible.length?visible.map(word=>`<article class="word-row"><h3>${escapeHtml(word.w)}<span class="word-phonetic">/${escapeHtml(word.ph)}/</span></h3><p class="translation">${escapeHtml(word.t)}</p><div class="word-roots">${word.roots.length?word.roots.map(root=>`<button class="root-link" data-group="${root.id}" title="${escapeHtml(shortText(root.meaning,80))}">${escapeHtml(root.form)}</button>`).join(""):'<span class="independent-label">独立词汇项</span>'}</div></article>`).join(""):emptyState("没有匹配的单词","请检查拼写，或尝试搜索更短的片段。");
  updateLoad(words.length,visible.length);
}
function emptyState(title,copy){return `<div class="empty" style="grid-column:1/-1"><strong>${escapeHtml(title)}</strong><p>${escapeHtml(copy)}</p></div>`;}
function updateLoad(total,visible){el.loadWrap.hidden=visible>=total;el.loadMore.textContent=`加载更多 · 已显示 ${number.format(visible)} / ${number.format(total)}`;}
function openGroup(id){
  const data=DATA.exams[state.exam],group=data.groups.find(item=>item.id===id);
  if(!group)return;
  state.view="roots";state.filter="all";state.query=group.form.toLowerCase();state.open=id;state.shown=ROOT_PAGE_SIZE;
  el.search.value=group.form;render();
  requestAnimationFrame(()=>document.getElementById(`group-${id}`)?.scrollIntoView({behavior:"smooth",block:"center"}));
}
init();
</script>
</body>
</html>'''


if __name__ == "__main__":
    build()
