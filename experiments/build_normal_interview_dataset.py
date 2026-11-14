"""정상 면접 100건과 사기/정상 비교 평가셋 작성, 외부 API 호출 없음."""

import argparse
from collections import Counter
import copy
import csv
import hashlib
import json
from pathlib import Path
import random
import re
import statistics

from build_interview_dataset import pairs, require


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "datasets/interview_phishing/interview_phishing_100.json"
DEST = ROOT / "datasets/interview_normal"
CSV_PATH = ROOT / "experiments/data/interview_200_plan1.csv"
SOURCE_SHA256 = "67b77a45be13750840bba9b5cd5fb75d89b4507caf5527b3a4adf832d5b861f9"
SEED = 261107


# 기존 사기 유형과 주제를 맞추되 실제 대화는 정상 채용·면접 절차로 직접 작성한다.
# 8개 문답은 사기 대화의 8개 문답과 길이와 위치를 맞춘다.
TOPICS = {
    "training_fee": ("신입 교육 일정과 교육비 지원", """
직무 교육은 입사 후 첫 주에 회사 비용으로 진행할 예정입니다.|교육 시간도 근무 일정에 포함되나요?
네 오전에는 교육을 듣고 오후에는 담당자와 실습하게 됩니다.|처음 배우는 사람도 따라갈 수 있는 구성인가요?
기초 과정부터 시작하고 이해가 어려운 부분은 개별로 질문하실 수 있어요.|교육 자료를 미리 읽어 볼 수 있을까요?
채용 결과가 나온 뒤 입사 안내와 함께 목차를 보내드리겠습니다.|목차를 보고 준비할 부분을 확인하겠습니다.
교육 담당자는 실무에서 같은 업무를 맡는 직원입니다.|실제 업무 사례도 같이 다루나요?
연습용 자료를 사용하고 마지막에 담당자 피드백을 드릴 예정이에요.|교육 중 실수한 부분도 다시 해 볼 수 있나요?
다시 연습할 시간이 있고 추가 설명이 필요하면 일정을 조정합니다.|초기에 어느 부분이 부족한지 알 수 있으면 좋겠습니다.
오늘 면접에서는 새 도구를 배웠던 경험을 중심으로 평가하겠습니다.|제가 익혔던 과정과 질문했던 방법을 말씀드리겠습니다.
"""),
    "equipment_deposit": ("업무 장비 지급과 수령 일정", """
업무에 필요한 노트북과 주변 기기는 회사에서 준비합니다.|장비는 입사일에 받는 건가요?
출근하는 날 담당자와 수령 목록을 확인하고 받으시면 됩니다.|사용할 프로그램도 설치돼 있나요?
공통 프로그램은 설치해 두고 직무별 설정은 교육 때 맞춥니다.|제가 미리 준비할 장비가 있는지 궁금했습니다.
개인 장비를 따로 구매하실 필요는 없습니다.|그럼 제가 쓰던 컴퓨터는 가져가지 않아도 되겠네요.
장비를 받은 뒤 기본 작동을 확인하고 문제가 있으면 교체 요청하시면 돼요.|수령한 날 점검할 시간이 있나요?
첫날 일정에 계정 설정과 장비 점검 시간을 포함했습니다.|담당자와 확인하면 처음 쓰는 장비여도 괜찮겠습니다.
재택 일정이 생기면 회사에서 승인된 장비 반출 절차를 안내합니다.|외부에서 사용할 때 지켜야 할 기준도 교육받나요?
네 자료 보관과 반납 절차까지 입사 교육에서 설명합니다.|업무와 장비 관리 기준을 같이 익히겠습니다.
"""),
    "background_fee": ("경력 확인과 추천인 동의", """
서류 내용 중 실제로 담당하신 업무 범위를 면접에서 확인하려고 합니다.|제가 참여한 부분과 다른 팀원이 한 부분을 나눠 설명드릴게요.
추가 확인이 필요하면 지원자 동의를 받은 뒤 참고 자료를 요청합니다.|어떤 자료가 필요한지 미리 알 수 있을까요?
직무에 관련된 활동 내역이나 공개 가능한 결과물이면 됩니다.|팀 자료는 외부에 보여드려도 되는지 먼저 확인하겠습니다.
공개하기 어려운 자료는 설명으로 대신하실 수 있습니다.|설명할 때 민감한 내용은 빼고 말씀드리겠습니다.
추천인 확인이 필요한 단계가 되면 대상과 범위를 먼저 안내합니다.|추천인에게 연락이 가기 전에 제가 알 수 있는 거죠?
네 동의 없이 이전 활동처에 연락하지 않습니다.|그 부분이 궁금했는데 확인돼서 다행입니다.
자료 확인 때문에 비용을 납부하는 절차는 없습니다.|제가 준비할 내용 위주로 정리해 두겠습니다.
면접 뒤 필요한 자료가 있으면 항목을 적어 회사 메일로 안내합니다.|안내를 보고 제출 가능한 자료를 답장드리겠습니다.
"""),
    "medical_fee": ("입사 검진 안내와 일정 협의", """
이 직무의 입사 검진은 최종 합격 이후에 안내할 예정입니다.|오늘 바로 예약해야 하는 건가요?
아직 예약 단계는 아니고 채용 결과가 확정되면 일정을 협의합니다.|미리 어떤 검사를 받는지 알 수 있을까요?
직무에 필요한 검사 항목과 검진 기관을 안내문에 적어 드립니다.|기관과 항목을 확인한 뒤 가능한 날을 말씀드릴게요.
회사에서 기관과 비용을 정산하므로 면접 중 결제할 일은 없습니다.|비용 처리 방식도 안내문에서 확인하겠습니다.
가능한 날짜가 여러 개 있으니 기존 일정과 겹치면 알려 주세요.|지정된 날짜를 바꿀 수 있는지 궁금했습니다.
검진 예약 변경은 안내된 기관의 접수 창구에서도 확인할 수 있어요.|예약할 때 기관 안내를 함께 읽어 보겠습니다.
결과 서류는 필요한 항목만 인사 담당자가 확인합니다.|제출 범위도 안내를 받고 준비하고 싶습니다.
결과를 받는 시점에 따라 입사 준비 일정을 조정할 수 있습니다.|제 일정이 확정되면 담당자에게 말씀드리겠습니다.
"""),
    "certificate_fee": ("직무 자격과 학습 계획", """
공고에 적힌 자격 사항은 우대 조건이며 필수 지원 요건은 아닙니다.|관련 자격증이 없어도 면접 평가를 받을 수 있나요?
네 자격증보다 실제로 배운 내용과 활용 경험을 보겠습니다.|직접 작업해 본 사례를 중심으로 설명드리겠습니다.
앞으로 관련 자격을 준비하실 계획이 있는지도 궁금합니다.|직무를 더 익힌 뒤 필요한 시험을 검토하고 싶습니다.
입사 후에는 사내 학습 자료와 교육 일정을 참고하실 수 있어요.|어떤 기초 내용을 먼저 공부하면 좋을까요?
처음에는 업무 용어와 기본 도구를 익히는 게 도움이 됩니다.|면접에서 부족했던 부분도 같이 정리해 보겠습니다.
시험 응시 여부는 본인 계획에 따라 결정하시면 됩니다.|합격을 위해 지금 발급받아야 하는 건 아니군요.
취득 비용 지원이 가능한 항목은 입사 후 복지 기준에서 확인합니다.|지원 범위와 신청 시점을 나중에 확인하겠습니다.
오늘은 자격증 유무와 별도로 문제 해결 과정을 설명해 주세요.|자료를 찾아 배우고 적용했던 순서대로 말씀드리겠습니다.
"""),
    "otp_payroll": ("급여 계좌 등록과 직접 인증", """
급여 계좌 등록은 입사 확정 후 본인이 인사 포털에서 진행합니다.|지금 전화로 계좌 정보를 말씀드리면 되나요?
오늘은 절차만 설명드리고 실제 입력은 계약 후에 하시면 됩니다.|계약 내용을 먼저 읽은 뒤 등록하겠습니다.
포털 접속 방법은 회사 메일로 안내할 예정입니다.|본인 확인은 제가 화면에서 진행하는 건가요?
네 필요한 인증은 본인이 직접 입력하고 완료 여부만 확인합니다.|화면 안내를 읽으면서 처리하겠습니다.
문자 인증번호를 전화로 전달하는 단계는 없습니다.|다른 서류가 필요한 경우도 안내받을 수 있나요?
본인 명의와 계좌 명의 확인에 필요한 항목을 제출 목록에 적어 드립니다.|목록을 보고 누락된 항목이 없는지 확인하겠습니다.
등록 정보 수정은 인사 포털의 변경 메뉴에서 신청합니다.|입사 후 계좌가 바뀌면 그 메뉴로 처리하면 되겠네요.
첫 급여 지급일과 등록 마감일은 근로조건 안내에 함께 적습니다.|지급 일정과 마감일을 문서로 확인하겠습니다.
"""),
    "remote_control": ("화상 면접 연결과 장비 점검", """
다음 면접이 화상으로 진행될 수 있어서 접속 환경을 확인하고 있습니다.|지금 사용하는 컴퓨터로 참여해도 괜찮을까요?
브라우저에서 참여할 수 있고 카메라와 마이크만 확인하면 됩니다.|별도 프로그램을 설치해야 하는지 궁금했습니다.
설치 없이 접속하는 방법도 안내문에 포함돼 있습니다.|면접 전에 그 방법으로 접속해 보겠습니다.
소리가 안 들리면 먼저 마이크 선택과 음소거 상태를 확인해 주세요.|기본 설정부터 확인하겠습니다.
면접관이 지원자 기기를 조작하는 방식으로 점검하지는 않습니다.|제가 설정 화면을 보고 직접 바꾸면 되겠네요.
연결이 계속 어려우면 전화 면접으로 바꾸는 방법도 있습니다.|문제가 생기면 어느 창구로 말씀드리면 될까요?
안내 메일에 있는 채용 문의 창구로 증상을 알려 주시면 됩니다.|접속이 안 되는 화면과 상황을 정리해서 문의하겠습니다.
접속 점검 때문에 면접 기회가 없어지는 일은 없도록 일정을 조율하겠습니다.|미리 테스트하고 필요하면 일정 변경을 요청드리겠습니다.
"""),
    "identity_package": ("면접 본인확인과 서류 제출 범위", """
오늘 면접에서는 지원서의 성함과 지원 직무만 확인하겠습니다.|신분증 사진도 지금 제출해야 하나요?
입사 서류는 채용 확정 뒤에 필요한 항목을 따로 안내합니다.|먼저 제출 항목과 목적을 확인하고 싶습니다.
안내할 때 수집 목적과 보관 기간을 함께 알려드립니다.|내용을 읽고 궁금한 점을 문의해도 될까요?
네 제출 전에 인사 담당자에게 확인하실 수 있습니다.|지원 단계와 입사 단계의 서류를 구분해서 준비하겠습니다.
면접 자료는 채용 시스템에서 관리하고 개인 메신저로 받지 않습니다.|서류가 추가되면 같은 시스템을 사용하면 되나요?
추가 제출 요청도 항목과 제출 경로를 적어 안내합니다.|제가 임의로 더 많은 자료를 보내지 않도록 확인하겠습니다.
제출 후에는 등록한 자료의 접수 상태를 확인할 수 있습니다.|잘못 올린 파일이 있으면 수정할 수 있나요?
수정이 필요한 경우 담당자가 항목을 확인하고 방법을 안내합니다.|그럼 요청받은 범위에 맞춰 준비하겠습니다.
"""),
    "account_rental": ("정산 업무의 권한과 회사 계좌", """
정산 보조 업무는 회사 시스템에서 거래 내역을 대조하는 일입니다.|제 개인 계좌로 회사 돈을 받는 업무도 있나요?
거래는 회사 계좌로 처리하고 지원자 개인 계좌를 사용하는 업무는 없습니다.|제가 맡는 범위를 조금 더 설명해 주세요.
처음에는 증빙과 금액을 비교하고 차이가 있으면 담당자에게 보고합니다.|제가 직접 송금을 실행하는 단계도 포함되나요?
송금 승인은 권한을 가진 담당자가 별도로 처리합니다.|검토와 승인을 나누어 진행하는 방식이군요.
작업자는 필요한 자료만 볼 수 있도록 권한을 설정합니다.|권한 밖의 자료가 필요하면 어떻게 요청하나요?
업무 목적과 필요한 항목을 정리해 담당자에게 요청하시면 됩니다.|임의로 다른 계정을 사용하지 않고 요청하겠습니다.
입사 교육에서는 정산 자료를 다루는 기준을 설명합니다.|실습할 때는 연습용 자료를 사용하나요?
네 실제 이체 없이 예시 자료로 처리 순서를 익힙니다.|그 방식이면 업무 흐름을 먼저 배울 수 있겠습니다.
"""),
    "transfer_test": ("모의 송금 자료 기반 직무 과제", """
직무 과제는 가상의 송금 내역에서 오류를 찾는 방식입니다.|실제 돈을 보내거나 제 계좌를 쓰는 과제인가요?
아니요 예시 표를 읽고 잘못된 항목을 표시하면 됩니다.|그럼 자료 안의 금액만 비교하면 되겠네요.
문제에는 거래일과 금액 그리고 승인 상태가 들어 있습니다.|처리 기준도 같이 제공되나요?
기준표를 함께 드리고 애매한 항목은 판단 이유를 적게 합니다.|정답만 고르는 것보다 근거를 설명하는 과제군요.
평가 시간은 안내문에 적고 시작 전에 질문을 받습니다.|파일이 열리지 않으면 어디에 문의하면 될까요?
기술 문제가 있으면 채용 문의 메일로 알려 주시면 됩니다.|문제가 생긴 시점과 상황을 적어 보내겠습니다.
과제 결과물은 채용 시스템에 올리시면 됩니다.|실제 고객 정보가 들어 있는 자료는 아니죠?
네 평가용으로 만든 가상 자료만 사용합니다.|자료와 기준을 읽고 제가 판단한 순서를 적겠습니다.
"""),
    "purchase_rebate": ("상품 비교와 구매 제안 과제", """
면접 과제는 상품 세 가지를 비교해 구매 제안서를 쓰는 것입니다.|상품을 직접 구입해야 작성할 수 있나요?
제공하는 상품 설명과 가격표만으로 작성하시면 됩니다.|비교 기준은 제가 정하는 건가요?
예산과 사용 목적은 문제에 적고 세부 판단 근거는 본인이 설명합니다.|예산 안에서 조건을 비교해 보겠습니다.
판매 사이트에 실제 주문을 만들 필요는 없습니다.|그럼 자료를 보고 선택 이유를 쓰면 되겠네요.
가격이 변했을 때의 대응도 한두 줄 적어 주세요.|처음 제안한 상품을 바꿔야 하는 상황도 가정하겠습니다.
분량은 두 쪽 이내이고 디자인보다 근거를 보겠습니다.|표와 짧은 설명으로 정리해도 괜찮을까요?
네 본인이 판단한 기준이 보이면 형식은 자유입니다.|표에 비교 항목과 선택 이유를 함께 적겠습니다.
준비 시간은 이틀이며 개인 비용이 드는 활동은 요구하지 않습니다.|기한에 맞춰 제안서를 제출하겠습니다.
"""),
    "crypto_test": ("해외 정산 자료 확인 면접", """
해외 정산 관련 업무는 지급 자료의 통화와 금액을 확인하는 일입니다.|실제 자금을 제 계정으로 옮기는 업무인가요?
개인 계정을 쓰지 않고 회사 자료를 검토하는 보조 업무입니다.|어떤 내용을 확인하게 되는지 궁금합니다.
거래 통화와 적용 환율 그리고 정산 일자를 대조합니다.|기준이 되는 환율 자료도 회사에서 제공하나요?
날짜별 기준표를 제공하고 예외는 담당자가 확인합니다.|제가 판단하기 어려운 항목은 표시해 두겠습니다.
면접 실습은 가상 거래 표를 읽고 차이를 설명하는 방식이에요.|가상자산을 구매하거나 전송하는 절차는 없는 건가요?
네 실습에는 실제 거래나 지갑 연결이 없습니다.|표와 기준을 보고 계산 과정에 집중하겠습니다.
숫자가 다르더라도 이유를 확인한 뒤 수정 요청을 남겨야 합니다.|차이가 난 원인을 먼저 찾아보고 근거를 쓰겠습니다.
업무에 쓰는 계산 도구는 입사 교육 때 안내합니다.|처음 다루는 도구도 사용법을 익혀 보겠습니다.
"""),
    "credit_check": ("금융 자료 검수 업무 범위", """
이 직무는 금융 관련 문서의 필수 항목을 확인하는 업무입니다.|입사 과정에서 제 신용 거래를 확인하기도 하나요?
오늘 면접은 문서를 읽는 능력과 업무 경험을 중심으로 진행합니다.|과제로 확인할 자료는 어떤 내용인가요?
실제 고객 정보 대신 가상의 신청서와 기준표를 제공합니다.|신청 내용을 비교해 빠진 항목을 찾는 방식인가요?
네 본인이 대출을 신청하거나 금융 상품에 가입하는 과제는 없습니다.|직무 평가 범위를 알겠습니다.
실제 업무에서 예외가 나오면 승인 담당자에게 전달합니다.|보조 담당자가 승인 여부까지 결정하지는 않는군요.
결정 권한과 검수 권한을 나눠 운영합니다.|제가 판단한 근거와 확인이 필요한 부분을 구분하겠습니다.
교육에서는 개인정보가 포함된 문서의 취급 기준도 다룹니다.|자료를 다룰 때 필요한 주의사항을 알고 싶습니다.
자세한 교육 내용과 담당 업무는 채용 안내문에 적어 드립니다.|안내를 읽고 제 경험과 맞는지 검토하겠습니다.
"""),
    "salary_card": ("급여 지급일과 계좌 확인 서류", """
급여 지급일과 산정 기간을 근로조건 안내에서 확인하실 수 있습니다.|월 중간에 입사하면 첫 급여는 어떻게 계산하나요?
실제 근무 시작일에 맞춰 산정하는 기준을 문서에 적어 드립니다.|지급일과 계산 기간을 같이 확인하겠습니다.
급여 계좌는 입사 후 본인 명의 계좌를 등록하시면 됩니다.|카드 사진을 제출하는 단계도 있나요?
계좌 명의 확인에 필요한 서류만 제출 목록에 안내합니다.|제출 전에 필요한 항목을 읽어 보겠습니다.
카드번호나 카드 보안번호는 급여 서류에 포함하지 않습니다.|계좌 확인 서류와 카드 정보는 구분해서 준비하겠습니다.
계좌가 바뀌면 인사 포털에서 변경 요청을 남기면 됩니다.|마감일 이후에 바꾸면 다음 지급부터 적용되나요?
처리 일정에 따라 적용 시점을 담당자가 안내합니다.|변경이 생기면 미리 문의하겠습니다.
급여 명세서는 정해진 조회 경로로 확인하실 수 있습니다.|지급 내역도 제가 직접 확인할 수 있겠네요.
"""),
    "payroll_login": ("채용 포털 계정과 결과 확인", """
면접 결과는 지원하신 채용 포털에서 확인하실 수 있습니다.|지금 쓰는 계정으로 로그인하면 되나요?
네 지원서 접수 때 사용하신 계정으로 본인이 접속하시면 됩니다.|비밀번호를 잊었을 때는 어떻게 하나요?
포털의 비밀번호 재설정 메뉴에서 직접 변경하실 수 있습니다.|채용 담당자에게 비밀번호를 전달할 필요는 없겠네요.
담당자는 접수 상태만 확인하고 지원자 비밀번호를 받지 않습니다.|접수 상태가 다르게 보이면 문의하겠습니다.
문의할 때는 지원 직무와 오류가 난 화면의 안내 문구를 알려 주세요.|개인 정보가 보이는 부분은 가리고 보내도 되나요?
네 오류 확인에 필요한 부분만 보내 주시면 됩니다.|필요한 내용만 정리해 문의하겠습니다.
합격 이후 입사 계정은 회사에서 별도로 발급합니다.|개인 메일 계정을 회사 계정과 같이 쓰지는 않나요?
업무 계정과 개인 계정은 분리해서 사용합니다.|발급 안내를 받은 뒤 회사 계정을 설정하겠습니다.
"""),
    "gift_card": ("고객 응대 모의 실습", """
고객 응대 과제는 상품권 문의를 예시로 답변을 작성하는 것입니다.|실제 상품권을 사서 확인해야 하나요?
구매는 필요 없고 예시 문의와 이용 조건을 자료로 드립니다.|자료에 적힌 조건 안에서 답하면 되겠네요.
고객이 유효기간을 물었을 때 어떤 순서로 확인할지 설명해 주세요.|조건을 확인한 뒤 적용되는 기준을 안내하겠습니다.
실제 코드나 고객 결제 정보는 과제에 넣지 않습니다.|개인 정보를 확인하는 상황은 설명으로 적어도 되나요?
네 어떤 항목이 필요한지와 확인 이유를 적으시면 됩니다.|필요한 정보만 확인하는 방식으로 작성하겠습니다.
답변을 모르는 질문에 어떻게 대응할지도 평가합니다.|확인할 부서와 다시 안내할 시점을 설명하겠습니다.
문장 길이보다 고객이 다음 행동을 이해할 수 있는지를 보겠습니다.|가능한 처리와 추가 확인이 필요한 부분을 나누겠습니다.
제출 기한은 이틀이며 과제에 대한 질문도 받습니다.|문제를 읽고 모호한 조건이 있으면 먼저 문의하겠습니다.
"""),
    "interview_penalty": ("면접 일정 변경과 지원 철회", """
면접 일정이나 지원 의사가 바뀌면 채용 문의 창구로 알려 주세요.|다른 일정이 생기면 변경을 요청할 수 있나요?
가능한 시간대를 몇 개 적어 주시면 면접관 일정과 맞춰 보겠습니다.|변경이 필요하면 미리 연락드리겠습니다.
지원 철회도 포털이나 채용 메일로 요청하실 수 있습니다.|철회하면 이후 같은 직무에 다시 지원할 수 있나요?
다음 공고의 지원 요건을 충족하면 다시 지원하실 수 있습니다.|이번 결정을 서둘러야 하는지 궁금했습니다.
전형 참여와 철회에 별도 비용이나 위약금은 없습니다.|절차를 확인하고 결정할 시간을 갖겠습니다.
이미 준비한 자료의 처리 방식은 개인정보 안내에 적혀 있습니다.|보관 기간과 삭제 방법을 읽어 보겠습니다.
일정 변경 여부는 담당자가 접수 후 답장으로 확인해 드립니다.|제가 보낸 요청이 접수됐는지도 확인할 수 있겠네요.
오늘 면접을 마친 뒤 조건을 검토하고 의사를 알려 주셔도 됩니다.|설명을 정리하고 필요하면 추가로 질문드리겠습니다.
"""),
    "support_fee": ("교육 지원 제도와 복지 안내", """
입사 후 사용할 수 있는 교육 지원 제도가 있어서 간단히 설명드리겠습니다.|교육비 지원은 언제 신청할 수 있나요?
신청 자격과 지원 한도는 복지 안내문에서 확인하실 수 있습니다.|교육을 고르기 전에 기준을 읽어 보고 싶습니다.
담당 부서가 인정하는 교육인지 확인받은 뒤 신청하는 방식입니다.|원하는 교육이 있으면 어떤 자료를 준비하나요?
교육명과 비용 그리고 직무 관련 내용을 적어 제출하시면 됩니다.|신청서를 보고 필요한 항목을 준비하겠습니다.
지원 결정을 받기 위해 담당자에게 수수료를 보내는 절차는 없습니다.|승인 절차와 비용 정산 시점은 문서로 확인하겠습니다.
승인 여부는 회사 시스템에서 안내하고 문의도 남길 수 있습니다.|처음 신청할 때 예시가 있으면 도움이 되겠습니다.
입사 교육 때 신청 예시와 담당 창구를 안내합니다.|안내를 받고 제 학습 계획과 맞춰 보겠습니다.
오늘 면접에서는 어떤 내용을 더 배우고 싶은지 말씀해 주세요.|실무 도구와 처리 기준을 차근차근 익히고 싶습니다.
"""),
    "phone_installment": ("업무용 연락 수단과 기기 지급", """
업무에 별도 연락 수단이 필요하면 회사 명의 번호를 배정합니다.|제 명의로 휴대전화를 개통해야 하나요?
기기와 회선은 회사에서 준비하고 개인 개통 실적을 요구하지 않습니다.|입사 전에 통신 매장에 갈 필요는 없겠네요.
배정 일정은 입사 준비 안내에 적어 드릴 예정입니다.|언제 받는지 확인해서 일정에 맞추겠습니다.
업무용 번호 사용 기준과 비용 처리는 교육 때 설명합니다.|개인 통화와 업무 통화를 어떻게 구분하나요?
회사 장비 사용 기준을 확인하고 업무 목적으로 사용하시면 됩니다.|개인 기기를 같이 사용해야 하는 경우도 있나요?
필요한 업무는 회사가 제공한 수단으로 처리하는 것을 기준으로 합니다.|사용할 수단과 담당 업무를 함께 확인하겠습니다.
기기에 문제가 생기면 회사 지원 창구에 점검을 요청합니다.|제가 임의로 수리하거나 다른 사람에게 넘기지는 않겠습니다.
반납이 필요할 때는 목록을 확인하고 담당자에게 인계합니다.|받을 때와 반납할 때 모두 기록을 남기는 방식이군요.
"""),
    "refund_deposit": ("면접 참여 수당 지급 안내", """
이번 전형은 전화 면접 참여자에게 정해진 참여 수당을 지급합니다.|교통비가 들지 않은 전화 면접도 대상인가요?
네 이번 공고에는 전화 면접 참여도 지급 대상에 포함돼 있습니다.|지급 기준을 어디서 확인할 수 있나요?
공고의 전형 안내와 수당 신청 안내문에 같은 기준이 적혀 있습니다.|안내문을 읽어 보고 신청하겠습니다.
면접 종료 후 필요한 계좌 확인 항목을 공식 신청 화면에 입력하시면 됩니다.|지금 통화하면서 정보를 전달해야 하나요?
지금은 안내만 드리고 통화가 끝난 뒤 본인이 신청하시면 됩니다.|다른 일정이 있어도 마감 안에 신청하면 되겠네요.
네 신청 기한과 지급 예정일을 안내문에 적어 드립니다.|예정일까지 입금이 안 되면 어디에 문의하나요?
채용 담당 창구에서 접수 상태와 지급 일정을 확인해 드립니다.|접수 내역을 확인한 뒤 문의하겠습니다.
수당 지급 전에 지원자가 검증금을 보내는 절차는 없습니다.|확인 서류와 신청 일정에 맞춰 처리하겠습니다.
"""),
}


ENDINGS = [
    ("independent_verification", "공식 안내 확인 후 답변", """
설명드린 조건은 {company} 채용 안내문에서도 확인하실 수 있습니다.|공고와 안내문을 다시 읽고 확인할 내용이 있으면 문의하겠습니다.
채용 문의 창구에 질문을 남기시면 담당자가 확인해 드립니다.|제가 따로 확인할 수 있는 경로가 있어서 좋습니다.
오늘 말씀하신 경험과 업무 조건을 함께 검토해 결과를 안내하겠습니다.|결과를 받으면 안내된 절차를 확인하겠습니다.
추가 질문은 문서로 남겨 주셔도 됩니다.|검토한 뒤 궁금한 항목을 정리해 보내겠습니다.
"""),
    ("postponed", "근무 조건을 검토한 뒤 결정", """
지금 입사 의사를 확정하지 않으셔도 됩니다.|근무 조건을 다시 읽고 기존 일정과 비교하고 싶습니다.
검토 후 안내된 기한까지 답을 주시면 됩니다.|마감일을 확인해서 그 전에 제 의사를 말씀드리겠습니다.
조건 중 이해가 어려운 내용은 문의하셔도 됩니다.|궁금한 부분을 적어 두었다가 한 번에 여쭤보겠습니다.
오늘 면접 결과는 검토가 끝난 뒤 별도로 알려드립니다.|결과와 조건을 확인한 다음 결정하겠습니다.
"""),
    ("declined", "일정 또는 조건이 맞지 않아 지원 철회", """
안내드린 업무와 근무 조건이 지원자님 계획에 맞는지 궁금합니다.|업무는 관심 있지만 현재 일정과 맞지 않아 이번 지원은 철회하려고 합니다.
알겠습니다 지원 철회로 기록하고 처리 결과를 안내하겠습니다.|절차를 설명해 주셔서 감사합니다.
다음 공고에서 조건이 맞으면 다시 지원하실 수 있습니다.|일정이 맞는 기회가 생기면 다시 확인해 보겠습니다.
오늘 면접에 참여해 주셔서 감사드리고 안내 메일로 마무리하겠습니다.|네 제 지원 철회가 접수됐는지 메일을 확인하겠습니다.
"""),
    ("awaiting_result", "면접 결과 대기", """
업무에 대해 설명드린 내용 중 더 궁금한 부분이 있으세요?|지금 궁금했던 내용은 확인했고 세부 사항은 자료를 읽어 보겠습니다.
면접 결과는 다른 지원자 면접을 마친 뒤 안내할 예정입니다.|전체 전형 일정 안에서 결과를 기다리겠습니다.
결과 안내가 예정일보다 늦어지면 별도로 연락드리겠습니다.|일정이 바뀌면 안내받은 내용을 확인하겠습니다.
그럼 오늘 전화 면접은 여기서 마치겠습니다.|제 경험을 설명드릴 기회를 주셔서 감사합니다.
"""),
    ("next_step", "후속 면접 일정 협의", """
오늘은 기본 면접이고 추가 전형이 필요한 경우 별도 일정을 안내합니다.|다음 단계는 어떤 방식으로 진행되나요?
직무 담당자와 구체적인 사례를 이야기하는 면접이 예정돼 있습니다.|가능한 날짜를 받아 보고 제 일정을 확인하겠습니다.
진행 장소와 준비 자료는 일정 안내에 함께 적어 드립니다.|필요한 내용만 정리해 준비하겠습니다.
일정이 확정되면 참석 가능 여부를 답장해 주세요.|안내를 확인한 뒤 참석 여부를 회신하겠습니다.
"""),
]


def load_source():
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256,
            "사기 원본이 기준 파일과 다름: 기존 데이터 변경 여부를 먼저 확인해야 함")
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def render_inputs(calls):
    rendered = []
    for index, call in enumerate(calls):
        counterpart = next(s for s in call["speakers"] if s != "나")
        mapping = {"나": "A", counterpart: "B"} if index % 2 == 0 else {"나": "B", counterpart: "A"}
        rendered.append({"call_id": call["call_id"], "utterances": [
            {"sentence_id": u["sentence_id"], "speaker": mapping[u["speaker"]], "text": u["text"]}
            for u in call["utterances"]]})
    return {"schema_version": "1.0", "calls": rendered}


def build(source):
    calls = []
    for index, src in enumerate(source["calls"]):
        call = copy.deepcopy(src)
        call["call_id"] = f"normal_interview_{index + 1:03d}"
        call["label"] = "normal"
        call["speakers"] = {"나": "입사 지원자", "면접관": "회사 채용 담당자"}
        for row in call["utterances"]:
            if row["speaker"] == "피싱범":
                row["speaker"] = "면접관"
        scenario = src["annotations"]["scenario_id"]
        title, block = TOPICS[scenario]
        replacement = pairs(block)
        require(len(replacement) == 8, f"{scenario}: 문답 8개 필요")
        original_core = src["annotations"]["evidence_sentence_ids"][:8]
        for sid, (question, answer) in zip(original_core, replacement):
            call["utterances"][sid - 1]["text"] = question
            call["utterances"][sid]["text"] = answer
        for row in call["utterances"]:
            if row["text"] == "준비 절차에 대한 질문은 남겨두고 직무 면접을 조금 더 이어가겠습니다.":
                row["text"] = "세부 일정은 안내문에서 확인하시고 직무 면접을 조금 더 이어가겠습니다."
            elif row["text"] == "업무 질문에는 답하되 안내하신 조건에 동의한 것은 아닙니다.":
                row["text"] = "네 조건은 안내문으로 다시 확인하고 면접 질문에 답하겠습니다."
        variant = index % 5
        outcome, outcome_ko, ending_block = ENDINGS[variant]
        ending = pairs(ending_block, company=call["context"]["company"])
        # 사기 본문의 마지막 핵심 문답 바로 뒤에 오는 반응·종결부 전체를 교체한다.
        tail_start = original_core[-1] + 1
        tail = []
        for pair_index, (question, answer) in enumerate(ending):
            tail.extend([{"speaker": "면접관", "text": question}, {"speaker": "나", "text": answer}])
            if pair_index == 2 and call["sentence_count"] % 2:
                tail.append({"speaker": "나", "text": "오늘 설명하신 내용은 따로 적어 두겠습니다."})
        require(len(call["utterances"][tail_start:]) == len(tail), "종결부 길이 불일치")
        for dest, replacement_row in zip(call["utterances"][tail_start:], tail):
            dest.update(replacement_row)
        call["annotations"] = {
            "scenario_id": f"normal_{scenario}", "scenario_name": title,
            "requested_action": "직무 면접 및 채용 절차 확인",
            "first_evidence_sentence_id": None, "evidence_sentence_ids": [],
            "outcome": outcome, "outcome_description": outcome_ko,
            "paired_source_call_id": src["call_id"],
            "normal_topic_sentence_ids": original_core,
        }
        calls.append(call)
    return {"metadata": {
        "dataset_id": "interview_normal_100", "schema_version": "1.0", "version": "1.0.0",
        "created_on": "2026-11-07", "language": "ko-KR", "topic": "면접 상황",
        "synthetic": True, "call_count": 100, "speaker_count_per_call": 2,
        "sentence_count_range": [50, 100], "seed": SEED,
        "sentence_unit": "발화 항목 하나에 종결 부호 하나로 끝나는 문장 하나",
        "generation_method": "사기 통화와 직무·경력·길이를 맞추고 20개 정상 채용 문답과 5개 종료 경로를 직접 작성",
        "paired_source_dataset": "interview_phishing_100", "paired_source_sha256": SOURCE_SHA256,
        "scope": "면접 상황의 지원자와 실제 채용 담당자 간 정상 1대1 통화",
        "limitations": ["합성 문답과 대응되는 경력 사례를 공유하므로 독립 실측 표본이 아님",
                        "정상 절차의 예시로 법령·현실 기업의 채용 관행을 보증하지 않음",
                        "음성·ASR·화자 분리 모델 결과나 모델 성능 측정값이 아님"],
    }, "calls": calls}


def build_comparison(source, normal):
    mapping = {c["call_id"]: c for c in source["calls"] + normal["calls"]}
    # 화자 대응은 각 클래스에서 50/50으로 균형화하고, 이후 통화를 섞는다.
    rendered = render_inputs(source["calls"])["calls"] + render_inputs(normal["calls"])["calls"]
    random.Random(SEED).shuffle(rendered)
    keys = []
    for index, item in enumerate(rendered, 1):
        original_id = item["call_id"]
        call = mapping[original_id]
        item["call_id"] = f"eval_{index:03d}"
        keys.append({"call_id": item["call_id"], "label": call["label"],
                     "source_call_id": original_id,
                     "paired_group_id": call["annotations"].get("paired_source_call_id", original_id),
                     "scenario_id": call["annotations"]["scenario_id"]})
    return {"schema_version": "1.0", "calls": rendered}, {"schema_version": "1.0", "answers": keys}


def validate(source, data, inputs, comparison, answers):
    require(set(data) == {"metadata", "calls"} and data["metadata"]["call_count"] == 100, "원본 구조 오류")
    calls = data["calls"]
    require(len(calls) == 100 and len({c["call_id"] for c in calls}) == 100, "정상 통화는 고유한 100건 필요")
    lengths, texts, digests, topics, outcomes = [], [], [], Counter(), Counter()
    forbidden = re.compile(r"https?://|www\.|\{[^}]+\}|\[[^\]]+\]|010[- ]?\d{4}|\d{8,}")
    for src, call in zip(source["calls"], calls):
        cid, rows, ann = call["call_id"], call["utterances"], call["annotations"]
        require(call["label"] == "normal" and call["topic"] == "면접 상황" and call["is_synthetic"], f"{cid}: 주제·라벨 오류")
        require(call["context"] == src["context"], f"{cid}: 대응 직무·경력 불일치")
        require(len(rows) == call["sentence_count"] == src["sentence_count"] and 50 <= len(rows) <= 100, f"{cid}: 길이 오류")
        require(set(call["speakers"]) == {"나", "면접관"} and {r["speaker"] for r in rows} == {"나", "면접관"}, f"{cid}: 화자 오류")
        require([r["sentence_id"] for r in rows] == list(range(1, len(rows) + 1)), f"{cid}: 문장 순번 오류")
        require(ann["first_evidence_sentence_id"] is None and ann["evidence_sentence_ids"] == [], f"{cid}: 정상 정답 오류")
        require(ann["paired_source_call_id"] == src["call_id"], f"{cid}: 대응 ID 오류")
        for row in rows:
            text = row["text"]
            require(set(row) == {"sentence_id", "speaker", "text"}, f"{cid}: 발화 키 오류")
            require(isinstance(text, str) and len(text) >= 6 and text == text.strip(), f"{cid}: 빈문장 오류")
            require(len(re.findall(r"[.!?。！？]", text)) == 1 and text[-1] in ".?", f"{cid}: 한 항목 한 문장 오류")
            require(re.search(r"[가-힣]", text) and not forbidden.search(text), f"{cid}: 한국어·자리표시자·연락처 오류")
            require("피싱범" not in text and "정상 통화" not in text, f"{cid}: 본문 정답 누출")
        local_texts = [r["text"] for r in rows]
        require(len(set(local_texts)) == len(local_texts), f"{cid}: 통화 내 반복 문장")
        for sid in src["annotations"]["evidence_sentence_ids"][:8]:
            require(rows[sid - 1]["text"] != src["utterances"][sid - 1]["text"], f"{cid}: 사기 핵심 문장이 교체되지 않음")
        require(call["context"]["job"] in " ".join(local_texts), f"{cid}: 직무 본문 불일치")
        lengths.append(len(rows))
        texts.extend(local_texts)
        digests.append(hashlib.sha256("\n".join(local_texts).encode()).hexdigest())
        topics[ann["scenario_id"]] += 1
        outcomes[ann["outcome"]] += 1
    require(len(set(digests)) == 100, "전체 통화 중복")
    require(set(lengths) == set(range(50, 101)), "50~100 길이 다양성 오류")
    require(topics == Counter({f"normal_{topic}": 5 for topic in TOPICS}), "20개 주제 각 5통화 조건 오류")
    require(outcomes == Counter({item[0]: 20 for item in ENDINGS}), "종료 경로 분포 오류")
    require(inputs == render_inputs(calls), "정상 평가 입력 불일치 또는 정답 누출")
    require((comparison, answers) == build_comparison(source, data), "혼합 평가 입력·정답 키 불일치")
    require(len(comparison["calls"]) == 200 and len({c["call_id"] for c in comparison["calls"]}) == 200, "혼합 200건 ID 오류")
    require(Counter(a["label"] for a in answers["answers"]) == {"phishing": 100, "normal": 100}, "혼합 정답 분포 오류")
    freq = Counter(texts)
    return {
        "status": "PASS", "normal_call_count": 100, "phishing_call_count": 100, "comparison_call_count": 200,
        "normal_total_sentences": sum(lengths), "comparison_total_sentences": sum(lengths) * 2,
        "sentence_count_min": min(lengths), "sentence_count_max": max(lengths),
        "sentence_count_mean": statistics.mean(lengths), "distinct_sentence_counts": len(set(lengths)),
        "length_distribution_matches_phishing": True, "each_pair_has_same_length_and_job": True,
        "topic_counts": dict(topics), "outcome_counts": dict(outcomes),
        "distinct_jobs": len({c["context"]["job"] for c in calls}),
        "distinct_sectors": len({c["context"]["sector"] for c in calls}),
        "unique_sentence_texts": len(freq), "unique_sentence_ratio": round(len(freq) / len(texts), 4),
        "duplicate_full_calls": 0, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "semantic_review": "정상 라벨은 직접 작성한 채용 절차의 설정이며 독립 검수자 간 합의 검증은 아님",
    }


def products(source):
    normal = build(source)
    inputs = render_inputs(normal["calls"])
    comparison, answers = build_comparison(source, normal)
    return {"interview_normal_100.json": normal, "interview_normal_inputs.json": inputs,
            "interview_comparison_200_inputs.json": comparison, "interview_comparison_200_answers.json": answers}


def write_csv(comparison, answers):
    labels = {a["call_id"]: int(a["label"] == "phishing") for a in answers["answers"]}
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "transcript", "label"])
        writer.writeheader()
        for call in comparison["calls"]:
            writer.writerow({"id": call["call_id"], "transcript": "\n".join(
                f"{r['speaker']}: {r['text']}" for r in call["utterances"]), "label": labels[call["call_id"]]})


def validate_csv(comparison, answers):
    labels = {a["call_id"]: str(int(a["label"] == "phishing")) for a in answers["answers"]}
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 200, "Plan1 CSV는 정확히 200행 필요")
    for row, call in zip(rows, comparison["calls"]):
        expected = {"id": call["call_id"], "label": labels[call["call_id"]], "transcript": "\n".join(
            f"{u['speaker']}: {u['text']}" for u in call["utterances"])}
        require(row == expected, f"{call['call_id']}: Plan1 CSV 대화·정답 불일치")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="저장된 데이터셋 검사만 수행")
    args = parser.parse_args()
    source = load_source()
    expected = products(source)
    validate(source, expected["interview_normal_100.json"], expected["interview_normal_inputs.json"],
             expected["interview_comparison_200_inputs.json"], expected["interview_comparison_200_answers.json"])
    if args.check:
        stored = {name: json.loads((DEST / name).read_text(encoding="utf-8")) for name in expected}
        require(stored == expected, "저장본이 재현 결과와 다름")
    else:
        DEST.mkdir(parents=True, exist_ok=True)
        for name, data in expected.items():
            (DEST / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stored = {name: json.loads((DEST / name).read_text(encoding="utf-8")) for name in expected}
    report = validate(source, stored["interview_normal_100.json"], stored["interview_normal_inputs.json"],
                      stored["interview_comparison_200_inputs.json"], stored["interview_comparison_200_answers.json"])
    if args.check:
        require(json.loads((DEST / "validation_report.json").read_text(encoding="utf-8")) == report, "검사 보고서 불일치")
    else:
        (DEST / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_csv(stored["interview_comparison_200_inputs.json"], stored["interview_comparison_200_answers.json"])
    validate_csv(stored["interview_comparison_200_inputs.json"], stored["interview_comparison_200_answers.json"])
    print(json.dumps({k: report[k] for k in (
        "status", "normal_call_count", "comparison_call_count", "normal_total_sentences", "sentence_count_min",
        "sentence_count_max", "sentence_count_mean", "distinct_sentence_counts", "unique_sentence_ratio")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
