import re

from app.models import OptionObject

_SINGLE_LABEL_PATTERN = re.compile(r"(?<![A-Z])([A-Z])(?![A-Z])")


def _option_labels(options: list[str | OptionObject] | None) -> list[str]:
    if not options:
        return []
    return [
        (option.label or chr(ord("A") + index)).upper()
        if isinstance(option, OptionObject)
        else chr(ord("A") + index)
        for index, option in enumerate(options)
    ]


def _choice_labels(
    raw: str, options: list[str | OptionObject] | None
) -> list[str]:
    labels = _option_labels(options)
    valid_labels = set(labels) if labels else set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    text = raw.strip().upper()
    if labels:
        for index, option in enumerate(options or []):
            option_text = option.text if isinstance(option, OptionObject) else option
            if option_text.strip().casefold() in text.casefold():
                return [labels[index]]

    candidates = _SINGLE_LABEL_PATTERN.findall(text)
    if not candidates and re.fullmatch(r"[A-Z]+", text):
        candidates = list(text)
    if not candidates:
        raise ValueError("The model response contains no option labels")

    unique = list(dict.fromkeys(label for label in candidates if label in valid_labels))
    if not unique:
        raise ValueError("The model response contains no valid option labels")
    return unique


def parse_answer(
    raw: str, qtype: str, options: list[str | OptionObject] | None
) -> str:
    normalized_type = qtype.lower()
    if normalized_type in ("judge", "judgement", "judgment", "truefalse", "tf"):
        text = raw.strip().casefold()
        if any(token in text for token in ("错误", "不正确", "不对", "错", "false", "no")):
            return "错误"
        if any(token in text for token in ("正确", "对", "true", "yes")):
            return "正确"
        raise ValueError("The model response is not a recognizable judgment")

    selected = _choice_labels(raw, options)
    if normalized_type == "single":
        if len(selected) != 1:
            raise ValueError("The model returned multiple answers for a single-choice question")
        return selected[0]
    return "#".join(selected)
