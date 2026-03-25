import os
import json
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
    url = 'https://news.google.com/rss/search?q=Claude+AI+OR+AI+agent+OR+LLM+OR+Anthropic&hl=ko&gl=KR&ceid=KR:ko'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            tree = ET.parse(resp)
            root = tree.getroot()
            items = root.findall('.//item')[:5]
            return [item.find('title').text for item in items if item.find('title') is not None]
    except Exception as e:
        print(f"News fetch error: {e}")
        return ["Claude AI 최신 업데이트", "AI 에이전트 활용법", "LLM 기술 동향"]


def generate_post(topics):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    topic_list = '\n'.join(f'- {t}' for t in topics)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""아래 AI 뉴스 토픽을 바탕으로 블로그 글을 써줘.

토픽:
{topic_list}

[글쓰기 스타일 - 반드시 이 스타일로 써야 해]
- 첫 문장은 반드시 "안녕하세요" 로 시작
- 문장은 짧고 간결하게, 자주 줄바꿈
- 겸손하고 친근한 톤 (예: "제가 직접 써보니까요", "부족하지만", "감사합니다")
- 코딩 모르는 비전문가도 이해할 수 있게 쉽게 설명
- 기술 용어는 괄호로 짧게 설명 달기 (예: VPS (ai agent 들이 일하는 공간))
- 내가 직접 써봤거나 느낀 것처럼 1인칭 경험담 스타일
- 구체적인 예시, 숫자, 비용 언급 (예: "이 모든 구축에 사용된 비용은 0원입니다")
- 마지막은 "부족한 글 읽어주셔서 감사합니다" 류의 인사로 마무리
- 전체 분량 600-900자

[형식]
순수 HTML만 출력. 코드블록 없이.
<h1>제목</h1> 으로 시작, <h2>와 <p> 태그 사용.
제목도 친근하고 일상적인 말투로."""
        }]
    )
    html = message.content[0].text.strip()
    if html.startswith('```html'):
        html = html[7:]
    elif html.startswith('```'):
        html = html[3:]
    if html.endswith('```'):
        html = html[:-3]
    return html.strip()


def extract_title(html_content):
    try:
        start = html_content.index('<h1>') + 4
        end = html_content.index('</h1>')
        return html_content[start:end].strip()
    except ValueError:
        return f"AI 이야기 - {datetime.now().strftime('%Y.%m.%d')}"


def post_to_blogger(access_token, title, content):
    url = f'https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/'
    data = json.dumps({
        'kind': 'blogger#post',
        'title': title,
        'content': content,
        'labels': ['AI', 'Claude', 'AI에이전트', '인공지능', '비전공자']
    }).encode()
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    })
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"Posted: {result.get('url', 'unknown')}")
        return result


def main():
    print(f"Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    topics = get_trending_topics()
    print(f"Topics: {len(topics)}")
    html_content = generate_post(topics)
    title = extract_title(html_content)
    print(f"Title: {title}")
    access_token = get_access_token()
    post_to_blogger(access_token, title, html_content)
    print("Done!")


if __name__ == '__main__':
    main()
