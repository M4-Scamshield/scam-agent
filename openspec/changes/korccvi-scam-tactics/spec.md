# 변경 요구사항

## 충족해야 할 동작과 계약

- `prepare.py`는 로컬 manifest의 `speaker_name`으로 통화별 `<줄번호> [화자] 발화` 대본을 만들고, 글자 수가 고르게 9묶음으로 나눈다.
- 라벨은 통화당 JSON 한 줄이며 [지침](../../../experiments/korccvi_tactics/ANNOTATION.md)의 필드(type, impersonated, scammer_speakers, diarization_ok, title_matches, tactics[code, label, line, quote, paraphrase], notes)를 따른다.
- 유형은 FSS 파일 제목이 아니라 내용으로 판단한다. 목록에 없는 수법은 `NEW`로 남기고 억지로 R 코드에 맞추지 않는다.
- `aggregate.py`는 원문(quote)을 출력하지 않고 집계·label만 `experiments/korccvi_tactics/results/`에 쓴다.

## 정상·실패 조건

- 묶음별 라벨 수가 묶음의 통화 수와 같고 call_id가 중복되지 않아야 한다. 빠진 통화는 집계의 `missing`에 남는다.
- 판단할 수 없는 짧은 구간은 `판단불가`로 두며 수법을 추측해 넣지 않는다.

## 검증 가능한 완료 조건

`aggregate.py` 출력의 calls=706, missing=0. 결과 파일에 원문 인용이 없는지 확인한다.

## 관련 상위 설계와 기준 문서

[proposal](proposal.md), [분석 문서](../../../docs/analysis/korccvi-scam-tactics.md).
