import os
import json
import base64
import urllib.request
import urllib.parse
from main import generate_post, fetch_x_content
from blogger import get_access_token, post_to_blogger

NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = 'aca94fdd059c41528a114542db3abbe8'
IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY', '')

NOTION_HEADERS = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}


# ──────────────────────────────────────────
# Notion API 헬퍼
# ──────────────────────────────────────────

def notion_request(method, path, body=None):
    url = f'https://api.notion.com/v1{path}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=NOTION_HEADERS, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def query_db(status):
    return notion_request('POST', f'/databases/{NOTION_DB_ID}/query', {
        'filter': {'property': '상태', 'select': {'equals': status}}
    })


def update_page(page_id, properties):
    notion_request('PATCH', f'/pages/{page_id}', {'properties': properties})


def update_status(page_id, status):
    update_page(page_id, {'상태': {'select': {'name': status}}})


def get_blocks(page_id):
    return notion_request('GET', f'/blocks/{page_id}/children')


def delete_block(block_id):
    try:
        notion_request('DELETE', f'/blocks/{block_id}')
    except Exception:
        pass


def append_blocks(page_id, children):
    notion_request('PATCH', f'/blocks/{page_id}/children', {'children': children})


def save_html_to_page(page_id, html):
    """HTML을 페이지 본문 코드블록에 저장"""
    existing = get_blocks(page_id)
    for block in existing.get('results', []):
        delete_block(block['id'])

    chunks = [html[i:i+1990] for i in range(0, len(html), 1990)]
    blocks = [{
        'type': 'code',
        'code': {
            'rich_text': [{'type': 'text', 'text': {'content': chunk}}],
            'language': 'html'
        }
    } for chunk in chunks]
    append_blocks(page_id, blocks)


def read_html_from_page(page_id):
    """페이지 본문 코드블록에서 HTML 읽기"""
    blocks = get_blocks(page_id)
    parts = []
    for block in blocks.get('results', []):
        if block['type'] == 'code':
            for text in block['code']['rich_text']:
                parts.append(text['plain_text'])
    return ''.join(parts)


def get_prop(page, name, prop_type):
    prop = page['properties'].get(name, {})
    if prop_type == 'title':
        items = prop.get('title', [])
        return items[0]['plain_text'] if items else ''
    elif prop_type == 'rich_text':
        items = prop.get('rich_text', [])
        return items[0]['plain_text'] if items else ''
    elif prop_type == 'url':
        return prop.get('url') or ''
    elif prop_type == 'select':
        sel = prop.get('select')
        return sel['name'] if sel else ''
    return ''


def get_notion_image(page) -> str:
    """Notion 이미지 첨부 → imgbb 업로드 → 영구 URL"""
    files_prop = page['properties'].get('이미지', {})
    files = files_prop.get('files', [])
    if not files:
        return ''

    file_obj = files[0]
    if file_obj['type'] == 'file':
        notion_url = file_obj['file']['url']
    elif file_obj['type'] == 'external':
        notion_url = file_obj['external']['url']
    else:
        return ''

    if not IMGBB_API_KEY:
        return notion_url

    try:
        req = urllib.request.Request(notion_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            image_bytes = resp.read()
        b64 = base64.b64encode(image_bytes).decode()
        data = urllib.parse.urlencode({'key': IMGBB_API_KEY, 'image': b64}).encode()
        upload_req = urllib.request.Request('https://api.imgbb.com/1/upload', data=data, method='POST')
        with urllib.request.urlopen(upload_req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get('success'):
                url = result['data']['url']
                print(f"이미지 업로드 완료: {url}")
                return url
    except Exception as e:
        print(f"이미지 업로드 실패: {e}")

    return notion_url


# ──────────────────────────────────────────
# 파이프라인 1: 입력됨 → 검수대기
# ──────────────────────────────────────────

def process_pending():
    results = query_db('입력됨').get('results', [])
    if not results:
        print("대기 항목 없음")
        return

    for page in results:
        page_id = page['id']
        try:
            update_status(page_id, '생성중')

            url = get_prop(page, '원본 URL', 'url')
            content = get_prop(page, '원본 내용', 'rich_text')
            type_raw = get_prop(page, '타입', 'select')
            post_type = type_raw[0] if type_raw else 'auto'

            if url and not content:
                content = fetch_x_content(url)
                print(f"URL 크롤링 완료: {len(content)}자")

            source = content or url or ''
            if not source:
                print(f"내용 없음 [{page_id}] — 건너뜀")
                update_status(page_id, '입력됨')
                continue

            result = generate_post(source, url, post_type)
            print(f"글 생성 완료: {result['title']}")

            update_page(page_id, {
                '제목': {'title': [{'text': {'content': result['title']}}]},
                '상태': {'select': {'name': '검수대기'}}
            })
            save_html_to_page(page_id, result['html_content'])
            print(f"✓ 검수대기: {result['title']}")

        except Exception as e:
            print(f"✗ 글 생성 실패 [{page_id}]: {e}")
            update_status(page_id, '입력됨')


# ──────────────────────────────────────────
# 파이프라인 2: 승인 → 포스팅완료
# ──────────────────────────────────────────

def process_approved():
    results = query_db('승인').get('results', [])
    if not results:
        print("승인 항목 없음")
        return

    for page in results:
        page_id = page['id']
        try:
            title = get_prop(page, '제목', 'title')
            type_raw = get_prop(page, '타입', 'select')
            labels = [type_raw] if type_raw else ['AIgent Labs']

            html_content = read_html_from_page(page_id)
            if not html_content:
                print(f"HTML 없음 [{page_id}] — 건너뜀")
                continue

            image_url = get_notion_image(page)
            access_token = get_access_token()
            post_url = post_to_blogger(access_token, title, html_content, image_url, labels)

            update_page(page_id, {
                '상태': {'select': {'name': '포스팅완료'}},
                '블로그 URL': {'url': post_url}
            })
            print(f"✓ 포스팅 완료: {post_url}")

        except Exception as e:
            print(f"✗ 포스팅 실패 [{page_id}]: {e}")


# ──────────────────────────────────────────
# 실행
# ──────────────────────────────────────────

def main():
    print("=== Notion 파이프라인 실행 ===")
    process_pending()
    process_approved()
    print("=== 완료 ===")


if __name__ == '__main__':
    main()
