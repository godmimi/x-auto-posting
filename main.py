import os
import re
import anthropic
import requests
from bs4 import BeautifulSoup

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ──────────────────────────────────────────
# 1. URL → 본문 텍스트 추출
# ──────────────────────────────────────────
def fetch_content(url: str) -> str:
    """URL에서 텍스트 추출. X(트위터) 링크 포함."""
    tweet_id = extract_tweet_id(url)
    if tweet_id:
        for mirror in ["https://nitter.privacydev.net", "https://nitter.poast.org"]:
            try:
                r = requests.get(f"{mirror}/i/status/{tweet_id}", timeout=8,
                                 headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    tweet_div = soup.find("div", class_="tweet-content")
                    if tweet_div:
                        return tweet_div.get_text(strip=True)
            except Exception:
                continue

    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        meta = soup.find("meta", property="og:description")
        if meta:
            return meta.get("content", "")
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception:
        pass

    return ""


def extract_tweet_id(url: str) -> str:
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else ""


# ──────────────────────────────────────────
# 2. 타입 분류
# ──────────────────────────────────────────
def classify_type(content: str) -> str:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": f"""다음 내용을 분류해. 반드시 A, B, C 중 하나만 답해.
A: 튜토리얼/하우투 (단계별 방법, 설정법)
B: 뉴스/이슈 분석 (새로운 소식, 논란, 발표)
C: 개념 설명 (10분 이내로 이해 가능한 주제)

내용: {content[:300]}"""}]
    )
    t = resp.content[0].text.strip().upper()
    return t if t in ["A", "B", "C"] else "B"


# ──────────────────────────────────────────
# 3. 제목 생성
# ──────────────────────────────────────────
def generate_title(content: str) -> str:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": f"""다음 블로그 글에 가장 어울리는 제목 1개를 만들어.

규칙:
- 독자 입장에서 "나한테 뭐가 달라지냐"가 바로 보일 것
- 단순 팩트 나열이나 "더 좋아졌다" 식은 피할 것
- 이모지, 연도 없음
- 제목만 출력

글 내용: {content[:500]}"""}]
    )
    return resp.content[0].text.strip()


# ──────────────────────────────────────────
# 4. HTML 버전 생성 (구글 블로그용)
# ──────────────────────────────────────────
COMMON_RULES = """
작성 규칙:
- 독자: AI에 관심 많은 한국 직장인, AI 툴 활용 중인 중간 실력 유저
- 말투: ~입니다 / ~됩니다 / ~있습니다 (절대 ~하면 돼요 사용 금지)
- AI 클리셰 금지: "혁신적", "놀라운", "게임체인저", "주목할 만한"
- 마크다운 금지, HTML만 출력
- 출력 형식:

<LABELS>라벨1,라벨2,라벨3</LABELS>
<CONTENT>HTML 본문 전체</CONTENT>
"""


def build_prompt_a(content: str, url: str) -> str:
    return f"""다음 내용을 바탕으로 A타입 블로그 포스트를 HTML로 작성해.

내용: {content}
원문 링크: {url}

---

HTML 구조와 작성 규칙:

[도입부]
- 첫 문장: 무슨 일이 있었는지 한 줄
- 독자가 공감할 수 있는 상황 묘사
- 이 글이 그 문제를 해결해준다는 흐름
- 문장은 짧게, 줄바꿈으로 호흡 나누기
- 말투: ~입니다 / ~됩니다 / ~있습니다

[핵심 포인트]
- 원문에서 가장 핵심 내용을 짧게 뽑아낼 것
- 한 문장으로 담기면 한 줄, 두 문장 이상이면 문장마다 줄바꿈

[목차]
1. 준비물
2. 단계별 실행 가이드
3. 실제 활용 예시
4. 주의사항

[준비물]
- "이게 없으면 시작도 못 한다"는 것만 작성
- 비용이 드는 항목은 반드시 금액 명시
- 한도 초과 시 추가 과금 가능성도 포함

[단계별 실행 가이드]
- 단계 제목과 내용을 분리해서 작성
- 내용은 한 문장씩 줄바꿈
- 단계 안에서 세부 단계가 필요하면 숫자로 쪼갤 것
- 말투: ~입니다 / ~됩니다 / ~있습니다
- ~하면 돼요 절대 사용 금지

[실제 활용 예시]
- 3가지 작성
- 각 예시 구조:
  ① 예시 제목
  상황 설명 (어떤 경우에 쓰는지)
  <ul>
    <li>동작 설명<br><br>
    <span style="margin-left: 20px;">ex) "구체적인 예시 문장"</span></li>
    <br>
    <li>결과 설명</li>
  </ul>
- 상황 → 동작 → 결과 흐름 유지
- 단계별 가이드에서 나온 내용 반복 금지

[주의사항]
- "독자가 따라하다가 실제로 막힐 수 있는 것"만 작성
- 각 항목 구조:
  ⚠️ 막히는 상황
  원인 설명
  해결법
- 일반적인 면책 문구는 제외

[마무리]
- 이 글 내용과 연결되는 팩트 기반 한 줄평
- 독자가 공감할 수 있는 멘트
- 행동 유도 한 줄
- 고정 멘트:
  📌 AIgent Labs는 매일 AI 관련 최신 내용을 업로드합니다.
  아래 다른 글들도 확인해보세요.

---

공통 작성 규칙:
- 말투: ~입니다 / ~됩니다 / ~있습니다 (절대 ~하면 돼요 사용 금지)
- AI 클리셰 금지: "혁신적", "놀라운", "게임체인저", "주목할 만한" 사용 금지
- 독자: AI에 관심 많은 한국 직장인, AI 툴 활용 중인 중간 실력 유저
- 마크다운 금지, HTML만 출력

출력 형식:
<LABELS>라벨1,라벨2,라벨3</LABELS>
<CONTENT>HTML 본문 전체</CONTENT>
"""


def build_prompt_b(content: str, url: str) -> str:
    return f"""다음 내용을 바탕으로 B타입 블로그 포스트를 HTML로 작성해.

내용: {content}
원문 링크: {url}

---

HTML 구조와 작성 규칙:

[헤드라인]
- 첫 문장: 언제, 누가, 무엇을 했는지 팩트 한 줄
- 핵심 변화들: 줄바꿈으로 나열
- 마지막 문장: 독자에게 의미있는 한 줄
- 틀에 맞추지 말고 내용에 따라 자연스럽게

[팩트체크]
- ✅ 사실: 독자가 "진짜야?" 싶을 만한 것만
- ❌ 오해: 독자가 실제로 잘못 알고 있을 가능성이 높은 것만
- 미확인 항목 없음
- 각 항목은 짧고 간결하게
- 억지로 개수 채우지 말 것

[이슈 분석]
소제목 3개: 무슨 일이 있었나 / 왜 중요한가 / 우리에게 미치는 영향
- 소제목 다음 줄부터 내용 시작
- 헤드라인과 팩트체크에서 이미 나온 내용은 반복하지 말 것
- "왜 이게 중요한가", "그래서 나한테 뭐가 달라지냐"를 깊게 파고들 것
- 독자 기준: AI 툴을 업무에 활용 중인 직장인, 중간 실력 유저
- 각 섹션은 2~3문장으로 간결하게

[마무리]
- 이 글 내용과 연결되는 팩트 기반 한 줄평
- 독자가 공감할 수 있는 멘트
- 행동 유도 한 줄
- 고정 멘트:
  📌 AIgent Labs는 매일 AI 관련 최신 내용을 업로드합니다.
  아래 다른 글들도 확인해보세요.

---

공통 작성 규칙:
- 말투: ~입니다 / ~됩니다 / ~있습니다
- AI 클리셰 금지: "혁신적", "놀라운", "게임체인저", "주목할 만한" 사용 금지
- 독자: AI에 관심 많은 한국 직장인, AI 툴 활용 중인 중간 실력 유저
- 마크다운 금지, HTML만 출력

출력 형식:
<LABELS>라벨1,라벨2,라벨3</LABELS>
<CONTENT>HTML 본문 전체</CONTENT>
"""


def build_prompt_c(content: str, url: str) -> str:
    return f"""다음 내용을 바탕으로 C타입 블로그 포스트를 HTML로 작성해.
(C타입: 빠른 개념 설명 — 짧고 임팩트 있게)

내용: {content}
원문 링크: {url}

HTML 구조:
1. 핵심 개념 한 줄 요약
2. 쉬운 비유로 설명 (일상 예시)
3. 실제로 써먹는 법 3가지
4. 자주 묻는 질문 2~3개 (Q&A)

{COMMON_RULES}"""


def generate_html_post(content: str, url: str, post_type: str) -> dict:
    """HTML 버전 생성 (구글 블로그용)"""
    if post_type == "A":
        prompt = build_prompt_a(content, url)
    elif post_type == "B":
        prompt = build_prompt_b(content, url)
    else:
        prompt = build_prompt_c(content, url)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text

    def extract(tag):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
        return m.group(1).strip() if m else ""

    html_content = extract("CONTENT")
    labels = [l.strip() for l in extract("LABELS").split(",") if l.strip()]
    title = generate_title(html_content)

    return {"title": title, "html_content": html_content, "labels": labels}


# ──────────────────────────────────────────
# 5. 텍스트 버전 생성 (네이버 블로그용)
# ──────────────────────────────────────────
def generate_text_post(content: str, url: str, post_type: str) -> str:
    """네이버 블로그용 plain text 버전 생성"""

    if post_type == "A":
        structure = """
[도입부]
- 첫 문장: 무슨 일이 있었는지 한 줄
- 독자가 공감할 수 있는 상황 묘사
- 문장은 짧게, 줄바꿈으로 호흡 나누기

[핵심 포인트]
- 원문에서 가장 핵심 내용을 짧게 뽑아낼 것

【준비물】
- "이게 없으면 시작도 못 한다"는 것만 작성
- 비용이 드는 항목은 반드시 금액 명시

【단계별 실행 가이드】
- 단계 제목과 내용을 분리해서 작성
- 내용은 한 문장씩 줄바꿈
- 단계 안에서 세부 단계가 필요하면 숫자로 쪼갤 것

【실제 활용 예시】
- 3가지 작성
- 상황 → 동작 → 결과 흐름 유지
- ex) 예시 문장은 들여쓰기로 구분

【주의사항】
- "독자가 따라하다가 실제로 막힐 수 있는 것"만 작성
- ⚠️ 막히는 상황 / 원인 / 해결법 구조

【마무리】
- 팩트 기반 한 줄평
- 독자 공감 멘트
- 행동 유도 한 줄
- 고정 멘트: 📌 AIgent Labs는 매일 AI 관련 최신 내용을 업로드합니다. 아래 다른 글들도 확인해보세요.
"""
    elif post_type == "B":
        structure = """
[헤드라인]
- 첫 문장: 언제, 누가, 무엇을 했는지 팩트 한 줄
- 핵심 변화들: 줄바꿈으로 나열
- 마지막 문장: 독자에게 의미있는 한 줄

【팩트체크】
- ✅ 사실: 독자가 "진짜야?" 싶을 만한 것만
- ❌ 오해: 독자가 실제로 잘못 알고 있을 가능성이 높은 것만
- 억지로 개수 채우지 말 것

【이슈 분석】
소제목 3개: 무슨 일이 있었나 / 왜 중요한가 / 우리에게 미치는 영향
- 소제목 다음 줄부터 내용 시작
- 헤드라인과 팩트체크에서 나온 내용 반복 금지
- 각 섹션 2~3문장으로 간결하게

【마무리】
- 팩트 기반 한 줄평
- 독자 공감 멘트
- 행동 유도 한 줄
- 고정 멘트: 📌 AIgent Labs는 매일 AI 관련 최신 내용을 업로드합니다. 아래 다른 글들도 확인해보세요.
"""
    else:
        structure = """
【핵심 요약】
- 핵심 개념 한 줄 요약

【쉬운 설명】
- 일상적인 비유로 설명

【써먹는 법】
- 실제로 활용할 수 있는 방법 3가지

【자주 묻는 질문】
- Q&A 2~3개

【마무리】
- 팩트 기반 한 줄평
- 독자 공감 멘트
- 고정 멘트: 📌 AIgent Labs는 매일 AI 관련 최신 내용을 업로드합니다. 아래 다른 글들도 확인해보세요.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": f"""다음 내용을 바탕으로 네이버 블로그용 글을 작성해.

내용: {content}
원문 링크: {url}

구조:
{structure}

작성 규칙:
- HTML 태그 없이 순수 텍스트로
- 말투: ~입니다 / ~됩니다 / ~있습니다 (절대 ~하면 돼요 사용 금지)
- AI 클리셰 금지: "혁신적", "놀라운", "게임체인저", "주목할 만한"
- 이모지 없음 (마무리 고정 멘트의 📌 제외)
- 독자: AI에 관심 많은 한국 직장인, AI 툴 활용 중인 중간 실력 유저
"""}]
    )
    return response.content[0].text.strip()
