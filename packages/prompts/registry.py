from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    template_id: str
    role: str
    system: str
    user: str


class PromptRegistry:
    def __init__(self, templates: list[PromptTemplate] | None = None) -> None:
        self._templates = {t.template_id: t for t in (templates or [])}

    def get(self, template_id: str) -> PromptTemplate:
        if template_id not in self._templates:
            raise KeyError(template_id)
        return self._templates[template_id]

    def register(self, template: PromptTemplate) -> None:
        self._templates[template.template_id] = template
