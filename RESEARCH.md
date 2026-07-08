# MUSINSA Need-aware Look-first Agent 설계서

## 0. 문서 목적

이 문서는 Codex 플러그인 **MUSINSA Need-aware Look-first Agent**의 문제 정의, 제품 철학,
파이프라인 아키텍처, 데이터 계약, AI 적용 지점, 룩 라벨링·랭킹 방식, 홈 노출 로직, 검증 방법을
하나로 정리한 설계 문서다.

핵심은 **사용자 검색어 기반 추천이 아니라, MD/서비스 기획자가 홈·추천판·기획전에 활용할
코디 중심 노출 슬롯을 빠르게 기획하도록 돕는 구조**다. 현재 시즌·날씨·이벤트·패션 트렌드 신호를
공개 웹에서 검색해 "지금 어떤 코디를 어떤 이유로 보여줄지"를 근거와 함께 제안한다.

> **아키텍처 요약:** 통제 태그 매칭을 쓰지 않는다. 웹 검색 → LLM 자유서술 신호 추출 →
> 창발 테마 그룹핑 → LLM 제로샷 룩 랭킹(브랜드 전문성 반영) → 전역 배정으로 슬롯 구성.
> 초기 태그 기반 설계에서 이 구조로 전환한 경위는 §부록(설계 변천) 및 `PLAN.md §15` 참고.

---

## 1. 플러그인 한 줄 정의

> 현재 시즌·이벤트·날씨·패션 트렌드 신호를 분석해 홈·추천판·기획전에 쓸 대표 키워드와 전신 코디
> 슬롯 후보를 만들고, 연결 상품과 선정 근거 리포트를 생성하는 Codex 플러그인.

---

## 2. 문제 정의

무신사는 이미 개인화 추천과 AI 트렌드 큐레이션을 운영한다. 따라서 본 플러그인의 목적은 기존 추천
시스템을 대체하거나 또 하나의 개인화 추천 모델을 만드는 것이 아니다.

여전히 MD/서비스 기획자가 특정 시즌·이벤트·TPO에 맞는 **코디 중심 노출 슬롯을 빠르게 기획하고,
왜 이 주제와 룩을 선택했는지 설명 가능한 형태로 정리하는 업무**는 복잡하다. 공개 트렌드·이벤트·날씨
신호를 검토하고, 대표 주제를 정하고, 적합한 스냅·코디룩과 상품을 연결하고, 노출 근거까지 작성해야
하기 때문이다.

많은 사용자는 막연한 상태로 홈 화면에 진입한다("요즘 뭐 입지?", "여름 옷 좀 볼까?",
"이번 시즌 뭐가 유행하지?", "페스티벌 갈 때 입을 옷 없나?"). 이때 상품만 먼저 노출하면 사용자는
"이걸 어떻게 입지?"를 해결하지 못한다. 반대로 코디룩을 먼저 보여주면 스타일링 맥락을 먼저 이해한다.

> 문제 정의: 현재 시점의 트렌드·이벤트·날씨·시즌 맥락을 분석해 홈·추천판·기획전에 쓸 대표 키워드를
> 추출하고, 그 키워드를 시각적으로 보여주는 모델/스냅의 전신 코디 슬롯 후보와 연결 상품, 선정 근거를
> 자동 생성한다.

서비스 맥락 참고: [무신사 추천판](https://www.musinsa.com/main/musinsa/recommend?gf=A)

---

## 3. MVP 범위

### 3.1 구현하는 것

```text
1. 공개 웹 검색(OpenAI Responses web_search)으로 트렌드·이벤트·날씨 신호 수집
2. 검색 결과의 URL·제목·수집일·출처 저장 (그라운딩)
3. LLM으로 자유서술 트렌드 신호 + 노출용 대표 키워드 추출 (통제 태그 없음)
4. 신호를 창발 테마 3~6개로 그룹핑 (사전 카테고리 없음)
5. 룩 전신(full_body) 검증 및 label_confidence 계산
6. LLM 제로샷 룩 랭킹 — 브랜드 전문성·아이덴티티를 fit_score에 반영
7. 전역 배정 + min_fit_score 하한으로 노출 슬롯 조립
8. 룩에 핵심·보조·대체 상품 매핑
9. 근거 기반 Look-first 카드 + 검증 리포트 생성
```

여기서 검색은 트렌드·행사·날씨 자료를 찾는 **수집 검색**이다. 사용자가 입력한 쇼핑 검색어에 맞춰
상품을 추천하는 **사용자 검색 기반 추천**과는 구분한다.

### 3.2 제외하는 것

```text
1. 사용자 검색어 기반 추천 / 추천 검색 키워드 칩
2. 실시간 무신사 스냅 전체 크롤링 / 내부 API·DB 접근
3. 실시간 개인화 추천 서버 / 딥러닝 추천 모델 학습
4. 실제 매출·전환율 향상 주장
5. 오프라인 sample 모드 (live 단일)
6. PDP 문구·캠페인 브리프 생성
```

### 3.3 향후 고도화 (앱 확장)

```text
1. 무신사 코디 DB/API 연동 + 벡터(멀티모달 임베딩) 검색 → LLM 재랭킹 2단계
   (현재 "카탈로그 전체를 LLM에 넣어 랭킹"은 소규모 PoC 방식이라 스케일에서 무너짐)
2. 사용자 검색어 기반 Look-first 추천 / 개인화 피드
3. A/B 테스트 기반 슬롯 수·하한 최적화
자세한 확장 로드맵은 PLAN.md §16.
```

---

## 4. 핵심 UX 원칙

### 4.1 잘못된 접근

```text
트렌드 감지 → 상품 리스트 추천
예: 락시크 유행 → 레더 재킷 상품만 노출
```
이 방식은 "이걸 어떻게 입지?"를 해결하지 못한다.

### 4.2 올바른 접근

```text
트렌드/이벤트/아이템/날씨 맥락 감지
→ 자유서술 신호 추출 → 창발 테마 그룹핑
→ 라벨링된 전신 코디룩을 LLM으로 랭킹 (브랜드 전문성 반영)
→ 상품보다 룩 먼저 노출
→ 룩에 포함된 핵심 상품·대체 상품 연결
→ 근거 기반 룩 카드 생성
```

### 4.3 핵심 표현 단위: 대표 키워드 + 전신 코디

모든 노출 슬롯은 두 요소를 한 쌍으로 제공한다.

```text
1. 대표 키워드(display_keyword): 슬롯 주제를 즉시 이해시키는 짧은 한국어 표현
2. 전신 코디: 그 키워드가 실제 착장으로 어떻게 구현되는지 보여주는 전신 이미지
```

대표 키워드는 내부 식별자가 아니라 사용자·MD가 이해하는 표시 문구다. 같은 룩도 어떤 테마로
노출되느냐에 따라 키워드가 달라진다(테마 조건부 생성).

| 테마(예) | 대표 키워드 예 | 전신 코디 예 |
|---|---|---|
| 강한 색 대비 룩 | `컬러블로킹 룩` | 블루 그래픽 상의·쇼츠가 보이는 전신 착장 |
| 여름 물놀이 | `워터 페스티벌룩` | 방수 상의·쇼츠·샌들·방수백이 보이는 전신 착장 |
| 우천·기능성 | `장마 출근룩` | 방수 아우터·레인부츠가 보이는 전신 착장 |
| 미니멀 데일리 | `버킷백 미니멀 코디` | 버킷백·상하의 조합이 보이는 전신 착장 |

전신 코디는 상반신 컷이 아니라 상의·하의·신발·주요 액세서리 조합을 볼 수 있는 이미지다.
`look_catalog_raw.csv`의 `shot_type`/`full_body_visible`로 확인하고, 전신 여부를 검증할 수 없는
룩은 슬롯 후보에서 제외한다.

---

## 5. Codex 플러그인 개념

Codex 플러그인은 특정 업무를 반복 가능하게 수행하는 확장 패키지다.

| 구성 요소 | 역할 |
|---|---|
| `.codex-plugin/plugin.json` | 이름·버전·설명 메타데이터 |
| `skills/<skill>/SKILL.md` | Codex가 따를 업무 절차·규칙 |
| `tools/*.py` | 검색·추출·랭킹·리포트 실제 실행 코드 |
| `inputs/` | 입력 데이터 |
| `outputs/`·`reports/` | 산출물 |

이 플러그인은 "MD/운영자가 지금 홈 화면에 어떤 코디룩을 먼저 노출할지 판단하는 업무"를 자동화한다.

## 6. 플러그인 이름

`musinsa-need-aware-look-first-agent` — 폴더명과 manifest `name`을 일치시킨다.

---

## 7. 전체 파이프라인 (`tools/pipeline.py::run`, live 전용)

```text
1. live_search        web_search로 트렌드/이벤트/날씨 검색 + 인용 수집
                      (검색 강제 tool_choice, 카테고리별 재시도, 실패 시 skip, 전부 실패면 예외)
2. extract            LLM: 자유서술 신호 추출 (display_keyword/description/evidence_source_ids/confidence)
3. group_signals      LLM: 신호를 창발 테마 3~6개로 그룹핑 (한국어 라벨 생성)
4. label_looks        전신 검증 + label_confidence(상품 연결 기반)
5. rank_looks         LLM 제로샷: 테마별 룩 랭킹 + 브랜드 전문성 반영 + 사후검증
6. assemble_slots     전역 배정: (테마,룩) fit 정렬 상위부터, min_fit_score 하한, 중복無, 채운 만큼
7. map_products       핵심/보조/대체 상품 연결
8. feedback_scores    참고 지표 (report_only, 선별 미사용)
9. generate_reports   카드·이유 리포트·근거표
10. validate          완화 검증 (하드 게이트만 실패)
```

중간 단계 실패 시 이후를 실행하지 않고 원인을 출력한다.

---

## 8. AI 적용 범위

### 8.1 LLM(AI)이 하는 것
- 검색 근거에서 **자유서술 신호 추출** (통제 태그 강제 없음)
- 신호를 **창발 테마로 그룹핑** (사전 카테고리 없이 데이터에서 도출)
- 테마별 **룩 제로샷 랭킹** + 한국어 근거 생성 + 브랜드 전문성 가중

### 8.2 AI가 아닌 것 (규칙/결정론)
- 전신(full_body) 검증, `label_confidence` 계산
- 전역 배정·min_fit_score 하한·중복 제거(assemble)
- 상품 매핑, 리포트 생성, 검증 게이트

### 8.3 AI라고 주장하지 않는 것
- 실시간 지배력·매출·전환율·재고·판매 순위 주장 (금지)
- 피드백은 계산만 하고 슬롯 선별엔 쓰지 않음 (클릭 최적화 회피)

---

## 9. 소스 수집 구조

- OpenAI Responses API의 `web_search` 도구로 트렌드·이벤트·날씨·시즌 신호를 검색한다.
- 별도의 소스 레지스트리 파일은 쓰지 않는다. 카테고리별 검색 프롬프트(트렌드/이벤트/날씨/아이템/일상)로
  다양한 각도를 커버하되, 이 카테고리는 검색 질의 버킷일 뿐 최종 노출 카테고리가 아니다.
- 접근 제한 페이지 본문을 우회 수집하지 않는다. 검색 실패 카테고리는 재시도 후 건너뛰고, 전부 실패하면
  결과를 위조하지 않고 중단한다.

---

## 10. 자유서술 신호 (Signal)

과거의 통제어휘 Anchor(8개 태그 필드)를 폐기하고, LLM이 검색 근거에서 **의미를 자유롭게 서술**한다.

```json
{
  "signal_id": "SIG001",
  "display_keyword": "컬러블로킹",
  "description": "강한 색을 과감히 섞어 개성을 드러내는 스타일이 다시 힘을 얻고 있다 …",
  "evidence_source_ids": ["LIVE001", "LIVE004"],
  "confidence": 0.84
}
```

검증: 필수 필드 누락, `[0,1]` 범위 밖 confidence, 제공 목록에 없는 `source_id`(부분집합 위반),
빈 `display_keyword`는 거부한다.

---

## 11. 창발 테마 (Emergent Theme)

사전 정의된 5개 카테고리를 폐기하고, LLM이 신호를 의미별로 묶어 **테마 3~6개를 스스로 만든다**.
라벨은 데이터에서 생성된다(예: "강한 색 대비로 존재감을 만드는 룩", "실용성과 날씨 대응형 스타일").

```json
{
  "theme_id": "T1",
  "theme_label": "여름 물축제·페스티벌",
  "member_signal_ids": ["SIG001", "SIG003"],
  "rationale": "물놀이·방수 수요가 하나로 묶임"
}
```

테마는 실행마다 달라질 수 있다(완전 창발의 대가이며 다양성과 맞바꾼 것). 검증은 테마 라벨이 아니라
계약(전신·그라운딩·중복無·채운 만큼)으로 한다.

---

## 12. 룩 라벨링 구조

### 12.1 왜 필요한가
룩 카탈로그를 노출에 쓰려면 전신 여부와 신뢰도를 확인해야 한다. `look_catalog_raw.csv`를 입력받아
`look_catalog_labeled.csv`를 만든다.

### 12.2 라벨링 방식 (최소)
태그·taxonomy·synonym·사람 검수는 쓰지 않는다. 스타일 매칭은 라벨이 아니라 LLM 랭킹이 담당한다.

```text
기존 룩 메타데이터(제목, 브랜드, shot_type, full_body_visible, season)
+ 연결 상품 유무
= look_catalog_labeled.csv (label_confidence 포함)
```

### 12.3 AI/비AI 구분

| 작업 | AI 여부 | 설명 |
|---|---|---|
| 전신 검증 | AI 아님 | shot_type/full_body_visible 확인 |
| label_confidence 계산 | AI 아님 | `0.75 + (연결 상품 있으면 0.05)` |
| 스타일 해석·룩 매칭 | AI | 태그가 아니라 LLM 창발 테마 + 제로샷 랭킹(§13) |

---

## 13. LLM 제로샷 룩 랭킹 (매칭 핵심)

Anchor 태그 교집합 매칭을 폐기하고, 테마별로 **LLM이 룩을 제로샷 랭킹**한다.

- 룩을 텍스트 카드로 직렬화: `look_id, look_title, season, full_body_visible, linked_products,
  brand, brand_specialty, brand_identity`.
- 각 테마마다 LLM이 fit_score(0~1)·한국어 `display_keyword`·`reason`으로 랭킹.
- **브랜드 반영:** 브랜드 전문성이 테마와 강하게 맞으면(예: 수영복 전문 **배럴** ↔ 물놀이 테마)
  fit_score를 높이고 reason에 브랜드를 언급한다. 무관하면 브랜드로 점수를 올리지 않는다.
- **사후검증:** `look_id ∈ 카탈로그`, `full_body==true`, `evidence_source_ids ⊆ 테마 신호 source_id`.
  위반 행은 드롭.
- 산출물: `theme_look_ranking.csv` (테마×룩 전 조합의 fit·근거·브랜드).

---

## 14. 슬롯 조립 및 선별 규칙

### 14.1 전역 배정 (`assemble_slots`)
```text
- 모든 (테마,룩) 쌍을 fit_score로 전역 정렬 → 상위부터 배정
  (각 룩이 자신에게 가장 잘 맞는 테마로 감; 라운드로빈의 오배정 회피)
- fit_score < min_fit_score(기본 0.6) 인 쌍은 버림 (저품질 강제 삽입 차단)
- 한 look_id 중복 배치 금지, 테마당 최대 per_theme_cap
- target_slots까지 채우되 하한 통과 후보가 부족하면 그대로 진행 (강제 채움 없음)
```

### 14.2 테마 균형은 강제하지 않음
트렌드는 특정 테마에 쏠릴 수 있고 그게 실제 모습이다. 전역 배정은 총 매칭 품질을 우선하며,
희소 테마는 슬롯이 적거나 없을 수 있다. rigid한 "정확히 N슬롯" 요구는 폐기했다.

### 14.3 피드백 데이터의 역할
`feedback_scores`(CTR·저장률·체류)는 리포트 참고용으로만 표시하고 슬롯 선별·랭킹에는 쓰지 않는다.
클릭이 곧 구매 의도를 의미하지 않으므로, 클릭 최적화로의 편향을 의도적으로 피한다.

---

## 15. 상품 매핑 (`map_products`)
- 룩에 직접 연결된 상품(`linked_product_ids`)은 **core/supporting**.
- 같은 카테고리의 미연결 상품은 **substitute** 후보(재고는 확인하지 않는다고 명시).
- 산출물: `look_product_mapping.csv`.

---

## 16. 최종 산출물

### 16.1 Look-first 카드 (`reports/look_first_cards.md`)
슬롯마다: 대표 키워드, 전신 코디 이미지, `look_id`/전신여부, 코디명, **브랜드**, 선정 근거,
근거 source ID, 연결 상품(core/supporting/substitute).

### 16.2 노출 전략 리포트 (`reports/exposure_reason_report.md`)
슬롯별 테마·선정 이유·근거 ID (기획자용).

### 16.3 근거표·검증 (`reports/evidence_table.md`, `reports/validation_report.md`)
source_id·제목·URL 근거표와 검증 결과(전신·그라운딩·중복·금지문구·커버리지 갭).

---

## 17. 제출용 파일 구조

```text
src/
└── musinsa-need-aware-look-first-agent/
    ├── .codex-plugin/plugin.json
    ├── skills/
    │   ├── 01-trend-context-ingestion/SKILL.md    # 검색 + 자유서술 신호 추출 + 그라운딩
    │   ├── 02-look-labeling/SKILL.md              # 전신 검증 + confidence
    │   ├── 03-home-exposure-planning/SKILL.md     # 창발 테마 + LLM 랭킹 + 전역 배정
    │   ├── 04-product-mapping/SKILL.md            # 핵심/보조/대체 상품
    │   └── 05-report-generation/SKILL.md          # 근거 카드·검증 리포트
    ├── inputs/
    │   ├── home_context_config.yaml               # target_slots/per_theme_cap/min_fit_score/theme_count/as_of
    │   ├── look_catalog_raw.csv                   # 룩 재고(제목/brand/전신여부/season/연결상품)
    │   ├── brand_catalog.csv                      # 실존 브랜드 전문성·아이덴티티
    │   ├── product_catalog.csv                    # 상품 메타데이터
    │   └── feedback_log_sample.csv                # 룩별 노출·클릭·저장·체류 샘플(참고용)
    ├── tools/
    │   ├── run_pipeline.py                        # 엔트리포인트(live 전용)
    │   ├── pipeline.py                            # 전체 로직
    │   └── common.py                              # 공통 입출력·유틸
    ├── outputs/
    │   ├── source_search_results.json  extracted_signals.json  emergent_themes.json
    │   ├── look_catalog_labeled.csv    theme_look_ranking.csv   feedback_scores.csv
    │   └── look_product_mapping.csv    home_exposure_plan.csv
    ├── reports/
    │   ├── look_first_cards.md  exposure_reason_report.md  evidence_table.md  validation_report.md
    ├── tests/
    │   ├── conftest.py  test_assemble_slots.py  test_validate.py
    │   └── test_look_labeling.py  test_report_generation.py
    └── README.md
```

## 18. plugin.json 예시

```json
{
  "name": "musinsa-need-aware-look-first-agent",
  "version": "1.0.0",
  "description": "Generate grounded, emergent-theme Look-first home exposure plans from fashion trend signals.",
  "skills": "./skills/"
}
```

---

## 19. SKILL 5종 요약

| skill | 핵심 지시 |
|---|---|
| 01 trend-context-ingestion | web_search 강제·재시도, 자유서술 신호(키워드/서술/근거/confidence) 추출, 그라운딩, 근거 없는 주장 금지 |
| 02 look-labeling | 전신(full_body) 검증, 상품 기반 confidence. 미제공 시 전신 추론 금지 |
| 03 home-exposure-planning | 창발 테마 3~6, LLM 제로샷 랭킹(브랜드 전문성 반영), 전역 배정 + min_fit_score, 테마 균형 비강제 |
| 04 product-mapping | core/supporting(직접 연결) + substitute(동일 카테고리), 재고 미확인 명시 |
| 05 report-generation | 대표 키워드·전신 코디·연결 상품·근거 ID 포함, 금지 문구 없음 |

---

## 20. README 실행 예시

```powershell
python -m pytest -q
$env:OPENAI_API_KEY="..."
python tools/run_pipeline.py --clean-output
```

sample(오프라인) 모드는 없다. 결정론 검증은 순수 함수 단위테스트로, LLM 단계는 live 실행으로 확인한다.

---

## 21. 예시 시나리오

- **여름 물놀이 테마:** 검색이 워터·페스티벌 트렌드를 물어오면 신호가 "물놀이·방수"로 묶여 테마가
  창발한다. 수영복 전문 **배럴**의 워터룩(L003)이 브랜드 전문성 가중으로 높은 fit을 받아 상위 노출된다.
- **우천·기능성 테마:** 장마 신호 → 레인부츠 전문 **락피쉬 웨더웨어**의 장마 데일리룩(L006)이 가점.
- **미니멀 데일리:** 뉴트럴·오피스 신호 → 무신사 스탠다드·아모멘토의 린넨/버킷백 룩이 매칭.
- **로맨틱:** 원피스·메리제인 신호 → 마르디 메크르디 룩이 매칭.

각 슬롯은 대표 키워드 + 전신 코디 + 브랜드 + 연결 상품 + 근거 source ID를 함께 제공한다.

---

## 22. 사용자 검색어 기반 추천은 고도화 항목

MVP는 사용자가 입력한 검색어에 반응하지 않는다. 홈 화면 선노출형 기획을 돕는 것이 목적이며,
사용자 검색어 라우팅·추천 검색 키워드 칩·개인화는 향후 고도화로 분리한다.

---

## 23. 검증 방법

### 23.1 단위 테스트 (결정론, LLM 불필요)
- `test_assemble_slots` — 전역 배정이 룩을 최적 테마로 보내는지, `min_fit_score` 하한이 저품질을
  버리는지, 목표를 강제 채우지 않는지, 중복無·전신·그라운딩.
- `test_validate` — 하드 게이트(전신·그라운딩·중복·금지문구·빈 계획) 실패, 슬롯 부족 시 PASS+gap.
- `test_look_labeling` — 상품 기반 confidence·full_body.
- `test_report_generation` — 리포트 생성·그라운딩 계약.

### 23.2 LLM 계약 / live 스모크
- extract/group/rank는 스키마·사후검증(근거 부분집합, 룩 존재, 전신, 테마 3~6)을 모의 응답 또는
  live 실행으로 확인.
- live 스모크는 `OPENAI_API_KEY`가 있을 때만. 결과는 비용·날짜에 따라 달라지므로 단위테스트 합격
  조건과 분리한다.

### 23.3 하드 게이트 (validate)
전신만·슬롯당 근거 source_id·중복 룩 금지·금지 문구 미포함·빈 계획 아님. 슬롯 수가 `target_slots`에
미달해도(커버리지 갭) 실패가 아니다.

---

## 24. 한계와 주의사항

1. 실시간 프로덕션 추천 엔진이 아니다. 로컬 배치 분석 도구이며 결과는 CSV·JSON·Markdown 파일이다.
2. 사용자 검색어 기반 추천이 아니라 홈 화면 선노출형이다.
3. 룩 라벨링은 전신 검증 + 상품 기반 confidence로 최소화했고, 스타일 매칭은 LLM 랭킹이 담당한다.
4. 클릭·저장·체류는 선호의 간접 신호일 뿐이며 슬롯 선별에 쓰지 않는다.
5. 매출·전환율·반품률 개선은 내부 데이터·A/B 테스트 없이 주장하지 않는다.
6. **인벤토리 한계:** 룩 카탈로그가 작으면(현재 10개·여름 위주) 계절 밖 트렌드는 매칭 대상 자체가
   없어 슬롯이 빌 수 있다. `min_fit_score` 하한 때문에 슬롯이 target보다 적을 수 있고 이는 정상이다.
7. **스케일 한계:** 현재 "카탈로그 전체를 LLM 프롬프트에 넣어 랭킹"하는 방식은 수만~수백만 코디에는
   맞지 않는다. 앱 확장 시 벡터(멀티모달 임베딩) 검색 → LLM 재랭킹 2단계가 필요하다(PLAN §16).
8. 브랜드 배정은 실존 브랜드를 스타일에 맞춰 예시로 넣은 **샘플 데이터**이며 특정 브랜드에 대한 주장은
   아니다.
9. 테마 라벨은 실행마다 달라질 수 있다(완전 창발). 검증은 라벨이 아닌 계약으로 한다.

---

## 25. 최종 제출용 요약 문장

> 본 플러그인은 개인화 추천이나 AI 트렌드 큐레이션을 대체하지 않고, MD/서비스 기획자가 홈·추천판·
> 기획전에 활용할 Look-first 코디 슬롯을 빠르게 기획하도록 돕는다. 공개 웹을 검색해 트렌드·이벤트·
> 날씨 근거를 수집하고, LLM으로 비정형 자료에서 자유서술 신호와 대표 키워드를 추출한 뒤, 신호를
> 창발 테마로 묶고, 브랜드 전문성을 반영한 LLM 제로샷 랭킹으로 전신 코디를 선별한다. 전역 배정과
> 품질 하한으로 슬롯을 구성하며, 대표 키워드·전신 코디·브랜드·연결 상품·선정 근거를 담은 카드와
> 근거 리포트를 생성한다. 통제 태그 매칭·사용자 검색어 추천·개인화는 쓰지 않거나 향후 고도화로 둔다.

---

## 부록. 설계 변천 (태그 기반 → 현재)

초기 MVP는 8개 통제어휘 태그(style/color/item/…)로 신호와 룩을 정확 집합 교집합 매칭하고, 고정 5개
카테고리에 quota를 배분하며, sample/live 두 모드를 두었다. 그러나 live 모드에서 LLM은 한국어
자유서술 태그를 뽑는데 매칭은 영어 snake_case 통제어휘를 요구해 교집합이 항상 비었고(후보 0 → 슬롯 0),
통제어휘 방식 자체가 자유 트렌드 발굴과 맞지 않았다.

이에 **태그 카탈로그 의존을 제거하고 자유서술 신호 → 창발 테마 → LLM 제로샷 랭킹**으로 전환했다.
sample 모드·통제어휘 파일·가짜 사람 검수 데이터·미사용 입력을 제거하고, 라운드로빈 조립을 전역 배정 +
`min_fit_score` 하한으로 교체했으며, 브랜드 전문성 반영을 추가했다. 재설계 계획·구현 순서는
`PLAN.md §15`, 확장 로드맵은 `PLAN.md §16` 참고.
