"""Эвристическая оценка «температуры» лида для админской очереди (без ML)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Temperature = Literal["hot", "warm", "cold"]


@dataclass(frozen=True)
class LeadScoringResult:
    priority_score: int
    temperature: Temperature
    temperature_label: str
    summary: str
    recommended_department: str
    personal_manager_recommended: bool
    worth_pursuing: bool
    reasons: list[str]


def _norm(s: str | None) -> str:
    if not s:
        return ""
    return s.lower().strip()


def _combined(*parts: str | None) -> str:
    return " ".join(_norm(p) for p in parts if p)


def _extract_budget_ceiling_rub(label: str | None) -> float | None:
    """Грубый парсер верхней границы из строк вроде «50M–120M ₽», «до 30k», «25млн»."""
    if not label:
        return None
    s = label.replace(" ", "").replace("\u202f", "").replace(",", ".").lower()
    s = s.replace("руб", "").replace("₽", "").replace("р.", "")
    values: list[float] = []

    def add_val(num: float, mult: float) -> None:
        v = num * mult
        if v > 0:
            values.append(v)

    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:m|млн|mln)", s):
        add_val(float(m.group(1)), 1_000_000)
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:k|к)(?!ал)", s):
        add_val(float(m.group(1)), 1000)
    for m in re.finditer(r"до(\d+(?:\.\d+)?)\s*(?:k|к)(?!ал)", s):
        add_val(float(m.group(1)), 1000)
    for m in re.finditer(r"до(\d+(?:\.\d+)?)(?:k|к)(?!ал)", s):
        add_val(float(m.group(1)), 1000)

    if not values:
        return None
    return max(values)


def _company_size_score(company_size: str | None) -> tuple[int, str | None]:
    t = _norm(company_size)
    if not t:
        return 5, None
    if re.search(r"1000\+|>\s*900|\b1500\b", t):
        return 20, "Крупная команда / холдинг"
    if re.search(r"500|600|700|800", t):
        return 18, "Средне-крупная компания"
    if re.search(r"200|250|300|350", t):
        return 14, "Средний бизнес"
    if re.search(r"80|100|120", t):
        return 10, "Компания до ~120 чел."
    if re.search(r"30|40|50", t) and ("человек" in t or "сотрудник" in t):
        return 7, "Малый бизнес"
    if re.search(r"\b1\b|2\s*чел|ип|самозанят", t):
        return 2, "Микробизнес / ИП / 1–2 человека"
    return 6, None


def _role_score(role: str | None) -> tuple[int, str | None]:
    t = _norm(role)
    if not t:
        return 4, None
    if re.search(r"\bceo\b|директор|учредит|владелец|сооснователь", t):
        return 12, "Роль с полномочиями бюджета"
    if re.search(r"\bcto\b|cio\b|текдир|техдир|главный\s+тех", t):
        return 11, "Техническое лидерство"
    if "chief" in t or "cco" in t or "комплаенс" in t or "coo" in t:
        return 10, "Стратегическая / комплаенс-роль"
    if "product" in t or "продакт" in t:
        return 8, "Продуктовая роль"
    if "руковод" in t or "директор по" in t:
        return 9, "Линейное руководство"
    if "менедж" in t:
        return 5, "Операционный менеджер"
    if "студент" in t:
        return 2, "Студент / без бюджета"
    return 5, None


def _deadline_and_urgency(
    result_deadline: str | None,
    comments: str | None,
    need_scope: str | None,
) -> tuple[int, list[str]]:
    blob = _combined(result_deadline, comments, need_scope)
    if not blob:
        return 6, []
    score = 6
    notes: list[str] = []
    urgent = (
        r"немедленн|срочн|критич|72\s*час|48\s*час|24\s*час|инцидент"
        r"|простой\s*(линии)?|регулятор|инспекц|black\s*friday|пиков"
        r"|жёстк(ая|ую)?\s+дат|через\s*10\s*дн|14\s*календарн"
    )
    if re.search(urgent, blob):
        score += 18
        notes.append("В тексте есть маркеры сжатых сроков или рисков")
    soft = r"полгод|семестр|не\s*раньше|нет\s*срок|когда\s*освобод|узнать\s*цен|просто\s*спрос|не\s*уверен"
    if re.search(soft, blob):
        score -= 12
        notes.append("Сигналы низкой срочности или разведки")
    # явные «до N дней / недель»
    if re.search(r"до\s*\d{1,2}\s*(дн|недел|календар)", blob):
        score += 8
    if score < 0:
        score = 0
    if score > 25:
        score = 25
    return score, notes


def _niche_task_bonus(niche: str | None, task_category: str | None, product_interest: str | None) -> tuple[int, str | None]:
    blob = _combined(niche, task_category, product_interest)
    if not blob:
        return 0, None
    if re.search(r"финтех|платеж|банк|aml|kyc|комплаенс|регулятор", blob):
        return 10, "Финтех / комплаенс — выше сложность и чек"
    if re.search(r"промышлен|mes|производств|завод", blob):
        return 8, "Промышленность / операционный риск"
    if re.search(r"e-?com|маркетплейс|checkout|нагруз|perf", blob):
        return 8, "E-com / нагрузки — чувствительно к срокам"
    if re.search(r"bi|аналит|etl|дашборд", blob):
        return 6, "Аналитика / данные"
    if re.search(r"образован|edtech|школ", blob):
        return 4, "EdTech — средняя динамика"
    return 3, None


def _cold_penalty(blob: str) -> tuple[int, list[str]]:
    if not blob:
        return 0, []
    pen = 0
    notes: list[str] = []
    if re.search(r"студент|магистратур|диплом|исследован", blob):
        pen += 18
        notes.append("Образовательный / исследовательский контекст")
    if re.search(r"до\s*50\s*k|до\s*30\s*k|\b30k\b|\b50k\b|дешёв|самый\s*деш", blob):
        pen += 12
        notes.append("Очень низкий заявленный бюджет")
    if re.search(r"просто\s*понять|собираю\s*информа|не\s*уверен|думаю\s*о", blob):
        pen += 8
        notes.append("Размытая потребность")
    return pen, notes


def _department(niche: str | None, task_category: str | None, product_interest: str | None) -> str:
    blob = _combined(niche, task_category, product_interest)
    if re.search(r"финтех|aml|kyc|комплаенс|регулятор|безопас", blob):
        return "Регуляторика и информационная безопасность"
    if re.search(r"нагруз|инфра|e-?com|checkout|cdn|монитор", blob):
        return "Нагрузки, SRE и инфраструктура"
    if re.search(r"bi|аналит|etl|отчёт", blob):
        return "Аналитика и данные"
    if re.search(r"интеграц|erp|wms|crm|mes", blob):
        return "Интеграции и корпоративные системы"
    return "Продуктовый консалтинг и разработка"


def score_lead(
    *,
    budget_label: str | None,
    company_size: str | None,
    role_type: str | None,
    business_niche: str | None,
    task_category: str | None,
    product_interest: str | None,
    result_deadline: str | None,
    comments: str | None,
    need_scope: str | None,
    business_info: str | None,
    task_scope: str | None,
) -> LeadScoringResult:
    reasons: list[str] = []

    ceiling = _extract_budget_ceiling_rub(budget_label)
    b_score = 6
    if ceiling is not None:
        if ceiling < 80_000:
            b_score = 4
            reasons.append("Низкий оценочный бюджет по строке")
        elif ceiling < 500_000:
            b_score = 9
        elif ceiling < 3_000_000:
            b_score = 16
        elif ceiling < 12_000_000:
            b_score = 24
        else:
            b_score = 32
            reasons.append("Высокий оценочный бюджет")
    else:
        reasons.append("Бюджет не распознан — низкий базовый вклад")

    cs, cs_note = _company_size_score(company_size)
    if cs_note:
        reasons.append(cs_note)

    rs, rs_note = _role_score(role_type)
    if rs_note:
        reasons.append(rs_note)

    du, du_notes = _deadline_and_urgency(result_deadline, comments, need_scope)
    reasons.extend(du_notes)

    nb, nb_note = _niche_task_bonus(business_niche, task_category, product_interest)
    if nb_note:
        reasons.append(nb_note)

    cold_blob = _combined(comments, business_info, need_scope, task_scope)
    pen, pen_notes = _cold_penalty(cold_blob)
    reasons.extend(pen_notes)

    raw = b_score + cs + rs + du + nb - pen
    priority = max(0, min(100, raw))

    if priority >= 68:
        temp: Temperature = "hot"
        tlabel = "Горячий"
    elif priority >= 42:
        temp = "warm"
        tlabel = "Тёплый"
    else:
        temp = "cold"
        tlabel = "Холодный"

    dept = _department(business_niche, task_category, product_interest)

    pm = bool(
        (ceiling is not None and ceiling >= 3_000_000)
        or cs >= 14
        or rs >= 10
        or temp == "hot"
    )

    worth = priority >= 38 and pen < 22

    if temp == "hot":
        summary = "Высокая срочность или ценность: рекомендуется быстрый контакт и фиксация следующего шага."
    elif temp == "warm":
        summary = "Умеренный интерес: стоит квалифицировать и предложить внятный следующий шаг в течение 1–3 дней."
    else:
        summary = "Низкая готовность или маленький чек — автоответ или длинный цикл; персонального менеджера можно не выделять."

    if not worth and temp != "cold":
        summary += " При этом по совокупности сигналов окупаемость ручной работы под вопросом."

    return LeadScoringResult(
        priority_score=priority,
        temperature=temp,
        temperature_label=tlabel,
        summary=summary,
        recommended_department=dept,
        personal_manager_recommended=pm,
        worth_pursuing=worth,
        reasons=list(dict.fromkeys([r for r in reasons if r]))[:8],
    )

