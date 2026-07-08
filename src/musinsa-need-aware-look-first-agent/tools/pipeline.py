from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import as_bool, clamp, joined, load_structured, read_csv, tags, write_csv, write_json


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
OUTPUTS = ROOT / "outputs"
REPORTS = ROOT / "reports"
BANNED_CLAIMS = ["전환율을", "매출을 증가", "가장 많이 팔", "재고가 충분"]


def _iso(as_of: str) -> str:
    return f"{as_of}T00:00:00+00:00"


def _llm_client_model() -> tuple[Any, str]:
    from openai import OpenAI

    return OpenAI(), os.getenv("OPENAI_MODEL", "gpt-5.4-mini")


# --- 1. live 웹 검색 (유지: 검색 강제 / 재시도 / 실패 카테고리 skip) ---

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


# --- 2. extract: 자유서술 신호 추출 (통제어휘 태그 없음) ---

def extract(search_data: dict[str, Any]) -> list[dict[str, Any]]:
    client, model = _llm_client_model()
    sources = [
        {key: source.get(key, "") for key in ["source_id", "title", "url", "snippet"]}
        for source in search_data["results"]
    ]
    valid_ids = {source["source_id"] for source in search_data["results"]}
    schema = {
        "type": "object", "additionalProperties": False, "required": ["signals"],
        "properties": {"signals": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["display_keyword", "description", "evidence_source_ids", "confidence"],
            "properties": {
                "display_keyword": {"type": "string"},
                "description": {"type": "string"},
                "evidence_source_ids": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
        }}},
    }
    response = client.responses.create(
        model=model,
        input=(
            "다음 검색 근거에서 한국 패션 트렌드 신호를 자유롭게 추출하라. "
            "통제된 태그 목록에 얽매이지 말고 신호의 의미를 서술하라. "
            "display_keyword는 한국어 20자 이내 대표 키워드, description은 한국어 서술이다. "
            "evidence_source_ids는 제공된 source_id 목록에서만 고르고 근거 없는 값을 만들지 마라.\n"
            + json.dumps(sources, ensure_ascii=False)
        ),
        text={"format": {"type": "json_schema", "name": "fashion_signals", "strict": True, "schema": schema}},
    )
    extracted = json.loads(response.output_text)["signals"]
    signals: list[dict[str, Any]] = []
    for index, item in enumerate(extracted, start=1):
        evidence = [sid for sid in item["evidence_source_ids"] if sid in valid_ids]
        if not item["display_keyword"].strip() or not evidence:
            raise RuntimeError("LLM extraction failed display_keyword or evidence validation")
        signals.append({
            "signal_id": f"SIG{index:03d}",
            "display_keyword": item["display_keyword"].strip(),
            "description": item["description"].strip(),
            "evidence_source_ids": evidence,
            "confidence": clamp(float(item["confidence"])),
        })
    if not signals:
        raise RuntimeError("extraction produced no signals")
    return signals


# --- 3. group_signals: 창발 테마 도출 (사전 카테고리 없음) ---

def group_signals(signals: list[dict[str, Any]], theme_count: dict[str, int]) -> list[dict[str, Any]]:
    client, model = _llm_client_model()
    valid_ids = {signal["signal_id"] for signal in signals}
    payload = [
        {"signal_id": s["signal_id"], "display_keyword": s["display_keyword"], "description": s["description"]}
        for s in signals
    ]
    schema = {
        "type": "object", "additionalProperties": False, "required": ["themes"],
        "properties": {"themes": {
            "type": "array", "minItems": theme_count["min"], "maxItems": theme_count["max"],
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["theme_label", "member_signal_ids", "rationale"],
                "properties": {
                    "theme_label": {"type": "string"},
                    "member_signal_ids": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
            },
        }},
    }
    response = client.responses.create(
        model=model,
        input=(
            f"다음 패션 신호들을 의미가 비슷한 것끼리 묶어 {theme_count['min']}~{theme_count['max']}개의 테마로 그룹핑하라. "
            "사전 정의된 카테고리를 쓰지 말고, 데이터에서 드러나는 테마에 한국어 라벨을 직접 붙여라. "
            "member_signal_ids는 제공된 signal_id에서만 고르라.\n"
            + json.dumps(payload, ensure_ascii=False)
        ),
        text={"format": {"type": "json_schema", "name": "emergent_themes", "strict": True, "schema": schema}},
    )
    raw = json.loads(response.output_text)["themes"]
    themes: list[dict[str, Any]] = []
    for index, theme in enumerate(raw, start=1):
        members = [sid for sid in theme["member_signal_ids"] if sid in valid_ids]
        if not theme["theme_label"].strip() or not members:
            continue
        themes.append({
            "theme_id": f"T{index}",
            "theme_label": theme["theme_label"].strip(),
            "member_signal_ids": members,
            "rationale": theme["rationale"].strip(),
        })
    if not themes:
        raise RuntimeError("grouping produced no themes")
    return themes


# --- 4. rank_looks: LLM 제로샷 룩 랭킹 (후보 집합을 인자로 받음 = 확장 이음새) ---

def _look_card(look: dict[str, Any], products: dict[str, dict[str, Any]], brands: dict[str, dict[str, Any]]) -> dict[str, Any]:
    linked = sorted(tags(look.get("linked_product_ids")))
    names = ", ".join(products[p]["product_name"] for p in linked if p in products)
    brand = look.get("brand", "")
    brand_row = brands.get(brand, {})
    return {
        "look_id": look["look_id"],
        "look_title": look.get("look_title", ""),
        "season": look.get("season", ""),
        "full_body_visible": look.get("full_body_visible", ""),
        "linked_products": names,
        "brand": brand,
        "brand_specialty": brand_row.get("specialty", ""),
        "brand_identity": brand_row.get("identity", ""),
    }


def rank_looks(themes: list[dict[str, Any]], candidate_looks: list[dict[str, Any]], signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    client, model = _llm_client_model()
    products = {row["product_id"]: row for row in read_csv(INPUTS / "product_catalog.csv")}
    brands = {row["brand"]: row for row in read_csv(INPUTS / "brand_catalog.csv")}
    signal_by_id = {s["signal_id"]: s for s in signals}
    look_by_id = {look["look_id"]: look for look in candidate_looks}
    look_ids = set(look_by_id)
    cards = [_look_card(look, products, brands) for look in candidate_looks]
    schema = {
        "type": "object", "additionalProperties": False, "required": ["ranked"],
        "properties": {"ranked": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["look_id", "display_keyword", "fit_score", "reason"],
            "properties": {
                "look_id": {"type": "string"},
                "display_keyword": {"type": "string"},
                "fit_score": {"type": "number", "minimum": 0, "maximum": 1},
                "reason": {"type": "string"},
            },
        }}},
    }
    ranked: list[dict[str, Any]] = []
    for theme in themes:
        members = [signal_by_id[sid] for sid in theme["member_signal_ids"] if sid in signal_by_id]
        theme_source_ids: set[str] = set()
        for signal in members:
            theme_source_ids.update(signal["evidence_source_ids"])
        theme_ctx = {
            "theme_label": theme["theme_label"],
            "rationale": theme["rationale"],
            "signals": [{"display_keyword": s["display_keyword"], "description": s["description"]} for s in members],
        }
        response = client.responses.create(
            model=model,
            input=(
                "다음 테마에 어울리는 전신 코디(룩)를 골라 적합도(fit_score) 순으로 랭킹하라. "
                "제공된 look_id 목록에서만 고르고 목록에 없는 룩을 만들지 마라. "
                "display_keyword는 이 룩을 이 테마로 노출할 때 쓸 한국어 대표 키워드, "
                "reason은 테마 근거에 기반한 한국어 설명이다. "
                "각 룩에는 브랜드와 그 브랜드의 전문 분야(brand_specialty)·아이덴티티가 있다. "
                "브랜드 전문성이 이 테마와 강하게 맞으면(예: 수영복 전문 브랜드가 물놀이 테마) fit_score를 더 높이고, "
                "그 경우 reason에 브랜드와 전문성을 언급하라. 브랜드가 테마와 무관하면 브랜드 때문에 점수를 올리지 마라. "
                "매출·전환율·재고·판매 순위 같은 근거 없는 주장을 하지 마라.\n"
                "테마: " + json.dumps(theme_ctx, ensure_ascii=False) + "\n"
                "룩 후보: " + json.dumps(cards, ensure_ascii=False)
            ),
            text={"format": {"type": "json_schema", "name": "look_ranking", "strict": True, "schema": schema}},
        )
        items = json.loads(response.output_text)["ranked"]
        for item in items:
            if item["look_id"] not in look_ids or not item["display_keyword"].strip() or not theme_source_ids:
                continue
            ranked.append({
                "theme_id": theme["theme_id"],
                "theme_label": theme["theme_label"],
                "look_id": item["look_id"],
                "brand": look_by_id[item["look_id"]].get("brand", ""),
                "display_keyword": item["display_keyword"].strip(),
                "fit_score": clamp(float(item["fit_score"])),
                "reason": item["reason"].strip(),
                "evidence_source_ids": sorted(theme_source_ids),
            })
    return ranked


# --- 5. 룩 라벨링 (유지) ---

def label_looks() -> list[dict[str, Any]]:
    looks = read_csv(INPUTS / "look_catalog_raw.csv")
    labeled = []
    for look in looks:
        linked_count = len(tags(look["linked_product_ids"]))
        confidence = 0.75 + (0.05 if linked_count else 0)
        look["label_confidence"] = clamp(confidence)
        look["label_sources"] = "metadata,products"
        look["full_body_visible"] = str(as_bool(look["full_body_visible"])).lower()
        labeled.append(look)
    return labeled


# --- 6. assemble_slots: 전역 배정 (fit 상위부터, min_fit_score 하한, 채운 만큼) ---

def assemble_slots(ranked: list[dict[str, Any]], looks: list[dict[str, Any]], target_slots: int, per_theme_cap: int, min_fit_score: float = 0.0) -> list[dict[str, Any]]:
    """모든 (테마,룩) 쌍을 fit_score 전역 정렬해 상위부터 배정한다.

    각 룩은 자신에게 가장 잘 맞는 테마로 간다(라운드로빈의 오배정 회피).
    fit_score < min_fit_score 인 쌍은 버린다. 룩 중복 금지, 테마당 per_theme_cap,
    슬롯은 target_slots까지 채우되 후보가 부족하면 그대로 둔다(강제 채움 없음).
    """
    look_by_id = {look["look_id"]: look for look in looks}
    pairs = [row for row in ranked if row["fit_score"] >= min_fit_score]
    pairs.sort(key=lambda row: (-row["fit_score"], row["theme_id"], row["look_id"]))
    used: set[str] = set()
    theme_counts: dict[str, int] = defaultdict(int)
    selected: list[dict[str, Any]] = []
    for row in pairs:
        if len(selected) >= target_slots:
            break
        look = look_by_id.get(row["look_id"])
        if row["look_id"] in used or look is None or theme_counts[row["theme_id"]] >= per_theme_cap:
            continue
        selected.append({
            "slot": len(selected) + 1,
            "category": row["theme_label"],
            "display_keyword": row["display_keyword"],
            "look_id": row["look_id"],
            "look_title": look.get("look_title", ""),
            "brand": look.get("brand", ""),
            "image_url": look.get("image_url", ""),
            "full_body_visible": look.get("full_body_visible", ""),
            "source_ids": joined(row["evidence_source_ids"]),
            "selection_reason": row["reason"],
        })
        used.add(row["look_id"])
        theme_counts[row["theme_id"]] += 1
    return selected


# --- 7. 피드백 지표 (유지, 참고용) ---

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


# --- 8. 상품 매핑 (유지) ---

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


# --- 9. 리포트 (유지, category=테마 라벨) ---

def generate_reports(plan: list[dict[str, Any]], mappings: list[dict[str, Any]], sources: dict[str, Any], distribution: dict[str, int]) -> None:
    products_by_look: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in mappings:
        products_by_look[row["look_id"]].append(row)
    cards = ["# Look-first 카드", ""]
    reasons = ["# 노출 전략 리포트", "", "테마별 슬롯 수: " + json.dumps(distribution, ensure_ascii=False), ""]
    for row in plan:
        cards.extend([
            f"## {row['slot']}. {row['display_keyword']}",
            "",
            f"![{row['look_title']}]({row['image_url']})",
            "",
            f"- 전신 코디: `{row['look_id']}` / `{row['full_body_visible']}`",
            f"- 코디명: {row['look_title']}",
            f"- 브랜드: {row.get('brand', '')}",
            f"- 선정 근거: {row['selection_reason']}",
            f"- 출처: {row['source_ids']}",
            "- 연결 상품:",
        ])
        for product in products_by_look[row["look_id"]]:
            cards.append(f"  - {product['mapping_type']}: {product['product_name']}")
        cards.append("")
        reasons.extend([
            f"## 슬롯 {row['slot']} — {row['display_keyword']}",
            f"- 테마: `{row['category']}`",
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


# --- 10. 검증 (완화) ---

def validate(plan: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    errors = []
    target = int(config["target_slots"])
    if not plan:
        errors.append("no slots generated")
    if len({row["look_id"] for row in plan}) != len(plan):
        errors.append("duplicate look in plan")
    if any(not row["display_keyword"] for row in plan):
        errors.append("missing display keyword")
    if any(not as_bool(row["full_body_visible"]) for row in plan):
        errors.append("non-full-body look selected")
    if any(not row["source_ids"] for row in plan):
        errors.append("missing evidence source ids")
    report_text = "\n".join(path.read_text(encoding="utf-8") for path in REPORTS.glob("*.md"))
    for claim in BANNED_CLAIMS:
        if claim in report_text:
            errors.append(f"banned claim detected: {claim}")
    coverage_gap = max(target - len(plan), 0)
    theme_counts: dict[str, int] = defaultdict(int)
    for row in plan:
        theme_counts[row["category"]] += 1
    keyword_coverage = sum(bool(row["display_keyword"]) for row in plan) / max(len(plan), 1)
    full_body_coverage = sum(as_bool(row["full_body_visible"]) for row in plan) / max(len(plan), 1)
    result = {
        "status": "PASS" if not errors else "FAIL",
        "slot_count": len(plan),
        "target_slots": target,
        "coverage_gap": coverage_gap,
        "theme_counts": dict(theme_counts),
        "keyword_coverage": keyword_coverage,
        "full_body_look_coverage": full_body_coverage,
        "errors": errors,
    }
    text = [
        "# Validation report", "",
        f"- Status: **{result['status']}**",
        f"- Slot count: {len(plan)} / {target}  (coverage gap: {coverage_gap})",
        f"- Keyword Coverage: {keyword_coverage:.1f}",
        f"- Full-body Look Coverage: {full_body_coverage:.1f}",
        f"- Theme counts: `{json.dumps(dict(theme_counts), ensure_ascii=False)}`",
        f"- Errors: `{json.dumps(errors, ensure_ascii=False)}`",
        "",
        "슬롯 수가 target에 미달해도(커버리지 갭) 실패가 아니다. 하드 게이트(전신·그라운딩·중복·금지문구·빈 계획)만 실패로 본다.",
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


def run(as_of: str | None = None, clean_output: bool = False) -> dict[str, Any]:
    config = load_structured(INPUTS / "home_context_config.yaml")
    as_of = as_of or config["as_of"]
    if clean_output:
        clean_generated()
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    search_data = live_search(as_of)
    write_json(OUTPUTS / "source_search_results.json", search_data)

    signals = extract(search_data)
    write_json(OUTPUTS / "extracted_signals.json", {"signals": signals})

    theme_count = config.get("theme_count", {"min": 3, "max": 6})
    themes = group_signals(signals, theme_count)
    write_json(OUTPUTS / "emergent_themes.json", {"themes": themes})

    looks = label_looks()
    look_fields = list(looks[0].keys())
    write_csv(OUTPUTS / "look_catalog_labeled.csv", looks, look_fields)

    min_conf = float(config["minimum_label_confidence"])
    eligible_looks = [
        look for look in looks
        if (look.get("shot_type") == "full_body" or as_bool(look.get("full_body_visible")))
        and float(look["label_confidence"]) >= min_conf
        and bool(tags(look.get("linked_product_ids")))
    ]

    ranked = rank_looks(themes, eligible_looks, signals)
    ranking_rows = [{**row, "evidence_source_ids": joined(row["evidence_source_ids"])} for row in ranked]
    ranking_fields = ["theme_id", "theme_label", "look_id", "brand", "display_keyword", "fit_score", "reason", "evidence_source_ids"]
    write_csv(OUTPUTS / "theme_look_ranking.csv", ranking_rows, ranking_fields)

    feedback = feedback_scores()
    write_csv(OUTPUTS / "feedback_scores.csv", feedback, ["look_id", "smoothed_ctr", "save_rate", "normalized_dwell_time", "feedback_score", "usage"])

    target_slots = int(config["target_slots"])
    per_theme_cap = int(config["per_theme_cap"])
    min_fit_score = float(config.get("min_fit_score", 0.0))
    plan = assemble_slots(ranked, looks, target_slots, per_theme_cap, min_fit_score)
    plan_fields = ["slot", "category", "display_keyword", "look_id", "look_title", "brand", "image_url", "full_body_visible", "source_ids", "selection_reason"]
    write_csv(OUTPUTS / "home_exposure_plan.csv", plan, plan_fields)

    mappings = map_products(plan, looks)
    mapping_fields = ["slot", "look_id", "display_keyword", "mapping_type", "product_id", "product_name", "category", "reason"]
    write_csv(OUTPUTS / "look_product_mapping.csv", mappings, mapping_fields)

    distribution: dict[str, int] = defaultdict(int)
    for row in plan:
        distribution[row["category"]] += 1
    generate_reports(plan, mappings, search_data, dict(distribution))

    validation = validate(plan, config)
    if validation["status"] != "PASS":
        raise RuntimeError("pipeline validation failed: " + "; ".join(validation["errors"]))
    return validation
