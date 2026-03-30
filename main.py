import os
import json
import base64
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import anthropic

ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
GOOGLE_REFRESH_TOKEN = os.environ['GOOGLE_REFRESH_TOKEN']
BLOG_ID = os.environ['BLOG_ID']


def get_access_token():
    data = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': GOOGLE_REFRESH_TOKEN,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())['access_token']


def get_trending_topics():
    url = 'https://news.google.com/rss/search?q=Claude+AI+OR+AI+에이전트+OR+LLM+OR+Anthropic&hl=ko&gl=KR&ceid=KR:ko'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            tree = ET.parse(resp)
            root = tree.getroot()
            items = root.findall('.//item')[:5]
            topics = [item.find('title').text for item in items if item.find('title') is not None]
            return topics
    except Exception as e:
        print(f"News fetch error: {e}")
        return ["Claude AI", "AI agent", "LLM trends"]


def generate_image_prompt(client, title, summary):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=60,
        messages=[{"role": "user", "content": f"Make an image prompt in English (max 30 words):\n- Visualize 1-2 core concepts from this blog\n- flat vector illustration style, soft pastel colors\n- no text, no faces, simple background\n\nTitle: {title}\nSummary: {summary[:200]}\n\nOutput prompt only."}]
    )
    return msg.content[0].text.strip()


def get_image_base64(prompt):
    clean = urllib.parse.quote(prompt)
    poll_url = f"https://image.pollinations.ai/prompt/{clean}?width=800&height=420&model=flux-anime&nologo=true"
    for url in [poll_url, "https://picsum.photos/800/420"]:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=90) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status}")
                data = resp.read()
                if len(data) < 10000:
                    raise Exception(f"Image too small: {len(data)} bytes")
                if data[:2] not in (b'\xff\xd8', b'\x89P'):
                    raise Exception("Not a valid image")
                mime = 'image/jpeg' if data[:2] == b'\xff\xd8' else 'image/png'
                b64 = base64.b64encode(data).decode()
                print(f"Image ok: {url[:40]} ({len(data)} bytes)")
                return f"data:{mime};base64,{b64}"
        except Exception as e:
            print(f"Image failed ({url[:40]}): {e}")
    return None


def generate_post(topics):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    topic_list = '\n'.join(f'- {t}' for t in topics)
    prompt = f"""다음 AI 뉴스 토픽을 바탕으로 한국어 블로그 글을 작성해줘:
{topic_list}

스타일 규칙 (반드시 따를 것):
- 제목: 짧고 임팩트 있게, 최대 8단어, 콜론 없이
- "혹시 이런 경험 있으신가요?" 식의 공감 훅으로 시작
- 친근하고 대화체로. 단락은 최대 3줄.
- 번호 대신 아이콘 사용: 🔹 단계, ✅ 장점, ❌ 실수/단점, 💡 팁
- 비교 또는 요약 <table> 1개 포함 (2~3열)
- 구조: 훅 → 핵심 내용 → 주요 포인트 3개(아이콘) → 실수(❌) → 팁(💡) → 핵심요약 박스 → CTA → 해시태그 5개
- 핵심요약 박스: <div style="background:#f0f4ff;padding:16px;border-radius:8px;margin:20px 0"><strong>핵심 요약</strong><br>3줄 이내</div>

순수 HTML만 출력. <h1>제목</h1>으로 시작, <h2><p> 태그 사용. 700~900자. 코드블록 없이."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1800,
        messages=[{"role": "user", "content": prompt}]
    )
    html = message.content[0].text.strip()
    for tag in ['```html', '```']:
        if html.startswith(tag):
            html = html[len(tag):]
    if html.endswith('```'):
        html = html[:-3]
    html = html.strip()

    # Generate relevant image prompt and embed
    try:
        title_text = html[html.index('<h1>') + 4:html.index('</h1>')]
    except ValueError:
        title_text = "AI"
    img_prompt = generate_image_prompt(client, title_text, topic_list[:200])
    print(f"Image prompt: {img_prompt}")
    img_src = get_image_base64(img_prompt)
    if img_src:
        img_tag = f'<img src="{img_src}" alt="{title_text}" style="width:100%;max-width:800px;height:auto;margin:20px 0;border-radius:8px;" />'
        html = html.replace('</h1>', f'</h1>\n{img_tag}', 1)

    return html


def extract_title(html_content):
    try:
        start = html_content.index('<h1>') + 4
        end = html_content.index('</h1>')
        return html_content[start:end].strip()
    except ValueError:
        return f"AI Trends Report - {datetime.now().strftime('%Y.%m.%d')}"


def post_to_blogger(access_token, title, content):
    url = f'https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/'
    data = json.dumps({
        'kind': 'blogger#post',
        'title': title,
        'content': content,
        'labels': ['AI', 'Claude', 'LLM', 'Productivity', 'Tech Tips']
    }).encode()
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    })
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"Posted: {result.get('url', 'unknown')}")
            return result
    except urllib.error.HTTPError as e:
        print(f"Blogger Error {e.code}: {e.read().decode('utf-8', errors='replace')}")
        raise


def main():
    print(f"Start: {datetime.now()}")
    topics = get_trending_topics()
    print(f"Topics: {topics[:3]}")
    html_content = generate_post(topics)
    title = extract_title(html_content)
    print(f"Title: {title}")
    access_token = get_access_token()
    post_to_blogger(access_token, title, html_content)
    print("Done!")


if __name__ == '__main__':
    main()
