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
    data = urllib.parse.urlencode({'grant_type':'refresh_token','refresh_token':GOOGLE_REFRESH_TOKEN,'client_id':GOOGLE_CLIENT_ID,'client_secret':GOOGLE_CLIENT_SECRET}).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())['access_token']

def get_trending_topics():
    try:
        url = 'https://news.google.com/rss/search?q=Claude+AI+OR+LLM+OR+Anthropic&hl=ko&gl=KR&ceid=KR:ko'
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.parse(resp).getroot()
            return [i.find('title').text for i in root.findall('.//item')[:5] if i.find('title') is not None]
    except:
        return ['Claude AI 업데이트','AI 에이전트 활용','LLM 트렌드']

def generate_post(topics):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=2000,
        messages=[{'role':'user','content':f'AI 뉴스 토픽을 바탕으로 한국어 블로그 글을 HTML로 작성해줘. <h1>제목</h1>으로 시작, <h2><p> 태그 사용, 800자 이상.\\n토픽: {topics}'}]
    )
    return msg.content[0].text

def extract_title(html):
    try:
        return html[html.index('<h1>')+4:html.index('</h1>')].strip()
    except:
        return f'AI 트렌드 - {datetime.now().strftime("%Y.%m.%d")}'

def post_to_blogger(tok, title, content):
    url = f'https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/'
    data = json.dumps({'kind':'blogger#post','title':title,'content':content,'labels':['AI','Claude','LLM']}).encode()
    req = urllib.request.Request(url,data=data,headers={'Authorization':f'Bearer {tok}','Content-Type':'application/json'})
    with urllib.request.urlopen(req) as resp:
        print('Posted:', json.loads(resp.read()).get('url','?'))

def main():
    topics = get_trending_topics()
    html = generate_post(topics)
    post_to_blogger(get_access_token(), extract_title(html), html)
    print('Done!')

if __name__ == '__main__':
    main()