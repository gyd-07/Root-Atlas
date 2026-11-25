from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from build_demo import EXAMS, PAGE, load_exam

BASE = Path(__file__).resolve().parent
DESTINATION = BASE / "demo" / "diy.html"


def replace_once(page: str, old: str, new: str) -> str:
    if old not in page:
        raise ValueError(f"DIY template marker not found: {old[:80]}")
    return page.replace(old, new, 1)


def build():
    data = {
        "generated": date.today().isoformat(),
        "exams": {exam: load_exam(exam) for exam in EXAMS},
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    page = PAGE.replace("/*__DEMO_DATA__*/null", payload)
    page = replace_once(page, '<html lang="zh-CN" data-theme="elegant">', '<html lang="zh-CN" data-theme="diy" data-distribution="night" data-radius="soft" data-font="serif" data-texture="none" data-shadow="lifted" data-density="comfortable">')
    page = replace_once(
        page,
        '<div class="theme-picker" role="group" aria-label="版面风格"><span>版面</span><button class="theme-choice" data-theme-choice="minimal" aria-pressed="false">简约</button><button class="theme-choice" data-theme-choice="classical" aria-pressed="false">古典</button><button class="theme-choice" data-theme-choice="elegant" aria-pressed="true">优雅</button><button class="theme-choice" data-theme-choice="joyful" aria-pressed="false">欢乐</button></div>',
        '<button class="studio-launch" id="openStudioTop" type="button">风格 DIY</button>',
    )
    page = replace_once(
        page,
        '<div class="hero-note"><span class="status-dot"></span>',
        STUDY_HERO + '\n  <div class="hero-note"><span class="status-dot"></span>',
    )
    page = replace_once(
        page,
        '本演示不包含学习、复习或拼写测试功能。',
        '本演示提供独立的翻卡学习与选择题测试流程，学习进度仅保存在当前浏览器，尚未接入 RootLearner 主项目。',
    )
    page = replace_once(page, "</style>", DIY_CSS + STUDY_CSS + "\n</style>")
    page = replace_once(page, "<noscript>", STUDY_HTML + DIY_STUDIO + "\n<noscript>")
    page = replace_once(
        page,
        '  let initialTheme="elegant";\n  try{const saved=localStorage.getItem("rootAtlas.theme");if(THEMES.includes(saved))initialTheme=saved;}catch{}\n  setTheme(initialTheme,false);\n  document.querySelectorAll("[data-theme-choice]").forEach(button=>button.addEventListener("click",()=>setTheme(button.dataset.themeChoice)));',
        '  document.documentElement.dataset.theme="diy";',
    )
    page = replace_once(
        page,
        'if(event.key==="/"&&document.activeElement!==el.search&&!el.dialog.open)',
        'if(event.key==="/"&&document.activeElement!==el.search&&!el.dialog.open&&!document.getElementById("studioDialog").open&&!document.getElementById("studyDialog").open)',
    )
    page = replace_once(page, "init();\n</script>", "init();\n" + STUDY_JS + "\n" + DIY_JS + "\n</script>")
    page = replace_once(
        page,
        "</head>",
        '<script id="diyExportedConfig">window.__ROOT_ATLAS_DIY_EXPORT__=null;</script>\n</head>',
    )
    DESTINATION.write_text(page, encoding="utf-8")
    print(f"Built {DESTINATION} ({DESTINATION.stat().st_size / 1024 / 1024:.1f} MiB)")


STUDY_HERO = r'''
  <div class="study-hero-actions"><button class="study-start" id="startStudy" type="button">开始背诵 · <span id="startStudyExam">CET4</span></button><button class="study-browse" id="browseAtlas" type="button">浏览词根图谱</button></div>
  <p class="study-hero-progress" id="studyHeroProgress">完成本组后自动保存学习进度</p>
'''

STUDY_CSS = r'''
.study-hero-actions{position:relative;z-index:1;display:flex;align-items:center;gap:12px;margin-top:26px}.study-start,.study-browse{border-radius:var(--radius-sm);padding:11px 20px;font-size:14px;font-weight:700;cursor:pointer}.study-start{border:1px solid var(--accent);background:var(--accent);color:var(--on-accent);box-shadow:var(--button-shadow)}.study-start:hover{filter:brightness(1.06)}.study-browse{border:1px solid color-mix(in srgb,var(--hero-ink) 38%,transparent);background:transparent;color:var(--hero-ink)}.study-browse:hover{background:color-mix(in srgb,var(--hero-ink) 9%,transparent)}.study-hero-progress{position:relative;z-index:1;margin:10px 0 0;color:var(--hero-ink);opacity:.68;font-size:11px}.study-dialog{padding:0;width:min(820px,calc(100% - 32px));height:min(820px,calc(100dvh - 40px));max-width:calc(100% - 32px);max-height:calc(100dvh - 40px);border:var(--border-width) solid var(--line);border-radius:var(--radius-lg);background:var(--card);color:var(--ink);box-shadow:0 30px 100px rgba(8,20,15,.35);overflow:hidden}.study-dialog::backdrop{background:rgba(8,20,15,.62);backdrop-filter:blur(3px)}.study-shell{display:flex;flex-direction:column;height:100%;min-height:0}.study-header{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:20px 26px 16px;border-bottom:1px solid var(--line)}.study-kicker{margin:0 0 3px;color:var(--muted);font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}.study-header h2{margin:0;font-family:var(--font-display);font-size:25px;font-weight:var(--display-weight,600)}.study-header-side{display:flex;align-items:center;gap:14px}.study-step{color:var(--muted);font-size:11px;white-space:nowrap}.study-close{flex:none;width:34px;height:34px;border:1px solid var(--line);border-radius:50%;background:var(--field);color:var(--ink);font-size:22px;cursor:pointer}.study-progress-track{flex:none;height:4px;background:var(--field)}.study-progress-track i{display:block;width:0;height:100%;background:var(--accent);transition:width .2s}.study-content{flex:1;min-height:0;overflow-y:auto;padding:26px}.study-lead{margin:0 0 22px;color:var(--muted);font-size:13px;line-height:1.75}.study-section-label{margin:22px 0 10px;color:var(--muted);font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase}.study-exam-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.study-exam-choice,.study-size-choice{border:1px solid var(--line);background:var(--field);color:var(--ink);border-radius:var(--radius-sm);cursor:pointer}.study-exam-choice{padding:13px 8px}.study-exam-choice strong{display:block;font-size:14px}.study-exam-choice span{display:block;margin-top:3px;color:var(--muted);font-size:10px}.study-exam-choice[aria-pressed="true"],.study-size-choice[aria-pressed="true"]{border-color:var(--green-2);background:var(--sage);color:var(--green-2);box-shadow:inset 0 0 0 1px var(--green-2)}.study-size-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.study-size-choice{padding:11px;font-size:13px;font-weight:650}.study-setup-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin:22px 0;background:var(--line);border:1px solid var(--line);border-radius:var(--radius-sm);overflow:hidden}.study-setup-stats div{background:var(--field);padding:15px;text-align:center}.study-setup-stats strong{display:block;font-family:var(--font-display);font-size:25px}.study-setup-stats span{color:var(--muted);font-size:10px}.study-primary,.study-secondary,.study-text-button{border-radius:var(--radius-sm);padding:11px 17px;font-size:13px;font-weight:700;cursor:pointer}.study-primary{border:1px solid var(--green);background:var(--green);color:var(--on-primary)}.study-primary:hover{filter:brightness(1.08)}.study-secondary{border:1px solid var(--line);background:var(--field);color:var(--ink)}.study-secondary:hover{border-color:var(--green-2)}.study-secondary:disabled{opacity:.4;cursor:default}.study-text-button{border:0;background:transparent;color:var(--muted);text-decoration:underline;text-underline-offset:3px}.study-wide{width:100%}.study-setup-note{margin:12px 0 0;color:var(--muted);font-size:10px;line-height:1.7;text-align:center}.study-reset{display:block;margin:14px auto 0}.study-flashcard{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:390px;padding:38px;border:1px solid var(--line);border-radius:var(--radius);background:var(--field);text-align:center;box-shadow:var(--card-shadow)}.study-card-label{margin:0;color:var(--muted);font-size:10px;font-weight:700;letter-spacing:.13em;text-transform:uppercase}.study-word{margin:20px 0 14px;font-family:var(--font-display);font-size:clamp(42px,7vw,68px);font-weight:var(--display-weight,600);line-height:1.1;overflow-wrap:anywhere}.study-hidden-copy{margin:22px 0 0;color:var(--muted);font-size:12px}.study-reveal{margin-top:24px}.study-card-answer{width:100%;margin-top:12px;padding-top:20px;border-top:1px solid var(--line)}.study-translation{margin:0;color:var(--ink);font-size:15px;line-height:1.8;white-space:pre-line;overflow-wrap:anywhere}.study-roots{display:flex;flex-wrap:wrap;justify-content:center;gap:7px;margin-top:18px}.study-root{display:inline-flex;align-items:baseline;gap:6px;max-width:100%;padding:5px 9px;border:1px solid var(--line);border-radius:var(--radius-sm);background:var(--sage);color:var(--green-2);font-size:11px;overflow-wrap:anywhere}.study-root b{font-family:var(--font-display);font-size:14px}.study-independent{color:var(--muted);font-size:11px}.study-card-actions{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:18px}.study-card-actions .study-text-button{margin-left:auto}.study-question-head{margin-bottom:18px}.study-question-meta{display:flex;justify-content:space-between;gap:12px;color:var(--muted);font-size:10px}.study-question-head h3{margin:16px 0 10px;font-family:var(--font-display);font-size:24px;font-weight:var(--display-weight,600)}.study-question-roots{justify-content:flex-start;margin:14px 0 0}.study-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin-top:22px}.study-option{min-height:62px;padding:13px 16px;border:1px solid var(--line);border-radius:var(--radius-sm);background:var(--field);color:var(--ink);text-align:left;font-family:var(--font-display);font-size:19px;cursor:pointer;overflow-wrap:anywhere}.study-option:hover:not(:disabled){border-color:var(--green-2);background:var(--sage)}.study-option:disabled{opacity:1;cursor:default}.study-option.is-correct{border-color:var(--green-2);background:var(--sage);color:var(--green-2);box-shadow:inset 0 0 0 1px var(--green-2)}.study-option.is-wrong{border-color:var(--accent);background:var(--accent-soft);color:var(--accent-text)}.study-feedback{margin-top:18px;padding:16px;border-left:3px solid var(--green-2);border-radius:0 var(--radius-sm) var(--radius-sm) 0;background:var(--field)}.study-feedback.is-wrong{border-left-color:var(--accent)}.study-feedback strong{display:block;margin-bottom:5px;font-size:14px}.study-feedback p{margin:0;color:var(--muted);font-size:12px;white-space:pre-line}.study-feedback .study-primary{margin-top:14px}.study-result{text-align:center}.study-result-score{margin:8px 0 4px;font-family:var(--font-display);font-size:64px;line-height:1;color:var(--green-2)}.study-result-sub{margin:0 0 20px;color:var(--muted);font-size:12px}.study-result-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin:22px 0}.study-result-stats div{padding:14px 8px;border:1px solid var(--line);border-radius:var(--radius-sm);background:var(--field)}.study-result-stats strong{display:block;font-family:var(--font-display);font-size:24px}.study-result-stats span{color:var(--muted);font-size:10px}.study-wrong-list{margin:18px 0;padding:16px;border:1px solid var(--line);border-radius:var(--radius-sm);background:var(--field);text-align:left}.study-wrong-list h3{margin:0 0 10px;font-size:12px}.study-wrong-list ul{margin:0;padding-left:20px;color:var(--muted);font-size:12px}.study-wrong-list li{margin:6px 0}.study-wrong-list b{color:var(--ink)}.study-result-actions{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin-top:20px}.study-done-note{margin:16px auto 0;max-width:560px;color:var(--muted);font-size:12px;line-height:1.75}.study-all-correct{margin:20px 0;padding:22px;border-radius:var(--radius-sm);background:var(--sage);color:var(--green-2);font-weight:650}
@media(max-width:640px){.study-hero-actions{align-items:stretch;flex-direction:column;gap:9px;margin-top:22px}.study-start,.study-browse{width:100%;padding:11px 16px}.study-hero-progress{font-size:10px}.study-dialog{width:100%;height:100dvh;max-width:none;max-height:none;border:0;border-radius:0}.study-header{padding:14px 16px 12px}.study-header h2{font-size:21px}.study-header-side{gap:8px}.study-step{font-size:9px}.study-content{padding:18px 16px 24px}.study-exam-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.study-flashcard{min-height:360px;padding:25px 18px}.study-word{font-size:46px}.study-card-actions{flex-wrap:wrap}.study-card-actions .study-text-button{width:100%;margin:0}.study-options{grid-template-columns:1fr}.study-option{min-height:54px;font-size:18px}.study-result-score{font-size:54px}.study-result-stats{gap:6px}.study-result-stats div{padding:12px 5px}}
'''

STUDY_CSS += r'''
.study-dialog{
  --study-ink:var(--hero-ink);
  --study-muted:color-mix(in srgb,var(--study-ink) 68%,transparent);
  --study-line:color-mix(in srgb,var(--study-ink) 22%,transparent);
  --study-surface:color-mix(in srgb,var(--study-ink) 6%,transparent);
  --study-surface-hover:color-mix(in srgb,var(--study-ink) 11%,transparent);
  --study-error:color-mix(in srgb,#ef9a8d 82%,var(--accent));
  background:var(--hero-bg);
  color:var(--study-ink);
  border-color:var(--hero-line);
  box-shadow:var(--shadow);
  font-family:var(--font-body);
}
.study-dialog::backdrop{background:rgba(5,12,9,.74);backdrop-filter:blur(6px)}
.study-shell{position:relative;isolation:isolate}
.study-shell::before{
  content:"";
  position:absolute;
  z-index:0;
  pointer-events:none;
  width:480px;
  height:480px;
  right:-205px;
  top:-245px;
  border:1px solid color-mix(in srgb,var(--study-ink) 13%,transparent);
  border-radius:50%;
  box-shadow:0 0 0 70px color-mix(in srgb,var(--study-ink) 3%,transparent),0 0 0 140px color-mix(in srgb,var(--study-ink) 2%,transparent);
}
.study-shell::after{content:"";position:absolute;z-index:0;inset:0;pointer-events:none;opacity:.42}
.study-header,.study-progress-track,.study-content{position:relative;z-index:1}
.study-header{border-bottom-color:var(--study-line)}
.study-kicker,.study-step,.study-lead,.study-section-label,.study-hidden-copy,.study-setup-note,.study-question-meta,.study-result-sub,.study-done-note{color:var(--study-muted)}
.study-header h2,.study-word,.study-question-head h3,.study-result-score{color:var(--study-ink);font-family:var(--font-display)}
.study-phonetic{margin:-4px 0 0;color:var(--study-muted);font-family:var(--font-body);font-size:17px;font-weight:400;line-height:1.6;overflow-wrap:anywhere}
.study-option-word,.study-option-phonetic{display:block}
.study-option-phonetic{margin-top:3px;font-family:var(--font-body);font-size:12px;font-weight:400;line-height:1.5;opacity:.72}
.study-wrong-phonetic{color:var(--study-muted);font-weight:400;overflow-wrap:anywhere}
.study-close{border-color:var(--study-line);background:var(--study-surface);color:var(--study-ink)}
.study-close:hover{background:var(--study-surface-hover)}
.study-progress-track{background:color-mix(in srgb,var(--study-ink) 12%,transparent)}
.study-progress-track i{background:var(--accent)}
.study-exam-choice,.study-size-choice,.study-option,.study-secondary{
  border-color:var(--study-line);
  background:var(--study-surface);
  color:var(--study-ink);
}
.study-exam-choice:hover,.study-size-choice:hover,.study-secondary:hover,.study-option:hover:not(:disabled){border-color:color-mix(in srgb,var(--study-ink) 48%,transparent);background:var(--study-surface-hover)}
.study-exam-choice span{color:var(--study-muted)}
.study-exam-choice[aria-pressed="true"],.study-size-choice[aria-pressed="true"]{
  border-color:var(--accent);
  background:var(--accent);
  color:var(--on-accent);
  box-shadow:var(--button-shadow);
}
.study-exam-choice[aria-pressed="true"] span{color:var(--on-accent);opacity:.72}
.study-primary{border-color:var(--accent);background:var(--accent);color:var(--on-accent);box-shadow:var(--button-shadow)}
.study-secondary:hover{border-color:color-mix(in srgb,var(--study-ink) 48%,transparent)}
.study-text-button{color:var(--study-muted)}
.study-text-button:hover{color:var(--study-ink)}
.study-setup-stats{border-color:var(--study-line);background:var(--study-line)}
.study-setup-stats div,.study-result-stats div,.study-wrong-list{background:var(--study-surface);color:var(--study-ink)}
.study-setup-stats span,.study-result-stats span{color:var(--study-muted)}
.study-flashcard{border-color:var(--study-line);background:var(--study-surface);box-shadow:var(--card-shadow);color:var(--study-ink)}
.study-card-label,.study-card-answer,.study-translation,.study-independent{color:var(--study-muted)}
.study-card-answer{border-top-color:var(--study-line)}
.study-root{border-color:var(--study-line);background:var(--study-surface-hover);color:var(--study-ink)}
.study-option.is-correct{border-color:var(--accent);background:var(--accent);color:var(--on-accent);box-shadow:var(--button-shadow)}
.study-option.is-wrong{border-color:var(--study-error);background:color-mix(in srgb,var(--study-error) 14%,transparent);color:var(--study-ink);box-shadow:none}
.study-feedback{border-left-color:var(--accent);background:var(--study-surface);color:var(--study-ink)}
.study-feedback.is-wrong{border-left-color:var(--study-error)}
.study-feedback p,.study-wrong-list ul{color:var(--study-muted)}
.study-result-stats div,.study-wrong-list{border-color:var(--study-line)}
.study-wrong-list b{color:var(--study-ink)}
.study-all-correct{background:var(--accent);color:var(--on-accent)}
.study-dialog button:focus-visible{outline:2px solid var(--study-ink);outline-offset:3px}
html[data-theme="diy"][data-distribution="night"] .study-dialog{outline:1px solid color-mix(in srgb,var(--accent) 35%,transparent);outline-offset:-7px}
html[data-theme="diy"][data-distribution="air"] .study-dialog{box-shadow:none}
html[data-theme="diy"][data-distribution="confetti"] .hero::before,
html[data-theme="diy"][data-distribution="confetti"] .study-shell::before{
  width:460px;
  height:400px;
  right:-35px;
  top:-95px;
  border:0;
  border-radius:0;
  background:
    radial-gradient(circle at 24% 32%,color-mix(in srgb,var(--green) 58%,transparent) 0 34px,transparent 36px),
    radial-gradient(circle at 67% 22%,color-mix(in srgb,var(--accent) 62%,transparent) 0 55px,transparent 57px),
    radial-gradient(circle at 72% 72%,color-mix(in srgb,#82bce8 58%,transparent) 0 43px,transparent 45px),
    radial-gradient(circle at 28% 78%,color-mix(in srgb,#f2cc68 60%,transparent) 0 25px,transparent 27px);
  box-shadow:none;
  opacity:.78;
  pointer-events:none;
}
html[data-theme="diy"][data-texture="paper"] .study-shell::after{background-image:radial-gradient(color-mix(in srgb,var(--study-ink) 7%,transparent) .7px,transparent .8px),linear-gradient(90deg,color-mix(in srgb,var(--study-ink) 2%,transparent) 50%,transparent 50%);background-size:7px 7px,5px 100%}
html[data-theme="diy"][data-texture="dots"] .study-shell::after{background-image:radial-gradient(color-mix(in srgb,var(--accent) 25%,transparent) 1.5px,transparent 1.8px),radial-gradient(color-mix(in srgb,#78b9e6 22%,transparent) 1px,transparent 1.3px);background-size:28px 28px,23px 23px;background-position:0 0,9px 11px}
html[data-theme="diy"][data-texture="grid"] .study-shell::after{background-image:linear-gradient(color-mix(in srgb,var(--study-ink) 5%,transparent) 1px,transparent 1px),linear-gradient(90deg,color-mix(in srgb,var(--study-ink) 5%,transparent) 1px,transparent 1px);background-size:32px 32px}
html[data-theme="diy"][data-density="compact"] .study-content{padding-top:20px;padding-bottom:20px}
html[data-theme="diy"][data-density="spacious"] .study-content{padding:34px}
@media(max-width:640px){
  .study-dialog{box-shadow:none;outline:none}
  .study-shell::before{width:360px;height:360px;right:-210px;top:-190px}
  html[data-theme="diy"][data-distribution="confetti"] .hero::before,
  html[data-theme="diy"][data-distribution="confetti"] .study-shell::before{width:330px;height:310px;right:-92px;top:-92px}
  html[data-theme="diy"][data-distribution="split"] .study-dialog{background:var(--green)}
  html[data-theme="diy"][data-density="compact"] .study-content{padding:14px 16px 18px}
  html[data-theme="diy"][data-density="spacious"] .study-content{padding:24px 18px 30px}
}
'''

STUDY_HTML = r'''
<dialog class="study-dialog" id="studyDialog" aria-labelledby="studyTitle">
  <div class="study-shell">
    <header class="study-header"><div><p class="study-kicker">Root Atlas / Recitation</p><h2 id="studyTitle">背诵设置</h2></div><div class="study-header-side"><span class="study-step" id="studyStep">四考试词库</span><button class="study-close" id="closeStudy" type="button" aria-label="关闭背诵面板">×</button></div></header>
    <div class="study-progress-track" id="studyProgressTrack" hidden><i id="studyProgressBar"></i></div>
    <main class="study-content" id="studyContent"></main>
  </div>
</dialog>
'''

STUDY_JS = r'''
const STUDY_STORAGE_KEY = "rootAtlas.study.v1";
const studyDialog = document.getElementById("studyDialog");
const studyContent = document.getElementById("studyContent");
const studySetup = {exam:state.exam,size:10};
let studySession = null;
let studyStorageOK = true;
let studyProgress = loadStudyProgress();
function loadStudyProgress(){
  const clean={exams:{}};
  try{
    const parsed=JSON.parse(localStorage.getItem(STUDY_STORAGE_KEY));
    if(!parsed||typeof parsed!=="object"||!parsed.exams||typeof parsed.exams!=="object")return clean;
    EXAMS.forEach(exam=>{
      const source=parsed.exams[exam];
      if(!source||typeof source!=="object"||Array.isArray(source))return;
      const records={};
      Object.entries(source).forEach(([word,rec])=>{
        if(!rec||typeof rec!=="object")return;
        records[word]={seen:Number.isFinite(rec.seen)?Math.max(0,rec.seen):0,correct:Number.isFinite(rec.correct)?Math.max(0,rec.correct):0,wrong:Number.isFinite(rec.wrong)?Math.max(0,rec.wrong):0,mastered:rec.mastered===true,last:Number.isFinite(rec.last)?rec.last:0};
      });
      clean.exams[exam]=records;
    });
  }catch{}
  return clean;
}
function saveStudyProgress(){try{localStorage.setItem(STUDY_STORAGE_KEY,JSON.stringify(studyProgress));studyStorageOK=true;}catch{studyStorageOK=false;}}
function studyRecords(exam){if(!studyProgress.exams[exam])studyProgress.exams[exam]={};return studyProgress.exams[exam];}
function studyStats(exam){
  const data=prepareExam(exam),records=studyRecords(exam);
  let learned=0,mastered=0,review=0;
  data.wordList.forEach(word=>{const rec=records[word.w];if(!rec||rec.seen<=0)return;learned++;if(rec.mastered)mastered++;else review++;});
  return {total:data.wordList.length,learned,mastered,review};
}
function updateStudyHero(){
  const stats=studyStats(state.exam);
  document.getElementById("startStudyExam").textContent=state.exam;
  document.getElementById("studyHeroProgress").textContent=stats.learned?`${state.exam} · 已学 ${number.format(stats.learned)} / ${number.format(stats.total)} 词 · 已掌握 ${number.format(stats.mastered)} 词`:`${state.exam} · 从第一组开始，完成本组后自动保存进度`;
}
function studyShuffle(list){
  const result=list.slice();
  for(let i=result.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[result[i],result[j]]=[result[j],result[i]];}
  return result;
}
function studyPickWords(exam,count){
  const data=prepareExam(exam),records=studyRecords(exam),review=[],fresh=[],mastered=[];
  data.wordList.forEach(word=>{
    const rec=records[word.w];
    if(!rec||rec.seen<=0)fresh.push(word);else if(rec.mastered)mastered.push(word);else review.push(word);
  });
  return [...studyShuffle(review),...studyShuffle(fresh),...studyShuffle(mastered)].slice(0,count);
}
function openStudy(){
  studySetup.exam=state.exam;studySession=null;renderStudy();
  if(!studyDialog.open)studyDialog.showModal();
}
function closeStudy(){
  if(studySession&&["study","quiz","roundend"].includes(studySession.phase)&&!window.confirm("退出后不会保存本次未完成的学习，确定退出吗？"))return;
  studyDialog.close();studySession=null;
}
function beginStudySession(){
  state.exam=studySetup.exam;prepareExam(state.exam);render();updateStudyHero();
  const words=studyPickWords(studySetup.exam,studySetup.size);
  if(!words.length)return;
  studySession={exam:studySetup.exam,words,queue:[],questions:[],phase:"study",idx:0,revealed:false,round:0,qidx:0,answered:false,picked:-1,roundWrong:[],everWrong:{},roundLog:[],totalRight:0,totalAnswered:0,initialRight:0};
  renderStudy();
}
function studyRootHtml(word){
  if(!word.roots.length)return '<span class="study-independent">独立词汇项 · 直接记忆单词与释义</span>';
  return word.roots.map(root=>`<span class="study-root"><b>${escapeHtml(root.form)}</b><span>${escapeHtml(shortText(root.meaning,100))}</span></span>`).join("");
}
function makeStudyQuestion(word){
  const data=DATA.exams[studySession.exam];
  const distractors=studyShuffle(data.wordList.filter(item=>item.w!==word.w)).slice(0,3);
  const options=studyShuffle([word,...distractors]).map(item=>item.w);
  return {word,options,answer:word.w};
}
function beginStudyRound(retry=false){
  if(!studySession)return;
  const queue=retry?studySession.roundWrong.slice():studySession.words.slice();
  if(!queue.length){finishStudy();return;}
  studySession.round++;
  studySession.queue=studyShuffle(queue);
  studySession.questions=studySession.queue.map(makeStudyQuestion);
  studySession.qidx=0;studySession.answered=false;studySession.picked=-1;studySession.roundWrong=[];studySession.phase="quiz";
  renderStudy();
}
function answerStudy(index){
  const session=studySession;
  if(!session||session.phase!=="quiz"||session.answered)return;
  const question=session.questions[session.qidx];
  if(index<0||index>=question.options.length)return;
  session.answered=true;session.picked=index;session.totalAnswered++;
  if(question.options[index]===question.answer)session.totalRight++;
  else{
    session.roundWrong.push(question.word);session.everWrong[question.word.w]=true;
  }
  renderStudy();
}
function afterStudyAnswer(){
  const session=studySession;
  if(!session||!session.answered)return;
  session.qidx++;session.answered=false;session.picked=-1;
  if(session.qidx>=session.questions.length){
    session.phase="roundend";
    session.roundLog.push({round:session.round,total:session.questions.length,wrong:session.roundWrong.length});
    if(session.round===1)session.initialRight=session.questions.length-session.roundWrong.length;
  }
  renderStudy();
}
function finishStudy(){
  const session=studySession;
  if(!session)return;
  const records=studyRecords(session.exam),now=Date.now();
  session.words.forEach(word=>{
    const old=records[word.w]||{seen:0,correct:0,wrong:0,mastered:false,last:0};
    const failed=session.everWrong[word.w]===true;
    records[word.w]={seen:old.seen+1,correct:old.correct+(failed?0:1),wrong:old.wrong+(failed?1:0),mastered:!failed,last:now};
  });
  saveStudyProgress();session.phase="done";updateStudyHero();renderStudy();
}
function resetStudyProgress(){
  if(!window.confirm(`清空 ${studySetup.exam} 的背诵进度？词库与风格设置不会受影响。`))return;
  delete studyProgress.exams[studySetup.exam];saveStudyProgress();updateStudyHero();renderStudy();
}
function studySetupHtml(){
  const stats=studyStats(studySetup.exam),data=DATA.exams[studySetup.exam];
  return `<div class="study-setup"><p class="study-lead">选择本次要背的考试与每组数量。学习时先翻卡，再进行四选一测试；答错的单词可立即重练。</p><div class="study-section-label">01 · 选择考试</div><div class="study-exam-grid">${EXAMS.map(exam=>`<button class="study-exam-choice" type="button" data-study-exam="${exam}" aria-pressed="${exam===studySetup.exam}"><strong>${exam}</strong><span>${number.format(DATA.exams[exam].summary.totalWords)} 词</span></button>`).join("")}</div><div class="study-section-label">02 · 每组数量</div><div class="study-size-grid">${[5,10,20].map(size=>`<button class="study-size-choice" type="button" data-study-size="${size}" aria-pressed="${size===studySetup.size}">${size} 词 / 组</button>`).join("")}</div><div class="study-setup-stats"><div><strong>${number.format(stats.learned)}</strong><span>已经学习</span></div><div><strong>${number.format(stats.review)}</strong><span>待巩固</span></div><div><strong>${number.format(stats.mastered)}</strong><span>已经掌握</span></div></div><button class="study-primary study-wide" type="button" data-study-begin>开始学习 ${studySetup.size} 词</button><p class="study-setup-note">优先安排待巩固单词，再从未学单词中抽题；不足时补充已掌握单词。完成本组后保存进度。${studyStorageOK?"":"当前浏览器无法保存，进度仅在本页有效。"}</p>${stats.learned?'<button class="study-text-button study-reset" type="button" data-study-reset>重置当前考试背诵进度</button>':""}</div>`;
}
function studyCardHtml(session){
  const word=session.words[session.idx],last=session.idx===session.words.length-1;
  return `<article class="study-flashcard"><p class="study-card-label">${escapeHtml(session.exam)} · 翻卡学习</p><h3 class="study-word">${escapeHtml(word.w)}</h3><p class="study-phonetic">/${escapeHtml(word.ph)}/</p>${session.revealed?`<div class="study-card-answer"><p class="study-translation">${escapeHtml(word.t)}</p><div class="study-roots">${studyRootHtml(word)}</div></div>`:'<p class="study-hidden-copy">先回忆中文释义和词根，再翻面核对。</p><button class="study-primary study-reveal" type="button" data-study-reveal>查看释义与词根</button>'}</article><div class="study-card-actions"><button class="study-secondary" type="button" data-study-prev ${session.idx===0?"disabled":""}>上一张</button>${session.revealed?`<button class="study-primary" type="button" ${last?"data-study-test":"data-study-next"}>${last?"开始测试":"下一张"}</button>`:""}<button class="study-text-button" type="button" data-study-test>直接开始测试</button></div>`;
}
function studyQuizHtml(session){
  const question=session.questions[session.qidx],word=question.word,answered=session.answered,wordMap=DATA.exams[session.exam].wordMap;
  return `<div class="study-question-head"><div class="study-question-meta"><span>中文释义 → 单词</span><span>本轮已错 ${session.roundWrong.length} 题</span></div><h3>根据释义选出对应单词</h3><p class="study-translation">${escapeHtml(word.t)}</p><div class="study-roots study-question-roots">${studyRootHtml(word)}</div></div><div class="study-options">${question.options.map((option,index)=>{let cls="study-option";if(answered&&option===question.answer)cls+=" is-correct";else if(answered&&index===session.picked)cls+=" is-wrong";const optionWord=wordMap.get(option);return `<button class="${cls}" type="button" data-study-answer="${index}" ${answered?"disabled":""}><span class="study-option-word">${index+1}. ${escapeHtml(option)}</span><span class="study-option-phonetic">/${escapeHtml(optionWord.ph)}/</span></button>`;}).join("")}</div>${answered?`<div class="study-feedback ${question.options[session.picked]===question.answer?"":"is-wrong"}"><strong>${question.options[session.picked]===question.answer?"答对了":"答错了 · 正确答案："+escapeHtml(question.answer)}</strong><p>${escapeHtml(word.w)} /${escapeHtml(word.ph)}/\n${escapeHtml(word.t)}</p><button class="study-primary" type="button" data-study-after>${session.qidx===session.questions.length-1?"查看本轮结果":"下一题"}</button></div>`:""}`;
}
function studyWrongList(words,title){
  if(!words.length)return "";
  return `<div class="study-wrong-list"><h3>${escapeHtml(title)}</h3><ul>${words.map(word=>`<li><b>${escapeHtml(word.w)}</b> <span class="study-wrong-phonetic">/${escapeHtml(word.ph)}/</span> · ${escapeHtml(shortText(word.t,90))}</li>`).join("")}</ul></div>`;
}
function studyRoundEndHtml(session){
  const total=session.questions.length,wrong=session.roundWrong.length,correct=total-wrong;
  return `<div class="study-result"><p class="study-card-label">第 ${session.round} 轮测试</p><div class="study-result-score">${correct} / ${total}</div><p class="study-result-sub">${wrong?`本轮还有 ${wrong} 个错词需要重练`:"本轮全部答对"}</p>${wrong?studyWrongList(session.roundWrong,"本轮错词"):'<div class="study-all-correct">本轮全部通过，可以查看本组小结。</div>'}<div class="study-result-actions">${wrong?`<button class="study-primary" type="button" data-study-retry>错词重练 · ${wrong} 题</button>`:""}<button class="study-secondary" type="button" data-study-finish>${wrong?"结束并保存本次进度":"查看本组小结"}</button></div></div>`;
}
function studyDoneHtml(session){
  const wrongWords=session.words.filter(word=>session.everWrong[word.w]);
  const score=session.words.length?Math.round(session.initialRight/session.words.length*100):0;
  const outstanding=session.roundWrong.length;
  return `<div class="study-result"><p class="study-card-label">${escapeHtml(session.exam)} · 本组完成</p><div class="study-result-score">${score}%</div><p class="study-result-sub">首轮正确率 · 学习进度已保存</p><div class="study-result-stats"><div><strong>${session.words.length}</strong><span>本组单词</span></div><div><strong>${session.round}</strong><span>测试轮数</span></div><div><strong>${wrongWords.length}</strong><span>本次曾答错</span></div></div>${studyWrongList(wrongWords,"本次错词记录")}<p class="study-done-note">${outstanding?`仍有 ${outstanding} 个错词未通过，已安排下次优先巩固。`:wrongWords.length?"错词已在重练中答对，但仍会安排后续巩固。":"本组全部答对，已标记为掌握。"}${studyStorageOK?"":" 浏览器禁止本地存储，刷新后进度会丢失。"}</p><div class="study-result-actions"><button class="study-primary" type="button" data-study-next-batch>再背一组</button><button class="study-secondary" type="button" data-study-setup>调整考试或数量</button><button class="study-text-button" type="button" data-study-home>返回词根图谱</button></div></div>`;
}
function renderStudy(){
  const title=document.getElementById("studyTitle"),step=document.getElementById("studyStep"),track=document.getElementById("studyProgressTrack"),bar=document.getElementById("studyProgressBar");
  if(!studySession){
    title.textContent="背诵设置";step.textContent=studySetup.exam;track.hidden=true;studyContent.innerHTML=studySetupHtml();return;
  }
  const session=studySession;
  track.hidden=false;
  if(session.phase==="study"){
    title.textContent="翻卡学习";step.textContent=`${session.exam} · ${session.idx+1} / ${session.words.length}`;bar.style.width=(session.idx/session.words.length*100)+"%";studyContent.innerHTML=studyCardHtml(session);
  }else if(session.phase==="quiz"){
    title.textContent=`第 ${session.round} 轮测试`;step.textContent=`${session.qidx+1} / ${session.questions.length}`;bar.style.width=(session.qidx/session.questions.length*100)+"%";studyContent.innerHTML=studyQuizHtml(session);
  }else if(session.phase==="roundend"){
    title.textContent="本轮结果";step.textContent=`第 ${session.round} 轮`;bar.style.width="100%";studyContent.innerHTML=studyRoundEndHtml(session);
  }else{
    title.textContent="本组完成";step.textContent=session.exam;bar.style.width="100%";studyContent.innerHTML=studyDoneHtml(session);
  }
}
document.getElementById("startStudy").addEventListener("click",openStudy);
document.getElementById("browseAtlas").addEventListener("click",()=>document.querySelector(".workspace").scrollIntoView({behavior:"smooth",block:"start"}));
document.getElementById("closeStudy").addEventListener("click",closeStudy);
studyDialog.addEventListener("cancel",event=>{event.preventDefault();closeStudy();});
el.examTabs.addEventListener("click",()=>{studySetup.exam=state.exam;updateStudyHero();});
studyContent.addEventListener("click",event=>{
  const button=event.target.closest("button");if(!button)return;
  if(button.dataset.studyExam){studySetup.exam=button.dataset.studyExam;renderStudy();return;}
  if(button.dataset.studySize){studySetup.size=Number(button.dataset.studySize);renderStudy();return;}
  if(button.hasAttribute("data-study-begin")){beginStudySession();return;}
  if(button.hasAttribute("data-study-reset")){resetStudyProgress();return;}
  if(!studySession)return;
  const session=studySession;
  if(button.hasAttribute("data-study-reveal")){session.revealed=true;renderStudy();}
  else if(button.hasAttribute("data-study-prev")&&session.idx>0){session.idx--;session.revealed=false;renderStudy();}
  else if(button.hasAttribute("data-study-next")&&session.idx<session.words.length-1){session.idx++;session.revealed=false;renderStudy();}
  else if(button.hasAttribute("data-study-test"))beginStudyRound(false);
  else if(button.hasAttribute("data-study-answer"))answerStudy(Number(button.dataset.studyAnswer));
  else if(button.hasAttribute("data-study-after"))afterStudyAnswer();
  else if(button.hasAttribute("data-study-retry"))beginStudyRound(true);
  else if(button.hasAttribute("data-study-finish"))finishStudy();
  else if(button.hasAttribute("data-study-next-batch")){studySetup.exam=session.exam;studySession=null;beginStudySession();}
  else if(button.hasAttribute("data-study-setup")){studySetup.exam=session.exam;studySession=null;renderStudy();}
  else if(button.hasAttribute("data-study-home"))closeStudy();
});
document.addEventListener("keydown",event=>{
  if(!studyDialog.open||!studySession)return;
  const session=studySession;
  if(session.phase==="study"){
    if(event.code==="Space"){event.preventDefault();session.revealed=true;renderStudy();}
    else if(event.key==="ArrowLeft"&&session.idx>0){session.idx--;session.revealed=false;renderStudy();}
    else if(event.key==="ArrowRight"&&session.idx<session.words.length-1){session.idx++;session.revealed=false;renderStudy();}
    else if(event.key==="Enter"&&session.idx===session.words.length-1){event.preventDefault();beginStudyRound(false);}
  }else if(session.phase==="quiz"){
    if(!session.answered&&/^[1-4]$/.test(event.key))answerStudy(Number(event.key)-1);
    else if(session.answered&&(event.key==="Enter"||event.code==="Space")){event.preventDefault();afterStudyAnswer();}
  }else if(session.phase==="roundend"&&event.key==="Enter"){
    event.preventDefault();if(session.roundWrong.length)beginStudyRound(true);else finishStudy();
  }
});
updateStudyHero();
'''

DIY_CSS = r'''
html[data-theme="diy"]{--font-body:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;--font-display:Georgia,"Songti SC",serif;--radius:12px;--radius-sm:7px;--radius-lg:24px;--border-width:1px}
html[data-theme="diy"] body{background-color:var(--paper);color:var(--page-ink);font-family:var(--font-body)}
html[data-theme="diy"] .shell{width:min(1180px,calc(100% - 40px))}
html[data-theme="diy"] .topbar{color:var(--page-ink)}
html[data-theme="diy"] .brand small,html[data-theme="diy"] .footer{color:var(--page-muted)}
html[data-theme="diy"] .brand-mark{background:var(--green);color:var(--on-primary);border:var(--border-width) solid var(--hero-line);border-radius:var(--radius-sm);box-shadow:var(--mark-shadow)}
html[data-theme="diy"] .text-button{color:var(--page-ink)}
html[data-theme="diy"] .hero{background:var(--hero-bg);color:var(--hero-ink);border:var(--border-width) solid var(--hero-line);border-radius:var(--radius-lg);box-shadow:var(--shadow)}
html[data-theme="diy"] .hero:before{border-color:color-mix(in srgb,var(--hero-ink) 14%,transparent);box-shadow:0 0 0 70px color-mix(in srgb,var(--hero-ink) 3%,transparent),0 0 0 140px color-mix(in srgb,var(--hero-ink) 2%,transparent)}
html[data-theme="diy"] .hero h1{color:var(--hero-ink);font-family:var(--font-display);font-weight:var(--display-weight,500)}
html[data-theme="diy"] .eyebrow,html[data-theme="diy"] .hero-copy,html[data-theme="diy"] .hero-note{color:var(--hero-ink);opacity:.76}
html[data-theme="diy"] .status-dot{background:var(--accent);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 18%,transparent)}
html[data-theme="diy"] .specimen{background:var(--card);color:var(--ink);border:var(--border-width) solid var(--line);border-radius:var(--radius);box-shadow:var(--specimen-shadow,var(--shadow))}
html[data-theme="diy"] .specimen-label,html[data-theme="diy"] .specimen-caption,html[data-theme="diy"] .specimen-root span{color:var(--muted)}
html[data-theme="diy"] .specimen-root{border-color:var(--line)}
html[data-theme="diy"] .specimen-root strong{color:var(--green-2);font-family:var(--font-display)}
html[data-theme="diy"] .specimen-words span{border-color:var(--line);border-radius:var(--radius-sm)}
html[data-theme="diy"] .exam-tab{background:var(--card);color:var(--ink);border:var(--border-width) solid var(--line);border-radius:var(--radius-sm);box-shadow:none}
html[data-theme="diy"] .exam-tab:hover{background:var(--field);border-color:var(--green-2)}
html[data-theme="diy"] .exam-tab[aria-selected="true"]{background:var(--sage);border-color:var(--green-2);box-shadow:var(--card-shadow)}
html[data-theme="diy"] .exam-tab[aria-selected="true"] strong{color:var(--green-2)}
html[data-theme="diy"] .exam-tab span{color:var(--muted)}
html[data-theme="diy"] .stats{background:var(--line);border-color:var(--line);border-radius:var(--radius-sm)}
html[data-theme="diy"] .stat{background:var(--card);color:var(--ink)}
html[data-theme="diy"] .stat strong{color:var(--green-2);font-family:var(--font-display);font-weight:var(--display-weight,500)}
html[data-theme="diy"] .stat span{color:var(--muted)}
html[data-theme="diy"] .workspace{background:var(--card);color:var(--ink);border:var(--border-width) solid var(--line);border-radius:var(--radius-lg);box-shadow:var(--shadow)}
html[data-theme="diy"] .workspace-head{background:var(--card)}
html[data-theme="diy"] .view-tab{color:var(--muted)}
html[data-theme="diy"] .view-tab[aria-selected="true"]{color:var(--ink)}
html[data-theme="diy"] .view-tab[aria-selected="true"]:after{background:var(--accent);height:3px}
html[data-theme="diy"] .data-note,html[data-theme="diy"] .sort-wrap{color:var(--muted)}
html[data-theme="diy"] .sort-wrap select{color:var(--ink)}
html[data-theme="diy"] .search-box{background:var(--field);border:var(--border-width) solid var(--line);border-radius:var(--radius-sm)}
html[data-theme="diy"] .search-box:focus-within{background:var(--card);border-color:var(--green-2);box-shadow:0 0 0 3px var(--sage)}
html[data-theme="diy"] .search-box input{color:var(--ink)}
html[data-theme="diy"] .search-box svg,html[data-theme="diy"] .search-box input::placeholder,html[data-theme="diy"] .key-hint{color:var(--muted)}
html[data-theme="diy"] .key-hint{border-color:var(--line);border-radius:var(--radius-sm)}
html[data-theme="diy"] .filter{color:var(--muted);border-radius:var(--radius-sm)}
html[data-theme="diy"] .filter:hover{background:var(--field)}
html[data-theme="diy"] .filter.active{background:var(--sage);color:var(--green-2)}
html[data-theme="diy"] .results-head{background:var(--field);border-color:var(--line);color:var(--muted)}
html[data-theme="diy"] .results-head strong{color:var(--ink)}
html[data-theme="diy"] .root-card{background:var(--card);border:var(--border-width) solid var(--line);border-radius:var(--radius);box-shadow:var(--card-shadow)}
html[data-theme="diy"] .root-card:hover{border-color:var(--green-2);box-shadow:var(--hover-shadow,var(--card-shadow))}
html[data-theme="diy"] .root-card.is-open{border-color:var(--green-2)}
html[data-theme="diy"] .group-summary{border-radius:var(--radius)}
html[data-theme="diy"] .root-form{color:var(--green-2);font-family:var(--font-display);font-weight:var(--display-weight,500)}
html[data-theme="diy"] .root-meaning{color:var(--ink);opacity:.82}
html[data-theme="diy"] .word-count{color:var(--muted);background:var(--field);border-radius:var(--radius-sm)}
html[data-theme="diy"] .homograph{color:var(--accent-text);border-color:var(--accent);border-radius:var(--radius-sm)}
html[data-theme="diy"] .badge{background:var(--sage);color:var(--green-2);border-radius:var(--radius-sm)}
html[data-theme="diy"] .badge.warm{background:var(--accent-soft);color:var(--accent-text)}
html[data-theme="diy"] .badge.neutral{background:var(--field);color:var(--muted)}
html[data-theme="diy"] .word-preview span,html[data-theme="diy"] .card-footer{color:var(--muted)}
html[data-theme="diy"] .card-footer{border-color:var(--line)}
html[data-theme="diy"] .expand-label,html[data-theme="diy"] .source-detail a{color:var(--green-2)}
html[data-theme="diy"] .group-detail{background:var(--field);border-color:var(--line);border-radius:0 0 var(--radius) var(--radius)}
html[data-theme="diy"] .detail-label,html[data-theme="diy"] .detail-words-title,html[data-theme="diy"] .lemma{color:var(--muted)}
html[data-theme="diy"] .source-detail,html[data-theme="diy"] .detail-word{border-color:var(--line)}
html[data-theme="diy"] .source-detail p,html[data-theme="diy"] .translation{color:var(--ink);opacity:.8}
html[data-theme="diy"] .morpheme{background:var(--sage);color:var(--green-2);border-radius:var(--radius-sm)}
html[data-theme="diy"] .morpheme.root{background:var(--accent-soft);color:var(--accent-text)}
html[data-theme="diy"] .morpheme.current{outline-color:var(--accent)}
html[data-theme="diy"] .word-row{border-color:var(--line)}
html[data-theme="diy"] .word-row h3{color:var(--green-2);font-family:var(--font-display);font-weight:var(--display-weight,500)}
html[data-theme="diy"] .root-link{border:var(--border-width) solid var(--line);background:var(--sage);color:var(--green-2);border-radius:var(--radius-sm)}
html[data-theme="diy"] .root-link:hover{background:var(--accent-soft);border-color:var(--accent)}
html[data-theme="diy"] .independent-label{background:var(--field);color:var(--muted);border-radius:var(--radius-sm)}
html[data-theme="diy"] .load-more{border:var(--border-width) solid var(--green-2);background:var(--green);color:var(--on-primary);border-radius:var(--radius-sm);box-shadow:var(--button-shadow)}
html[data-theme="diy"] .load-more:hover{background:var(--sage);color:var(--green-2)}
html[data-theme="diy"] .empty{color:var(--muted)}
html[data-theme="diy"] .empty strong{color:var(--ink);font-family:var(--font-display)}
html[data-theme="diy"] .dialog{background:var(--card);color:var(--ink);border:var(--border-width) solid var(--line);border-radius:var(--radius-lg)}
html[data-theme="diy"] .dialog h2{font-family:var(--font-display)}
html[data-theme="diy"] .dialog p,html[data-theme="diy"] .dialog li{color:var(--muted)}
html[data-theme="diy"] .dialog-close{background:var(--field);border-radius:var(--radius-sm)}
html[data-theme="diy"] .dialog .warning{background:var(--accent-soft);color:var(--accent-text);border-radius:var(--radius-sm)}
html[data-theme="diy"] button:focus-visible,html[data-theme="diy"] a:focus-visible,html[data-theme="diy"] select:focus-visible,html[data-theme="diy"] input:focus-visible{outline-color:var(--accent)}
html[data-theme="diy"][data-font="sans"]{--font-body:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;--font-display:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;--display-weight:550}
html[data-theme="diy"][data-font="serif"]{--font-body:Georgia,"Songti SC","SimSun",serif;--font-display:Georgia,"Songti SC","SimSun",serif;--display-weight:500}
html[data-theme="diy"][data-font="rounded"]{--font-body:"Trebuchet MS","PingFang SC","Microsoft YaHei",sans-serif;--font-display:"Trebuchet MS","PingFang SC","Microsoft YaHei",sans-serif;--display-weight:800}
html[data-theme="diy"][data-radius="sharp"]{--radius:0px;--radius-sm:0px;--radius-lg:0px}
html[data-theme="diy"][data-radius="soft"]{--radius:12px;--radius-sm:7px;--radius-lg:22px}
html[data-theme="diy"][data-radius="round"]{--radius:24px;--radius-sm:14px;--radius-lg:34px}
html[data-theme="diy"][data-radius="round"] .brand-mark{border-radius:50%}
html[data-theme="diy"][data-radius="round"] .filter,html[data-theme="diy"][data-radius="round"] .word-count,html[data-theme="diy"][data-radius="round"] .homograph,html[data-theme="diy"][data-radius="round"] .badge,html[data-theme="diy"][data-radius="round"] .load-more{border-radius:999px}
html[data-theme="diy"][data-shadow="none"]{--shadow:none;--card-shadow:none;--mark-shadow:none;--button-shadow:none;--specimen-shadow:none}
html[data-theme="diy"][data-shadow="soft"]{--shadow:0 12px 32px rgba(20,30,25,.09);--card-shadow:0 4px 14px rgba(20,30,25,.045);--hover-shadow:0 10px 24px rgba(20,30,25,.09);--mark-shadow:0 3px 8px rgba(20,30,25,.08);--button-shadow:0 3px 8px rgba(20,30,25,.08);--specimen-shadow:0 18px 34px rgba(20,30,25,.13)}
html[data-theme="diy"][data-shadow="lifted"]{--shadow:0 26px 60px rgba(10,20,15,.2);--card-shadow:0 8px 20px rgba(20,30,25,.07);--hover-shadow:0 18px 32px rgba(20,30,25,.13);--mark-shadow:0 5px 12px rgba(10,20,15,.16);--button-shadow:0 5px 12px rgba(10,20,15,.14);--specimen-shadow:12px 18px 34px rgba(10,20,15,.2)}
html[data-theme="diy"][data-shadow="hard"]{--shadow:7px 7px 0 var(--ink);--card-shadow:4px 4px 0 var(--ink);--hover-shadow:7px 7px 0 var(--ink);--mark-shadow:3px 3px 0 var(--ink);--button-shadow:4px 4px 0 var(--ink);--specimen-shadow:9px 9px 0 var(--ink)}
html[data-theme="diy"][data-shadow="hard"] .hero,html[data-theme="diy"][data-shadow="hard"] .workspace,html[data-theme="diy"][data-shadow="hard"] .root-card,html[data-theme="diy"][data-shadow="hard"] .exam-tab,html[data-theme="diy"][data-shadow="hard"] .load-more{border-width:2px}
html[data-theme="diy"][data-texture="paper"] body{background-image:radial-gradient(color-mix(in srgb,var(--page-ink) 6%,transparent) .7px,transparent .8px),linear-gradient(90deg,color-mix(in srgb,var(--page-ink) 2%,transparent) 50%,transparent 50%);background-size:7px 7px,5px 100%}
html[data-theme="diy"][data-texture="dots"] body{background-image:radial-gradient(color-mix(in srgb,var(--accent) 25%,transparent) 1.5px,transparent 1.8px),radial-gradient(color-mix(in srgb,#78b9e6 24%,transparent) 1px,transparent 1.3px);background-size:28px 28px,23px 23px;background-position:0 0,9px 11px}
html[data-theme="diy"][data-texture="grid"] body{background-image:linear-gradient(color-mix(in srgb,var(--page-ink) 5%,transparent) 1px,transparent 1px),linear-gradient(90deg,color-mix(in srgb,var(--page-ink) 5%,transparent) 1px,transparent 1px);background-size:32px 32px}
html[data-theme="diy"][data-distribution="night"] .workspace{border-color:color-mix(in srgb,var(--accent) 58%,var(--line))}
html[data-theme="diy"][data-distribution="night"] .hero{outline:1px solid color-mix(in srgb,var(--accent) 35%,transparent);outline-offset:-7px}
html[data-theme="diy"][data-distribution="split"] .stat:nth-child(2),html[data-theme="diy"][data-distribution="split"] .stat:nth-child(4){background:var(--accent-soft)}
html[data-theme="diy"][data-distribution="split"] .root-card:nth-child(4n+2),html[data-theme="diy"][data-distribution="split"] .root-card:nth-child(4n+3){background:var(--sage)}
html[data-theme="diy"][data-distribution="split"] .exam-tab:nth-child(even){background:var(--accent-soft)}
html[data-theme="diy"][data-distribution="air"] .hero{border-color:var(--line);box-shadow:none;padding-top:42px;padding-bottom:42px}
html[data-theme="diy"][data-distribution="air"] .hero:before{display:none}
html[data-theme="diy"][data-distribution="air"] .hero h1{letter-spacing:-.045em}
html[data-theme="diy"][data-distribution="air"] .workspace{box-shadow:none}
@media(min-width:641px){html[data-theme="diy"][data-density="compact"] .hero{padding:38px 44px}html[data-theme="diy"][data-density="compact"] .workspace-head{padding:20px 24px 0}html[data-theme="diy"][data-density="compact"] .root-grid{gap:9px;padding:14px 24px 20px}html[data-theme="diy"][data-density="compact"] .group-summary{padding:15px 17px 13px}html[data-theme="diy"][data-density="compact"] .stat{padding:13px 18px}html[data-theme="diy"][data-density="spacious"] .hero{padding:64px 64px}html[data-theme="diy"][data-density="spacious"] .workspace-head{padding:34px 34px 0}html[data-theme="diy"][data-density="spacious"] .root-grid{gap:22px;padding:28px 34px 36px}html[data-theme="diy"][data-density="spacious"] .group-summary{padding:28px 27px 23px}html[data-theme="diy"][data-density="spacious"] .stat{padding:25px 25px}}
.studio-launch{display:inline-flex;align-items:center;justify-content:center;border:1px solid color-mix(in srgb,var(--page-ink) 32%,transparent);background:transparent;color:var(--page-ink);border-radius:var(--radius-sm);padding:5px 9px;cursor:pointer;font-size:11px;font-weight:600;line-height:1.4;white-space:nowrap}.studio-launch:hover{background:var(--sage);color:var(--green-2);border-color:var(--green-2)}
.studio{position:fixed;z-index:1000;inset:0 0 0 auto;margin:0;padding:0;width:min(430px,100%);max-width:100%;height:100dvh;max-height:100dvh;border:0;border-left:1px solid #d7ddd7;background:#f6f7f4;color:#1e2924;box-shadow:-24px 0 70px rgba(10,25,18,.2);font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;overflow:hidden}.studio::backdrop{background:rgba(12,24,19,.42);backdrop-filter:blur(2px)}.studio[open]{display:flex;flex-direction:column}.studio-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;padding:24px 24px 18px;border-bottom:1px solid #dde2dc;background:#fff}.studio-kicker{margin:0 0 5px;color:#738078;font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}.studio-head h2{margin:0;font-family:Georgia,"Songti SC",serif;font-size:25px;font-weight:500}.studio-close{flex:none;width:34px;height:34px;border:1px solid #d8dfd8;border-radius:50%;background:#f5f7f3;color:#34453d;font-size:22px;cursor:pointer}.studio-body{flex:1;min-height:0;overflow-y:auto;padding:20px 24px 28px}.studio-intro{margin:0 0 18px;color:#68766e;font-size:12px;line-height:1.7}.style-recipe{display:flex;align-items:center;gap:8px;background:#e8eee8;border:1px solid #d4ded5;border-radius:10px;padding:10px 12px;margin-bottom:20px;color:#365247;font-size:11px}.style-recipe:before{content:"";width:8px;height:8px;border-radius:50%;background:#628272;box-shadow:0 0 0 4px rgba(98,130,114,.12)}.studio-section{border:0;border-top:1px solid #dce2dc;padding:19px 0 0;margin:0 0 21px}.studio-section legend{padding:0 10px 0 0;color:#263c32;font-size:13px;font-weight:700}.studio-hint{margin:-2px 0 12px;color:#829087;font-size:10px}.preset-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.preset{display:flex;align-items:center;gap:10px;border:1px solid #d8dfd8;background:#fff;border-radius:11px;padding:11px;text-align:left;cursor:pointer;color:#31463c;min-width:0}.preset:hover,.preset[aria-pressed="true"]{border-color:#587769;background:#eef3ee}.preset[aria-pressed="true"]{box-shadow:inset 0 0 0 1px #587769}.preset-swatches{display:flex;flex:none}.preset-swatches i{display:block;width:15px;height:28px;border:1px solid rgba(20,30,25,.12)}.preset-swatches i:first-child{border-radius:6px 0 0 6px}.preset-swatches i:last-child{border-radius:0 6px 6px 0;margin-left:-1px}.preset strong{display:block;font-size:12px}.preset small{display:block;color:#7c8981;font-size:9px;margin-top:2px}.control-stack{display:grid;gap:12px}.color-control{display:grid;grid-template-columns:1fr auto auto;align-items:center;gap:10px;font-size:12px;color:#46574e}.color-control input[type="color"]{width:42px;height:30px;padding:2px;border:1px solid #cfd8d0;border-radius:7px;background:#fff;cursor:pointer}.color-control output{min-width:62px;color:#718077;font-family:Consolas,monospace;font-size:10px;text-transform:uppercase}.select-control{display:grid;grid-template-columns:1fr minmax(150px,1.1fr);align-items:center;gap:14px;font-size:12px;color:#46574e}.select-control select{width:100%;min-width:0;border:1px solid #cfd8d0;border-radius:8px;background:#fff;color:#273d33;padding:8px 9px;cursor:pointer;font-size:11px}.studio-foot{padding:15px 24px 18px;border-top:1px solid #d9e0da;background:#fff}.studio-actions{display:grid;grid-template-columns:1fr 1.4fr;gap:9px}.studio-secondary,.studio-export{border-radius:9px;padding:10px 12px;font-size:12px;font-weight:650;cursor:pointer}.studio-secondary{border:1px solid #ccd6ce;background:#fff;color:#52675d}.studio-export{border:1px solid #294b3d;background:#294b3d;color:#fff}.studio-export:hover{background:#3b6253}.studio-status{min-height:17px;margin:9px 0 0;text-align:center;color:#7a8880;font-size:10px}.studio-note{margin:10px 0 0;color:#8a958e;font-size:9px;line-height:1.55;text-align:center}
.studio-head-actions{display:flex;align-items:center;gap:6px;flex:none}.studio-tool{width:32px;height:32px;border:1px solid #d8dfd8;border-radius:50%;background:#f5f7f3;color:#34453d;font-size:18px;cursor:pointer}.studio-tool:disabled{opacity:.35;cursor:default}.studio-tool:not(:disabled):hover{background:#e5ece6}.scheme-save-row,.scheme-load-row{display:grid;grid-template-columns:1fr auto;gap:8px;margin-top:9px}.scheme-save-row input,.scheme-load-row select,.share-link{width:100%;min-width:0;border:1px solid #cfd8d0;border-radius:8px;background:#fff;color:#273d33;padding:8px 10px;font:inherit;font-size:11px}.scheme-save-row button,.scheme-load-row button,.share-button{border:1px solid #b9c8bd;border-radius:8px;background:#edf2ed;color:#365247;padding:8px 11px;font-size:11px;font-weight:650;cursor:pointer;white-space:nowrap}.scheme-load-row button:disabled{opacity:.4;cursor:default}.contrast-panel{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-top:15px}.contrast-panel div{background:#fff;border:1px solid #dbe2dc;border-radius:8px;padding:8px;text-align:center}.contrast-panel span{display:block;color:#849087;font-size:9px}.contrast-panel strong{display:block;color:#355247;font-size:10px;margin-top:3px;white-space:nowrap}.contrast-hint{margin:8px 0 0;color:#718178;font-size:10px;line-height:1.55}.share-button{width:100%;background:#294b3d;border-color:#294b3d;color:#fff;padding:10px}.share-link{display:block;margin-top:9px;font-family:Consolas,monospace;font-size:9px}.share-link[hidden]{display:none}
@media(max-width:640px){html[data-theme="diy"] .shell{width:calc(100% - 24px)}html[data-theme="diy"] .header-actions{width:auto;min-width:0;margin-left:auto;justify-content:flex-end;gap:12px}html[data-theme="diy"] .studio-launch{flex:none}html[data-theme="diy"] .hero{padding:30px 24px}html[data-theme="diy"][data-distribution="split"] .hero{background:var(--green)}html[data-theme="diy"] .root-grid{min-width:0}html[data-theme="diy"][data-density="compact"] .group-summary{padding:14px}html[data-theme="diy"][data-density="spacious"] .group-summary{padding:22px 18px}html[data-theme="diy"][data-shadow="hard"] .hero{box-shadow:4px 5px 0 var(--ink)}html[data-theme="diy"][data-shadow="hard"] .workspace{box-shadow:4px 5px 0 var(--ink)}html[data-theme="diy"][data-shadow="hard"] .root-card{box-shadow:3px 3px 0 var(--ink)}.studio{inset:auto 0 0 0;width:100%;height:58dvh;max-height:58dvh;border-left:0;border-top:1px solid #d7ddd7;border-radius:18px 18px 0 0;box-shadow:0 -18px 50px rgba(10,25,18,.18)}.studio::backdrop{background:rgba(12,24,19,.12);backdrop-filter:none}.studio-head{padding:13px 16px 10px}.studio-head h2{font-size:21px}.studio-kicker{font-size:8px;margin-bottom:3px}.studio-body{padding:14px 16px 20px}.studio-foot{padding:10px 16px 12px}.studio-intro{font-size:11px;margin-bottom:12px}.style-recipe{margin-bottom:14px}.studio-note{display:none}}
@media(max-width:390px){html[data-theme="diy"] .header-actions .about-button{display:none}html[data-theme="diy"] .studio-launch{width:auto}.studio-actions{grid-template-columns:1fr 1.25fr}.select-control{grid-template-columns:1fr 140px}}
@media(prefers-reduced-motion:reduce){html[data-theme="diy"] *{scroll-behavior:auto!important;transition:none!important}}
'''


DIY_STUDIO = r'''
<dialog class="studio" id="studioDialog" aria-labelledby="studioTitle">
  <div class="studio-head"><div><p class="studio-kicker">Root Atlas / Design system</p><h2 id="studioTitle">DIY 风格实验室</h2></div><div class="studio-head-actions"><button class="studio-tool" id="undoDIY" type="button" aria-label="撤销" title="撤销" disabled>↶</button><button class="studio-tool" id="redoDIY" type="button" aria-label="重做" title="重做" disabled>↷</button><button class="studio-close" id="closeStudio" type="button" aria-label="关闭风格实验室">×</button></div></div>
  <div class="studio-body">
    <p class="studio-intro">先选一套起点，再独立调整每个元素。所有修改都会实时应用到背后的词根图谱。</p>
    <div class="style-recipe" id="styleRecipe">深色夜幕 · 小圆角 · 古典衬线</div>
    <fieldset class="studio-section"><legend>01 · 起点方案</legend><p class="studio-hint">预设不会锁定任何参数，选择后仍可自由组合。</p><div class="preset-grid">
      <button class="preset" type="button" data-preset="minimal" aria-pressed="false"><span class="preset-swatches" aria-hidden="true"><i style="background:#171a18"></i><i style="background:#fafaf7"></i></span><span><strong>简约 · 极净</strong><small>留白 / 尖角 / 无阴影</small></span></button>
      <button class="preset" type="button" data-preset="classical" aria-pressed="false"><span class="preset-swatches" aria-hidden="true"><i style="background:#5b302a"></i><i style="background:#b08a4c"></i></span><span><strong>古典 · 典藏</strong><small>纸纹 / 衬线 / 酒红金</small></span></button>
      <button class="preset" type="button" data-preset="elegant" aria-pressed="true"><span class="preset-swatches" aria-hidden="true"><i style="background:#173f35"></i><i style="background:#c39761"></i></span><span><strong>优雅 · 夜幕</strong><small>深绿 / 浮起 / 小圆角</small></span></button>
      <button class="preset" type="button" data-preset="joyful" aria-pressed="false"><span class="preset-swatches" aria-hidden="true"><i style="background:#72bdb0"></i><i style="background:#ef91a8"></i></span><span><strong>欢乐 · 轻盈</strong><small>奶油 / 彩点 / 圆角</small></span></button>
    </div></fieldset>
    <fieldset class="studio-section"><legend>02 · 我的方案</legend><p class="studio-hint">最多保存 30 套，方案仅保存在当前浏览器。</p><div class="scheme-save-row"><input id="schemeName" type="text" maxlength="24" placeholder="方案名称，例如 周末清爽" aria-label="方案名称"><button id="saveScheme" type="button">保存方案</button></div><div class="scheme-load-row"><select id="savedSchemes" aria-label="载入已保存方案"><option value="">载入已保存方案</option></select><button id="deleteScheme" type="button" disabled>删除</button></div></fieldset>
    <fieldset class="studio-section"><legend>03 · 色彩</legend><p class="studio-hint">文字与辅助色会自动计算，优先保持可读对比度。</p><div class="control-stack">
      <label class="color-control"><span>主色调</span><input type="color" data-diy="primary" value="#173f35" aria-label="主色调"><output data-color-output="primary">#173f35</output></label>
      <label class="color-control"><span>强调色</span><input type="color" data-diy="accent" value="#c39761" aria-label="强调色"><output data-color-output="accent">#c39761</output></label>
      <label class="color-control"><span>页面底色</span><input type="color" data-diy="background" value="#112f29" aria-label="页面底色"><output data-color-output="background">#112f29</output></label>
      <label class="select-control"><span>色彩分布</span><select data-diy="distribution"><option value="focus">主色焦点</option><option value="night">深色夜幕</option><option value="split">双色分区</option><option value="air">无底色留白</option><option value="confetti">浅色乐园</option></select></label>
    </div><div class="contrast-panel"><div><span>正文</span><strong id="contrastBody">—</strong></div><div><span>主色按钮</span><strong id="contrastPrimary">—</strong></div><div><span>强调文字</span><strong id="contrastAccent">—</strong></div></div><p class="contrast-hint" id="contrastHint">关键文字以达到 4.5:1 对比度为目标。</p></fieldset>
    <fieldset class="studio-section"><legend>04 · 形状与字体</legend><div class="control-stack">
      <label class="select-control"><span>边框形状</span><select data-diy="radius"><option value="sharp">尖角边框</option><option value="soft">小圆角</option><option value="round">圆形 / 大圆角</option></select></label>
      <label class="select-control"><span>字体气质</span><select data-diy="font"><option value="sans">现代无衬线</option><option value="serif">古典衬线</option><option value="rounded">活泼粗体</option></select></label>
    </div></fieldset>
    <fieldset class="studio-section"><legend>05 · 质感与密度</legend><div class="control-stack">
      <label class="select-control"><span>背景纹理</span><select data-diy="texture"><option value="none">无纹理</option><option value="paper">细腻纸纹</option><option value="dots">彩色点阵</option><option value="grid">编辑网格</option></select></label>
      <label class="select-control"><span>阴影层级</span><select data-diy="shadow"><option value="none">完全扁平</option><option value="soft">柔和阴影</option><option value="lifted">悬浮投影</option><option value="hard">撞色硬投影</option></select></label>
      <label class="select-control"><span>内容密度</span><select data-diy="density"><option value="compact">紧凑</option><option value="comfortable">舒适</option><option value="spacious">疏朗</option></select></label>
    </div></fieldset>
    <fieldset class="studio-section"><legend>06 · 轻量分享</legend><p class="studio-hint">链接只包含风格配置，对方需要有同一个 DIY HTML；分享全部词库请使用下方的完整导出。</p><button class="share-button" id="shareDIY" type="button">复制配置链接</button><input class="share-link" id="shareLink" type="text" readonly hidden aria-label="配置分享链接"></fieldset>
  </div>
  <div class="studio-foot"><div class="studio-actions"><button class="studio-secondary" id="resetDIY" type="button">恢复默认</button><button class="studio-export" id="exportDIY" type="button">导出我的 HTML</button></div><p class="studio-status" id="diyStatus" role="status">修改会实时预览并自动保存</p><p class="studio-note">导出文件包含当前风格及全部四考试数据，可离线打开；学习数据不受影响。</p></div>
</dialog>
'''


DIY_JS = r'''
const DIY_STORAGE_KEY = "rootAtlas.diyConfig.v1";
const DIY_DEFAULT = {primary:"#173f35",accent:"#c39761",background:"#112f29",distribution:"night",radius:"soft",font:"serif",texture:"none",shadow:"lifted",density:"comfortable"};
const DIY_PRESETS = {
  minimal:{primary:"#171a18",accent:"#62786d",background:"#fafaf7",distribution:"air",radius:"sharp",font:"sans",texture:"none",shadow:"none",density:"comfortable"},
  classical:{primary:"#5b302a",accent:"#b08a4c",background:"#eee2c9",distribution:"focus",radius:"sharp",font:"serif",texture:"paper",shadow:"soft",density:"spacious"},
  elegant:{...DIY_DEFAULT},
  joyful:{primary:"#72bdb0",accent:"#ef91a8",background:"#fffaf0",distribution:"confetti",radius:"round",font:"sans",texture:"dots",shadow:"soft",density:"comfortable"}
};
const DIY_OPTIONS = {distribution:["focus","night","split","air","confetti"],radius:["sharp","soft","round"],font:["sans","serif","rounded"],texture:["none","paper","dots","grid"],shadow:["none","soft","lifted","hard"],density:["compact","comfortable","spacious"]};
const DIY_LABELS = {distribution:{focus:"主色焦点",night:"深色夜幕",split:"双色分区",air:"无底色留白",confetti:"浅色乐园"},radius:{sharp:"尖角边框",soft:"小圆角",round:"大圆角"},font:{sans:"现代无衬线",serif:"古典衬线",rounded:"活泼粗体"},texture:{none:"无纹理",paper:"细腻纸纹",dots:"彩色点阵",grid:"编辑网格"},shadow:{none:"完全扁平",soft:"柔和阴影",lifted:"悬浮投影",hard:"撞色硬投影"},density:{compact:"紧凑",comfortable:"舒适",spacious:"疏朗"}};
const studio = document.getElementById("studioDialog");
const diyStatus = document.getElementById("diyStatus");
const DIY_SCHEMES_KEY = "rootAtlas.diySchemes.v1";
const DIY_SHARE_VERSION = 1;
const DIY_SHARE_KEYS = {p:"primary",a:"accent",b:"background",d:"distribution",r:"radius",f:"font",t:"texture",s:"shadow",n:"density"};
let diyConfig = {...DIY_DEFAULT};
let diySchemes = [];
let selectedSchemeId = "";
let diyHistory = [];
let diyHistoryIndex = -1;
function sanitizeDIY(candidate){
  const source=candidate&&typeof candidate==="object"&&!Array.isArray(candidate)?candidate:{};
  const clean={...DIY_DEFAULT};
  ["primary","accent","background"].forEach(key=>{if(typeof source[key]==="string"&&/^#[0-9a-fA-F]{6}$/.test(source[key]))clean[key]=source[key].toLowerCase();});
  Object.entries(DIY_OPTIONS).forEach(([key,values])=>{if(values.includes(source[key]))clean[key]=source[key];});
  return clean;
}
function rgbFromHex(hex){return [parseInt(hex.slice(1,3),16),parseInt(hex.slice(3,5),16),parseInt(hex.slice(5,7),16)];}
function hexFromRgb(rgb){return "#"+rgb.map(value=>Math.max(0,Math.min(255,Math.round(value))).toString(16).padStart(2,"0")).join("");}
function mixColor(first,second,amount){const a=rgbFromHex(first),b=rgbFromHex(second);return hexFromRgb(a.map((value,index)=>value+(b[index]-value)*amount));}
function luminance(hex){const channels=rgbFromHex(hex).map(value=>{const channel=value/255;return channel<=.04045?channel/12.92:Math.pow((channel+.055)/1.055,2.4);});return channels[0]*.2126+channels[1]*.7152+channels[2]*.0722;}
function contrastRatio(first,second){const a=luminance(first),b=luminance(second);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);}
function readableText(background){const dark="#17251f",light="#fffaf0";return contrastRatio(background,dark)>=contrastRatio(background,light)?dark:light;}
function ensureContrast(color,background){if(contrastRatio(color,background)>=4.5)return color;const target=readableText(background);let result=color;for(let step=1;step<=10;step++){result=mixColor(color,target,step/10);if(contrastRatio(result,background)>=4.5)break;}return result;}
function applyDIY(candidate,{save=true,message="已实时应用并保存",track=true,clearScheme=true}={}){
  diyConfig=sanitizeDIY(candidate);
  if(clearScheme){selectedSchemeId="";renderSchemeOptions();}
  const root=document.documentElement;
  Object.entries({distribution:diyConfig.distribution,radius:diyConfig.radius,font:diyConfig.font,texture:diyConfig.texture,shadow:diyConfig.shadow,density:diyConfig.density}).forEach(([key,value])=>root.dataset[key]=value);
  const darkPage=luminance(diyConfig.background)<.36;
  let card=darkPage?mixColor(diyConfig.background,"#ffffff",.1):mixColor(diyConfig.background,"#ffffff",.72);
  if(diyConfig.distribution==="night")card=mixColor("#fffaf0",diyConfig.accent,.035);
  if(diyConfig.distribution==="air")card=mixColor(diyConfig.background,"#ffffff",.88);
  const ink=readableText(card),pageInk=readableText(diyConfig.background);
  const greenText=ensureContrast(diyConfig.primary,card),accentText=ensureContrast(diyConfig.accent,card);
  let heroBackground=diyConfig.primary,heroInk=readableText(diyConfig.primary);
  if(diyConfig.distribution==="night")heroBackground=`linear-gradient(135deg,${mixColor(diyConfig.primary,"#000000",.08)},${mixColor(diyConfig.primary,"#000000",.36)})`;
  if(diyConfig.distribution==="split")heroBackground=`linear-gradient(120deg,${diyConfig.primary} 0%,${diyConfig.primary} 62%,${diyConfig.accent} 62%,${diyConfig.accent} 100%)`;
  if(diyConfig.distribution==="confetti"){heroBackground=`linear-gradient(135deg,${mixColor(diyConfig.background,"#ffffff",.58)},${mixColor(diyConfig.background,diyConfig.primary,.08)})`;heroInk=pageInk;}
  if(diyConfig.distribution==="air"){heroBackground="transparent";heroInk=pageInk;}
  const variables={
    "--paper":diyConfig.background,"--card":card,"--ink":ink,"--muted":mixColor(ink,card,.4),"--line":mixColor(ink,card,.83),
    "--green":diyConfig.primary,"--green-2":greenText,"--accent":diyConfig.accent,"--accent-text":accentText,
    "--accent-soft":mixColor(diyConfig.accent,card,.82),"--sage":mixColor(diyConfig.primary,card,.87),"--field":mixColor(card,ink,.035),
    "--page-ink":pageInk,"--page-muted":mixColor(pageInk,diyConfig.background,.38),"--hero-bg":heroBackground,"--hero-ink":heroInk,
    "--on-primary":readableText(diyConfig.primary),"--on-accent":readableText(diyConfig.accent),
    "--hero-line":diyConfig.distribution==="air"?mixColor(pageInk,diyConfig.background,.78):mixColor(heroInk,diyConfig.primary,.66)
  };
  Object.entries(variables).forEach(([key,value])=>root.style.setProperty(key,value));
  updateContrastPanel(card,ink,greenText,accentText);
  syncDIYControls();
  if(track)recordDIYHistory();
  updateHistoryControls();
  if(save)try{localStorage.setItem(DIY_STORAGE_KEY,JSON.stringify(diyConfig));}catch{}
  diyStatus.textContent=message;
}
function syncDIYControls(){
  document.querySelectorAll("[data-diy]").forEach(control=>{control.value=diyConfig[control.dataset.diy];});
  document.querySelectorAll("[data-color-output]").forEach(output=>{output.value=diyConfig[output.dataset.colorOutput].toUpperCase();});
  document.querySelectorAll("[data-preset]").forEach(button=>{const preset=DIY_PRESETS[button.dataset.preset];button.setAttribute("aria-pressed",Object.keys(DIY_DEFAULT).every(key=>preset[key]===diyConfig[key]));});
  document.getElementById("styleRecipe").textContent=[DIY_LABELS.distribution[diyConfig.distribution],DIY_LABELS.radius[diyConfig.radius],DIY_LABELS.font[diyConfig.font],DIY_LABELS.shadow[diyConfig.shadow]].join(" · ");
}
function updateContrastPanel(card,ink,greenText,accentText){
  const entries=[["contrastBody",contrastRatio(ink,card)],["contrastPrimary",contrastRatio(readableText(diyConfig.primary),diyConfig.primary)],["contrastAccent",contrastRatio(accentText,card)]];
  let hasLowContrast=false;
  entries.forEach(([id,ratio])=>{const grade=ratio>=7?"优秀":ratio>=4.5?"良好":"偏低";if(ratio<4.5)hasLowContrast=true;document.getElementById(id).textContent=`${ratio.toFixed(1)}:1 · ${grade}`;});
  const adjusted=greenText!==diyConfig.primary||accentText!==diyConfig.accent;
  document.getElementById("contrastHint").textContent=hasLowContrast?"部分对比度仍然偏低，建议调整对应颜色。":adjusted?"已自动增强过浅的文字色，你选择的背景色保持不变。":"正文、按钮和强调文字均达到 WCAG AA（4.5:1）。";
}
function recordDIYHistory(){
  if(diyHistoryIndex>=0&&JSON.stringify(diyHistory[diyHistoryIndex])===JSON.stringify(diyConfig))return;
  diyHistory=diyHistory.slice(0,diyHistoryIndex+1);
  diyHistory.push({...diyConfig});
  if(diyHistory.length>60)diyHistory.shift();
  diyHistoryIndex=diyHistory.length-1;
}
function updateHistoryControls(){
  document.getElementById("undoDIY").disabled=diyHistoryIndex<=0;
  document.getElementById("redoDIY").disabled=diyHistoryIndex<0||diyHistoryIndex>=diyHistory.length-1;
}
function travelDIY(offset){
  const next=diyHistoryIndex+offset;
  if(next<0||next>=diyHistory.length)return;
  diyHistoryIndex=next;
  applyDIY(diyHistory[next],{track:false,message:offset<0?"已撤销上一步修改":"已重做修改"});
}
function loadDIYSchemes(){
  try{
    const parsed=JSON.parse(localStorage.getItem(DIY_SCHEMES_KEY));
    if(Array.isArray(parsed))diySchemes=parsed.filter(item=>item&&typeof item.id==="string"&&typeof item.name==="string").slice(0,30).map(item=>({id:item.id,name:item.name.trim().slice(0,24)||"未命名方案",config:sanitizeDIY(item.config)}));
  }catch{}
}
function persistDIYSchemes(){try{localStorage.setItem(DIY_SCHEMES_KEY,JSON.stringify(diySchemes));}catch{}}
function renderSchemeOptions(){
  const select=document.getElementById("savedSchemes");
  select.replaceChildren(new Option("载入已保存方案",""));
  diySchemes.forEach(scheme=>select.add(new Option(scheme.name,scheme.id)));
  select.value=diySchemes.some(scheme=>scheme.id===selectedSchemeId)?selectedSchemeId:"";
  document.getElementById("deleteScheme").disabled=!select.value;
}
function saveDIYScheme(){
  const input=document.getElementById("schemeName");
  const name=input.value.trim().slice(0,24)||`我的方案 ${diySchemes.length+1}`;
  const existing=diySchemes.find(scheme=>scheme.name===name);
  if(existing){existing.config={...diyConfig};selectedSchemeId=existing.id;}
  else{
    if(diySchemes.length>=30){diyStatus.textContent="最多保存 30 套方案，请先删除不再使用的方案";return;}
    const id=Date.now().toString(36)+Math.random().toString(36).slice(2,8);
    diySchemes.push({id,name,config:{...diyConfig}});selectedSchemeId=id;
  }
  persistDIYSchemes();input.value=name;renderSchemeOptions();
  diyStatus.textContent=`${existing?"已更新":"已保存"}方案「${name}」`;
}
function loadDIYScheme(){
  const id=document.getElementById("savedSchemes").value;
  const scheme=diySchemes.find(item=>item.id===id);
  if(!scheme)return;
  applyDIY(scheme.config,{clearScheme:false,message:`已载入方案「${scheme.name}」`});
  selectedSchemeId=id;document.getElementById("schemeName").value=scheme.name;renderSchemeOptions();
}
function deleteDIYScheme(){
  const scheme=diySchemes.find(item=>item.id===selectedSchemeId);
  if(!scheme||!window.confirm(`删除方案「${scheme.name}」？当前页面风格会保留。`))return;
  diySchemes=diySchemes.filter(item=>item.id!==scheme.id);selectedSchemeId="";
  persistDIYSchemes();renderSchemeOptions();document.getElementById("schemeName").value="";
  diyStatus.textContent=`已删除方案「${scheme.name}」，当前风格未改变`;
}
function encodeDIYShare(config){
  const packed={v:DIY_SHARE_VERSION};
  Object.entries(DIY_SHARE_KEYS).forEach(([short,key])=>packed[short]=config[key]);
  return btoa(JSON.stringify(packed)).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,"");
}
function decodeDIYShare(encoded){
  if(!encoded||encoded.length>2048||!/^[A-Za-z0-9_-]+$/.test(encoded))throw new Error("Invalid share payload");
  const normalized=encoded.replace(/-/g,"+").replace(/_/g,"/");
  const packed=JSON.parse(atob(normalized+"=".repeat((4-normalized.length%4)%4)));
  if(!packed||typeof packed!=="object"||Array.isArray(packed)||packed.v!==DIY_SHARE_VERSION)throw new Error("Unsupported share version");
  const candidate={};
  Object.entries(DIY_SHARE_KEYS).forEach(([short,key])=>{if(Object.hasOwn(packed,short))candidate[key]=packed[short];});
  const config=sanitizeDIY(candidate);
  const repaired=Object.keys(DIY_DEFAULT).some(key=>candidate[key]!==config[key]);
  return {config,repaired};
}
function initialDIY(){
  let shareError="";
  const shared=new URLSearchParams(location.hash.slice(1)).get("style");
  if(shared){
    try{const decoded=decodeDIYShare(shared);return {config:decoded.config,message:decoded.repaired?"链接中的部分配置无效，已用默认值修复":"已载入分享链接中的风格"};}
    catch{shareError="分享链接无效或版本不兼容";}
  }
  if(window.__ROOT_ATLAS_DIY_EXPORT__&&typeof window.__ROOT_ATLAS_DIY_EXPORT__==="object")return {config:sanitizeDIY(window.__ROOT_ATLAS_DIY_EXPORT__),message:shareError||"已载入此文件内嵌的自定义风格"};
  try{const saved=JSON.parse(localStorage.getItem(DIY_STORAGE_KEY));if(saved&&typeof saved==="object")return {config:sanitizeDIY(saved),message:shareError?shareError+"；已恢复本地风格":"已载入你保存的自定义风格"};}catch{}
  return {config:{...DIY_DEFAULT},message:shareError||"选择起点，或逐项调整你的风格"};
}
async function shareDIY(){
  const url=new URL(location.href);url.hash="style="+encodeDIYShare(diyConfig);
  const input=document.getElementById("shareLink");input.hidden=false;input.value=url.href;
  let copied=false;
  try{if(navigator.clipboard){await navigator.clipboard.writeText(url.href);copied=true;}}catch{}
  if(!copied)try{input.focus();input.select();copied=document.execCommand("copy");}catch{}
  diyStatus.textContent=copied?"已复制轻量配置链接":"请选中链接并手动复制";
}
function exportDIY(){
  const clone=document.documentElement.cloneNode(true);
  clone.querySelector("#studioDialog")?.removeAttribute("open");
  clone.querySelector("#studyDialog")?.removeAttribute("open");
  clone.querySelector("#aboutDialog")?.removeAttribute("open");
  clone.querySelector("#shareLink")?.setAttribute("hidden","");
  const configScript=clone.querySelector("#diyExportedConfig");
  configScript.textContent="window.__ROOT_ATLAS_DIY_EXPORT__="+JSON.stringify(diyConfig).replace(/</g,"\\u003c")+";";
  const blob=new Blob(["<!doctype html>\n"+clone.outerHTML],{type:"text/html;charset=utf-8"});
  const url=URL.createObjectURL(blob),link=document.createElement("a");
  link.href=url;link.download="root-atlas-my-style.html";link.hidden=true;document.body.appendChild(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
  diyStatus.textContent="已导出包含当前风格的完整离线 HTML";
}
function openDIYStudio(){
  if(studio.open)return;
  syncDIYControls();
  if(window.matchMedia("(max-width:640px)").matches)studio.show();else studio.showModal();
}
document.getElementById("openStudioTop").addEventListener("click",openDIYStudio);
document.getElementById("closeStudio").addEventListener("click",()=>studio.close());
studio.addEventListener("click",event=>{if(event.target===studio&&window.matchMedia("(min-width:641px)").matches)studio.close();});
document.addEventListener("keydown",event=>{if(event.key==="Escape"&&studio.open&&!studio.matches(":modal"))studio.close();});
document.querySelectorAll("[data-preset]").forEach(button=>button.addEventListener("click",()=>applyDIY(DIY_PRESETS[button.dataset.preset],{message:"已应用起点方案，可继续逐项调整"})));
document.querySelectorAll("[data-diy]").forEach(control=>control.addEventListener("input",()=>applyDIY({...diyConfig,[control.dataset.diy]:control.value})));
document.getElementById("undoDIY").addEventListener("click",()=>travelDIY(-1));
document.getElementById("redoDIY").addEventListener("click",()=>travelDIY(1));
document.getElementById("saveScheme").addEventListener("click",saveDIYScheme);
document.getElementById("savedSchemes").addEventListener("change",loadDIYScheme);
document.getElementById("deleteScheme").addEventListener("click",deleteDIYScheme);
document.getElementById("shareDIY").addEventListener("click",shareDIY);
document.getElementById("shareLink").addEventListener("click",event=>event.target.select());
window.addEventListener("hashchange",()=>{
  const shared=new URLSearchParams(location.hash.slice(1)).get("style");
  if(!shared)return;
  try{const decoded=decodeDIYShare(shared);applyDIY(decoded.config,{save:false,message:decoded.repaired?"链接中的部分配置无效，已用默认值修复":"已载入分享链接中的风格"});}
  catch{diyStatus.textContent="分享链接无效或版本不兼容，当前风格未改变";}
});
document.getElementById("resetDIY").addEventListener("click",()=>applyDIY(DIY_DEFAULT,{message:"已恢复默认风格"}));
document.getElementById("exportDIY").addEventListener("click",exportDIY);
loadDIYSchemes();renderSchemeOptions();
const initialDIYState=initialDIY();
applyDIY(initialDIYState.config,{save:false,message:initialDIYState.message,track:false,clearScheme:false});
diyHistory=[{...diyConfig}];diyHistoryIndex=0;updateHistoryControls();
'''


if __name__ == "__main__":
    build()
