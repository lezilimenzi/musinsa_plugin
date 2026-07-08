from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from common import as_bool, clamp, joined, load_structured, read_csv, tags, write_csv, write_json


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
OUTPUTS = ROOT / "outputs"
REPORTS = ROOT / "reports"
CATEGORIES = ["trend_discovery", "event_tpo", "season_weather", "item_led", "occasion"]
BANNED_CLAIMS = ["전환율을", "매출을 증가", "가장 많이 팔", "재고가 충분"]

SIGNAL_FIELDS = [
    "signal_id", "source_id", "category", "display_keyword", "raw_text",
    "style_moods", "colors", "items", "materials", "events", "tpos",
    "weather", "seasons", "confidence", "extraction_method", "extracted_at",
]

SAMPLE_TAGS: dict[str, dict[str, list[str]]] = {
    "SRC001": {"style_moods": ["rock_chic"], "colors": ["black", "silver"], "items": ["leather_jacket", "boots", "chain_bag"], "materials": ["leather", "denim"], "tpos": ["concert"]},
    "SRC002": {"style_moods": ["sheer_layering"], "colors": ["blue", "white"], "items": ["sheer_top", "shorts"], "materials": ["sheer", "denim"], "weather": ["heat"], "seasons": ["summer"]},
    "SRC003": {"style_moods": ["festival", "sporty"], "colors": ["blue", "white"], "items": ["tshirt", "shorts", "sandals", "waterproof_bag"], "materials": ["nylon"], "events": ["water_festival"], "tpos": ["summer_outdoor"], "seasons": ["summer"]},
    "SRC004": {"style_moods": ["rock_chic"], "colors": ["black", "red"], "items": ["tshirt", "shorts", "boots"], "materials": ["cotton", "denim"], "events": ["concert"], "tpos": ["concert"], "seasons": ["summer"]},
    "SRC005": {"style_moods": ["minimal"], "colors": ["white", "beige"], "items": ["linen_shirt"], "materials": ["linen"], "tpos": ["office"], "weather": ["heat"], "seasons": ["summer"]},
    "SRC006": {"style_moods": ["sporty"], "colors": ["black"], "items": ["rain_boots", "waterproof_bag"], "materials": ["nylon", "waterproof"], "weather": ["monsoon"], "seasons": ["summer"]},
    "SRC007": {"style_moods": ["minimal"], "colors": ["beige", "brown"], "items": ["bucket_bag"], "materials": ["leather"], "tpos": ["office"], "seasons": ["summer"]},
    "SRC008": {"style_moods": ["romantic"], "colors": ["white", "black"], "items": ["mary_jane", "dress"], "materials": ["cotton", "leather"], "tpos": ["date"], "seasons": ["summer"]},
    "SRC009": {"style_moods": ["campus"], "colors": ["blue", "white"], "items": ["tshirt", "backpack"], "materials": ["cotton", "denim"], "tpos": ["campus"], "seasons": ["summer"]},
    "SRC010": {"style_moods": ["romantic"], "colors": ["white", "red"], "items": ["dress", "mary_jane"], "materials": ["cotton", "leather"], "tpos": ["date"], "weather": ["heat"], "seasons": ["summer"]},
}


def _iso(as_of: str) -> str:
    return f"{as_of}T00:00:00+00:00"


def sample_search(as_of: str) -> dict[str, Any]:
    rows = read_csv(INPUTS / "trend_signal_samples.csv")
    return {
        "query": "bundled sample signals",
        "collected_at": _iso(as_of),
        "results": [
            {
                "source_id": row["source_id"],
                "title": row["title"],
                "url": row["url"],
                "published_at": row["published_at"],
                "source_type": row["source_type"],
                "category": row["category"],
                "display_keyword": row["display_keyword"],
                "snippet": row["text"],
            }
            for row in rows
        ],
    }


def _walk_citations(value: Any) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        if value.get("type") == "url_citation" and value.get("url"):
            found.append({"url": value["url"], "title": value.get("title", value["url"])})
        for child in value.values():
            found.extend(_walk_citations(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_citations(child))
    return found


def _search_with_citations(client: Any, model: str, as_of: str, prompt: str, attempts: int) -> Any:
    """web_search를 강제하고, 인용이 나올 때까지 최대 attempts회 재시도한다.

    반환값은 인용을 하나 이상 포함한 response, 끝까지 실패하면 None.
    """
    response = None
    for attempt in range(1, attempts + 1):
        response = client.responses.create(
            model=model,
            tools=[{"type": "web_search"}],
            tool_choice={"type": "web_search"},
            input=(
                f"기준일은 {as_of}이다. {prompt} "
                "반드시 웹 검색을 사용해 최신 공개 출처를 인용하라. "
                "각 주제는 짧은 대표 키워드로 요약하라."
            ),
        )
        if _walk_citations(response.to_dict()):
            return response
        if attempt < attempts:
            time.sleep(attempt)
    return None


def live_search(as_of: str) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for live mode")
    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    attempts = int(os.getenv("LIVE_SEARCH_ATTEMPTS", "3"))
    prompts = {
        "trend_discovery": "한국 패션의 최근 스타일 트렌드 두 가지를 신뢰 가능한 공개 출처와 함께 찾아라.",
        "event_tpo": "서울의 가까운 패션 관련 공연·축제 TPO 두 가지와 코디 맥락을 공식 출처 중심으로 찾아라.",
        "season_weather": "서울의 현재 날씨와 시즌에 맞는 패션 코디 맥락 두 가지를 찾아라.",
        "item_led": "한국 패션에서 관심이 증가한 아이템 두 가지와 코디 방식을 찾아라.",
        "occasion": "현재 시즌의 캠퍼스·데이트 등 일상 TPO 코디 두 가지를 찾아라.",
    }
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    skipped: list[str] = []
    counter = 1
    for category, prompt in prompts.items():
        response = _search_with_citations(client, model, as_of, prompt, attempts)
        if response is None:
            skipped.append(category)
            print(f"[warn] no citations for {category} after {attempts} attempts; skipping")
            continue
        citations = _walk_citations(response.to_dict())
        for citation in citations:
            if citation["url"] in seen:
                continue
            seen.add(citation["url"])
            results.append({
                "source_id": f"LIVE{counter:03d}",
                "title": citation["title"],
                "url": citation["url"],
                "published_at": "",
                "source_type": "web_search",
                "category": category,
                "display_keyword": "",
                "snippet": response.output_text,
            })
            counter += 1
    if not results:
        raise RuntimeError(f"live search produced no citations for any category; skipped={skipped}")
    return {"query": "live category searches", "collected_at": _iso(as_of), "results": results}


def sample_extract(search_data: dict[str, Any], as_of: str) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for index, source in enumerate(search_data["results"], start=1):
        values = SAMPLE_TAGS.get(source["source_id"], {})
        signal = {
            "signal_id": f"SIG{index:03d}",
            "source_id": source["source_id"],
            "category": source["category"],
            "display_keyword": source["display_keyword"],
            "raw_text": source["snippet"],
            "confidence": 0.9,
            "extraction_method": "rule_fallback",
            "extracted_at": _iso(as_of),
        }
        for field in ["style_moods", "colors", "items", "materials", "events", "tpos", "weather", "seasons"]:
            signal[field] = values.get(field, [])
        signals.append(signal)
    return signals


def live_extract(search_data: dict[str, Any], as_of: str) -> list[dict[str, Any]]:
    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    sources = [
        {key: source.get(key, "") for key in ["source_id", "category", "title", "url", "snippet"]}
        for source in search_data["results"]
    ]
    item_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["source_id", "category", "display_keyword", "style_moods", "colors", "items", "materials", "events", "tpos", "weather", "seasons", "confidence"],
        "properties": {
            "source_id": {"type": "string"},
            "category": {"type": "string", "enum": CATEGORIES},
            "display_keyword": {"type": "string"},
            "style_moods": {"type": "array", "items": {"type": "string"}},
            "colors": {"type": "array", "items": {"type": "string"}},
            "items": {"type": "array", "items": {"type": "string"}},
            "materials": {"type": "array", "items": {"type": "string"}},
            "events": {"type": "array", "items": {"type": "string"}},
            "tpos": {"type": "array", "items": {"type": "string"}},
            "weather": {"type": "array", "items": {"type": "string"}},
            "seasons": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
    }
    response = client.responses.create(
        model=model,
        input="다음 검색 근거에서 패션 신호를 추출하라. 대표 키워드는 한국어 20자 이내로 작성하고 근거 없는 값을 만들지 마라.\n" + json.dumps(sources, ensure_ascii=False),
        text={"format": {"type": "json_schema", "name": "fashion_signals", "strict": True, "schema": {
            "type": "object", "additionalProperties": False, "required": ["signals"],
            "properties": {"signals": {"type": "array", "items": item_schema}},
        }}},
    )
    extracted = json.loads(response.output_text)["signals"]
    source_by_id = {item["source_id"]: item for item in search_data["results"]}
    signals = []
    for index, item in enumerate(extracted, start=1):
        if item["source_id"] not in source_by_id or not item["display_keyword"].strip():
            raise RuntimeError("LLM extraction failed source or display keyword validation")
        item.update({
            "signal_id": f"SIG{index:03d}",
            "raw_text": source_by_id[item["source_id"]]["snippet"],
            "extraction_method": "llm",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        })
        signals.append(item)
    return signals


def normalize_anchors(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anchors = []
    for signal in signals:
        if signal["category"] not in CATEGORIES or not signal["display_keyword"].strip():
            raise ValueError("invalid category or empty display keyword")
        anchors.append({
            "anchor_id": signal["signal_id"].replace("SIG", "ANC"),
            "category": signal["category"],
            "display_keyword": signal["display_keyword"].strip(),
            "style_moods": sorted(set(signal["style_moods"])),
            "colors": sorted(set(signal["colors"])),
            "items": sorted(set(signal["items"])),
            "materials": sorted(set(signal["materials"])),
            "events": sorted(set(signal["events"])),
            "tpos": sorted(set(signal["tpos"])),
            "weather": sorted(set(signal["weather"])),
            "seasons": sorted(set(signal["seasons"])),
            "evidence_source_ids": [signal["source_id"]],
            "confidence": clamp(float(signal["confidence"])),
        })
    return anchors


def label_looks() -> list[dict[str, Any]]:
    looks = read_csv(INPUTS / "look_catalog_raw.csv")
    reviewed = {row["look_id"] for row in read_csv(INPUTS / "human_labeled_looks.csv")}
    labeled = []
    for look in looks:
        linked_count = len(tags(look["linked_product_ids"]))
        confidence = 0.75 + (0.19 if look["look_id"] in reviewed else 0) + (0.05 if linked_count else 0)
        look["label_confidence"] = clamp(confidence)
        look["label_sources"] = "metadata,products" + (",human" if look["look_id"] in reviewed else "")
        look["full_body_visible"] = str(as_bool(look["full_body_visible"])).lower()
        labeled.append(look)
    return labeled


def _look_sets(look: dict[str, Any]) -> dict[str, set[str]]:
    return {
        "style_moods": tags(look.get("style_tags")),
        "colors": tags(look.get("color_tags")),
        "items": tags(look.get("item_tags")),
        "materials": tags(look.get("material_tags")),
        "events": tags(look.get("event_tags")),
        "tpos": tags(look.get("tpo_tags")),
        "weather": tags(look.get("weather_tags")),
        "seasons": {look.get("season", "")} - {""},
    }


MATCH_FIELDS = {
    "trend_discovery": ["style_moods", "materials", "items"],
    "event_tpo": ["events", "tpos"],
    "season_weather": ["weather", "seasons", "items", "materials"],
    "item_led": ["items"],
    "occasion": ["tpos"],
}

PRIMARY_FIELDS = {
    "trend_discovery": ["style_moods"],
    "event_tpo": ["events", "tpos"],
    "season_weather": ["weather"],
    "item_led": ["items"],
    "occasion": ["tpos"],
}


def retrieve_candidates(anchors: list[dict[str, Any]], looks: list[dict[str, Any]], minimum_confidence: float) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for anchor in anchors:
        fields = MATCH_FIELDS[anchor["category"]]
        for look in looks:
            look_values = _look_sets(look)
            primary_match = set()
            for field in PRIMARY_FIELDS[anchor["category"]]:
                primary_match |= set(anchor[field]) & look_values[field]
            if not primary_match:
                continue
            matched = set()
            for field in fields:
                matched |= set(anchor[field]) & look_values[field]
            eligible = (
                bool(anchor["display_keyword"])
                and (look.get("shot_type") == "full_body" or as_bool(look.get("full_body_visible")))
                and float(look["label_confidence"]) >= minimum_confidence
                and bool(tags(look.get("linked_product_ids")))
            )
            candidates.append({
                "category": anchor["category"],
                "anchor_id": anchor["anchor_id"],
                "display_keyword": anchor["display_keyword"],
                "source_ids": joined(anchor["evidence_source_ids"]),
                "look_id": look["look_id"],
                "look_title": look["look_title"],
                "image_url": look["image_url"],
                "shot_type": look["shot_type"],
                "full_body_visible": look["full_body_visible"],
                "matched_tags": joined(matched),
                "match_count": len(matched),
                "label_confidence": look["label_confidence"],
                "linked_product_ids": look["linked_product_ids"],
                "eligible": str(eligible).lower(),
            })
    return candidates


def _priority(candidate: dict[str, Any], category: str) -> tuple[Any, ...]:
    return (
        -int(candidate["match_count"]),
        -float(candidate["label_confidence"]),
        -len(tags(candidate["linked_product_ids"])),
        candidate["look_id"],
    )


def select_by_category(candidates: list[dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    quotas = {key: int(value) for key, value in config["quotas"].items()}
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        if candidate["eligible"] == "true":
            by_category[candidate["category"]].append(candidate)
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    actual = {category: 0 for category in CATEGORIES}
    unfilled = 0
    for category in CATEGORIES:
        choices = sorted(by_category[category], key=lambda row: _priority(row, category))
        count = 0
        anchor_ids = sorted({row["anchor_id"] for row in choices})
        for anchor_id in anchor_ids:
            if count >= quotas[category]:
                break
            for candidate in choices:
                if candidate["anchor_id"] != anchor_id or candidate["look_id"] in used:
                    continue
                picked = dict(candidate)
                picked["selection_reason"] = f"{category} 대표 키워드 직접 일치: {candidate['matched_tags']}"
                selected.append(picked)
                used.add(candidate["look_id"])
                count += 1
                actual[category] += 1
                break
        for candidate in choices:
            if candidate["look_id"] in used or count >= quotas[category]:
                continue
            picked = dict(candidate)
            picked["selection_reason"] = f"{category} 직접 일치: {candidate['matched_tags']}"
            selected.append(picked)
            used.add(candidate["look_id"])
            count += 1
            actual[category] += 1
        unfilled += quotas[category] - count
    if unfilled:
        for category in config["fallback_order"]:
            choices = sorted(by_category[category], key=lambda row: _priority(row, category))
            for candidate in choices:
                if not unfilled or candidate["look_id"] in used:
                    continue
                picked = dict(candidate)
                picked["selection_reason"] = f"재할당된 {category} 슬롯: {candidate['matched_tags']}"
                selected.append(picked)
                used.add(candidate["look_id"])
                actual[category] += 1
                unfilled -= 1
    return selected, actual


def feedback_scores() -> list[dict[str, Any]]:
    rows = read_csv(INPUTS / "feedback_log_sample.csv")
    max_dwell = max(float(row["dwell_seconds"]) / max(int(row["impressions"]), 1) for row in rows)
    result = []
    for row in rows:
        impressions, clicks, saves = int(row["impressions"]), int(row["clicks"]), int(row["saves"])
        smoothed_ctr = (clicks + 1) / (impressions + 21)
        save_rate = saves / max(impressions, 1)
        dwell = (float(row["dwell_seconds"]) / max(impressions, 1)) / max_dwell
        score = clamp(0.5 * smoothed_ctr + 0.3 * save_rate + 0.2 * dwell)
        result.append({"look_id": row["look_id"], "smoothed_ctr": round(smoothed_ctr, 6), "save_rate": round(save_rate, 6), "normalized_dwell_time": round(dwell, 6), "feedback_score": score, "usage": "report_only"})
    return result


def build_plan(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan = []
    for slot, row in enumerate(selected, start=1):
        plan.append({
            "slot": slot,
            "category": row["category"],
            "display_keyword": row["display_keyword"],
            "look_id": row["look_id"],
            "look_title": row["look_title"],
            "image_url": row["image_url"],
            "full_body_visible": row["full_body_visible"],
            "source_ids": row["source_ids"],
            "selection_reason": row["selection_reason"],
        })
    return plan


def map_products(plan: list[dict[str, Any]], looks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    products = {row["product_id"]: row for row in read_csv(INPUTS / "product_catalog.csv")}
    look_map = {row["look_id"]: row for row in looks}
    rows = []
    for slot in plan:
        look = look_map[slot["look_id"]]
        linked = sorted(tags(look["linked_product_ids"]))
        for index, product_id in enumerate(linked):
            product = products[product_id]
            rows.append({
                "slot": slot["slot"], "look_id": slot["look_id"], "display_keyword": slot["display_keyword"],
                "mapping_type": "core" if index == 0 else "supporting",
                "product_id": product_id, "product_name": product["product_name"],
                "category": product["category"], "reason": "룩에 직접 연결된 상품",
            })
        linked_categories = {products[item]["category"] for item in linked}
        substitutes = [
            product for product in products.values()
            if product["product_id"] not in linked and product["category"] in linked_categories
        ]
        if substitutes:
            product = sorted(substitutes, key=lambda item: item["product_id"])[0]
            rows.append({
                "slot": slot["slot"], "look_id": slot["look_id"], "display_keyword": slot["display_keyword"],
                "mapping_type": "substitute", "product_id": product["product_id"],
                "product_name": product["product_name"], "category": product["category"],
                "reason": "동일 카테고리의 샘플 대체 후보이며 재고는 확인하지 않음",
            })
    return rows


def generate_reports(plan: list[dict[str, Any]], mappings: list[dict[str, Any]], sources: dict[str, Any], actual: dict[str, int]) -> None:
    products_by_look: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in mappings:
        products_by_look[row["look_id"]].append(row)
    cards = ["# Look-first 카드", ""]
    reasons = ["# 노출 전략 리포트", "", "카테고리별 실제 슬롯 수: " + json.dumps(actual, ensure_ascii=False), ""]
    for row in plan:
        cards.extend([
            f"## {row['slot']}. {row['display_keyword']}",
            "",
            f"![{row['look_title']}]({row['image_url']})",
            "",
            f"- 전신 코디: `{row['look_id']}` / `{row['full_body_visible']}`",
            f"- 코디명: {row['look_title']}",
            f"- 선정 근거: {row['selection_reason']}",
            f"- 출처: {row['source_ids']}",
            "- 연결 상품:",
        ])
        for product in products_by_look[row["look_id"]]:
            cards.append(f"  - {product['mapping_type']}: {product['product_name']}")
        cards.append("")
        reasons.extend([
            f"## 슬롯 {row['slot']} — {row['display_keyword']}",
            f"- 카테고리: `{row['category']}`",
            f"- 전신 코디: `{row['look_id']}`",
            f"- 이유: {row['selection_reason']}",
            f"- 근거 ID: {row['source_ids']}",
            "",
        ])
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "look_first_cards.md").write_text("\n".join(cards), encoding="utf-8")
    (REPORTS / "exposure_reason_report.md").write_text("\n".join(reasons), encoding="utf-8")
    evidence = ["# Evidence table", "", "| source_id | title | URL |", "|---|---|---|"]
    for source in sources["results"]:
        evidence.append(f"| {source['source_id']} | {source['title']} | {source['url']} |")
    (REPORTS / "evidence_table.md").write_text("\n".join(evidence) + "\n", encoding="utf-8")


def validate(plan: list[dict[str, Any]], actual: dict[str, int], config: dict[str, Any]) -> dict[str, Any]:
    errors = []
    if len({row["look_id"] for row in plan}) != len(plan):
        errors.append("duplicate look in plan")
    if any(not row["display_keyword"] for row in plan):
        errors.append("missing display keyword")
    if any(not as_bool(row["full_body_visible"]) for row in plan):
        errors.append("non-full-body look selected")
    report_text = "\n".join(path.read_text(encoding="utf-8") for path in REPORTS.glob("*.md"))
    for claim in BANNED_CLAIMS:
        if claim in report_text:
            errors.append(f"banned claim detected: {claim}")
    keyword_coverage = sum(bool(row["display_keyword"]) for row in plan) / max(len(plan), 1)
    full_body_coverage = sum(as_bool(row["full_body_visible"]) for row in plan) / max(len(plan), 1)
    expected_slots = int(config["slot_count"])
    if len(plan) != expected_slots:
        errors.append(f"expected {expected_slots} slots, generated {len(plan)}")
    result = {
        "status": "PASS" if not errors else "FAIL",
        "slot_count": len(plan),
        "category_counts": actual,
        "keyword_coverage": keyword_coverage,
        "full_body_look_coverage": full_body_coverage,
        "errors": errors,
    }
    text = [
        "# Validation report", "",
        f"- Status: **{result['status']}**",
        f"- Slot count: {len(plan)} / {expected_slots}",
        f"- Keyword Coverage: {keyword_coverage:.1f}",
        f"- Full-body Look Coverage: {full_body_coverage:.1f}",
        f"- Category counts: `{json.dumps(actual, ensure_ascii=False)}`",
        f"- Errors: `{json.dumps(errors, ensure_ascii=False)}`",
        "",
        "피드백 로그는 참고용이며 슬롯 선별에는 사용하지 않았다.",
    ]
    (REPORTS / "validation_report.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    return result


def clean_generated() -> None:
    for directory in [OUTPUTS, REPORTS]:
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if path.is_file():
                path.unlink()


def run(mode: str = "sample", as_of: str | None = None, clean_output: bool = False) -> dict[str, Any]:
    config = load_structured(INPUTS / "home_context_config.yaml")
    as_of = as_of or config["as_of"]
    if clean_output:
        clean_generated()
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    search_data = sample_search(as_of) if mode == "sample" else live_search(as_of)
    write_json(OUTPUTS / "source_search_results.json", search_data)
    signals = sample_extract(search_data, as_of) if mode == "sample" else live_extract(search_data, as_of)
    write_json(OUTPUTS / "extracted_signals.json", {"signals": signals})
    anchors = normalize_anchors(signals)
    write_json(OUTPUTS / "normalized_anchors.json", {"anchors": anchors})
    write_json(OUTPUTS / "context_anchors.json", {"anchors": [row for row in anchors if row["category"] in {"event_tpo", "season_weather", "occasion"}]})

    trend_rows = [
        {"source_id": source["source_id"], "category": source["category"], "display_keyword": source["display_keyword"], "title": source["title"], "url": source["url"], "published_at": source["published_at"]}
        for source in search_data["results"] if source["category"] in {"trend_discovery", "item_led"}
    ]
    write_csv(OUTPUTS / "trend_candidates.csv", trend_rows, ["source_id", "category", "display_keyword", "title", "url", "published_at"])

    looks = label_looks()
    look_fields = list(looks[0].keys())
    write_csv(OUTPUTS / "look_catalog_labeled.csv", looks, look_fields)
    confidence_rows = [{"look_id": row["look_id"], "label_confidence": row["label_confidence"], "label_sources": row["label_sources"]} for row in looks]
    write_csv(OUTPUTS / "label_confidence_report.csv", confidence_rows, ["look_id", "label_confidence", "label_sources"])

    categories = {"slot_count": config["slot_count"], "quotas": config["quotas"], "fallback_order": config["fallback_order"]}
    write_json(OUTPUTS / "home_exposure_categories.json", categories)
    candidates = retrieve_candidates(anchors, looks, float(config["minimum_label_confidence"]))
    candidate_fields = ["category", "anchor_id", "display_keyword", "source_ids", "look_id", "look_title", "image_url", "shot_type", "full_body_visible", "matched_tags", "match_count", "label_confidence", "linked_product_ids", "eligible"]
    write_csv(OUTPUTS / "anchor_matched_look_candidates.csv", candidates, candidate_fields)

    feedback = feedback_scores()
    write_csv(OUTPUTS / "feedback_scores.csv", feedback, ["look_id", "smoothed_ctr", "save_rate", "normalized_dwell_time", "feedback_score", "usage"])
    selected, actual = select_by_category(candidates, config)
    selection_fields = candidate_fields + ["selection_reason"]
    write_csv(OUTPUTS / "category_look_selection.csv", selected, selection_fields)
    plan = build_plan(selected)
    plan_fields = ["slot", "category", "display_keyword", "look_id", "look_title", "image_url", "full_body_visible", "source_ids", "selection_reason"]
    write_csv(OUTPUTS / "home_exposure_plan.csv", plan, plan_fields)
    mappings = map_products(plan, looks)
    mapping_fields = ["slot", "look_id", "display_keyword", "mapping_type", "product_id", "product_name", "category", "reason"]
    write_csv(OUTPUTS / "look_product_mapping.csv", mappings, mapping_fields)
    generate_reports(plan, mappings, search_data, actual)
    validation = validate(plan, actual, config)
    if validation["status"] != "PASS":
        raise RuntimeError("pipeline validation failed: " + "; ".join(validation["errors"]))
    return validation
