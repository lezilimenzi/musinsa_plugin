# MUSINSA Need-aware Look-first Agent

공개 트렌드·이벤트·날씨 신호에서 대표 키워드를 추출하고, 키워드별 전신 코디 슬롯 후보와 연결 상품·선정 근거를 만드는 Codex 플러그인 MVP다.

플러그인 코드는 `src/musinsa-need-aware-look-first-agent/`에 있다. 실제 무신사 UI나 내부 API에는 연결하지 않으며 CSV, JSON, Markdown 산출물을 생성한다.

## 실행

Python 3.11 이상에서:

```powershell
python -m pip install -r requirements.txt
cd src/musinsa-need-aware-look-first-agent
python tools/run_pipeline.py
```

기본값은 API를 호출하지 않는 `sample` 모드다. 실제 웹 검색과 LLM 추출은 다음처럼 실행한다.

```powershell
$env:OPENAI_API_KEY="..."
python tools/run_pipeline.py --mode live
```

자세한 내용은 플러그인 내부 `README.md`를 참고한다.

