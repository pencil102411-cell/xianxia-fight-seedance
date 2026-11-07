#!/usr/bin/env python3
"""检查一条仙侠打戏的 Seedance 2.5 提示词。

用法：python check_prompt.py <提示词文本文件> [--music] [--not-canvas] [--single-shot]
  --music        用户明确要配乐时加，不查音乐禁词
  --not-canvas   不上玄上画布时加，允许 (音频N)
  --single-shot  首帧单镜头（一镜到底）时加，改查有没有切镜

只查格式、常见遗漏和实测踩过的坑（见 references/实测经验.md），不判断画面好不好看。
退出码：0 没有「必须改」；1 有「必须改」；2 读不到文件。
"""
import argparse
import re
import sys

HEADERS = ["素材引用", "生成目标", "光影设计", "时间轴", "保持一致"]
MUSIC_WORDS = ["音乐", "背景音乐", "BGM", "配乐", "器乐", "旋律", "氛围铺底音"]
VAGUE = ["炫酷", "华丽", "强大灵力", "强大的灵力", "仙气爆发", "满屏能量", "神秘光芒", "霸气", "震撼", "充满力量", "凌厉"]
TASK_WORDS = ["修改", "替换", "增加", "删除", "延长", "延续", "续写"]
MEDIUM = "雾|尘|烟|落叶|叶|水|雪|云|碎|草|石|沙|地面|瓦|火星|余烬"
LIT = "照亮|打亮|映|染|受光|反光|勾亮|点亮"
AFTERMATH = "飘落|慢飘|缓|余烬|尘|烟|俯拍|大远景|压黑|留下|收拢"
STRONG_CAMERA = "穿越机|FPV|环绕|急推|急拉|crash|手持|跟拍|甩镜|whip|跟着.{0,4}(翻滚|飞)"
SHOT_SIZES = re.compile(r"大远景|(?<!大)远景|全景|中景|近景|特写")
NEG = re.compile(r"没有|没|不|无|别|免得")
EYES_OK = re.compile(r"(眼睛|人眼|瞳孔|鸟眼)[^。]{0,16}不发光|不发光[^。]{0,4}(眼|人眼)")
PUNCT = re.compile(r"[\s，。、；：！？“”‘’（）()《》【】〈〉…—·,.;:!?\-\[\]{}<>\"']")


def split_blocks(text):
    marks = [(m.group(1), m.start(), m.end()) for m in re.finditer(r"【([^】]*)】", text)]
    blocks = {}
    for i, (name, _, end) in enumerate(marks):
        stop = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        blocks.setdefault(name, text[end:stop])
    return marks, blocks


def clauses(text):
    return [c.strip() for c in re.split(r"[，。；！？\n]", text) if c.strip()]


def hits_without_negation(text, pattern):
    """返回命中 pattern、且同一分句里没有否定词的分句。"""
    return [c for c in clauses(text) if re.search(pattern, c) and not NEG.search(c)]


def short(items, n=2):
    return "。原文：" + "".join(f"「{x[:30]}」" for x in items[:n]) + ("……" if len(items) > n else "")


def check_lessons(blocks, segments, prev, single_shot):
    """实测踩过的坑，全部算「建议看」。"""
    warn = []
    body = "\n".join(blocks.get(k, "") for k in ("生成目标", "光影设计", "时间轴"))
    timeline = blocks.get("时间轴", "")

    if re.search(r"从下往上[^。，]{0,6}照", body):
        warn.append("写了光「从下往上照」：实测这样眼睛会发光。特写用四分之三侧脸、法术光留在画面外、脸上只写自然光")
    face_lit = (r"(照亮|打亮|映|染|照着|照在|勾亮)[^，。；]{0,8}(脸|眼|面颊)"
                r"|(脸|眼|面颊)[^，。；]{0,4}(被|映成|染成|照得)[^，。；]{0,10}(光|红|蓝|绿|金|紫)")
    for a, b, line in segments:
        if re.search(face_lit, line) and not EYES_OK.search(line):
            warn.append(f"{a}-{b}s 法术光照到了脸，同一段却没写眼睛不发光：实测脸被法术光照亮，眼睛容易发蓝光、红光")
    hits = hits_without_negation(body, r"(霜|冰|雪)[^，。；]{0,10}(脸|眉|睫毛|眼皮|眼角)|(脸|眉|睫毛|眼皮|眼角)[^，。；]{0,6}(霜|冰)"
                                       r"|(擦着|碰到|擦过|贴着)[^，。；]{0,6}(脸|眉|眼)")
    if hits:
        warn.append("冰霜写到了脸上或擦着脸：实测霜会糊到脸上、冰戳进脸；冰只写在身外一臂远，写「脸上始终没有霜」" + short(hits))
    hits = hits_without_negation(body, r"拉长成|越拉越长")
    if hits:
        warn.append("「拉长」会被照字面执行，尾巴钉在画面边缘；要飞的东西写「整体移动，长短形状不变」" + short(hits))
    if re.search(r"响指|弹指", body):
        warn.append("打响指、弹指太装，也看不出法术射出；改成单手掐诀或翻手，指尖弹出火星")
    if re.search(r"双指夹", body):
        warn.append("双指夹刃会画成一根手指点着刃，换别的接法")
    hits = [c for c in hits_without_negation(body, r"笑|嘴角[^，。；]{0,3}(上扬|上翘|勾)|挑眉|轻蔑")
            if not re.search(r"眼神|目光", c) or "笑" in c]
    if hits:
        warn.append("写了笑、挑眉或轻蔑：模型容易给出歪嘴笑。轻蔑放在眼神里，写「嘴唇闭着，嘴角平直」" + short(hits))
    hits = hits_without_negation(body, r"血|(身上|衣服|衣袍|袍子|纱袍|皮肤|肩上)[^，。；]{0,6}(着火|在烧|烧起来|火苗)")
    if hits:
        warn.append("写了血或人身上着火：实测可能被判黑屏失败；写成「细细的红痕」「纱袍燎焦，冒几点火星」" + short(hits))
    hits = [c for c in clauses(timeline)
            if re.search(r"慢慢|缓缓|缓慢|慢悠悠", c)
            and re.search(r"(飞|射|冲|砸|扑|撞)向|推出|出掌|甩出|射出|冲过|飞过去|出手", c)]
    if hits:
        warn.append("出招、飞行写了「慢慢」「缓缓」：用户要快，实测生成本来就偏慢" + short(hits))
    hits = [c for c in hits_without_negation(
                body, r"冰(刃|锥|墙|块|刺|晶|层|面|柱|棱)[^，。；]{0,8}(发光|灵光|透光)|冰(里|内部|中)[^，。；]{0,6}光")
            if not re.search(r"霜点|光雾", c)]
    if hits:
        warn.append("冰写成发光：放出去的冰要写实、不发光，不然像贴图；冰墙这类法术凝成的防御可以有淡淡灵光，确认是有意的" + short(hits))
    if re.search(r"丝带|水带", body):
        warn.append("灵力写成丝带，实测会变成发光的水带；改成光雾裹着发光霜点")
    if re.search(r"(一直|始终|全程)[^，。；]{0,4}负在(背后|身后)", body):
        warn.append("写死「一只手一直负在背后」，强者容易站着不动；只在一两刀里写")

    for line in blocks.get("素材引用", "").splitlines():
        if re.search(r"\(图片\d+\)", line) and "归" in line and "所有" in line and "不取" not in line:
            warn.append(f"特效或道具图没写「不取图片背景」：实测参考图的背景色会带进视频。{line.strip()[:30]}……")

    for a, b, line in segments:
        places = set(re.findall(r"画面(?:左|右|上|下|正中|中间|中)|左侧|右侧|左上|左下|右上|右下", line))
        if "大远景" in line and len(places) < 2:
            warn.append(f"{a}-{b}s 大远景没写清各方在画面哪一侧：实测人一小就会被省掉。画面里有两方时写清左右和「身形看得清」")
        sizes = {m.group(0) for m in SHOT_SIZES.finditer(line)}
        if len(sizes) > 1 and not re.search(r"切|刀|推|拉|环绕|穿越机|甩|摇", line):
            warn.append(f"{a}-{b}s 一段里写了{'、'.join(sorted(sizes))}：实测一段只会拍出一个景别，要两个就分两段")

    if single_shot:
        if len(segments) > 1:
            warn.append("首帧单镜头的【时间轴】只写一段，写多段模型会切镜")
        hits = hits_without_negation(timeline, r"切到|快切|推近|摇镜|镜头往.{0,4}摇")
        if hits:
            warn.append("首帧单镜头里写了切镜、推近或摇镜：实测模型会自己切出别的景别" + short(hits))
        if not re.search(r"一镜到底|只有一个镜头", blocks.get("生成目标", "")):
            warn.append("首帧单镜头的【生成目标】要写死「只有一个镜头，一镜到底，固定机位，不切镜头，不换景别」")
    elif prev >= 8 and timeline and not re.search(STRONG_CAMERA, timeline):
        warn.append("没有强运镜（穿越机、环绕、急推急拉、手持跟拍）：用户觉得侧面平拍、固定机位多了就太平")
    return warn


def check(text, music=False, canvas=True, single_shot=False):
    must, warn = [], []
    marks, blocks = split_blocks(text)

    names = [m[0] for m in marks]
    missing = [h for h in HEADERS if h not in names]
    if missing:
        must.append("缺少区块：" + "、".join(missing))
    known = [n for n in names if n in HEADERS]
    if known != [h for h in HEADERS if h in known]:
        must.append("五个区块的顺序不对，应为：" + " → ".join(HEADERS))
    extra = sorted({n for n in names if n not in HEADERS})
    if extra:
        must.append("【】只能做区块标题（在 Seedance 里表示字幕），这些要改掉：" + "、".join(extra))

    for m in re.finditer(r"\(([^()]*)\)", text):
        if not re.fullmatch(r"(图片|视频|音频)[1-9]\d*", m.group(1)):
            must.append(f"半角括号在 Seedance 里表示音乐，术语括注改成全角：{m.group(0)}")
    for m in re.finditer(r"（\s*(图片|视频|音频)\s*\d+\s*）|@(图片|视频|音频)\d+", text):
        must.append(f"素材引用要写成半角 (图片N)：{m.group(0)}")
    for m in re.finditer(r"(?<![(（@])(图片|视频|音频)\s*\d+", text):
        must.append(f"素材引用要带括号：{m.group(0)}")
    if canvas and re.search(r"\(音频\d+\)", text):
        must.append("玄上画布第一版不支持参考音频，改成文字描述（不上画布请加 --not-canvas）")
    for kind in ("图片", "视频", "音频"):
        nums = sorted({int(n) for n in re.findall(rf"\({kind}(\d+)\)", text)})
        if nums and nums != list(range(1, nums[-1] + 1)):
            must.append(f"{kind}编号不连续：{nums}")
    placeholders = sorted(set(re.findall(r"@[^\s，。、；：(（]{1,12}", text)))
    if placeholders:
        warn.append("用了占位，上画布前要换成 (图片N)：" + "、".join(placeholders))

    timeline = blocks.get("时间轴", "")
    segments = []
    for line in timeline.splitlines():
        m = re.match(r"\s*(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*[sS秒]?\s*[：:]", line)
        if m:
            segments.append((m.group(1), m.group(2), line))
    if timeline and not segments:
        must.append("【时间轴】没有找到时间段，格式应为「0-2s：……」")
    prev = 0
    for a, b, _ in segments:
        if "." in a or "." in b:
            must.append(f"时间戳只用整数秒：{a}-{b}s")
            continue
        if int(a) != prev:
            must.append(f"时间段没有首尾相接：上一段到 {prev}s，这一段从 {a}s 开始")
        prev = int(b)
    if segments and not 4 <= prev <= 30:
        must.append(f"总时长 {prev} 秒，每条要在 4–30 秒之间，超了就拆条")

    length = len(PUNCT.sub("", timeline))
    limit = 4000 if prev <= 15 else 6000
    if length > limit:
        must.append(f"【时间轴】{length} 字，超过 {limit} 字上限")

    if not music:
        for name in ("生成目标", "保持一致"):
            lost = [w for w in MUSIC_WORDS if w not in blocks.get(name, "")]
            if name in blocks and lost:
                must.append(f"【{name}】的音乐禁词不全，缺：" + "、".join(lost))

    keep = blocks.get("保持一致", "")
    if keep and "不发光" not in keep:
        warn.append("【保持一致】没有「人物为正常人眼，不发光」；法术戏容易诱发眼睛发光，除非剧情要求")
    if len([x for x in keep.splitlines() if x.strip()]) > 5:
        warn.append("【保持一致】超过 5 行")

    for m in re.finditer(r"\d+\s*(?:帧|fps|FPS)|\d+\s*倍(?:速|升格)?", text):
        warn.append(f"帧率、倍率不要写进提示词，改成看得见的结果：{m.group(0)}")
    hits = [w for w in VAGUE if w in text]
    if hits:
        warn.append("空话，换成看得见的画面：" + "、".join(hits))
    hits = [w for w in TASK_WORDS if w in text]
    if hits:
        warn.append("参考生视频里出现了可能被判成编辑或延长的词（用首尾帧、编辑、延长任务时可忽略）：" + "、".join(hits))
    for m in re.finditer(r"(?<!画面)(?<!自己的)(?<!他的)(?<!她的)[左右][手脚肩臂侧边]", timeline):
        warn.append(f"左右要写「画面左/右」或「她自己的左手」：{m.group(0)}")
        break

    for i, (a, b, line) in enumerate(segments):
        if "同镜" not in line and "mm" not in line:
            warn.append(f"{a}-{b}s 没写焦距（同镜连续的段落写「同镜连续」）")
        if "结束时" not in line and "结束" not in line:
            warn.append(f"{a}-{b}s 没写结束时的状态")

    if timeline:
        if not re.search(LIT, timeline):
            warn.append("时间轴没写受光：特效照亮了谁？")
        if not re.search(MEDIUM, timeline):
            warn.append("时间轴没写环境介质：雾、尘、落叶、水、碎石……")
        tail = "".join(s[2] for s in segments[-2:]) if segments else ""
        if tail and not re.search(AFTERMATH, tail):
            warn.append("结尾没有余波，如果不是故意停在动作中，加碎片慢飘、尘云或俯拍")
        if not single_shot and prev >= 8 and not re.search("俯拍|俯瞰|大远景|远景|全景", timeline):
            warn.append("没有看清局面的镜头（俯拍或大远景）")
        if not single_shot and len(re.findall("mm", timeline)) < max(2, prev // 5):
            warn.append(f"{prev} 秒里切镜偏少；参考片约每秒 0.8 刀，确认这是有意的长镜")

    warn += check_lessons(blocks, segments, prev, single_shot)
    return must, warn


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="检查仙侠打戏的 Seedance 2.5 提示词")
    ap.add_argument("file")
    ap.add_argument("--music", action="store_true", help="用户要配乐，不查音乐禁词")
    ap.add_argument("--not-canvas", action="store_true", help="不上玄上画布，允许 (音频N)")
    ap.add_argument("--single-shot", action="store_true", help="首帧单镜头，一镜到底")
    args = ap.parse_args()
    try:
        with open(args.file, encoding="utf-8-sig") as f:
            text = f.read()
    except OSError as e:
        print(f"读不到文件：{e}")
        return 2
    must, warn = check(text, music=args.music, canvas=not args.not_canvas, single_shot=args.single_shot)
    print(f"必须改：{len(must)} 条")
    for x in must:
        print("  ✗ " + x)
    print(f"建议看：{len(warn)} 条")
    for x in warn:
        print("  ? " + x)
    if not must and not warn:
        print("格式和常见遗漏都没问题。")
    return 1 if must else 0


if __name__ == "__main__":
    sys.exit(main())
