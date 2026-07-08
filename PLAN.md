# MUSINSA Need-aware Look-first Agent 구현 계획 (재설계 · 방향 B)

상태: **초안 — 승인 전. 구현하지 말 것 (Do not implement yet).**
사전 분석: `RESEARCH.md §27`.

## 0. 배경 — 왜 재설계하나

초기 MVP는 "사람이 정의한 통제어휘 태그(style/color/item/… 8필드)"로 트렌드 신호와 룩을
매칭했다. 그러나 live 모드에서 LLM은 한국어 자유서술 태그(`미니멀`, `청바지`)를 뽑는데,
매칭은 영어 snake_case 통제어휘(`minimal`, `denim`)와 **정확 집합 교집합**을 요구한다.
두 어휘가 절대 겹치지 않아 후보 0 → 슬롯 0 → `expected 10 slots, generated 0` 검증 실패.

결론: **통제어휘 태그 매칭 방식 자체가 자유 트렌드 발굴과 맞지 않는다.** 이 계획은 태그
카탈로그 의존을 제거하고 **자유서술 신호 → 창발 테마 → LLM 제로샷 룩 랭킹** 구조로 전환한다.

### 확정된 설계 결정

| 항목 | 결정 |
|---|---|
| 매칭 엔진 | **LLM 제로샷 랭킹** (고정 태그 조인 제거) |
| 카테고리 | **완전 창발(emergent)** — 사전 5개 고정 폐기, 라벨·개수 LLM 생성 |
| 테마 개수 | **3~6개** |
| 커버리지 부족 시 | **채운 만큼 통과(검증 완화)** — 슬롯 하드요구 폐기, `target_slots`(소프트 목표)로 강등 |
| 실행 모드 | **live 단일** — sample 모드 완전 제거. 모든 테스트·검증은 live/순수함수 기준 |
| 그라운딩 | **슬롯당 source_id 필수 유지** (위조 방지) |
| 통제어휘 파일 | `label_taxonomy.yaml`·`synonym_dictionary.yaml` **삭제 완료** (2026-07-08) |

## 1. 목표

MD/서비스 기획자가 홈·추천판·기획전에 활용할 **대표 키워드 + 전신 코디 슬롯**을 만드는
로컬 배치 파이프라인. 다음을 수행한다.

1. 공개 웹 자료에서 패션 트렌드·행사·날씨·시즌 신호를 검색한다(`web_search`).
2. 검색 결과에서 LLM으로 **자유서술 신호**(대표 키워드 + 서술 + 근거 source_id + confidence)를 추출한다. 통제어휘 태그를 강제하지 않는다.
3. 신호를 **창발 테마(3~6개)** 로 묶는다(사전 카테고리 없음, LLM이 라벨 생성).
4. 각 테마에 대해 룩 카탈로그를 **LLM 제로샷 랭킹**으로 정렬한다(전신 룩만, 근거 기반).
5. 랭킹 상위에서 중복 없이 슬롯을 조립한다(채운 만큼, `target_slots`까지).
6. 선택한 룩에 핵심·보조·대체 상품을 연결한다.
7. Look-first 카드와 근거·검증 리포트를 CSV/JSON/Markdown으로 생성한다.

MVP는 실제 무신사 웹사이트나 UI에 연결하지 않는다. "홈 화면에 어떤 룩을 왜 노출할지"를
파일로 제안하는 PoC다.

## 2. 성공 기준

### 2.1 기능 기준

- `OPENAI_API_KEY`로 OpenAI Responses API 웹 검색·LLM 추출/그룹핑/랭킹을 실행한다.
- 검색 결과에는 제목, URL, 게시일(확인 가능 시), 수집일, 출처 유형이 저장된다.
- LLM 출력은 JSON Schema 검증 + 사후검증(근거 source_id 부분집합, 룩 존재, 전신)을 통과한 데이터만 후속 단계에 사용한다.
- 홈 피드는 **창발 테마별 LLM 랭킹**으로 구성하며 전역 가중치 점수를 쓰지 않는다.
- 채워진 모든 슬롯에는 `display_keyword`, 검증된 전신 코디, 근거 source_id, 연결 상품이 있다.
- 매출·전환율·재고·판매 순위에 관한 근거 없는 주장을 생성하지 않는다.
- 룩 인벤토리 부족으로 슬롯이 `target_slots`에 미달해도 실패로 보지 않는다(커버리지 갭으로 기록).

### 2.2 검증 기준

- 순수 함수 단위테스트(`assemble_slots`, `validate`)가 통과한다(LLM/네트워크 불필요, 결정론).
- LLM 단계는 모의 응답 주입 단위테스트로 스키마·사후검증 계약을 확인한다.
- `validation_report.md`의 하드 게이트(전신·그라운딩·중복無·금지문구無)가 `PASS`다.
- Codex 플러그인 validator가 manifest와 skill 구조를 승인한다.
- 실제 API 키가 제공된 경우에만 `live` smoke test를 별도로 수행한다(없으면 skip, CI 그린 유지).

## 3. 범위

### 3.1 이번 구현에 포함

- Codex plugin manifest
- 기능별 5개 skill(내용 재작성)
- 샘플 입력 데이터(룩·상품·행사·피드백 등)
- OpenAI 웹 검색 + LLM 추출/그룹핑/랭킹 (live)
- 자유서술 신호 추출
- 창발 테마 그룹핑(3~6)
- LLM 제로샷 룩 랭킹 + 완화 조립
- 상품 매핑
- Look-first 카드, 근거표, 검증 리포트
- 순수함수 단위 테스트 + live 스모크, 실행 문서

### 3.2 이번 구현에서 제외

- `.mcp.json` 및 MCP 서버
- 무신사 내부 API·DB 연동 / 실제 화면 수정 / SNS 무단 크롤링
- 사용자 검색어 기반 추천 / 개인화 추천 / 이미지 분석 / 딥러닝 모델 학습
- PDP 문구 및 캠페인 브리프 선택 기능
- 배포 서버, 스케줄러, 관리자 UI
- **sample(오프라인 규칙 기반) 실행 경로** — 재설계에서 제거

## 4. 전제와 설계 결정

### 4.1 제출 구조

Codex 플러그인 규칙(폴더명 = manifest `name`)에 맞춰 `src/` 아래 이름이 일치하는 루트를 둔다.

```text
src/
└── musinsa-need-aware-look-first-agent/
    ├── .codex-plugin/plugin.json
    ├── skills/
    ├── inputs/
    ├── tools/
    ├── outputs/
    ├── reports/
    ├── tests/
    └── README.md
```

### 4.2 실행 모드 (live 단일)

```text
live (유일 모드):
  OpenAI Responses API의 web_search 도구로 검색
  검색 결과를 로컬 JSON에 저장
  OpenAI 모델로 자유서술 신호 추출 → 창발 테마 그룹핑 → 룩 랭킹
  API 실패 시 결과를 위조하지 않고 명확히 실패
```

sample 모드는 제거한다. 결정론이 필요한 검증은 LLM을 타지 않는 순수 함수(`assemble_slots`,
`validate`)와 모의 응답 단위테스트로 확보한다.

### 4.3 기술 선택

- Python 3.11+
- 런타임 의존성: `openai`, `PyYAML`(config)
- 테스트 의존성: `pytest`
- 표준 라이브러리(`csv`, `json`, `argparse`, `datetime`, `pathlib`) 우선. pandas 미사용.
- API 키는 파일에 저장하지 않고 `OPENAI_API_KEY` 환경 변수만 사용. 모델명은 `OPENAI_MODEL`로 override, 코드엔 비용 효율적 기본 모델 하나.

### 4.4 과도한 분리를 피한다

핵심 로직은 `tools/pipeline.py`에 두고 공통 입출력/정규화는 `tools/common.py`에 둔다.
빈 파일이나 미래 확장용 추상 클래스는 만들지 않는다.

## 5. 전체 실행 흐름

```text
tools/run_pipeline.py  (live 전용, --mode 없음)
  │
  ├─ 1. live_search           web_search로 카테고리별 검색 + 인용 수집
  │                           (검색 강제 tool_choice, 재시도, 실패 카테고리 skip, 전부 실패면 예외)
  ├─ 2. extract               LLM: 자유서술 신호 추출(태그 없음)
  ├─ 3. group_signals         LLM: 신호를 창발 테마 3~6개로 그룹핑
  ├─ 4. rank_looks            LLM: 테마별 룩 제로샷 랭킹(전신만·근거 기반) + 사후검증
  ├─ 5. label_looks           full_body 검증 + confidence(인간리뷰/상품수)
  ├─ 6. assemble_slots        테마 라운드로빈, 중복無, 채운 만큼(target_slots)
  ├─ 7. map_products          핵심/보조/대체 상품 연결
  ├─ 8. feedback_scores       참고 지표(선별 미사용)
  ├─ 9. generate_reports      카드·근거표·이유 리포트
  └─10. validate              완화 검증(하드 게이트만 실패)
```

중간 단계가 실패하면 이후 단계를 실행하지 않고 원인을 출력한다.

## 6. 데이터 계약

### 6.1 검색 결과 — `outputs/source_search_results.json`

```json
{
  "query": "live category searches",
  "collected_at": "ISO-8601",
  "results": [
    {"source_id": "LIVE001", "title": "문서 제목", "url": "https://example.com/article",
     "published_at": "", "source_type": "web_search", "category": "season_weather",
     "display_keyword": "", "snippet": "검색 결과 요약"}
  ]
}
```

### 6.2 추출 신호 — `outputs/extracted_signals.json`

자유서술 신호. **통제어휘 태그 8필드 제거.**

```json
{
  "signals": [
    {"signal_id": "SIG001", "source_id": "LIVE001",
     "display_keyword": "워터 페스티벌룩", "description": "여름 물축제용 방수·경량 코디 관심 상승",
     "evidence_source_ids": ["LIVE001"], "confidence": 0.84}
  ]
}
```

**검증(구 line199 대체):** 필수 필드 누락, `[0,1]` 범위를 벗어난 confidence,
제공 목록에 없는 `source_id`(부분집합 위반), 빈 `display_keyword`는 거부한다.
(*통제어휘 값 검증은 폐기 — taxonomy 없음.*)

### 6.3 창발 테마 — `outputs/emergent_themes.json`

```json
{
  "themes": [
    {"theme_id": "T1", "theme_label": "여름 물축제·페스티벌",
     "member_signal_ids": ["SIG001", "SIG003"], "rationale": "물놀이·방수 수요 군집"}
  ]
}
```

LLM이 3~6개 테마를 생성하며 라벨은 데이터에서 만든다(사전 카테고리 없음).

### 6.4 룩 랭킹 — `outputs/theme_look_ranking.csv`

테마별 LLM 제로샷 랭킹. 컬럼: `theme_id, theme_label, look_id, fit_score, reason, evidence_source_ids`.
**사후검증:** `look_id ∈ 카탈로그`, `full_body==true`, `evidence_source_ids ⊆ 테마 신호 source_id`.
위반 행은 드롭한다.

### 6.5 슬롯 조립 규칙

```text
- 테마 라운드로빈으로 fit_score 상위 룩을 슬롯에 배치
- 한 look_id를 두 슬롯에 중복 배치하지 않음
- 테마당 최대 per_theme_cap
- target_slots까지 채우되, 후보가 부족하면 그대로 진행(강제 fallback 없음)
- 동점은 look_id 오름차순으로 결정
```

`target_slots`는 홈 피드가 원하는 슬롯 수의 **소프트 상한/목표**다. 과거의 "정확히 N개여야
PASS"라는 rigid `slot_count` 검증은 폐기한다.

### 6.6 피드백 참고 지표

```text
smoothed_ctr = (clicks + 1) / (impressions + 1 + 20)
feedback_score = 0.50*smoothed_ctr_norm + 0.30*save_rate + 0.20*normalized_dwell_time
```

피드백은 리포트 참고용으로만 표시하고 슬롯 조립·랭킹에는 사용하지 않는다.

## 7. 파일별 구현 계획 (실제 코드 기준)

### 7.1 프로젝트 루트
- `requirements.txt` — `openai`, `PyYAML`, `pytest` 버전 범위.
- `README.md` — 문제 정의, 제출 구조, live 실행, 검증, 한계.
- `.gitignore` — `__pycache__`, `.pytest_cache`, venv, 비밀키.

### 7.2 플러그인 manifest — `.codex-plugin/plugin.json`
- name `musinsa-need-aware-look-first-agent`, version `1.0.0`, `skills: "./skills/"`,
  author/developerName `lezilimenzi`, interface metadata 포함. `.mcp.json`/apps/hooks 미포함.

### 7.3 tools/common.py (유지)
- UTF-8 CSV/JSON/YAML 입출력, 태그 파싱, `[0,1]` clamp, 금지 주장 목록.

### 7.4 tools/pipeline.py (핵심 재작성)
- **유지:** `live_search`(검색 강제·재시도·skip 이미 반영, `tools/debugging.md` 참고), `label_looks`, `feedback_scores`, `map_products`, `generate_reports`.
- **교체:** `extract`(자유서술 신호 추출로 `live_extract` 대체).
- **신설:** `group_signals`(창발 테마 3~6), `rank_looks`(LLM 제로샷 랭킹+사후검증), `assemble_slots`(완화 조립).
- **제거:** `sample_search`, `sample_extract`, `SAMPLE_TAGS`, `normalize_anchors`(태그 set), `retrieve_candidates`, `select_by_category`, `MATCH_FIELDS`, `PRIMARY_FIELDS`, `_look_sets`.
- **완화:** `validate` — 하드 게이트(전신·그라운딩·중복無·금지문구無)만 실패, 슬롯 부족은 gap 기록 후 PASS, filled==0만 FAIL.
- `run` 재배선(mode 분기 제거).

### 7.5 tools/run_pipeline.py
- `--mode` 인자 제거(항상 live). `--as-of`, `--clean-output`만 유지.

### 7.6 inputs/
- 실제 입력 6종: `look_catalog_raw.csv`(전신 룩·상품 연결), `product_catalog.csv`, `human_labeled_looks.csv`, `feedback_log_sample.csv`, `home_context_config.yaml`, `trend_signal_samples.csv`.
- `home_context_config.yaml`: `quotas`/`fallback_order`/`slot_count` 폐기 → `target_slots`, `per_theme_cap`, `theme_count:{min:3,max:6}` 도입.
- `trend_signal_samples.csv`: sample 전용이라 sample 제거와 함께 삭제 예정.
- **삭제 완료:** `label_taxonomy.yaml`, `synonym_dictionary.yaml`, 미사용 입력 5종(`trend_sources`/`context_sources`/`event_calendar`/`social_event_posts`/`weather_season_context`).

### 7.7 tools/ 단계명 shim 정리 (완료)
RESEARCH 단계명을 모듈로 유지하던 4줄짜리 re-export shim 12종(`source_search`, `classify_anchors`,
`extract_information_with_llm`, `retrieve_anchor_matched_looks`, `select_looks_by_category`,
`route_home_exposure_categories`, `analyze_feedback_logs`, `plan_home_look_exposure`,
`match_looks_to_products`, `label_looks`, `generate_reports`, `validate_outputs`)은 **아무도 import하지
않는 dead 파일**이라 **삭제 완료**(2026-07-08). 실제 로직은 `pipeline.py`에만 존재하며 테스트 10종 통과 확인.

## 8. 필수 산출물

```text
outputs/
├── source_search_results.json
├── extracted_signals.json          # 자유서술 신호(태그 없음)
├── emergent_themes.json            # 창발 테마 (구 home_exposure_categories.json 대체)
├── theme_look_ranking.csv          # LLM 랭킹 (구 anchor_matched_look_candidates.csv 대체)
├── look_catalog_labeled.csv
├── label_confidence_report.csv
├── feedback_scores.csv
├── category_look_selection.csv     # category = theme_label
└── home_exposure_plan.csv

reports/
├── look_first_cards.md
├── exposure_reason_report.md
├── evidence_table.md
└── validation_report.md
```

**제거된 산출물:** `trend_candidates.csv`, `context_anchors.json`, `normalized_anchors.json`,
`home_exposure_categories.json`, `anchor_matched_look_candidates.csv`.

## 9. SKILL.md 재구성

skill 번호·개수는 5개 유지, 내용만 재작성. 신설 단계(group/rank)는 03에 흡수.

| skill | 조치 | 재구성 후 |
|---|---|---|
| **01-trend-context-ingestion** | 재작성 | live 웹검색 + 자유서술 신호 추출 + 그라운딩. "normalized anchors"·8태그·sample·구 출력 언급 삭제. |
| **02-look-labeling** | 재작성(축소) | synonym 태그 정규화 삭제(파일도 삭제). full_body 검증·confidence만. |
| **03-home-exposure-planning** | **전면 재작성** | quota/태그매치/fallback 전량 폐기 → 창발 테마(3~6)+LLM 랭킹+완화 조립. name 예: `emergent-theme-exposure-planning`. |
| **04-product-mapping** | 유지(경미) | `map_products` 재사용. "compatible tags"→category 기준 표현 정리. |
| **05-report-generation** | 유지 | 전신·그라운딩·근거ID·금지문구 계약, 출력 4종 동일. |

## 10. 테스트 계획

### 10.1 단위 테스트(결정론, LLM 불필요)
- `test_assemble_slots.py` — 중복 룩 0, 전 슬롯 full_body, 전 슬롯 source_ids≠∅, per_theme_cap 준수, target 미달 허용.
- `test_validate.py` — 하드 게이트(전신/그라운딩/중복/금지문구) FAIL 케이스, 슬롯 부족 시 PASS+gap, filled==0 FAIL.
- `test_look_labeling.py` — `label_looks` confidence/full_body(유지).
- `test_report_generation.py` — 모의 슬롯으로 카드·근거표 생성, source ID 포함, 금지문구 미포함(재작성).

### 10.2 LLM 계약 테스트
- `extract`/`group_signals`/`rank_looks`에 **모의 응답 주입** → 스키마·사후검증(근거 subset, 룩 존재, 전신, 테마 3~6) 확인.

### 10.3 live 스모크
- `OPENAI_API_KEY` 존재 + 사용자 승인 시에만. 결과는 비용·날짜에 따라 달라지므로 단위테스트 합격 조건과 분리.

**삭제:** `test_anchor_classification`, `test_category_look_selection`, `test_home_exposure_routing`(태그/quota/slot_count 전제).

## 11. 검증 명령

플러그인 루트에서:

```bash
python -m pytest -q
# live 실행(키 필요)
export OPENAI_API_KEY=...   # PowerShell: $env:OPENAI_API_KEY="..."
python tools/run_pipeline.py --clean-output
```

저장소 루트에서 플러그인 구조 검증:

```bash
python C:/Users/akswo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  src/musinsa-need-aware-look-first-agent
```

검증 후 직접 확인: `home_exposure_plan.csv`(중복/슬롯수),
`category_look_selection.csv`(테마·이유), `look_product_mapping.csv`(핵심/대체),
`evidence_table.md`(근거 추적), `validation_report.md`(PASS·커버리지 갭).

## 12. 구현 순서 (승인 후, 기계적)

1. `home_context_config.yaml` 스키마 변경(target_slots/per_theme_cap/theme_count).
2. `pipeline.py`: `extract` 교체 + `group_signals`/`rank_looks`/`assemble_slots` 신설 + `validate` 완화 + `run` 재배선, 구 태그/sample 코드 제거.
   - 검증: 순수함수 단위테스트 통과.
3. `run_pipeline.py`: `--mode` 제거.
4. 테스트 삭제/재작성/신규(순수함수 + 모의 LLM 중심).
   - 검증: `pytest -q` 초록.
5. SKILL.md 5종 조정(§9).
6. README 갱신.
7. live 스모크(§10.3): extract/group(3~6)/rank 스키마 통과, 슬롯≥1, 근거 subset 위반 0, 금지문구 0.

## 13. 트레이드오프 / 가정

- **가정 A:** live 목표는 태그 유지보수 없는 자유 트렌드 발굴. 다양성 최우선(완전 창발).
- **가정 B:** 룩은 태그 없이 제목/이미지/시즌/상품만으로 LLM 판단 가능(제목이 서술적).
- **인벤토리 한계:** 룩 10개·전원 여름. 계절 밖 트렌드는 매칭 대상 자체가 없어 슬롯이 빌 수 있음 → 검증 완화로 정상 수용, 커버리지 갭 기록.
- **sample 제거 대가:** 오프라인 end-to-end 결정론 검증이 사라짐 → 순수함수 단위테스트 + 모의 LLM + live 스모크로 방어. 테마 라벨은 실행마다 달라질 수 있음(다양성과 맞바꿈).
- **OpenAI 통합 검색:** 별도 검색 사업자 없이 단순하나 호출료·토큰 비용 발생, 키/네트워크 없으면 시연 불가.
- **롤백:** 브랜치 작업, 방향 틀리면 `git reset`.

## 14. 승인 전 확인할 항목 (기본 가정)

1. 플러그인 경로 `src/musinsa-need-aware-look-first-agent/`.
2. `.mcp.json` 미생성.
3. **live 단일 모드**(sample 없음).
4. `live`는 OpenAI Responses API 웹검색+구조화 출력 사용.
5. 실제 무신사/SNS 크롤링 없음.
6. `author.name`·`interface.developerName` = `lezilimenzi`.
7. PDP 문구·캠페인 브리프 미구현.
8. 테마 개수 `3~6`, `target_slots`/`per_theme_cap`는 config에서 조정.

## 15. 구현 상태

- 재설계 계획 승인: **완료** → 브랜치 `redesign/emergent-theme-ranking`에서 구현
- 파이프라인 재작성: **완료** (extract/group_signals/rank_looks/assemble_slots 신설, 태그·sample·shim 제거, validate 완화)
- config·run_pipeline·SKILL 5종·README 갱신: **완료**
- 테스트: **17개 통과** (assemble/validate/report 계약 + label_looks; LLM 단계는 모의/계약 검증)
- live 스모크(§10.3): **미실행** — API 키·비용 필요, 사용자 환경에서 확인 예정
- 초기 MVP(태그 기반): 본 재설계로 대체됨
- `live_search` 개선(검색 강제·재시도·skip): 적용 완료(`tools/debugging.md`)

## 16. 확장 로드맵 (앱 확장 시 · MVP 범위 밖, 문서화만)

> 아래는 **MVP 구현 범위가 아니다.** 나중에 실제 무신사 코디를 서비스에 연결할 때를 대비한
> 확장 지점 기록이다. MVP는 여전히 §1~§14 범위로만 구현한다.

### 16.1 왜 필요한가 — 스케일 병목
현재 `rank_looks`는 **룩 카탈로그 전체를 LLM 프롬프트에 넣어** 랭킹한다. 룩 10개에선 되지만,
무신사 실제 코디/스냅은 수만~수백만 건이라 프롬프트에 다 넣을 수 없다. 즉 "LLM이 전체 카탈로그를
훑어 랭킹"하는 방식은 **스케일에서 무너진다.** MVP는 의도된 소규모 PoC 지름길이다.

### 16.2 목표 구조 — 2단계 (검색 → 재랭킹)
```
트렌드/테마 ──① retrieval ──▶ 후보 수십 건 ──② LLM 재랭킹 ──▶ 최종 슬롯 + 근거
            (수백만 코디 중)                  (지금의 rank_looks)
```
- **① retrieval:** 수백만 코디를 후보 수십 건으로 좁히는 **벡터(임베딩) 검색** 인덱스. (MVP에서 미룬 임베딩이 여기서 필수화)
- **② rerank:** 후보 수십 건에 대해서만 **현재의 LLM 제로샷 랭킹**을 돌려 순위+한국어 근거 생성. LLM 랭킹은 검색기가 아니라 **재랭커**로 위치 이동.

### 16.3 핵심 캐비어트 — 코디는 이미지다
샘플 룩은 서술적 한국어 제목이 있어 텍스트만으로 매칭되지만, 실제 무신사 스냅/코디는 제목·태그가
빈약하고 정보 대부분이 **이미지**에 있다. 따라서 retrieval은 **멀티모달(이미지+텍스트) 임베딩**이어야
트렌드 의미에 맞는 코디를 제대로 불러온다. 텍스트-only 임베딩은 시각 스타일 신호를 놓친다.

### 16.4 데이터 모델 호환성
Signal/Theme/RankedLook 스키마는 그대로 확장 호환. 룩에 `embedding 벡터 + 실제 메타 + 이미지`만
추가되고, 바뀌는 건 "룩을 어디서 가져오나"(CSV → 무신사 코디 DB/API + 벡터 인덱스)이지 하류 로직이 아니다.

### 16.5 지금 넣어둘 확장 이음새 (권장, 저비용)
`rank_looks(themes, candidate_looks)` 를 **"후보 집합"을 인자로 받도록** 정의한다.
- MVP: `candidate_looks = 전체 룩` 을 넘긴다.
- 앱: `candidate_looks = 검색기 top-K` 로만 바꿔 끼우면 **재랭커 코드는 그대로 재사용**.

이 시그니처 하나로 "MVP의 전체 랭킹"과 "앱의 검색→재랭킹"이 드롭인 호환이 된다. (스코프 변경 아님 — MVP는 전체를 후보로 넘길 뿐)

### 16.6 앱 확장 시 추가로 필요한 것 (범위 밖)
- 무신사 코디 DB/API 연동, 이미지 파이프라인, 실시간 재고 확인.
- 벡터 인덱스 운영(색인 갱신, ANN 검색), 임베딩 모델 선택.
- 개인화·사용자 검색어 라우팅(별도 고도화).

---
**다음 액션:** 이 계획 검토/수정 후 승인해 주세요. 승인 전까지 구현하지 않습니다.
