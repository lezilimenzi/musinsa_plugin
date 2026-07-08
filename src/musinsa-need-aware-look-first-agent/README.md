# MUSINSA Need-aware Look-first Agent

MD/서비스 기획자가 홈·추천판·기획전에 사용할 대표 키워드와 전신 코디 슬롯 후보를 만드는 로컬 배치형 MVP다.

## 요구 사항

- Python 3.11+
- sample 모드: 추가 인증 없음
- live 모드: `OPENAI_API_KEY`

설치:

```powershell
python -m pip install -r ../../../requirements.txt
```

## 실행 모드

API 없는 기본 실행:

```powershell
python tools/run_pipeline.py --mode sample --clean-output
```

실제 OpenAI 웹 검색과 LLM 정보 추출:

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_MODEL="gpt-5.4-mini"
python tools/run_pipeline.py --mode live --clean-output
```

`live`가 실패하면 결과를 위조하거나 자동으로 sample로 전환하지 않고 중단한다.

## 기본 슬롯

| 카테고리 | 개수 |
|---|---:|
| 트렌드 | 2 |
| 이벤트 | 2 |
| 날씨·시즌 | 2 |
| 유행 아이템 | 2 |
| 일상 TPO | 2 |

모든 슬롯은 대표 키워드, 검증된 전신 코디, 연결 상품, 근거 source ID를 포함해야 한다.

## 검증

```powershell
python -m pytest -q
```

핵심 산출물은 `outputs/home_exposure_plan.csv`, `outputs/category_look_selection.csv`, `reports/look_first_cards.md`, `reports/validation_report.md`다.
