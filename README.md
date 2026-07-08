# MUSINSA Need-aware Look-first Agent

공개 트렌드·이벤트·날씨 신호에서 대표 키워드를 추출하고, 키워드별 전신 코디 슬롯 후보와 연결 상품·선정 근거를 만드는 Codex 플러그인 MVP다.

플러그인 코드는 `src/musinsa-need-aware-look-first-agent/`에 있다. 실제 무신사 UI나 내부 API에는 연결하지 않으며 CSV, JSON, Markdown 산출물을 생성한다.

## 실행

Python 3.11 이상, `OPENAI_API_KEY` 필요 (live 전용):

```powershell
python -m pip install -r requirements.txt
cd src/musinsa-need-aware-look-first-agent
$env:OPENAI_API_KEY="..."
python tools/run_pipeline.py --clean-output
```

공개 웹 검색으로 트렌드 신호를 모아 자유서술로 추출하고, 창발 테마로 묶은 뒤 LLM이 전신 코디를
랭킹해 슬롯을 만든다. sample(오프라인) 모드는 없다. 자세한 내용은 플러그인 내부 `README.md` 참고.

