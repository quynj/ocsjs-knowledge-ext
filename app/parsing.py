from typing import List, Optional, Union
import re


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def parse_single(raw: str, options: Optional[List[str]]) -> Union[str, List[str]]:
    m = re.search(r"\b([A-Z])\b", raw)
    if m:
        return m.group(1)
    if options:
        norm_raw = _normalize_text(raw)
        best_idx = -1
        for idx, o in enumerate(options):
            if _normalize_text(o) in norm_raw:
                best_idx = idx
                break
        if best_idx >= 0:
            return chr(ord('A') + best_idx)
    return raw.strip()


def parse_multiple(raw: str, options: Optional[List[str]]) -> Union[str, List[str]]:
    letters = re.findall(r"[A-Z]", raw)
    if letters:
        seen = set()
        uniq: List[str] = []
        for ch in letters:
            if ch not in seen:
                seen.add(ch)
                uniq.append(ch)
        return uniq
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
    return raw.strip()


def parse_fill(raw: str) -> str:
    return raw.strip()


def parse_answer(raw: str, qtype: Optional[str], options: Optional[List[str]]) -> Union[str, List[str]]:
    t = (qtype or "").lower()
    if t.startswith("single"):
        return parse_single(raw, options)
    if t.startswith("multiple"):
        return parse_multiple(raw, options)
    if t.startswith("judge") or t in ("tf", "truefalse"):
        return parse_judge(raw)
    if t.startswith("fill"):
        return parse_fill(raw)
    letters = re.findall(r"[A-Z]", raw)
    if len(letters) > 1:
        seen = set()
        uniq: List[str] = []
        for ch in letters:
            if ch not in seen:
                seen.add(ch)
                uniq.append(ch)
        return uniq
    return parse_single(raw, options)
