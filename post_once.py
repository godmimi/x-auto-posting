"""일회성 수동 포스팅 스크립트"""
import os
import json
import base64
import urllib.request
import urllib.parse
import urllib.error
import anthropic
from google import genai
from google.genai import types

GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
GOOGLE_REFRESH_TOKEN = os.environ['GOOGLE_REFRESH_TOKEN']
BLOG_ID = os.environ['BLOG_ID']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
IMGBB_API_KEY = os.environ['IMGBB_API_KEY']
CHARACTER_IMAGE_URL = os.environ.get('CHARACTER_IMAGE_URL', '')

TITLE = "Claude CLI 소스코드 유출 사태 4가지 - 핵심만 정리하기 🔥 2026년"
LABELS = ["AI뉴스", "Claude", "AI활용법", "LLM꿀팁"]
INTRO = "요즘 AI 뉴스를 보다가 Claude 소스코드 유출이라는 헤드라인에 깜짝 놀라지 않으셨나요? 51만 줄이 넘는 CLI 소스코드가 외부로 공개됐다는 소식은 AI 커뮤니티 전반에 큰 파장을 일으키고 있어요."

HTML_BODY = """<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:0 0 2px;">안녕하세요</p>
<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:0 0 20px;">하루에 2번, 우리 일상에 도움이 될 AI 꿀팁을 전해드리는 Geez 입니다🤖</p>

<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:0 0 8px;">요즘 AI 뉴스를 보다가 "Claude 소스코드 유출"이라는 헤드라인에 깜짝 놀라지 않으셨나요?</p>
<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:0 0 8px;">51만 줄이 넘는 CLI 소스코드가 외부로 공개됐다는 소식은 AI 커뮤니티 전반에 큰 파장을 일으키고 있어요.</p>
<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:0 0 8px;">단순한 개발자 이슈처럼 보여도, Claude를 매일 쓰는 직장인분들께도 충분히 영향이 미칠 수 있는 사건이에요.</p>
<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:0 0 8px;">복잡한 기술 용어 없이, 이 사태가 정확히 무엇인지 그리고 우리가 어떻게 대응하면 좋은지 함께 살펴볼게요.</p>
<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:0 0 24px;">천천히 따라오시면 어렵지 않게 전체 흐름을 파악하실 수 있을 거예요😊</p>

<div style="border-left:3px solid #2563EB;padding:12px 16px;background:#f8fafc;margin-bottom:24px;">
<p style="font-size:14px;color:#1e293b;line-height:1.7;margin:0;">💡 <strong>핵심 포인트</strong> — Claude CLI 소스코드 51만 줄 유출은 AI 업계 최대 보안 사고 중 하나로, 사용자 데이터 직접 유출은 없지만 내부 구조 노출로 인한 보안 리스크가 현실화되고 있어요.</p>
</div>

<div style="border:0.5px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:28px;">
<div style="display:flex;align-items:center;gap:8px;padding:12px 16px;background:#f8fafc;border-bottom:0.5px solid #e2e8f0;">
<span style="font-size:13px;font-weight:600;color:#1e293b;">📌 팩트체크</span>
</div>
<div style="display:flex;align-items:flex-start;gap:10px;padding:9px 16px;border-bottom:0.5px solid #f1f5f9;">
<span style="font-size:11px;font-weight:700;color:#166534;background:#dcfce7;padding:2px 8px;border-radius:99px;flex-shrink:0;margin-top:1px;">✅ 사실</span>
<span style="font-size:13px;color:#475569;line-height:1.7;">Claude CLI 소스코드 약 512,000줄이 외부에 공개됐어요.</span>
</div>
<div style="display:flex;align-items:flex-start;gap:10px;padding:9px 16px;border-bottom:0.5px solid #f1f5f9;">
<span style="font-size:11px;font-weight:700;color:#166534;background:#dcfce7;padding:2px 8px;border-radius:99px;flex-shrink:0;margin-top:1px;">✅ 사실</span>
<span style="font-size:13px;color:#475569;line-height:1.7;">Anthropic은 유출 이후 일부 API 사용자에 대해 이용 차단 조치를 시행했어요.</span>
</div>
<div style="display:flex;align-items:flex-start;gap:10px;padding:9px 16px;border-bottom:0.5px solid #f1f5f9;">
<span style="font-size:11px;font-weight:700;color:#991b1b;background:#fee2e2;padding:2px 8px;border-radius:99px;flex-shrink:0;margin-top:1px;">❌ 오해</span>
<span style="font-size:13px;color:#475569;line-height:1.7;">사용자 개인정보나 대화 내용이 직접 유출된 것은 아니에요.</span>
</div>
<div style="display:flex;align-items:flex-start;gap:10px;padding:9px 16px;">
<span style="font-size:11px;font-weight:700;color:#92400e;background:#fef3c7;padding:2px 8px;border-radius:99px;flex-shrink:0;margin-top:1px;">❓ 미확인</span>
<span style="font-size:13px;color:#475569;line-height:1.7;">유출 경로와 내부 관여 여부는 아직 공식 확인이 되지 않은 상태예요.</span>
</div>
</div>

<h2 style="font-size:17px;font-weight:600;color:#1e293b;border-bottom:1px solid #e2e8f0;padding-bottom:10px;margin:32px 0 16px;">이슈 분석</h2>

<div style="border:0.5px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin-bottom:10px;background:#fff;">
<span style="font-size:11px;font-weight:600;color:#2563EB;border:0.5px solid #2563EB;padding:1px 8px;border-radius:99px;display:inline-block;margin-bottom:8px;">01 무슨 일이 있었나</span>
<h3 style="font-size:14px;font-weight:500;color:#1e293b;margin:0 0 5px;">51만 줄 CLI 소스코드 공개 사건</h3>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0;">games.gg가 최초 보도한 이번 사건은 Claude CLI(명령줄 인터페이스) 소스코드 약 512,000줄이 외부에 공개된 사건이에요.</p>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:6px 0 0;">CLI는 개발자들이 터미널에서 Claude를 직접 제어하는 핵심 도구로, 내부 동작 방식이 그대로 드러났다는 점이 심각해요.</p>
</div>

<div style="border:0.5px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin-bottom:10px;background:#fff;">
<span style="font-size:11px;font-weight:600;color:#2563EB;border:0.5px solid #2563EB;padding:1px 8px;border-radius:99px;display:inline-block;margin-bottom:8px;">02 왜 중요한가</span>
<h3 style="font-size:14px;font-weight:500;color:#1e293b;margin:0 0 5px;">AI 업계 보안 정책 재편의 신호탄</h3>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0;">Anthropic은 유출 이후 일부 API 사용자에 대해 강력한 이용 차단 조치를 시행했고, 이는 AI 업계에서 이례적인 빠른 대응으로 평가받고 있어요.</p>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:6px 0 0;">BeInCrypto 등 해외 매체들은 이 차단 조치가 AI 업계 전반에 보안 정책 재편을 촉발할 수 있다고 분석하고 있어요.</p>
</div>

<div style="border:0.5px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin-bottom:10px;background:#fff;">
<span style="font-size:11px;font-weight:600;color:#2563EB;border:0.5px solid #2563EB;padding:1px 8px;border-radius:99px;display:inline-block;margin-bottom:8px;">03 나에게 미치는 영향</span>
<h3 style="font-size:14px;font-weight:500;color:#1e293b;margin:0 0 5px;">AI 코딩 도구 경쟁과 보안 리스크의 현실화</h3>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0;">이번 사태는 OpenAI의 VS Code + Codex 협업 발표 이후 터졌다는 점에서, AI 코딩 도구 경쟁이 얼마나 치열한지를 보여주는 사건이기도 해요.</p>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:6px 0 0;">소스코드 유출이 경쟁사 간 긴장 속에서 발생했다는 점에서, 앞으로 AI 도구 선택 시 보안 측면을 더 꼼꼼히 따져야 할 시점이 됐어요.</p>
</div>

<div style="border:0.5px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin-bottom:10px;background:#fff;">
<span style="font-size:11px;font-weight:600;color:#2563EB;border:0.5px solid #2563EB;padding:1px 8px;border-radius:99px;display:inline-block;margin-bottom:8px;">04 지금 당장 할 것</span>
<h3 style="font-size:14px;font-weight:500;color:#1e293b;margin:0 0 5px;">개인 계정 및 API 키 보안 점검</h3>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0;">Claude에 민감한 개인정보나 업무 기밀을 입력한 적이 있다면, 해당 대화 내역을 삭제하고 API 키를 재발급받는 것이 안전해요.</p>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:6px 0 0;">Anthropic의 공식 업데이트를 정기적으로 확인하고, 수상한 이메일이나 링크는 클릭하지 않도록 주의하는 것이 기본 대응이에요.</p>
</div>

<h2 style="font-size:17px;font-weight:600;color:#1e293b;border-bottom:1px solid #e2e8f0;padding-bottom:10px;margin:32px 0 16px;">주의사항</h2>

<div style="margin-bottom:16px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
<span style="font-size:12px;font-weight:600;color:#B45309;background:#FEF3C7;padding:3px 10px;border-radius:99px;border:0.5px solid #D97706;">⚠ 주의 01</span>
<span style="font-size:14px;font-weight:500;color:#1e293b;">유출된 코드를 직접 탐색하거나 배포하지 마세요</span>
</div>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0 0 4px;padding-left:4px;">유출된 소스코드를 다운받거나 공유하는 행위는 Anthropic의 지식재산권 침해에 해당할 수 있어요.</p>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0;padding-left:4px;">호기심에 접근했다가 법적·보안적 리스크를 떠안게 될 수 있으니 반드시 공식 경로로만 정보를 확인하세요.</p>
</div>
<div style="margin-bottom:16px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
<span style="font-size:12px;font-weight:600;color:#B45309;background:#FEF3C7;padding:3px 10px;border-radius:99px;border:0.5px solid #D97706;">⚠ 주의 02</span>
<span style="font-size:14px;font-weight:500;color:#1e293b;">루머성 정보에 흔들리지 마세요</span>
</div>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0 0 4px;padding-left:4px;">이런 사건이 터지면 SNS와 커뮤니티에 과장되거나 잘못된 정보가 빠르게 퍼지는 경향이 있어요.</p>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0;padding-left:4px;">반드시 Anthropic 공식 블로그, 신뢰할 수 있는 테크 미디어 보도만을 기준으로 판단하시는 게 중요해요.</p>
</div>
<div style="margin-bottom:16px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
<span style="font-size:12px;font-weight:600;color:#B45309;background:#FEF3C7;padding:3px 10px;border-radius:99px;border:0.5px solid #D97706;">⚠ 주의 03</span>
<span style="font-size:14px;font-weight:500;color:#1e293b;">API 키는 지금 바로 재발급 및 점검하세요</span>
</div>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0 0 4px;padding-left:4px;">Claude API를 업무나 개인 프로젝트에 활용 중이라면, 기존 API 키를 폐기하고 새로 발급받는 것을 권장해요.</p>
<p style="font-size:13px;color:#475569;line-height:1.7;margin:0;padding-left:4px;">특히 키가 코드 저장소나 공개 문서에 노출돼 있다면 즉각적인 조치가 필요한 상황이에요.</p>
</div>

<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:32px 0 8px;">Claude CLI 유출 사태는 AI 도구가 이제 단순한 편의 도구를 넘어 보안까지 챙겨야 할 인프라가 됐다는 사실을 다시 한번 일깨워주는 사건이에요.</p>
<p style="font-size:15px;line-height:1.8;color:#1e293b;margin:0 0 24px;">오늘 알려드린 4가지 대응 방법과 주의사항을 참고하셔서, 더 안전하게 AI 도구를 활용하시길 바랍니다 🔐</p>

<div style="background:#f8fafc;border-radius:10px;padding:14px 18px;border:0.5px solid #e2e8f0;">
<p style="font-size:13px;color:#64748b;margin:0;line-height:1.7;">📌 <strong style="color:#1e293b;">Geez on AI는</strong> 매일 AI에 관련된 최신 내용들을 업데이트하며, 모든 포스팅은 Claude를 이용해 자동으로 생성됩니다 🤖</p>
</div>"""


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


def load_character_image():
    if not CHARACTER_IMAGE_URL:
        return None
    try:
        req = urllib.request.Request(CHARACTER_IMAGE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        print(f"캐릭터 이미지 로드 실패: {e}")
        return None


def generate_manga_image(character_bytes=None):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = "2-panel horizontal black and white manga. Panel 1: a boy looking worried and stressed, holding his head. Panel 2: same boy with a relieved and determined expression, pointing forward confidently. No speech bubbles. No text. Black and white manga art style, clean lines."
        if character_bytes:
            contents = [
                types.Part.from_bytes(data=character_bytes, mime_type="image/png"),
                types.Part.from_text(
                    text=f"{prompt}\n\n"
                    "스타일 규칙:\n"
                    "- 위 이미지의 캐릭터 외모(단발머리, 얼굴형)만 레퍼런스로 사용해줘. 마이크나 특정 소품은 따라 그리지 마.\n"
                    "- 흑백 만화 스타일, 선명한 검은 선\n"
                    "- 두 컷을 가로로 나란히 배치\n"
                    "- do NOT draw any speech bubbles or text in the image\n"
                    "- no color, white background"
                )
            ]
        else:
            contents = [types.Part.from_text(text=prompt)]

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data
        return None
    except Exception as e:
        print(f"이미지 생성 실패: {e}")
        return None


def upload_to_imgbb(image_bytes):
    try:
        b64 = base64.b64encode(image_bytes).decode()
        data = urllib.parse.urlencode({'key': IMGBB_API_KEY, 'image': b64}).encode()
        req = urllib.request.Request('https://api.imgbb.com/1/upload', data=data, method='POST')
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get('success'):
                url = result['data']['url']
                print(f"imgbb 업로드 성공: {url}")
                return url
    except Exception as e:
        print(f"imgbb 업로드 실패: {e}")
    return None


def post_to_blogger(access_token, html, image_url=None):
    post_data = {
        'kind': 'blogger#post',
        'title': TITLE,
        'content': html,
        'labels': LABELS
    }
    if image_url:
        post_data['images'] = [{'url': image_url}]
    data = json.dumps(post_data).encode()
    req = urllib.request.Request(
        f'https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/',
        data=data,
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"포스팅 완료: {result.get('url')}")


def main():
    print("캐릭터 이미지 로드 중...")
    character_bytes = load_character_image()
    if character_bytes:
        print(f"캐릭터 이미지 로드 성공: {len(character_bytes)} bytes")

    print("만화 이미지 생성 중...")
    image_bytes = generate_manga_image(character_bytes)

    html = HTML_BODY
    image_url = None
    if image_bytes:
        image_url = upload_to_imgbb(image_bytes)
        if image_url:
            img_tag = f'<img src="{image_url}" alt="{TITLE}" style="width:100%;max-width:800px;height:auto;margin:0 0 24px;border-radius:10px;" />\n'
            html = img_tag + html

    access_token = get_access_token()
    post_to_blogger(access_token, html, image_url)


if __name__ == '__main__':
    main()
