# Root Atlas · 四考试词根图谱

Root Atlas 是一个独立的英语词根分析、浏览与离线背诵项目，覆盖 CET4、CET6、IELTS 和 TOEFL。它将单词组织为词根词族，展示构词结构、英文词根释义、中文释义和音标，并提供可自定义视觉风格的完整背诵流程。

> **非商业研究预览**：本项目包含 MorphoLex-EN 派生内容，只能用于非商业目的。自动分析与逐项复核结合，但不是全部词源判断均已人工审定的语言学数据集。详细署名与许可见 [NOTICE.md](NOTICE.md)。

## 直接使用

无需安装依赖或启动服务器，使用现代浏览器打开以下文件即可，支持 `file://` 离线运行：

| 文件 | 内容 |
|---|---|
| `demo/diy.html` | **完整版本**：四考试词根浏览、全部单词音标、翻卡与测试、错词重练、独立进度、风格 DIY |
| `demo/index.html` | 原始浏览 demo：简约、古典、优雅、欢乐四种主题 |
| `demo/extended.html` | 风格延伸版：四种主题的进一步强化设计 |

三个历史 demo 均保留。完整版本的背诵界面与当前封面共享视觉系统，DIY 是右上角的小工具，不改变页面主要内容。

## 功能与数据

- 四考试完整标签词条：CET4 3,834、CET6 5,395、IELTS 5,007、TOEFL 6,951；考试之间允许重叠。
- 合并后 10,510 个不同单词，全部具有非空音标。
- 词根词族、独立词汇项、构词切分、英文释义类型和逐项来源。
- 单词搜索、词族筛选、排序、来源链接与全部单词浏览。
- 独立翻卡学习、选择题测试、错词重练和完成统计。
- 60 步 DIY 撤销/重做、命名方案、对比度检查、配置分享、HTML 导出和移动端预览。
- 单文件离线页面，无第三方运行时库、外部字体或网络请求。

背诵进度使用 `rootAtlas.study.v1`，**不会读取或写入 RootLearner 的 `rootLearner.v1`**。进度只存于当前浏览器，按文件路径隔离。

## 构建与测试

开发脚本使用 Python 标准库。重新生成三份 demo：

```bash
python build_demo.py
python build_demo_extended.py
python build_demo_diy.py
```

构建脚本读取已提交的四考试输出和 `data/phonetics.json`，会在音标缺失、释义为空或输出检查不完整时直接报错。

运行分析器回归测试：

```bash
python -m unittest -v
```

原始 ECDICT CSV 与 MorphoLex XLSX 不随仓库分发。若需从原始数据重新生成中间数据，请按 [NOTICE.md](NOTICE.md) 的来源获取文件并放入 `data/raw/`；缺少这些可选原始文件时，对应原始文件检查会跳过。直接浏览 demo 和重新构建 demo 不需要下载它们。

## 目录

```text
root-atlas/
├── demo/                     # 可直接打开的三份离线 HTML
├── data/                     # 分析索引、复核结果、音标与来源信息
├── output/                   # CET4/CET6/IELTS/TOEFL 完整分析输出
├── licenses/                 # 随第三方数据保留的许可文本
├── root_analyzer.py          # 词根切分、回链与保守复核
├── generate_exam.py          # 四考试分组、释义补全与输出
├── prepare_root_meanings.py  # 外部词根释义准备
├── build_demo.py             # 原始浏览 demo
├── build_demo_extended.py    # 风格延伸 demo
├── build_demo_diy.py         # 完整背诵与 DIY demo
└── test_analyzer.py          # 分析器与输出回归测试
```

## 许可

原创脚本与界面代码使用 MIT License；第三方数据及其派生内容仍分别遵循原许可，不因仓库根目录的 MIT License 而改变。尤其注意：

- MorphoLex-EN 及其派生切分：**CC BY-NC-SA 4.0，仅限非商业使用，并须同许可共享**。
- Wikipedia 与 Wiktionary 内容：CC BY-SA 4.0。
- ECDICT：MIT；CMUdict：BSD。

完整来源、修改说明和引用方式见 [NOTICE.md](NOTICE.md)。
