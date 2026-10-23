from app.models import OptionObject


def build_prompt(
    title: str, options: list[str | OptionObject] | None, qtype: str
) -> tuple[str, str]:
    normalized_type = qtype.lower()
    if normalized_type in ("single",):
        instruction = "单选题：只返回一个选项字母，例如 A。"
    elif normalized_type == "multiple":
        instruction = "多选题：只返回所有正确选项字母，例如 A,C。"
    else:
        instruction = "判断题：只返回“正确”或“错误”。"

    lines = [f"题目：{title}"]
    if options:
        for index, option in enumerate(options):
            label = option.label if isinstance(option, OptionObject) else None
            label = label or chr(ord("A") + index)
            text = option.text if isinstance(option, OptionObject) else option
            lines.append(f"{label}. {text}")

    return (
        "你是一个严谨的答题助手。请根据题目作答。"
        f"{instruction}不要输出解释或其他内容。",
        "\n".join(lines),
    )
