from typing import List, Optional, Union
import re


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def parse_single(raw: str, options: Optional[List[str]]) -> Union[str, List[str]]:
    # 优先匹配字母
    m = re.search(r"\b([A-Z])\b", raw)
    if m:
        return m.group(1)
    if options:
        norm_raw = _normalize_text(raw)
        scores = [(_normalize_text(o) in norm_raw, idx) for idx, o in enumerate(options)]
        scores.sort(reverse=True)
        if scores and scores[0][0]:
            return chr(ord('A') + scores[0][1])
    # 兜底返回原文
    return raw.strip()


def parse_multiple(raw: str, options: Optional[List[str]]) -> Union[str, List[str]]:
    # 抽取多个大写字母
    letters = re.findall(r"[A-Z]", raw)
    if letters:
        # 去重保持顺序
        seen = set()
        uniq = []
        for ch in letters:
            if ch not in seen:
                seen.add(ch)
                uniq.append(ch)
        return uniq
    # 兜底：按单选逻辑
    single = parse_single(raw, options)
    if isinstance(single, list):
        return single
    return [single] if isinstance(single, str) else single


def parse_judge(raw: str) -> str:
    s = _normalize_text(raw)
    if any(x in s for x in ["true", "正确", "对", "yes"]):
        return "正确"
    if any(x in s for x in ["false", "错误", "错", "no"]):
        return "错误"
    # 兜底原文
    return raw.strip()


def parse_fill(raw: str) -> str:
    return raw.strip()


def parse_answer(raw: str, qtype: Optional[str], options: Optional[List[str]]) -> Union[str, List[str]]:
    t = (qtype or "").lower()
    if t.startswith("single"):
        return parse_single(raw, options)
    if t.startswith("multiple"):
        return parse_multiple(raw, options)
    if (t.startswith("judge") or t in ("tf", "truefalse", "judgement", "judgment")):
        return parse_judge(raw)
    if t.startswith("fill"):
        return parse_fill(raw)
    # 未知题型，尝试智能推断：若抽到多字母则多选，否则单选
    letters = re.findall(r"[A-Z]", raw)
    if len(letters) > 1:
        seen = set()
        uniq = []
        for ch in letters:
            if ch not in seen:
                seen.add(ch)
                uniq.append(ch)
        return uniq
    return parse_single(raw, options)
