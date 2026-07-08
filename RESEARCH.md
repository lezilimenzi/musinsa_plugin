# MUSINSA Need-aware Look-first Agent 설계서

## 0. 문서 목적

이 문서는 AX 해커톤 예선 제출용 Codex 플러그인 아이디어인 **MUSINSA Need-aware Look-first Agent**의 문제 정의, 플러그인 구조, MVP 파이프라인, 파일 구조, AI 적용 지점, 룩 라벨링 방식, 홈 화면 노출 로직, 검증 방법을 하나의 설계 문서로 정리한 것이다.

이번 MVP의 핵심은 **사용자 검색어 기반 추천이 아니라, MD/서비스 기획자가 홈·추천판·기획전에 활용할 코디 중심 노출 슬롯을 빠르게 기획하도록 돕는 구조**다. 현재 시즌·날씨·이벤트·패션 트렌드·무신사 룩 데이터를 바탕으로 “지금 어떤 코디를 어떤 이유로 보여줄지”를 제안한다. 단, 트렌드와 이벤트 근거를 확보하기 위한 **공개 웹·데이터 소스 검색**은 MVP 수집 기능에 포함한다.

다만 사용자 검색어 기반 추천, 추천 검색 키워드 칩, 개인화 검색 라우팅은 향후 고도화 항목으로 분리한다.

---

## 1. 플러그인 한 줄 정의

> 현재 시즌, 이벤트, 날씨, 패션 트렌드 신호를 분석해 홈·추천판·기획전에 사용할 대표 키워드와 전신 코디 슬롯 후보를 만들고, 연결 상품과 선정 근거 리포트를 생성하는 Codex 플러그인.

---

## 2. 문제 정의

무신사는 이미 개인화 추천과 AI 트렌드 큐레이션을 운영하며 콘텐츠 기반 상품 발견 경험을 강화하고 있다. 따라서 본 플러그인의 목적은 기존 추천 시스템을 대체하거나 또 하나의 개인화 추천 모델을 만드는 것이 아니다.

여전히 MD/서비스 기획자가 특정 시즌·이벤트·TPO에 맞는 **코디 중심 노출 슬롯을 빠르게 기획하고, 왜 이 주제와 룩을 선택했는지 설명 가능한 형태로 정리하는 업무**는 복잡하다. 공개 트렌드·SNS·이벤트·날씨 신호를 검토하고, 대표 주제를 정하고, 적합한 스냅·코디룩과 상품을 연결하고, 노출 근거까지 작성해야 하기 때문이다.

많은 사용자는 다음과 같은 막연한 상태로 홈 화면에 진입한다.

```text
“요즘 뭐 입지?”
“여름 옷 좀 볼까?”
“이번 시즌에 뭐가 유행하지?”
“페스티벌 갈 때 입을 만한 옷 없나?”
“그냥 예쁜 코디를 보고 싶다.”
```

이 상황에서 상품만 먼저 노출하면 사용자는 “이걸 어떻게 입어야 하지?”라는 문제를 해결하지 못한다. 반대로 코디룩을 먼저 보여주면 사용자는 상품보다 먼저 스타일링 맥락을 이해할 수 있다.

따라서 본 플러그인의 문제 정의는 다음과 같다.

> 현재 시점의 트렌드, 이벤트, 날씨, 시즌 맥락을 분석해 홈·추천판·기획전에 사용할 대표 키워드를 추출하고, 그 키워드를 시각적으로 보여주는 모델 또는 스냅의 전신 코디 슬롯 후보와 연결 상품, 선정 근거를 자동 생성한다.

서비스 맥락 참고: [무신사 추천판](https://www.musinsa.com/main/musinsa/recommend?gf=A)

---

## 3. MVP 범위

### 3.1 MVP에서 구현하는 것

```text
1. 공개 웹·데이터 소스 검색 및 샘플 데이터 입력
2. 검색 결과의 URL·제목·게시일·수집일·본문 요약 저장
3. LLM 기반 트렌드/컨텍스트 정보와 노출용 대표 키워드 추출
4. Trend Anchor / Context Anchor 분류
5. 무신사 스냅·코디룩 샘플 데이터 라벨링 및 전신 코디 여부 확인
6. 홈 화면용 Look-first 피드 생성
7. 카테고리별 노출 수 할당 및 라벨링된 룩 선별
8. 룩에 연결된 핵심 상품·대체 상품 매핑
9. 근거 기반 Look-first 카드 생성
10. 검증 리포트 생성
```

여기서 검색은 검색 API 또는 허용된 공개 소스 조회를 통해 트렌드·행사·날씨·매거진 자료를 찾는 **수집 검색**을 의미한다. 사용자가 입력한 쇼핑 검색어에 맞춰 상품이나 룩을 추천하는 **사용자 검색 기반 추천**과는 구분한다.

### 3.2 MVP에서 제외하는 것

```text
1. 사용자가 검색한 이후의 검색 기반 추천
2. 추천 검색 키워드 칩
3. 실시간 무신사 스냅 전체 크롤링
4. 실시간 개인화 추천 서버
5. 딥러닝 추천 모델 학습
6. 실제 매출/전환율 향상 주장
7. 무신사 내부 데이터 접근을 전제로 한 기능
```

### 3.3 향후 고도화 항목

```text
1. 사용자 검색어 기반 Look-first 추천
2. 추천 검색 키워드 칩
   예: 봄 유행 패션, 26 FW 트렌드, 흠뻑쇼 코디, 버킷백 코디
3. 개인별 클릭/저장 이력 기반 개인화 피드
4. 이미지 기반 룩 분석
5. A/B 테스트 기반 카테고리별 슬롯 수 최적화
6. 프로덕션 추천 API 연동
```

---

## 4. 핵심 UX 원칙

### 4.1 잘못된 접근

```text
트렌드 감지 → 상품 리스트 추천
예: 락시크 유행 → 레더 재킷 상품만 노출
예: 버킷백 유행 → 버킷백 상품만 노출
예: 흠뻑쇼 시즌 → 파란 티셔츠 상품만 노출
```

이 방식은 사용자가 “이걸 어떻게 입지?”라는 질문을 해결하지 못한다.

### 4.2 올바른 접근

```text
트렌드/이벤트/아이템/날씨 맥락 감지
→ 스타일링 앵커 분류
→ 라벨링된 코디룩 검색
→ 상품보다 룩 먼저 노출
→ 룩에 포함된 핵심 상품과 대체 상품 연결
→ 근거 기반 룩 카드 생성
```

예시:

```text
락시크 유행
→ 블랙 레더 + 부츠 + 데님 + 실버 액세서리 룩 노출
→ 해당 룩에 연결된 레더 재킷, 부츠, 데님, 체인백 상품 추천
```

```text
흠뻑쇼 시즌
→ 블루/화이트 기반 페스티벌룩 노출
→ 블루 티셔츠, 쇼츠, 샌들, 방수백, 캡 상품 연결
```

```text
장마철
→ 나일론 셔츠, 방수백, 레인부츠, 어두운 컬러 팬츠 중심 룩 노출
→ 장마철 출근룩/데일리룩으로 상품 연결
```

### 4.3 핵심 표현 단위: 대표 키워드 + 전신 코디

모든 노출 슬롯은 다음 두 요소를 한 쌍으로 제공한다.

```text
1. 대표 키워드: 사용자가 슬롯의 주제를 즉시 이해할 수 있는 짧은 표현
2. 전신 코디: 해당 키워드가 실제 착장으로 어떻게 구현되는지 보여주는 모델 또는 스냅 이미지
```

대표 키워드는 내부 Anchor를 그대로 노출하는 기술적 라벨이 아니라 사용자와 MD가 이해할 수 있는 표시 문구다.

| 내부 Anchor | 대표 키워드 예시 | 전신 코디 예시 |
|---|---|---|
| `style_mood=rock_chic` | `락시크` | 블랙 레더 재킷·데님·부츠가 모두 보이는 전신 착장 |
| `event_tpo=water_festival` | `워터 페스티벌룩` | 블루 상의·쇼츠·샌들·방수백이 보이는 전신 착장 |
| `weather=monsoon` | `장마 출근룩` | 방수 아우터·팬츠·레인슈즈가 보이는 전신 착장 |
| `item=bucket_bag` | `버킷백 코디` | 버킷백과 상·하의 조합이 함께 보이는 전신 착장 |
| `occasion=campus` | `캠퍼스룩` | 상의·하의·신발·가방의 조합이 보이는 전신 착장 |

여기서 대표 키워드는 향후 고도화 항목인 **추천 검색 키워드 칩**과 다르다. MVP의 키워드는 검색을 유도하는 인터랙션이 아니라 각 Look-first 슬롯의 주제와 선정 근거를 명확하게 표시하는 제목이다.

전신 코디는 단일 상품 컷이나 상반신 중심 이미지가 아니라 상의, 하의, 신발과 주요 액세서리의 조합을 확인할 수 있는 이미지를 의미한다. MVP에서는 `look_catalog_raw.csv`의 `shot_type` 또는 `full_body_visible` 메타데이터로 이를 확인하고, 전신 여부를 검증할 수 없는 이미지는 핵심 슬롯 후보에서 제외한다.

---

## 5. Codex 플러그인 개념

Codex 플러그인은 Codex가 특정 업무를 반복 가능하게 수행하도록 만드는 **업무용 확장 패키지**다.

일반 프롬프트는 매번 사용자가 지시를 길게 적어야 하고 결과가 흔들릴 수 있다. 반면 Codex 플러그인은 다음 요소를 묶는다.

| 구성 요소 | 역할 |
|---|---|
| `.codex-plugin/plugin.json` | 플러그인 이름, 버전, 설명 등 메타데이터 정의 |
| `skills/<skill>/SKILL.md` | Codex가 따라야 할 업무 절차와 규칙 정의 |
| `tools/*.py` | 데이터 분석, 라벨링, 점수 계산, 리포트 생성 등 실제 실행 코드 |
| `inputs/` | 샘플 입력 데이터 |
| `outputs/` | 중간 분석 결과 |
| `reports/` | 최종 산출 리포트 |
| `logs/` | AI와 주고받은 전체 대화 로그 |

이 프로젝트에서 플러그인은 “무신사 MD/입점 브랜드/상품 운영자가 현재 시점에 홈 화면에서 어떤 코디룩을 먼저 노출할지 판단하는 업무”를 자동화한다.

---

## 6. 최종 플러그인 이름

```text
musinsa-need-aware-look-first-agent
```

대체 이름:

```text
musinsa-home-look-first-agent
musinsa-look-first-exposure-planner
musinsa-context-to-look-agent
musinsa-trend-context-look-brief-agent
```

추천 최종명:

> **MUSINSA Need-aware Look-first Agent**

---

## 7. 전체 MVP 파이프라인

```text
[1] Fashion Trend Source Search & Ingestion
    검색 API 또는 허용된 공개 소스 조회를 통해 Google Trends, Naver DataLab, Pinterest Trends, 패션 유튜버, 인플루언서, TikTok, Instagram, 패션 매거진 등의 패션 트렌드 후보와 출처 메타데이터를 수집한다.

[2] Event & Context Source Search & Ingestion
    공공 행사 데이터, 티켓 플랫폼, 공식 행사 SNS, 페스티벌 큐레이션 SNS, 지역 문화 계정, 날씨/시즌 데이터를 검색·수집하고 URL, 게시일, 수집일을 기록한다.

[3] LLM-based Information Extraction
    검색·수집한 비정형 텍스트에서 색상, 아이템, 소재, 스타일 무드, 이벤트, TPO, 시즌 정보를 구조화하고, 슬롯 제목으로 사용할 짧은 대표 키워드 후보를 생성한다. 각 추출 결과에는 원문 또는 출처 ID, 추출 신뢰도, 추출 시각을 함께 저장한다.

[4] Anchor Classification
    추출된 신호를 style_mood, item, color, material, silhouette, event_tpo, weather, season, occasion 등 Anchor로 분류한다.

[5] Look Catalog Labeling
    무신사 스냅·코디맵·모델룩 샘플에 style, item, color, TPO, event, material, season 라벨과 shot_type/full_body_visible 메타데이터를 부여한다.

[6] Home Exposure Category Routing
    현재 시점에 홈 화면에서 어떤 카테고리의 룩을 우선 노출할지 규칙 기반으로 결정한다.
    예: 트렌드형, 이벤트형, 날씨형, 시즌형, 아이템형

[7] Anchor-based Look Retrieval
    Anchor 조건과 일치하는 라벨링된 코디룩 후보를 검색한다.

[8] Category Quota-based Look Selection
    트렌드, 이벤트, 날씨/시즌 등 카테고리별 노출 슬롯 수를 먼저 정하고, 각 카테고리에서 직접 일치하는 룩을 우선순위 규칙으로 선별한다.

[9] Look-to-Product Mapping
    선택된 룩에 포함된 핵심 상품, 보조 상품, 대체 상품을 연결한다.

[10] Grounded Look Card Generation
     입력 데이터와 근거를 바탕으로 대표 키워드와 전신 코디를 중심으로 한 Look-first 카드를 생성한다.

[11] Evidence & Validation Report Generation
     왜 이 Anchor가 선택됐고, 왜 이 룩이 노출됐는지 근거와 한계를 리포트로 생성한다.
```

---

## 8. AI 기술 적용 범위

이 플러그인은 모든 단계를 AI로 처리하는 시스템이 아니다. 해석 가능성과 재현성을 위해 홈 피드 구성은 카테고리별 슬롯 할당과 규칙 기반 선별로 구현한다. AI는 주로 **비정형 정보를 구조화하고, Anchor로 분류하고, 근거 기반 설명을 생성하는 부분**에 핵심적으로 적용된다.

### 8.1 핵심 AI 적용 지점

| AI 기술 | 적용 위치 | 설명 |
|---|---|---|
| **LLM 기반 정보 추출** | 트렌드/SNS/이벤트/매거진 텍스트 분석 | 비정형 텍스트에서 색상, 아이템, 소재, 스타일 무드, 이벤트, TPO, 시즌 정보를 추출 |
| **Trend/Context Anchor Classification** | Anchor 분류 단계 | 추출된 신호를 `style_mood`, `item`, `color`, `event_tpo`, `weather`, `season` 등으로 구조화 |
| **RAG / Grounded Generation** | Look-first 카드와 리포트 생성 | 입력 데이터, 룩 라벨, 상품 매핑, 이벤트 근거를 바탕으로 과장 없는 설명 생성 |

### 8.2 보조적으로 사용할 수 있는 AI

| AI 기술 | 적용 위치 | 설명 |
|---|---|---|
| **LLM 기반 라벨 보정** | 룩 라벨링 단계 | 제목·해시태그·설명만으로 스타일 무드나 TPO가 애매할 때 보조 판단 |
| **LLM 기반 근거 검토** | 리포트 검증 단계 | 근거 없는 매출/전환율/최고 인기 등의 표현을 탐지하고 수정 |

### 8.3 AI라고 주장하지 않는 부분

| 기능 | 정확한 명칭 | 설명 |
|---|---|---|
| 홈 노출 카테고리 선택 | 규칙 기반 라우팅 | 시즌, 이벤트 근접도, 날씨, 트렌드 점수 기준으로 노출 카테고리 결정 |
| 사용자 니즈 분류 | MVP에서는 규칙 기반 | 검색어 기반 개인 의도 분류가 아니라, 홈 화면용 노출 카테고리 라우팅 중심 |
| 룩 선별 | 카테고리 쿼터·우선순위 규칙 | 카테고리별 슬롯 수를 먼저 정하고 직접 일치, 근거, 상품 연결 조건으로 후보를 선별 |
| 연결 상품 속성 기반 룩 라벨링 | 메타데이터 기반 라벨 전파 | 룩에 연결된 상품의 색상·소재·카테고리를 룩 라벨로 전달 |
| 동의어 통합 | 사전 기반 정규화 | 버킷백, 복조리백, bucket bag 등 표현 통합 |
| 피드백 분석 | 참고 지표 | CTR smoothing, 저장률, 체류시간을 리포트에 표시하되 MVP 노출 순서를 직접 결정하지 않음 |

### 8.4 제출 답변용 AI 활용 문장

> 본 플러그인은 추천 전 과정을 AI 모델로 처리하지 않는다. 홈 화면은 해석 가능성과 재현성을 위해 트렌드, 이벤트, 날씨/시즌 등 카테고리별 슬롯 수를 먼저 정하고, 각 카테고리에서 직접 일치하는 룩을 우선순위 규칙으로 선별한다. AI는 주로 비정형 정보를 구조화하는 단계에 사용된다. 구체적으로 LLM을 활용해 검색 트렌드, SNS 캡션, 유튜브 제목/자막, 이벤트 설명, 매거진 문장 등에서 색상·아이템·TPO·스타일 무드·이벤트 정보를 추출하고, 이를 Trend Anchor 또는 Context Anchor로 분류한다. 이후 라벨링된 코디룩과 상품 데이터를 검색해 홈 화면에 노출할 룩을 선정하고, RAG 방식으로 근거 있는 Look-first 카드와 검증 리포트를 생성한다. 카테고리별 슬롯 할당, 룩 선별, 상품 속성 기반 라벨 전파는 AI 모델이 아니라 명시적인 규칙으로 구현한다.

---

## 9. 소스 수집 구조

### 9.1 패션 트렌드 탐지 소스

| 소스 | 역할 |
|---|---|
| Google Trends | 검색 수요 변화 탐지 |
| Naver DataLab | 한국 시장 검색 수요 탐지 |
| Pinterest Trends | 시각적 관심도와 스타일 무드 탐지 |
| 패션 유튜버 | 빠른 코디 방식, 대중 언어, 실제 착용 맥락 탐지 |
| 인스타그램 인플루언서 | 실제 착장 확산, 스타일 조합, 해시태그 탐지 |
| TikTok | 조기 바이럴 신호, 짧은 주기 트렌드 탐지 |
| Vogue/WGSN/Elle/Bazaar/GQ | 패션적 의미와 신뢰성 보강 |
| McKinsey/BoF/Lyst | 산업 흐름과 사업적 타당성 보강 |

### 9.2 이벤트·TPO·상황 맥락 소스

| 소스 | 역할 |
|---|---|
| 대한민국 구석구석 / TourAPI | 축제·행사 존재, 날짜, 장소 검증 |
| 서울문화포털 / 지자체 문화행사 정보 | 지역 공연·전시·문화행사 검증 |
| 티켓 플랫폼 | 콘서트·페스티벌 일정 보조 검증 |
| 공식 행사 SNS | 행사 콘셉트, 드레스코드, 분위기 확인 |
| 페스티벌 큐레이션 SNS | 사람들이 실제 관심 가지는 행사 조기 탐지 |
| 인플루언서/유튜버 콘텐츠 | 이벤트룩, 페스티벌룩, 수영장룩 착장 방식 탐지 |
| 해시태그 | #페스티벌룩, #워터밤룩, #흠뻑쇼룩, #수영장룩 등 사용자 언어 탐지 |
| 기상청/날씨 데이터 | 장마, 폭염, 한파, 비, 습도 등 날씨 맥락 탐지 |
| 시즌 캘린더 | 개강, 휴가철, 연말, 면접 시즌, 장마철 등 시즌성 반영 |

### 9.3 트렌드 데이터 업데이트 주기

| 데이터 유형 | 업데이트 주기 | 이유 |
|---|---:|---|
| SNS/인플루언서/해시태그 | 매일 1회 | 트렌드 민감도 높음 |
| 행사/축제/공연 SNS·캘린더 | 매일 1회 | 이벤트 임박도 반영 필요 |
| 날씨/시즌 컨텍스트 | 매일 1회 | 홈 화면 TPO 추천에 직접 영향 |
| 무신사 스냅/코디룩 샘플 | 매일 또는 주 2~3회 | 노출 가능한 룩 후보 갱신 |
| 검색 트렌드 | 주 1회 | 노이즈 줄이고 상승 흐름 확인 |
| 패션 매거진/산업 리포트 | 월 1회 또는 시즌 1회 | 트렌드 검증·해석용 |
| 홈 화면 Look-first 피드 | 매일 1회 | 앱 홈 노출안 생성 |

---

## 10. 신호의 역할 분리

| 레이어 | 주요 자료 | 역할 |
|---|---|---|
| Early Signal Detection | 검색, Pinterest, 유튜버, 인플루언서, TikTok, Instagram | 빠르게 트렌드 후보를 찾음 |
| Context Detection | 행사 SNS, 축제 캘린더, 티켓 플랫폼, 날씨/시즌 | 이벤트·TPO·날씨·시즌 수요를 찾음 |
| Editorial Validation | Vogue, WGSN, Elle, Bazaar, GQ | 패션적 의미와 신뢰도 검증 |
| Musinsa Look Translation | 무신사 스냅, 코디맵, 패션톡 | 트렌드를 실제 노출 가능한 룩으로 번역 |
| Business Context Validation | McKinsey, BoF, Lyst | AI 상품 발견/트렌드 대응의 사업적 타당성 보강 |

중요한 점은 무신사 스냅·코디맵·패션톡이 단순 검증 자료가 아니라는 것이다. 이들은 최종적으로 **어떤 룩을 먼저 보여줄지 결정하는 실행 레이어**다.

---

## 11. Anchor 개념

트렌드는 항상 “스타일” 형태로만 등장하지 않는다. 유행하는 대상은 스타일, 이벤트, 색상, 아이템, 소재, 실루엣, 디테일 등 다양하다.

| Anchor Type | 예시 | 룩 노출 방식 |
|---|---|---|
| `style_mood` | 락시크, 고프코어, 발레코어 | 해당 무드를 가진 전체 착장룩 노출 |
| `event_tpo` | 흠뻑쇼, 워터밤, 페스티벌, 콘서트 | 행사/TPO에 맞는 룩 노출 |
| `color` | 블루, 버건디, 실버 | 해당 색상을 중심으로 한 룩 노출 |
| `item` | 버킷백, 메리제인, 카고팬츠 | 해당 아이템을 활용한 코디룩 노출 |
| `material` | 나일론, 데님, 레더, 시어 | 해당 소재가 드러나는 룩 노출 |
| `silhouette` | 와이드핏, 크롭, 오버핏 | 해당 실루엣 중심 룩 노출 |
| `detail` | 리본, 스터드, 체크 | 디테일이 포인트인 룩 노출 |
| `weather` | 장마, 폭염, 한파 | 기능성/소재/TPO 기반 룩 노출 |
| `season` | 휴가철, 개강, 연말 | 시즌 맥락에 맞는 룩 노출 |

### 11.1 Anchor Classification 예시

```json
{
  "raw_signal": "흠뻑쇼 시즌에는 블루 계열 페스티벌룩과 방수백, 샌들 조합이 자주 언급된다.",
  "anchor_type": "event_tpo_color",
  "display_keyword": "워터 페스티벌룩",
  "event": "soak_show",
  "colors": ["blue", "white"],
  "items": ["tshirt", "shorts", "sandals", "waterproof_bag", "cap"],
  "tpo": ["water_festival", "summer_outdoor"],
  "season": "summer"
}
```

```json
{
  "raw_signal": "락시크 룩이 다시 주목받고 있으며 블랙 레더, 부츠, 실버 액세서리 조합이 많이 보인다.",
  "anchor_type": "style_mood",
  "display_keyword": "락시크",
  "style_mood": ["rock_chic"],
  "colors": ["black", "silver"],
  "materials": ["leather", "denim"],
  "items": ["leather_jacket", "boots", "chain_bag", "graphic_tshirt"]
}
```

---

## 12. 홈 화면 노출 카테고리 라우팅

MVP에서는 사용자가 검색하기 전 홈 화면에 룩을 먼저 제공한다. 따라서 사용자 검색어 기반 니즈 분류보다, **현재 시점의 홈 노출 카테고리 라우팅**이 중심이다.

### 12.1 노출 카테고리

| Exposure Category | 의미 | 예시 룩 |
|---|---|---|
| `trend_discovery` | 지금 유행하는 패션 트렌드 탐색 | 락시크, 긱시크, 고프코어 룩 |
| `event_tpo` | 다가오는 행사·공연·축제 대응 | 흠뻑쇼룩, 워터밤룩, 페스티벌룩 |
| `season_weather` | 계절·날씨 대응 | 장마철 코디, 폭염 출근룩, 한파룩 |
| `item_led` | 특정 유행 아이템 중심 | 버킷백 코디, 메리제인 코디, 카고팬츠 코디 |
| `occasion` | 일상 상황/TPO 대응 | 출근룩, 데이트룩, 캠퍼스룩, 여행룩 |
| `practical_buying` | 실용 목적 구매 | 수영복, 래시가드, 샌들, 방수백 룩 |
| `brand_exploration` | 브랜드 발견 | 신진 브랜드, 무신사 브랜드 기반 룩 |

### 12.2 카테고리별 슬롯 할당

```text
기본 10개 슬롯:
- trend_discovery: 2개
- event_tpo: 2개
- season_weather: 2개
- item_led: 2개
- occasion: 2개
```

카테고리별 개수는 `home_context_config.yaml`에 명시한다. 현재 시점에 관련 이벤트가 없거나 해당 카테고리의 적격 룩이 부족하면 빈 슬롯을 다음 순서로 넘긴다.

```text
event_tpo → season_weather → trend_discovery → item_led → occasion
```

예를 들어 행사 후보가 1개뿐이라면 `event_tpo`에 1개만 배치하고 남은 2개 슬롯은 현재 날씨/시즌 룩과 트렌드 룩에 순서대로 재할당한다. 상품 연결이 없거나 최소 라벨 신뢰도를 충족하지 못한 룩은 슬롯을 채우기 위해 억지로 노출하지 않는다.

### 12.3 홈 화면 기본 슬롯 예시

```text
홈 화면 Look-first 피드 10개 슬롯 예시

1~2번: 트렌드 코디룩 2개
3~4번: 행사/공연/축제 코디룩 2개
5~6번: 날씨/시즌 코디룩 2개
7~8번: 유행 아이템 중심 코디룩 2개
9~10번: 일상 TPO 코디룩 2개
```

예: 7월, 폭염, 워터밤/흠뻑쇼 시즌

```text
1. 락시크 블랙 포인트룩
2. 시어 소재 레이어드룩
3. 블루 워터 페스티벌룩
4. 방수백 포함 여름 공연룩
5. 린넨 셔츠 폭염 출근룩
6. 수영장/휴가 리조트룩
7. 버킷백 오피스 코디룩
8. 메리제인 캐주얼 코디룩
9. 캠퍼스 캐주얼룩
10. 여름 데이트룩
```

---

## 13. 룩 라벨링 구조

### 13.1 왜 룩 라벨링이 필요한가

코디룩을 홈 화면에 노출하려면, 각 룩이 어떤 카테고리에 맞는지 알 수 있어야 한다.

예를 들어 다음 추천이 가능하려면 룩마다 라벨이 필요하다.

| 추천 상황 | 필요한 룩 라벨 |
|---|---|
| 락시크 유행 | `style_mood=rock_chic`, `color=black`, `material=leather`, `item=boots` |
| 흠뻑쇼 시즌 | `event=soak_show`, `color=blue/white`, `tpo=water_festival`, `item=sandals/waterproof_bag` |
| 버킷백 유행 | `anchor_type=item`, `item=bucket_bag`, `style_variant=minimal/casual/office` |
| 장마철 | `weather=rain`, `material=nylon/waterproof`, `item=rain_boots/waterproof_bag` |
| 수영장/휴가 | `tpo=pool/vacation`, `item=swimwear/rashguard/sandals/beach_bag` |

따라서 MVP에서는 `look_catalog_raw.csv`를 입력받아 `look_catalog_labeled.csv`를 생성한다.

### 13.2 라벨링 방식

룩 라벨링은 전체를 사람이 수작업으로 붙이는 방식이 아니다. 다음 요소를 결합한다.

```text
기존 무신사 룩 메타데이터
+ 룩 제목/설명/해시태그
+ 연결 상품의 색상·소재·카테고리·태그
+ label_taxonomy.yaml
+ synonym_dictionary.yaml
+ 일부 사람 검수 데이터
= look_catalog_labeled.csv
```

### 13.3 AI와 비AI 역할 구분

| 라벨링 작업 | AI 여부 | 설명 |
|---|---|---|
| 연결 상품 속성을 룩 라벨로 전파 | AI 아님 | 상품 색상, 소재, 카테고리, 브랜드 태그를 룩으로 전달 |
| 해시태그를 표준 라벨로 매핑 | 주로 AI 아님 | 동의어 사전과 규칙 기반 정규화 |
| 애매한 제목/설명에서 스타일 무드 추론 | AI 보조 가능 | LLM으로 락시크, 긱시크, 오피스코어 등 해석 |
| 라벨 confidence 계산 | AI 아님 | 메타데이터 일치 수, 상품 연결 수, 사람 검수 여부 기반 |

### 13.4 룩 카탈로그 예시

```csv
look_id,look_title,image_url,source_type,shot_type,full_body_visible,season,gender,style_tags,tpo_tags,event_tags,color_tags,item_tags,material_tags,linked_product_ids,engagement_score,label_confidence
L001,락시크 블랙 레더 룩,https://example.com/L001.jpg,snap,full_body,true,fall,women,"rock_chic,chic","concert,weekend","none","black,silver","leather_jacket,boots,chain_bag","leather,denim","P001,P002,P003",842,0.91
L002,흠뻑쇼 블루 페스티벌룩,https://example.com/L002.jpg,codimap,full_body,true,summer,unisex,"festival,sporty","water_festival,summer_outdoor","soak_show","blue,white","tshirt,shorts,sandals,waterproof_bag","nylon,polyester","P011,P012,P013",733,0.88
L003,버킷백 미니멀 데일리룩,https://example.com/L003.jpg,snap,full_body,true,spring,women,"minimal,daily","office,date","none","beige,brown","bucket_bag,shirt,wide_pants,loafers","cotton,leather","P021,P022,P023",610,0.86
```

---

## 14. Anchor 기반 룩 검색 및 선별

### 14.1 기본 검색 방식

Anchor Classification 이후에는 해당 Anchor 조건과 맞는 `look_catalog_labeled.csv`의 룩을 검색한다.

예: 흠뻑쇼 Anchor

```json
{
  "anchor_type": "event_tpo_color",
  "event": "soak_show",
  "required_colors": ["blue", "white"],
  "required_tpo": ["festival", "water_event"],
  "preferred_items": ["tshirt", "shorts", "sandals", "waterproof_bag", "cap"],
  "season": "summer"
}
```

검색 조건:

```text
event_tags contains soak_show
OR tpo_tags contains water_festival
AND color_tags contains blue or white
AND season = summer
```

예: 버킷백 Anchor

```text
item_tags contains bucket_bag
```

예: 락시크 Anchor

```text
style_tags contains rock_chic
OR item_tags contains leather_jacket / boots / chain_bag
AND color_tags contains black
```

### 14.2 검색 후 선별

검색된 모든 룩을 하나의 점수로 경쟁시키지 않는다. 먼저 카테고리별 슬롯 수를 확정한 뒤, 해당 카테고리와 직접 일치하는 룩만 선별한다.

```text
1. home_context_config.yaml에서 카테고리별 목표 개수 확인
2. 카테고리와 직접 일치하는 룩 검색
3. 최소 품질 조건을 통과하지 못한 룩 제외
4. 카테고리별 우선순위 규칙으로 필요한 개수만 선택
5. 후보 부족 시 남은 슬롯을 다른 카테고리에 재할당
```

공통 최소 품질 조건:

- 해당 카테고리의 핵심 Anchor가 하나 이상 직접 일치해야 한다.
- 사용자에게 표시할 대표 키워드가 있어야 한다.
- `shot_type=full_body` 또는 `full_body_visible=true`로 확인된 전신 코디여야 한다.
- `label_confidence`가 설정된 최소 기준 이상이어야 한다.
- 연결 가능한 핵심 상품이 하나 이상 있어야 한다.
- 현재 계절이나 날씨와 명백히 충돌하지 않아야 한다.
- 이미 선택된 동일 룩을 중복 배치하지 않는다.

카테고리별 우선순위:

| 카테고리 | 1순위 | 2순위 | 3순위 |
|---|---|---|---|
| `trend_discovery` | 스타일·아이템 Anchor 직접 일치 | 서로 다른 출처에서 교차 확인 | 연결 상품 수 |
| `event_tpo` | 이벤트/TPO 직접 일치 | 행사 날짜가 가까운 순 | 드레스코드·컬러 일치 |
| `season_weather` | 날씨 직접 일치 | 현재 시즌 일치 | 기능성 소재·아이템 일치 |
| `item_led` | 유행 아이템 직접 포함 | 코디 변형이 다른 룩 | 연결 상품 수 |
| `occasion` | TPO 직접 일치 | 현재 시즌 일치 | 기존 선택 룩과 스타일 중복이 적은 순 |

예를 들어 `event_tpo=2개`라면 이벤트 후보 중 흠뻑쇼/워터 페스티벌 Anchor가 직접 일치하는 룩을 먼저 찾고, 행사 날짜와 드레스코드 일치 여부에 따라 2개를 선택한다. 이 룩들은 트렌드 후보와 전역 점수로 경쟁하지 않는다.

동일한 우선순위 조건까지 같으면 `look_id` 오름차순으로 결정해 결과를 재현 가능하게 만든다. 클릭·저장·체류시간은 MVP의 노출 결정에 사용하지 않고 참고 리포트에만 표시한다.

---

## 15. 카테고리 쿼터와 선별 규칙

### 15.1 기본 카테고리 쿼터

```text
trend_discovery = 2
event_tpo = 2
season_weather = 2
item_led = 2
occasion = 2
```

기본값은 10개 슬롯 기준이며 설정 파일에서 변경할 수 있다. 총합은 `slot_count`와 같아야 한다.

### 15.2 후보 부족 시 재할당

```text
if category has fewer eligible looks than its quota:
    keep all eligible looks
    move remaining slots to fallback categories in configured order
```

재할당 과정에서도 최소 품질 조건은 완화하지 않는다. 전체 적격 룩이 슬롯 수보다 적으면 빈 슬롯을 허용하고 그 이유를 검증 리포트에 기록한다.

### 15.3 피드백 데이터의 역할

클릭률, 저장률, 체류시간은 선택 결과를 설명하는 참고 자료로만 계산한다. 실제 운영 로그가 없는 MVP에서 샘플 피드백으로 노출 순서를 바꾸면 근거가 약해지므로 카테고리 쿼터와 룩 선별에는 사용하지 않는다.

---

## 16. 이벤트 시간 윈도우

이벤트/TPO 추천은 일정에 따라 노출 전략이 달라져야 한다.

| 시점 | 노출 전략 |
|---|---|
| T-30일 | 관심 환기, “미리 준비하는 페스티벌룩” |
| T-14일 | 코디 탐색, 대표 룩 집중 노출 |
| T-7일 | 구매 전환, 준비물/배송/실용 아이템 강조 |
| T-1일~D-day | 체크리스트형 룩, 방수백/샌들/캡 등 실용 아이템 |
| D+1~D+7 | 후기 스냅 재활용, 다음 지역/다음 행사 룩으로 확장 |

예시:

```text
흠뻑쇼 T-14일
→ 블루/화이트 페스티벌룩 45%
→ 방수·활동성 룩 25%
→ 커플/단체룩 15%
→ 일반 여름 페스티벌룩 15%
```

---

## 17. 최종 산출물 정의

### 17.1 Look-first 카드

홈·추천판·기획전 슬롯에 활용할 코디 소개 카드다. MVP의 핵심 산출물이며, 모든 카드는 **대표 키워드와 전신 코디**를 필수로 포함한다.

```text
[대표 키워드]
워터 페스티벌룩

[모델 또는 스냅의 전신 코디 이미지]

코디 포인트
- 블루 컬러 상의로 흠뻑쇼 분위기 반영
- 젖어도 부담 적은 나일론 쇼츠
- 샌들과 방수백으로 활동성 강화

이 룩에 연결된 상품
1. 블루 그래픽 티셔츠
2. 나일론 쇼츠
3. 방수 크로스백
4. 샌들

선정 근거
- 이벤트/TPO: 흠뻑쇼·워터 페스티벌
- 대표 키워드 출처: SRC001, SRC004
- 전신 코디 확인: full_body_visible=true
```

### 17.2 노출 전략 리포트

MD/운영자가 보는 리포트다. 왜 이 룩이 홈 화면에 올라왔는지 근거를 설명한다.

```text
선정 이유:
- 현재 시즌: 여름
- 이벤트 근접도: 흠뻑쇼/워터 페스티벌 시즌
- Anchor: blue, water_festival, sandals, waterproof_bag
- 룩 라벨 일치도: 0.88
- 상품 연결성: 4개 상품 연결 가능
```

### 17.3 PDP 문구와 캠페인 브리프

MVP 핵심은 아니며, 선택 산출물로 둔다.

| 산출물 | MVP 우선순위 | 설명 |
|---|---:|---|
| Look-first 카드 | 1순위 | 사용자에게 직접 노출할 코디 카드 |
| 노출 전략 리포트 | 2순위 | 왜 이 룩을 노출했는지 근거 설명 |
| 상품 매핑표 | 3순위 | 룩과 핵심/대체 상품 연결 |
| PDP 문구 제안 | 선택 | 상품 상세페이지에 넣을 스타일링 문구 |
| 캠페인 브리프 | 선택 | MD/브랜드용 기획전·마케팅 문서 |

---

## 18. 제출용 파일 구조

```text
submission.zip                                           # 예선 최종 제출 압축 파일
├── src/                                                # Codex 플러그인 루트. 과제 요구사항상 전체 플러그인 루트가 src 안에 있어야 함
│   ├── .codex-plugin/                                 # Codex 플러그인 메타데이터 폴더
│   │   └── plugin.json                                # 플러그인 이름, 버전, 설명, skill 경로를 정의하는 필수 파일
│   │
│   ├── skills/                                        # Codex가 사용할 skill 정의 폴더. 기능별로 SKILL.md를 분리해 역할을 명확히 함
│   │   ├── 01-trend-context-ingestion/                # 트렌드·이벤트·날씨·시즌 신호를 읽고 구조화하는 skill
│   │   │   └── SKILL.md                               # LLM 정보 추출과 Anchor 후보 생성을 지시하는 문서
│   │   ├── 02-look-labeling/                          # 스냅·코디룩에 스타일/TPO/아이템 라벨을 붙이는 skill
│   │   │   └── SKILL.md                               # 메타데이터 라벨 전파, 해시태그 정규화, LLM 보정 규칙을 정의
│   │   ├── 03-home-exposure-planning/                 # 검색 전 홈 화면 Look-first 피드를 구성하는 skill
│   │   │   └── SKILL.md                               # 카테고리별 슬롯 할당, 룩 검색, 우선순위 선별 절차를 정의
│   │   ├── 04-product-mapping/                        # 선택된 룩과 상품을 연결하는 skill
│   │   │   └── SKILL.md                               # 핵심 상품, 보조 상품, 대체 상품 매핑 규칙을 정의
│   │   └── 05-report-generation/                      # Look-first 카드와 검증 리포트를 생성하는 skill
│   │       └── SKILL.md                               # RAG 기반 문구 생성, 근거 표, 검증 리포트 작성 규칙을 정의
│   │
│   ├── inputs/                                        # 샘플 입력 데이터 폴더
│   │   ├── trend_signal_samples.csv                   # 검색량, 해시태그, 유튜브 제목/자막 등 패션 트렌드 후보 샘플 데이터
│   │   ├── home_context_config.yaml                   # MVP 실행 시점의 홈 화면 노출 조건. 날짜, 시즌, 지역, 목표 슬롯 수 등을 정의
│   │   ├── product_catalog.csv                        # 상품 ID, 상품명, 브랜드, 카테고리, 색상, 소재, 가격, 태그, 이미지 URL 등 상품 메타데이터
│   │   ├── look_catalog_raw.csv                       # 원본 스냅/코디 데이터. image_url, shot_type, full_body_visible, 제목, 설명, 해시태그, 연결상품을 포함
│   │   ├── human_labeled_looks.csv                    # 사람이 검수한 소량의 룩 라벨 데이터. 자동 라벨 검증 기준으로 사용
│   │   └── feedback_log_sample.csv                    # 룩별 impression, click, save, dwell_seconds 샘플 로그. 실제 운영 로그가 없으므로 MVP 샘플 사용
│   │
│   ├── tools/                                         # 파이프라인 코드 폴더 (실제 로직은 pipeline.py에 집중)
│   │   ├── run_pipeline.py                            # 엔트리포인트 CLI wrapper (from pipeline import run)
│   │   ├── pipeline.py                                # 검색·추출·라벨·매칭·선별·상품매핑·리포트·검증 전체 로직
│   │   ├── common.py                                  # 공통 CSV/JSON/YAML 입출력·정규화 유틸
│   │   └── debugging.md                               # live_search 디버깅 기록
│   │
│   ├── outputs/                                       # 중간 산출물 폴더
│   │   ├── trend_candidates.csv                       # 초기 트렌드 후보 목록과 점수
│   │   ├── context_anchors.json                       # 이벤트/날씨/시즌/TPO 기반 상황 Anchor 목록
│   │   ├── normalized_anchors.json                    # 중복 표현을 정리한 최종 Anchor 구조
│   │   ├── look_catalog_labeled.csv                   # 최종 라벨링된 룩 카탈로그
│   │   ├── label_confidence_report.csv                # 룩별 라벨 출처와 신뢰도 리포트
│   │   ├── home_exposure_categories.json              # 홈 화면 카테고리별 목표 슬롯 수와 재할당 순서
│   │   ├── anchor_matched_look_candidates.csv         # Anchor 조건과 일치하는 1차 룩 후보 목록
│   │   ├── feedback_scores.csv                        # 룩별 클릭률, 저장률, 체류시간, feedback score
│   │   ├── category_look_selection.csv                # 카테고리별 목표 개수와 선별된 룩 목록
│   │   ├── look_product_mapping.csv                   # 룩과 연결 상품/대체 상품 매핑 결과
│   │   └── home_exposure_plan.csv                     # 홈/추천판/기획전 슬롯별 대표 키워드와 전신 코디 노출 계획
│   │
│   ├── reports/                                       # 최종 제출/시연용 리포트 폴더
│   │   ├── look_first_cards.md                        # 실제 홈 화면에 보여줄 Look-first 카드 예시
│   │   ├── exposure_reason_report.md                  # 각 룩이 왜 노출됐는지 Anchor, 라벨, 상품 연결성 기준으로 설명
│   │   ├── evidence_table.md                          # 각 주장·트렌드·룩 선정의 공개 근거 또는 입력 데이터 근거 표
│   │   ├── validation_report.md                       # 검증 방법, 지표, 한계, 환각 방지 결과
│   │   ├── pdp_copy_suggestions_optional.md           # 선택 산출물. 상품 상세페이지 개선 문구와 스타일링 제안
│   │   └── campaign_brief_optional.md                 # 선택 산출물. MD/브랜드 담당자용 캠페인 브리프
│   │
│   ├── tests/                                         # 최소 검증 테스트 폴더
│   │   ├── test_anchor_classification.py              # Anchor 분류가 기대대로 작동하는지 테스트
│   │   ├── test_look_labeling.py                      # 룩 라벨링 결과가 taxonomy와 일치하는지 테스트
│   │   ├── test_home_exposure_routing.py              # 홈 노출 카테고리 라우팅 테스트
│   │   ├── test_category_look_selection.py            # 카테고리별 쿼터, 우선순위, 부족 슬롯 재할당 테스트
│   │   └── test_report_generation.py                  # 리포트 파일 생성 테스트
│   │
│   └── README.md                                      # src 내부 실행 방법, 입력 데이터 설명, 명령어, 산출물 설명
│
├── README.md                                          # 제출물 전체 설명. 문제 정의, 실행 방법, 검증 방법, 한계 포함
└── logs/                                              # AI 작업 로그 제출 폴더
    └── conversation_log.md                            # 플러그인 제작 과정에서 AI와 주고받은 전체 대화 로그. 편집·발췌 금지
```

---

## 19. plugin.json 예시

```json
{
  "name": "musinsa-need-aware-look-first-agent",
  "version": "1.0.0",
  "description": "A Codex plugin that generates home-screen, look-first exposure plans for Musinsa-style fashion commerce using trend/context anchors and labeled look catalogs.",
  "skills": "./skills/"
}
```

---

## 20. SKILL.md 세분화 전략

기술적으로는 하나의 `SKILL.md`로도 가능하다. 하지만 본 플러그인은 기능이 여러 단계로 나뉘므로 MVP에서도 5개 skill로 분리하는 것이 좋다.

| Skill | 역할 |
|---|---|
| `01-trend-context-ingestion` | 트렌드·이벤트·날씨·시즌 신호를 읽고 LLM 정보 추출과 Anchor 후보 생성을 수행 |
| `02-look-labeling` | 룩 메타데이터, 상품 속성, 해시태그를 기반으로 룩 라벨링 수행 |
| `03-home-exposure-planning` | 홈 화면 카테고리별 슬롯 수를 정하고, 각 카테고리에서 룩을 검색·선별 |
| `04-product-mapping` | 선택된 룩과 핵심/보조/대체 상품을 연결 |
| `05-report-generation` | Look-first 카드, 근거표, 검증 리포트를 생성 |

### 20.1 `01-trend-context-ingestion/SKILL.md` 핵심 지시

```markdown
---
name: trend-context-ingestion
description: Extract fashion trend and event/context anchors from sample trend, social, event, weather, and seasonal data.
---

Goal:
Read trend and context input files and generate normalized Trend/Context Anchors.

AI usage:
Use LLM-based information extraction for unstructured text.
Use LLM-based Anchor Classification when rules are insufficient.

Do not:
- Claim real-time trend dominance unless supported by input data.
- Claim sales uplift or conversion improvement.

Outputs:
- outputs/trend_candidates.csv
- outputs/context_anchors.json
- outputs/normalized_anchors.json
```

### 20.2 `02-look-labeling/SKILL.md` 핵심 지시

```markdown
---
name: look-labeling
description: Label Musinsa-style looks using metadata, product attributes, hashtags, taxonomy, synonym dictionary, and optional LLM refinement.
---

Goal:
Create outputs/look_catalog_labeled.csv.

Rules:
- Prefer metadata and product attribute propagation first.
- Use synonym_dictionary.yaml for normalization.
- Use LLM only when title/hashtags/descriptions are ambiguous.
- Track label source and label confidence.

Outputs:
- outputs/look_catalog_labeled.csv
- outputs/label_confidence_report.csv
```

### 20.3 `03-home-exposure-planning/SKILL.md` 핵심 지시

```markdown
---
name: home-exposure-planning
description: Generate a proactive home-screen look-first feed without requiring user search.
---

Goal:
Create a home-screen Look-first exposure plan from anchors and labeled looks.

Rules:
- MVP is not search-based.
- Use rule-based exposure category routing.
- Allocate an explicit number of slots to each exposure category.
- Select direct matches using deterministic priority rules, not a weighted ranking model.
- Reassign unfilled slots without relaxing minimum quality requirements.

Outputs:
- outputs/home_exposure_categories.json
- outputs/anchor_matched_look_candidates.csv
- outputs/category_look_selection.csv
- outputs/home_exposure_plan.csv
```

### 20.4 `04-product-mapping/SKILL.md` 핵심 지시

```markdown
---
name: product-mapping
description: Map selected looks to core, supporting, and substitute products.
---

Goal:
Connect selected looks to purchasable products.

Rules:
- Core products must directly appear in or strongly match the look.
- Substitute products must share category, color/material/style compatibility.
- Do not claim stock availability unless provided.

Outputs:
- outputs/look_product_mapping.csv
```

### 20.5 `05-report-generation/SKILL.md` 핵심 지시

```markdown
---
name: report-generation
description: Generate grounded Look-first cards and validation reports.
---

Goal:
Generate user-facing Look-first cards and evidence-based reports.

AI usage:
Use RAG / grounded generation. Use only provided inputs and intermediate outputs.

Do not:
- Invent sales, conversion, ranking, or inventory claims.
- Say a look is “most popular” unless input data supports it.

Outputs:
- reports/look_first_cards.md
- reports/exposure_reason_report.md
- reports/evidence_table.md
- reports/validation_report.md
```

---

## 21. README 실행 예시

전체 파이프라인을 하나의 명령으로 실행한다(live 전용, sample 모드 없음).

```bash
python -m pytest -q
python tools/run_pipeline.py --clean-output   # OPENAI_API_KEY 필요
```

내부 단계(`pipeline.py`): live_search → extract(자유서술 신호) → group_signals(창발 테마 3~6)
→ rank_looks(LLM 제로샷 룩 랭킹) → label_looks → assemble_slots(채운 만큼) → map_products
→ feedback_scores → generate_reports → validate(완화). 자세한 계획은 `PLAN.md` 참조.

## 22. 예시 시나리오

### 22.1 7월 홈 화면: 흠뻑쇼/워터 페스티벌 시즌

입력 신호:

```text
현재 시점: 7월
이벤트 캘린더: 흠뻑쇼/워터 페스티벌 시즌
SNS 맥락: 블루 코디, 방수백, 샌들, 페스티벌룩 언급
날씨 맥락: 폭염, 야외 활동
```

Anchor 결과:

```json
{
  "anchor_type": "event_tpo_color",
  "event": "soak_show_or_water_festival",
  "colors": ["blue", "white"],
  "items": ["tshirt", "shorts", "sandals", "waterproof_bag", "cap"],
  "tpo": ["water_festival", "summer_outdoor"],
  "season": "summer"
}
```

홈 노출 예시:

```text
1. 블루 티셔츠 + 쇼츠 + 샌들 + 방수백 룩
2. 블루/화이트 커플 페스티벌룩
3. 방수백 중심 워터 페스티벌룩
4. 캡/샌들/나일론 소재 중심 실용 룩
```

### 22.2 FW 트렌드 홈 화면: 락시크

입력 신호:

```text
패션 트렌드 신호: 락시크 콘텐츠 증가
매거진/소셜 맥락: 블랙 레더, 부츠, 실버 액세서리
무신사 룩 데이터: 레더 재킷, 부츠, 블랙 데님 룩 다수 존재
```

Anchor 결과:

```json
{
  "anchor_type": "style_mood",
  "style_mood": ["rock_chic"],
  "colors": ["black", "silver"],
  "materials": ["leather", "denim"],
  "items": ["leather_jacket", "boots", "chain_bag", "graphic_tshirt"]
}
```

홈 노출 예시:

```text
1. 블랙 레더 재킷 + 슬림 데님 + 부츠 룩
2. 밴드 티셔츠 + 블랙 데님 룩
3. 실버 액세서리 포인트 락시크룩
4. 미니멀하게 해석한 락시크 데일리룩
```

### 22.3 아이템 트렌드 홈 화면: 버킷백

입력 신호:

```text
아이템 트렌드 신호: 버킷백/복조리백 언급 증가
무신사 룩 데이터: 버킷백 연결 코디 다수 존재
상품 데이터: 버킷백 관련 상품 연결 가능
```

Anchor 결과:

```json
{
  "anchor_type": "item",
  "item": "bucket_bag",
  "style_variants": ["minimal", "casual", "office", "date"],
  "optional_items": ["shirt", "wide_pants", "loafers", "knit"]
}
```

홈 노출 예시:

```text
1. 버킷백 + 셔츠 + 와이드 팬츠 출근룩
2. 버킷백 + 니트 + 데님 데일리룩
3. 버킷백 + 원피스 데이트룩
4. 버킷백 + 재킷 미니멀룩
```

### 22.4 시즌/TPO 홈 화면: 수영장·휴가

입력 신호:

```text
현재 시즌: 여름
시즌 맥락: 수영장, 휴가, 리조트
상품 데이터: 수영복, 래시가드, 샌들, 비치백 상품 존재
```

Anchor 결과:

```json
{
  "anchor_type": "season_tpo",
  "context": "pool_vacation",
  "items": ["swimwear", "rashguard", "sandals", "beach_bag", "coverup"],
  "style_mood": ["resort", "sporty", "summer_casual"]
}
```

홈 노출 예시:

```text
1. 수영복 + 커버업 + 샌들 룩
2. 래시가드 + 쇼츠 + 비치백 룩
3. 리조트 원피스 + 라탄백 룩
4. 비치 액세서리 중심 휴가룩
```

---

## 23. 사용자 검색어 기반 추천은 고도화 항목으로 분리

MVP에서는 홈 화면 선노출형 구조만 구현한다. 사용자 검색어 기반 추천은 나중에 다음과 같이 확장할 수 있다.

```text
Home Look-first Feed
→ 추천 검색 키워드 칩 제공
→ 사용자가 키워드 클릭
→ 해당 키워드를 Anchor로 변환
→ 라벨링된 룩 재검색
→ 검색 의도 기반 Look-first 피드 생성
```

추천 키워드 칩 예시:

```text
[봄 유행 패션] [26 FW 트렌드] [흠뻑쇼 코디] [워터밤룩]
[버킷백 코디] [장마철 코디] [수영장룩] [출근룩]
```

하지만 본 MVP에서는 이 기능을 구현하지 않는다. 이는 기능 범위가 넓어지고 사용자 검색 의도 처리, 자연어 질의 해석, 검색 결과 피드 재구성이 추가되기 때문이다.

---

## 24. 검증 방법

### 24.1 Anchor Classification 검증

샘플 트렌드/이벤트 문장 30~50개를 사람이 직접 라벨링하고, 플러그인의 Anchor 결과와 비교한다.

| sample_id | text | human_anchor | plugin_anchor | match |
|---|---|---|---|---|
| A001 | 흠뻑쇼 블루 페스티벌룩 | event_tpo_color | event_tpo_color | O |
| A002 | 락시크 블랙 레더 부츠 | style_mood | style_mood | O |
| A003 | 버킷백 미니멀 코디 | item | item | O |

지표:

```text
Anchor Classification Accuracy
```

### 24.2 룩 라벨링 검증

사람이 검수한 `human_labeled_looks.csv`와 자동 생성된 `look_catalog_labeled.csv`를 비교한다.

지표:

```text
Label Precision
Label Recall
Label Confidence Calibration
```

### 24.3 룩 매칭 검증

Anchor별로 Top-3/Top-5 룩이 사람이 보기에도 적합한지 평가한다.

지표:

```text
Top-3 Look Precision
Top-5 Look Precision
```

### 24.4 홈 노출 구성 검증

홈 화면 슬롯이 현재 시즌, 이벤트, 날씨, 트렌드 맥락을 균형 있게 반영하는지 검토한다.

지표:

```text
Exposure Category Coverage
Diversity Score
Context Relevance Score
```

추가 필수 조건:

```text
Keyword Coverage = 대표 키워드가 있는 슬롯 수 / 전체 슬롯 수
Full-body Look Coverage = 전신 코디로 확인된 슬롯 수 / 전체 슬롯 수
```

두 지표는 MVP 필수 슬롯에 대해 `1.0`이어야 한다.

### 24.5 상품 연결 검증

선택된 룩에 연결된 핵심 상품과 대체 상품이 실제 룩 맥락에 맞는지 사람이 검토한다.

지표:

```text
Core Product Relevance
Substitute Product Relevance
```

### 24.6 근거 추적률

Look-first 카드와 리포트의 주요 주장마다 입력 데이터 또는 공개 출처 근거가 붙어 있는지 확인한다.

지표:

```text
Evidence Coverage = 근거가 있는 주장 수 / 전체 주요 주장 수
```

### 24.7 환각 방지 테스트

금지 주장:

```text
이 룩은 구매 전환율을 20% 높입니다.
이 추천은 실제 매출을 증가시켰습니다.
이 상품은 무신사에서 가장 많이 팔렸습니다.
이 상품은 재고가 충분합니다.
```

실제 내부 데이터나 A/B 테스트 없이는 매출, 전환율, 반품률, 재고, 판매 순위 개선을 주장하지 않는다.

---

## 25. 한계와 주의사항

1. 이 플러그인은 실시간 무신사 프로덕션 추천 엔진이 아니다. 예선 제출물에서는 공개 자료 검색·LLM API 호출이 가능한 로컬 배치 분석 도구로 구현하며, 결과는 CSV·JSON·Markdown 파일로 출력한다.
2. MVP는 사용자 검색어 기반 추천이 아니라 홈 화면 선노출형 추천이다. 다만 트렌드·이벤트 근거를 찾기 위한 공개 소스 검색은 MVP에 포함한다.
3. SNS 데이터는 플랫폼 약관과 재현성 문제가 있으므로, 공개적으로 확인 가능한 샘플 데이터 또는 수동 정리 데이터를 사용한다.
4. 룩 라벨링은 기본적으로 메타데이터와 연결 상품 속성 기반이다. LLM은 애매한 텍스트 해석에 보조적으로만 사용한다.
5. 룩 노출은 학습된 추천 모델이나 전역 가중치 점수가 아니라 카테고리별 슬롯 수와 명시적인 우선순위 규칙으로 결정한다.
6. 클릭·저장·체류시간은 선호의 간접 신호일 뿐이다. 클릭이 곧 구매 의도를 의미하지 않는다.
7. 실제 매출 증가, 전환율 개선, 반품률 감소는 내부 데이터와 A/B 테스트 없이는 주장하지 않는다.
8. 개인 단위 민감 프로파일링보다 홈 화면 컨텍스트, 세션 단위 또는 세그먼트 단위 니즈 추론을 우선한다.
9. 유튜버·인플루언서 신호는 빠르지만 광고성·알고리즘 편향이 있을 수 있으므로 검색 데이터, 매거진, 무신사 룩 데이터로 교차 확인한다.
10. 검색 및 LLM 기능은 API 키, 호출 한도, 네트워크 연결에 영향을 받는다. 검색 실패 시 저장된 샘플 입력으로 재현 가능하게 실행하고, LLM 출력은 스키마 검증 후 파이프라인에 반영한다.

---

## 26. 최종 제출용 요약 문장

> 본 플러그인은 기존 개인화 추천이나 AI 트렌드 큐레이션을 대체하지 않고, MD/서비스 기획자가 홈·추천판·기획전에 활용할 Look-first 코디 슬롯을 빠르게 기획하도록 돕는다. 공개 웹·데이터 소스를 검색해 트렌드와 이벤트 근거를 수집하고, LLM을 사용해 비정형 자료에서 색상·아이템·소재·스타일 무드·이벤트·TPO 정보와 사용자에게 표시할 대표 키워드를 추출한다. 이후 트렌드, 이벤트, 날씨/시즌, 아이템, 일상 TPO 카테고리별 노출 개수를 정하고, 라벨링된 스냅·코디룩 카탈로그에서 각 키워드를 실제 착장으로 보여주는 모델 또는 스냅의 전신 코디를 선별한다. 최종적으로 대표 키워드, 전신 코디, 연결 상품, 선정 근거를 포함한 Look-first 카드와 근거 리포트를 생성한다. 카테고리별 슬롯 할당과 룩 선별은 AI 모델이나 전역 가중치 점수가 아니라 재현 가능한 규칙으로 구현하며, 사용자 검색어 기반 추천과 추천 검색 키워드 칩은 향후 고도화 항목으로 둔다.

---

## 27. Phase 2 재설계 사전 분석 — 태그 카탈로그 의존 제거

작성일: 2026-07-08
목적: 현재 파이프라인이 "사람이 정의한 고정 태그 구조(taxonomy)"에 어떻게 얽혀 있는지
정밀 파악하고, 이를 걷어낸 재설계(방향 B)의 범위를 확정한다. 계획 본문은 `PLAN.md §15`.

### 27.1 전체 데이터 흐름 (`tools/pipeline.py::run`)

| # | 단계 | 함수 | 산출물 |
|---|---|---|---|
| 1 | 검색 | `sample_search` / `live_search` | `source_search_results.json` |
| 2 | 신호 추출 | `sample_extract` / `live_extract` | `extracted_signals.json` |
| 3 | 앵커 정규화 | `normalize_anchors` | `normalized_anchors.json`, `context_anchors.json` |
| 4 | 트렌드 후보 | (인라인) | `trend_candidates.csv` |
| 5 | 룩 라벨링 | `label_looks` | `look_catalog_labeled.csv`, `label_confidence_report.csv` |
| 6 | 카테고리 설정 | (인라인) | `home_exposure_categories.json` |
| 7 | **후보 매칭** | `retrieve_candidates` | `anchor_matched_look_candidates.csv` |
| 8 | 피드백 점수 | `feedback_scores` | `feedback_scores.csv` (참고용, 선별 미사용) |
| 9 | 카테고리별 선별 | `select_by_category` | `category_look_selection.csv` |
| 10 | 슬롯 계획 | `build_plan` | `home_exposure_plan.csv` |
| 11 | 상품 매핑 | `map_products` | `look_product_mapping.csv` |
| 12 | 리포트 | `generate_reports` | `look_first_cards.md`, `exposure_reason_report.md`, `evidence_table.md` |
| 13 | 검증 | `validate` | `validation_report.md` (FAIL 시 예외) |

### 27.2 "고정 태그 구조" 의존 지점 (= 걷어낼 대상)

- **입력 파일**
  - `label_taxonomy.yaml` — 8개 필드 통제어휘 정의(style_moods/colors/items/materials/events/tpos/weather/seasons). *(삭제 완료)*
  - `synonym_dictionary.yaml` — 한국어→canonical 매핑. **코드 실사용 없음(이미 dead)**. *(삭제 완료)*
  - `look_catalog_raw.csv`의 `*_tags` 컬럼 — 룩을 통제어휘로 수동 태깅.
- **코드**
  - `SAMPLE_TAGS`, `sample_extract`/`live_extract`(8태그 생성), `normalize_anchors`(태그 set),
    `_look_sets`, `MATCH_FIELDS`/`PRIMARY_FIELDS`, **`retrieve_candidates`(태그 정확 교집합)**, `_priority`(match_count).

→ live 실패 근본 원인: `live_extract`가 한국어 자유서술 태그를 뽑는데 `retrieve_candidates`는
영어 snake_case 통제어휘와 정확 교집합을 요구 → 항상 공집합 → 후보 0 → 슬롯 0.

### 27.3 재설계해도 유지해야 하는 제품 불변식 (스캐폴딩)

- 슬롯 필수: 한국어 `display_keyword`, 검증된 **전신(full_body) 룩**, 연결 상품, **근거 source_id**.
- 중복 룩 금지, 금지문구(BANNED_CLAIMS) 리포트 미포함, 그라운딩(evidence_table).
- 피드백은 참고용, 선별 미사용.
- 후단(quota/상품매핑/리포트/검증)은 태그가 아니라 "카테고리+룩+상품+근거"에 의존 → **대부분 재사용 가능**.

### 27.4 핵심 관찰 / 제약

- **인벤토리 한계는 매칭 방식으로 못 넘는다:** 룩 10개·전원 여름. 계절 밖 트렌드는 매칭 대상
  자체가 없음. 어떤 방식이든 슬롯이 빌 수 있어 `10슬롯` 검증과 충돌 → Phase 2에서 검증 완화로 대응.
- **테스트가 곧 스펙:** 태그/quota/10슬롯을 직접 단언하는 테스트 3종은 재작성 불가피.

*(방향 B의 결정·설계·구현 순서는 `PLAN.md §15` 참조.)*
