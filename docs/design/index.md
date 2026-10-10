# 상세 설계 문서

구현 전 구조·계약·예외 동작을 구체화하는 위치다. 설계가 존재한다는 사실과 구현이 완료됐다는 사실을 구분한다. 전체 진입점은 [문서 지도](../index.md)다.

## 문서 목록

상세 설계 문서는 아직 없다. 다음은 문서를 작성할 때 사용할 주제 안내이며, 파일이 이미 있다는 뜻이 아니다. 작업 범위에 맞게 주제를 합치거나 나눌 수 있다.

| 주제 | 포함할 내용 |
|---|---|
| LangGraph | Node·Edge·분기·검증 후 재판단·한 발화의 종료 조건 |
| ScamState | 필드·초기값·갱신 방식·Transcript 누적·통화별 Checkpointer |
| Jev 계약 | 전체 한국어 입력·이전 phase·검증 결과·출력 검증·실패 처리 |
| Agent | Suspect·Verify 역할·프롬프트·입출력·Tool 권한과 호출 방식 |
| Verification Tool | 도구 인자·결과 schema·Mock 데이터·조회 한계 |
| 입력과 응답 | STT 진입점·API 검증·risk 전달·프론트엔드 응답 |

이미 합의한 범위는 [프로젝트 컨텍스트](../project-context.md)에서 확인한다. 선택의 근거는 [결정](../decisions/index.md), 조사·실험은 [분석](../analysis/index.md), 변경별 요구·설계와 구현·검증 진행은 [OpenSpec](../../openspec/index.md)에 연결한다.
