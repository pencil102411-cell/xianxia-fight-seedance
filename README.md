# xianxia-fight-seedance

**仙侠打斗 · Seedance 2.5 提示词**：把打戏、斗法、空中缠斗、法术对轰、飞剑法阵、化身变身、人斗巨兽、放大招、破防受击写成可以直接生成的中文提示词；也能设计一场打戏的招式节奏、强弱关系和切镜衔接，拆一场戏分几条，写首帧单镜头，规划法术特效设定图，并按生成结果或粗剪镜头号一轮轮返修。

知识有三个来源：

- **三段参考打戏的逐帧拆解**：共 445 秒、12,760 帧、363 个镜头。切镜、闪亮、镜长都用脚本算过，结论写在 `references/` 里，每条都标了原片时间码。
- **一场空中打戏的实测**：一场两人高空云海白天打戏（冰系对火系），在 Seedance 2.5 上跑了 13 批、约 75 条，改了四轮，粗剪 139 秒、99 刀。哪些写法有效、哪些会出问题，写在 [references/实测经验.md](references/实测经验.md)。
- **公开 AI 打斗作品的镜头字幕**：15 条 Seedance 2.5 打斗作品，作者把每个镜头的景别和关键句打在画面上。补了贴身兵刃连招、法术成形、破坏顺序、几种运镜和句式，标「未实测」。

标了「实测」的说法在 Seedance 上跑过；没标的是从参考片总结的，冲突时以实测为准。

采用 [Agent Skills](https://agentskills.io) 开放格式：Claude Code、Codex 等支持该格式的 agent 可以直接安装；不支持技能的平台也能当系统提示词使用。

## 能做什么

| 任务 | 交付 |
| --- | --- |
| 写打戏提示词 | 五区块提示词（素材引用 / 生成目标 / 光影设计 / 时间轴 / 保持一致），可直接上玄上画布 |
| 设计一场打戏 | 强弱关系、拍型、镜头表、拆条和两条之间怎么接；附一整场的结构模板 |
| 按结果返修 | 按粗剪镜头号对到原片和提示词，查实测经验找原因，只改受影响的段落 |
| 首帧单镜头 | 从一张首帧图一镜到底跑一个镜头的写法 |
| 特效设定图 | 哪些法术要出图、图要怎样、在提示词里怎么引用 |
| 检查提示词 | `scripts/check_prompt.py` 查格式、常见遗漏和实测踩过的坑 |

本仓库只写提示词，不调用任何生成服务。

## 目录

| 文件 | 内容 |
| --- | --- |
| `SKILL.md` | 工作流程、打戏底线、多轮返修、十三条核心规律、输出格式 |
| `references/实测经验.md` | 实测问题、原因、改法和验证状态，分九类 |
| `references/节奏拍型.md` | 节奏数据、十八个拍型、一整场的模板、实测出片数据 |
| `references/特效光效.md` | 配色、受光、爆炸分层、护盾法阵、冰火、化身、特效图准备、高空云海 |
| `references/运镜与衔接.md` | 机位、运镜、过刀、强运镜、两条之间怎么接 |
| `references/武打与施法动作.md` | 定姿、手势、受击、近身缠斗、强弱对比、缩地成寸、表情和带伤 |
| `references/Seedance写法与返修.md` | 符号、素材引用、时间轴细则、首帧单镜头、返修表 |
| `references/完整示例.md` | 五条成品提示词，示例四是实测跑过的（附生成结果），示例五用的是标「未实测」的写法 |
| `references/看片索引.md` | 三段参考片的时间码索引 |

## 安装

仓库根目录就是技能目录。克隆到所用 agent 的技能目录，文件夹名保持 `xianxia-fight-seedance`。

| Agent | 技能目录 |
| --- | --- |
| Claude Code | `~/.claude/skills/`（只给当前项目用：项目内 `.claude/skills/`） |
| Codex | `$CODEX_HOME/skills/`，默认 `~/.codex/skills/` |
| 其他支持 Agent Skills 的工具 | 各工具的 skills 目录，以其文档为准 |

Windows PowerShell（以 Claude Code 为例；Codex 把 `.claude` 换成 `.codex`）：

```powershell
git clone https://github.com/pencil102411-cell/xianxia-fight-seedance.git "$HOME\.claude\skills\xianxia-fight-seedance"
```

macOS / Linux：

```bash
git clone https://github.com/pencil102411-cell/xianxia-fight-seedance.git ~/.claude/skills/xianxia-fight-seedance
```

安装后新开一个会话生效。以后更新：进入该目录执行 `git pull`。

## 检查脚本

只需要 Python 3，没有其他依赖。

```bash
python scripts/check_prompt.py 提示词.txt
```

可选参数：`--single-shot`（首帧单镜头）、`--music`（用户要配乐）、`--not-canvas`（不上玄上画布，允许参考音频）。输出分「必须改」和「建议看」两类。

## 说明

- 参考片的拆解只有文字和时间码，仓库里没有视频。其中两段是别人的作品，不要拿来当参考视频上传。
- 实测场的人名、特效图编号只是例子，换一场戏时换成那场的。
- 配合「上古影视工作流」插件（[shanggu-film-pipeline-fqllg](https://github.com/pencil102411-cell/shanggu-film-pipeline-fqllg)）使用时，存文件、进度表和上画布由插件负责，本技能只写打戏内容。
