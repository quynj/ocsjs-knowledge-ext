from typing import List, Dict, Optional

SYSTEM_BASE = (
    "你是一个严谨的阅卷老师。请只输出答案，不要解释。"
)

SYSTEM_SINGLE = SYSTEM_BASE + "\n题型: 单选题。仅输出一个大写字母，如 A。"
SYSTEM_MULTIPLE = SYSTEM_BASE + "\n题型: 多选题。仅输出不带分隔的多个大写字母，如 ABC。"
SYSTEM_JUDGE = SYSTEM_BASE + "\n题型: 判断题。仅输出 正确 或 错误。"
SYSTEM_FILL = SYSTEM_BASE + "\n题型: 填空题。仅输出填空文本答案。"


def build_messages(title: str, options: Optional[List[str]], qtype: Optional[str], system_prompt: Optional[str]) -> List[Dict[str, str]]:
    t = (qtype or "").lower()

    # 选择系统提示
    if t.startswith("single"):
        system = SYSTEM_SINGLE
    elif t.startswith("multiple"):
        system = SYSTEM_MULTIPLE
    elif t.startswith("judge") or t in ("tf", "truefalse"):
        system = SYSTEM_JUDGE
    elif t.startswith("fill"):
        system = SYSTEM_FILL
    else:
        system = SYSTEM_BASE

    if system_prompt:
        system = system_prompt.strip() + "\n" + system

    user_lines = [f"题目：{title.strip()}"]
    if options:
        for idx, opt in enumerate(options):
            user_lines.append(f"{chr(ord('A') + idx)}. {opt}")

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(user_lines)}
    ]
    return messages
