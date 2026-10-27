# 2AS 적용 설계

## 기존 구조와 변경

Fake Jev의 OBSERVE/SUSPECT/VERIFY/WARN, Suspect/Verify 역할, Mock case_lookup·재판단 loop를 제거한다. 기존 callId·대화 누적·InMemorySaver·순차 실행·오류 경계는 활용한다. 공통 계약은 [State·Graph](../../../docs/design/state-and-graph.md), 코드별 책임은 [아키텍처](../../../docs/architecture/overview.md)를 따른다.

## 적용 방법과 선택

`Detector.detect(transcript)`와 `Analyst.analyze(state)`의 Protocol을 분리한다. JevClient는 표준 라이브러리 HTTP로 TypeSafe의 Choice API를 호출하므로 SDK 의존성을 추가하지 않는다. Yes/No와 각 선택 확률이 제공되는 Choice를 사용해 임의의 Noul threshold를 도입하지 않는다.

GeminiAnalyst는 기존 ChatGoogleGenerativeAI를 사용하고 네이티브 JSON schema 출력으로 `reason/response`를 받는다. Gemini 설정은 Yes 경로에서만 수행한다. 분석은 Gemini의 대화 근거 요약이며 Jev 내부 추론의 설명으로 표시하지 않는다.

## 정리와 호환성

`roles.py`, `tools.py`와 해당 Mock Tool 테스트를 제거하고 그래프 이미지를 교체한다. 과거 change는 당시 실행 기록으로 보존하고 제거 파일의 링크는 당시 커밋으로 연결한다. 기존 미커밋 Verify/스트리밍 설계는 삭제하지 않고 이전 구조 기준 자료임을 표시한다. 새 State는 기존 State와 호환되지 않으며 InMemorySaver를 새 프로세스에서 시작한다.

## 검증

Yes/No 경로, 새 발화/통화 상태 분리, 오류·잘못된 출력, 실제 HTTP payload와 Gemini SDK 변환을 API 없이 검사한다. 별도로 등록된 키로 예제 통화 두 건의 실제 호출을 확인한다. 테스트·실제 호출·그래프 생성 결과는 [work](work.md)에 구분한다.
