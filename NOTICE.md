# 数据来源、署名与许可

Root Atlas 的原创脚本和界面代码使用根目录 `LICENSE` 中的 MIT License。该许可**不覆盖**第三方词典、构词数据、词源材料及其派生内容；各项数据保留各自许可。公开使用或再分发时，必须同时保留下列署名和对应许可。

## 非商业限制

本项目包含 MorphoLex-EN 及其派生构词切分，依据 **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International（CC BY-NC-SA 4.0）** 使用。因此，本项目的相关派生数据与包含这些数据的离线 HTML **仅限非商业目的**，派生切分须以相同许可共享。

- 许可：https://creativecommons.org/licenses/by-nc-sa/4.0/
- 本地许可文本：`licenses/MorphoLex-CC-BY-NC-SA-4.0.md`

## ECDICT

- 项目：ECDICT / Free English to Chinese Dictionary Database
- 作者与维护者：Linwei 及项目贡献者
- 来源：https://github.com/skywind3000/ECDICT
- 许可：MIT
- 本地许可文本：`licenses/ECDICT-MIT.txt`
- 使用内容：CET4/CET6/IELTS/TOEFL 标签、中文翻译、英文自由词词典释义、词形变化、大部分音标。
- 修改：按考试标签筛选，还原 lemma，整理为词族和独立词，并将文本嵌入离线 HTML。ECDICT 的“自由词词典释义”不是古典词源本义，界面中分别标注。

## MorphoLex-EN

- 项目：MorphoLex-EN
- 来源：https://github.com/hugomailhot/MorphoLex-en
- 许可：CC BY-NC-SA 4.0
- 使用内容：英文单词的词根、前缀、后缀切分和 PRS 完整性信息。
- 修改：解析原始工作表，与 RootLearner 和外部词源资料回链，进行逐词复核、分组并嵌入离线 HTML。
- 引用：Sánchez-Gutiérrez, C.H., Mailhot, H., Deacon, S.H. et al. *Behavior Research Methods* (2017). https://doi.org/10.3758/s13428-017-0981-8

## RootLearner

- 项目：RootLearner
- 来源：https://github.com/gyd-07/RootLearner
- 使用内容：342 个词根组的英文释义与审核例词，只读衔接。
- 修改：按词根 ID、根形、释义与审核例词回链；没有覆盖或替换 RootLearner 的词库和学习记录。

## Wikipedia

- 材料：*List of Greek and Latin roots in English* 及其分字母页面
- 作者：Wikipedia contributors
- 入口：https://en.wikipedia.org/wiki/List_of_Greek_and_Latin_roots_in_English
- 许可：Creative Commons Attribution-ShareAlike 4.0 International（CC BY-SA 4.0）
- 许可：https://creativecommons.org/licenses/by-sa/4.0/
- 使用内容：部分词源词根释义和匹配例词。
- 修改：按根形和适用单词筛选、复核并整理为词族；每条记录保留来源页。相关派生释义继续按 CC BY-SA 4.0 共享。

## Wiktionary

- 材料：English Wiktionary 词条中的词源信息
- 作者：Wiktionary contributors
- 来源：https://en.wiktionary.org/
- 许可：Creative Commons Attribution-ShareAlike 4.0 International（CC BY-SA 4.0）
- 许可：https://creativecommons.org/licenses/by-sa/4.0/
- 使用内容：逐词族复核的英文词源释义。
- 修改：按“根形＋适用单词”筛选、消歧并整理为词族；分析输出和 demo 中保留具体来源条目与链接。相关派生释义继续按 CC BY-SA 4.0 共享。

## CMUdict

- 项目：CMUdict / Carnegie Mellon University Pronouncing Dictionary
- 来源：https://github.com/cmusphinx/cmudict
- 许可：BSD
- 使用内容：为 ECDICT 缺失或格式异常的音标提供发音依据。
- 修改：在构建数据阶段通过 `eng_to_ipa` 0.0.2 转为 IPA；327 个词条由该路径补齐，全部音标静态嵌入，无运行时依赖。
- `eng_to_ipa` 0.0.2 仅作为临时构建辅助工具，未作为第三方运行时代码分发；其包元数据未明确声明许可证，不能据此标为 MIT。

## 逐项补充与整理

16 个未被上述自动路径覆盖的派生词、拼写变体和缩写逐项补充音标。词根归属、同形词源消歧、独立词保留和页面代码还包含项目作者及 AI 辅助的整理工作。

“复核队列为 0”只表示当前程序规则下没有剩余待处理记录，不等于所有词源判断已经人工审定。“独立词汇项”也不等于该词在词源上无根。
