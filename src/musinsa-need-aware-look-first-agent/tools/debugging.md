# Debugging Log

## 2026-07-08 — live 모드 web search 인용 실패로 파이프라인 중단

### 증상
```
python .\src\musinsa-need-aware-look-first-agent\tools\run_pipeline.py --mode live --clean-output
...
RuntimeError: web search returned no citations for season_weather
```
`pipeline.py`의 `live_search`에서 5개 카테고리 중 `season_weather` 하나가
web search 인용(`url_citation`)을 반환하지 않았고, 코드가 곧바로 `RuntimeError`를
던져 **전체 파이프라인이 중단**됨.

### 원인
- `season_weather`("서울의 현재 날씨와 시즌 코디") 같은 질문은 모델이 web_search
  도구를 호출하지 않고 자체 지식으로 답하기 쉬워 인용이 비는 경우가 발생.
- 기존 코드는 "카테고리 1개라도 인용이 없으면 즉시 전체 중단"이라는 취약한 설계였음.
  네트워크 실패가 아니라 이 설계 때문에 에러가 드러남.

### 조치 (`pipeline.py`의 `live_search`만 수정 — 다른 로직 불변)
확정된 동작 방향: **강제 검색 → 실패 시 재시도 → 그래도 안 되면 건너뛰기**

1. **검색 강제** — `_search_with_citations` 헬퍼 신설.
   - `tool_choice={"type": "web_search"}`로 web_search 호출을 강제.
   - 프롬프트에 "반드시 웹 검색을 사용해 최신 공개 출처를 인용하라" 문구 추가.
2. **재시도** — 카테고리별 최대 `attempts`회(기본 3, 환경변수 `LIVE_SEARCH_ATTEMPTS`로
   조절), 재시도 사이 점증 backoff(`time.sleep(attempt)`).
3. **실패 격리** — 재시도 소진 후에도 인용이 없으면 `[warn] ... skipping` 로깅 후
   해당 카테고리만 건너뜀 → 한 카테고리 실패로 전체가 죽지 않음.
4. **안전장치** — 모든 카테고리가 실패해 결과가 0개면 `RuntimeError`로 명확히 실패
   (조용히 빈 결과를 내보내지 않음).
5. `import time` 추가.

### 검증
- `python -m py_compile pipeline.py` 통과.
- end-to-end 실행은 `OPENAI_API_KEY` 필요 → 키 있는 환경에서 원래 명령 재실행으로 확인 필요.

### 남은 확인 사항
- `tool_choice={"type": "web_search"}`는 OpenAI Responses API 버전/모델에 따라
  지원 형태가 다를 수 있음. 실행 시 `tool_choice` 관련 400 에러가 나면
  대안으로 `tool_choice="required"`로 교체.

### 참고 — 사용자 셸 입력 오타 (코드 문제 아님)
```
/c:/.../python.exe -m python -m pip install -r .\requirements.txt
```
- `/c:/...`는 Git Bash 경로 형식 → PowerShell 미인식. `C:\...` 사용.
- `-m python`은 불필요/무의미. `-m pip`만 필요.
- 올바른 명령:
  ```powershell
  & "C:\Users\akswo\Desktop\study\musinsa_plugin\.venv\Scripts\python.exe" -m pip install -r .\requirements.txt
  ```
