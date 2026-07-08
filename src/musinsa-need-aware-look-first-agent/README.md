# MUSINSA Need-aware Look-first Agent

MD/서비스 기획자가 홈·추천판·기획전에 사용할 대표 키워드와 전신 코디 슬롯 후보를 만드는 로컬 배치형 MVP다.
공개 웹 트렌드를 검색해 **자유서술 신호 → 창발 테마 → LLM 제로샷 룩 랭킹**으로 슬롯을 구성한다.
통제어휘 태그 매칭은 쓰지 않는다.

## 요구 사항

- Python 3.11+
- `OPENAI_API_KEY` (live 전용, sample 모드 없음)

설치:

```powershell
python -m pip install -r ../../../requirements.txt
```

## 실행

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_MODEL="gpt-5.4-mini"   # 선택
python tools/run_pipeline.py --clean-output
```

검색·추출·그룹핑·랭킹이 모두 실제 OpenAI 호출로 이뤄진다. 실패 시 결과를 위조하지 않고 중단한다.

## 슬롯 구성

- 카테고리는 사전 고정이 아니라 신호에서 **창발한 테마 3~6개**다.
- 룩 랭킹에 **브랜드 전문성**을 반영한다 — 각 룩의 브랜드와 `brand_catalog.csv`의 전문 분야·아이덴티티를 LLM에 주고, 브랜드 전문성이 테마와 맞으면(예: 수영복 전문 브랜드 ↔ 물놀이 테마) 적합도를 더 높인다.
- 모든 (테마,룩) 쌍을 fit_score로 **전역 배정**하고 `min_fit_score` 미만은 버린다. 중복 없이 `target_slots`(기본 10)까지, 테마당 최대 `per_theme_cap`.
- 룩 인벤토리가 부족하면 채운 만큼만 만들고 커버리지 갭을 리포트에 기록한다.
- 채워진 모든 슬롯은 대표 키워드, 검증된 전신 코디, 연결 상품, 근거 source ID를 포함한다.

설정은 `inputs/home_context_config.yaml`의 `target_slots`, `per_theme_cap`, `theme_count`로 조정한다.

## 검증

```powershell
python -m pytest -q
```

순수 함수(`assemble_slots`, `validate`)와 리포트 계약을 단위테스트로 검증한다(LLM/네트워크 불필요).
LLM 단계의 실제 동작은 위 live 실행으로 확인한다.

핵심 산출물: `outputs/home_exposure_plan.csv`, `outputs/theme_look_ranking.csv`,
`reports/look_first_cards.md`, `reports/validation_report.md`.
