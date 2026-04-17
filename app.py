"""《Python爬虫开发，从入门到实战》配套练习网站。

单文件 Flask 服务，托管全部练习题页面与后端接口。
对外由 nginx 反向代理到 127.0.0.1:5000。
"""
import datetime
import io
import os
import random
import string
import time

from flask import (
    Flask,
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
)
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTCHA_DIR = os.path.join(BASE_DIR, 'static', 'captcha')
os.makedirs(CAPTCHA_DIR, exist_ok=True)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get(
    'FLASK_SECRET_KEY', 'exercise.kingname.info-python-spider-book'
)


# -------------------------------------------------------------------
# 首页
# -------------------------------------------------------------------
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


# -------------------------------------------------------------------
# 第 4 章 —— requests 入门
# -------------------------------------------------------------------
@app.route('/exercise_requests_get.html')
def requests_get_page():
    return render_template('exercise_requests_get.html')


@app.route('/exercise_requests_post', methods=['GET', 'POST'])
def requests_post_endpoint():
    if request.method == 'GET':
        return render_template('exercise_requests_post.html')
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        return jsonify({'message': '成功收到 JSON 格式的数据', 'data': payload})
    payload = request.form.to_dict()
    return jsonify({'message': '成功收到 Form 格式的数据', 'data': payload})


# -------------------------------------------------------------------
# 第 5 章 —— BeautifulSoup
# -------------------------------------------------------------------
@app.route('/exercise_bs_1.html')
def bs_1_page():
    return render_template('exercise_bs_1.html')


# -------------------------------------------------------------------
# 第 7 章 —— AJAX 练习 1：GET + POST 两种异步请求
# -------------------------------------------------------------------
@app.route('/exercise_ajax_1.html')
def ajax_1_page():
    return render_template('exercise_ajax_1.html')


@app.route('/ajax_1_backend', methods=['GET'])
def ajax_1_backend():
    return jsonify({'code': '行动代号：基础通关，GET 异步请求没问题'})


@app.route('/ajax_1_postbackend', methods=['POST'])
def ajax_1_postbackend():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '')
    age = data.get('age', '')
    if name == '青南' and str(age) == '24':
        return jsonify({'code': f'欢迎回来，{name}！你已经 {age} 岁啦'})
    if not name:
        return jsonify({'code': '请在 body 中提供 name 参数'})
    return jsonify({'code': f'Hello {name}，不过你好像不是青南'})


# -------------------------------------------------------------------
# 第 7 章 —— AJAX 练习 2：假异步（数据藏在页面源码的 JS 变量里）
# -------------------------------------------------------------------
FAKE_AJAX_SECRET = '{"code": "\\u884c\\u52a8\\u4ee3\\u53f7\\uff1a\\u5929\\u738b\\u76d6\\u5730\\u864e"}'
# 解码后：{"code": "行动代号：天王盖地虎"}


@app.route('/exercise_ajax_2.html')
def ajax_2_page():
    return render_template('exercise_ajax_2.html', secret=FAKE_AJAX_SECRET)


# -------------------------------------------------------------------
# 第 7 章 —— AJAX 练习 3：多次串联异步请求
# secret_2 写在 HTML 源码中；secret_1 来自 /ajax_3_backend 的 GET 返回。
# -------------------------------------------------------------------
AJAX_3_SECRET_1 = 'nicai-zhege-caishi-secret1'
AJAX_3_SECRET_2 = 'haha-secret2-wo-jiu-fangzai-yuandaima-li'


@app.route('/exercise_ajax_3.html')
def ajax_3_page():
    return render_template('exercise_ajax_3.html', secret_2=AJAX_3_SECRET_2)


@app.route('/ajax_3_backend', methods=['GET'])
def ajax_3_backend():
    return jsonify({'code': AJAX_3_SECRET_1})


@app.route('/ajax_3_postbackend', methods=['POST'])
def ajax_3_postbackend():
    data = request.get_json(silent=True) or {}
    secret1 = data.get('secret1')
    secret2 = data.get('secret2')
    if secret1 is None or secret2 is None:
        return jsonify({'code': 'secret1 和 secret2 都必需提供', 'success': False})
    if secret1 != AJAX_3_SECRET_1 or secret2 != AJAX_3_SECRET_2:
        return jsonify({'code': 'secret1 或 secret2 错误，请检查是否正确获取', 'success': False})
    return jsonify({'code': '行动代号：哎呦不错哦', 'success': True})


# -------------------------------------------------------------------
# 第 7 章 —— AJAX 练习 4：模拟登录（用户名 kingname，密码 genius）
# -------------------------------------------------------------------
@app.route('/exercise_ajax_4.html')
def ajax_4_page():
    return render_template('exercise_ajax_4.html')


@app.route('/ajax_4_backend', methods=['POST'])
def ajax_4_backend():
    data = request.get_json(silent=True) or {}
    if data.get('username') == 'kingname' and data.get('password') == 'genius':
        return jsonify({'code': '通关口令：人生苦短，我用 Python', 'success': True})
    return jsonify({'code': '用户名或密码错误', 'success': False})


# -------------------------------------------------------------------
# 第 7 章 —— AJAX 练习 5 + Selenium 练习
# 同一个页面（exercise_advanced_ajax.html）
# 页面上的 JavaScript 会自动算出正确的 ReqTime 和 sum 并发起 POST 请求
# 后端 /ajax_5_backend 校验 ReqTime 必须在最近 30 秒内、sum 必须等于 '6'
# -------------------------------------------------------------------
REQTIME_TOLERANCE_MS = 30_000


@app.route('/exercise_advanced_ajax.html')
def advanced_ajax_page():
    return render_template('exercise_advanced_ajax.html')


@app.route('/ajax_5_backend', methods=['POST'])
def ajax_5_backend():
    req_time_raw = request.headers.get('ReqTime')
    data = request.get_json(silent=True) or {}
    sum_val = data.get('sum')

    if not req_time_raw:
        return jsonify({'code': '请求头中缺少 ReqTime 参数', 'success': False})
    try:
        req_time = int(req_time_raw)
    except (ValueError, TypeError):
        return jsonify({'code': 'ReqTime 必须为毫秒时间戳整数', 'success': False})

    now_ms = int(time.time() * 1000)
    if abs(now_ms - req_time) > REQTIME_TOLERANCE_MS:
        return jsonify({'code': 'ReqTime 已过期，请使用当前时间戳', 'success': False})

    if str(sum_val) != '6':
        return jsonify({'code': 'sum 的值不对', 'success': False})

    return jsonify({'code': '通关口令：异步加载也难不倒你', 'success': True})


# -------------------------------------------------------------------
# 第 7 章 —— Headers 练习
# 要求 anhao: kingname，且 User-Agent、X-Requested-With、Referer 合规
# -------------------------------------------------------------------
@app.route('/exercise_headers.html')
def headers_page():
    return render_template('exercise_headers.html')


@app.route('/exercise_headers_backend', methods=['GET'])
def headers_backend():
    ua = request.headers.get('User-Agent', '')
    anhao = request.headers.get('anhao', '')
    xrw = request.headers.get('X-Requested-With', '')
    referer = request.headers.get('Referer', '')

    if 'python-requests' in ua.lower() or not ua:
        return jsonify({'code': '你的 User-Agent 看起来像爬虫', 'success': False})
    if anhao != 'kingname':
        return jsonify({'code': '请求头缺少正确的暗号 (anhao)', 'success': False})
    if xrw != 'XMLHttpRequest':
        return jsonify({'code': '请求头缺少 X-Requested-With: XMLHttpRequest', 'success': False})
    if 'exercise_headers.html' not in referer:
        return jsonify({'code': 'Referer 不正确', 'success': False})
    return jsonify({'code': '通关口令：请求头伪造大师', 'success': True})


# -------------------------------------------------------------------
# 第 8 章 —— 模拟登录（Form 登录 + Session Cookie + 302 跳转）
# -------------------------------------------------------------------
@app.route('/exercise_login.html')
def login_page():
    return render_template('exercise_login.html')


@app.route('/exercise_login', methods=['POST'])
def login_submit():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if username == 'kingname' and password == 'genius':
        session['logged_in'] = True
        session['login_user'] = username
        return redirect('/exercise_login_success', code=302)
    return render_template('exercise_login.html', error='用户名或密码错误')


@app.route('/exercise_login_success', methods=['GET', 'POST'])
def login_success():
    if not session.get('logged_in'):
        return render_template('exercise_login.html')
    return render_template(
        'exercise_login_success.html',
        username=session.get('login_user', ''),
    )


@app.route('/exercise_logout')
def logout():
    session.clear()
    return redirect('/exercise_login.html')


# -------------------------------------------------------------------
# 第 8 章 —— 验证码
# 动态生成 4 位字母数字验证码，图片落盘在 static/captcha/
# 验证码答案存在 session 中，POST 时比对
# -------------------------------------------------------------------
CAPTCHA_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def _generate_captcha_text(length: int = 4) -> str:
    return ''.join(random.choice(CAPTCHA_CHARS) for _ in range(length))


_FONT_CANDIDATES = (
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial.ttf',
)


def _load_captcha_font(size: int = 32):
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_captcha_image(text: str) -> bytes:
    width, height = 160, 50
    img = Image.new('RGB', (width, height), color=(245, 245, 250))
    draw = ImageDraw.Draw(img)
    font = _load_captcha_font(32)
    # 干扰点
    for _ in range(400):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)),
        )
    # 干扰线
    for _ in range(4):
        draw.line(
            (
                random.randint(0, width), random.randint(0, height),
                random.randint(0, width), random.randint(0, height),
            ),
            fill=(random.randint(120, 180), random.randint(120, 180), random.randint(120, 180)),
            width=1,
        )
    # 主字符
    for i, ch in enumerate(text):
        draw.text(
            (16 + i * 32 + random.randint(-4, 4), 4 + random.randint(-3, 6)),
            ch,
            font=font,
            fill=(random.randint(20, 80), random.randint(20, 80), random.randint(20, 80)),
        )
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def _cleanup_old_captchas(keep_seconds: int = 600):
    """验证码图片是临时文件，只保留最近 10 分钟的。"""
    now = time.time()
    try:
        for name in os.listdir(CAPTCHA_DIR):
            if not name.endswith('.png'):
                continue
            path = os.path.join(CAPTCHA_DIR, name)
            if now - os.path.getmtime(path) > keep_seconds:
                try:
                    os.remove(path)
                except OSError:
                    pass
    except FileNotFoundError:
        pass


@app.route('/exercise_captcha.html')
def captcha_page():
    _cleanup_old_captchas()
    text = _generate_captcha_text()
    session['captcha'] = text
    # 文件名使用时间戳，贴近原站行为
    fname = f'{time.time()}.png'
    with open(os.path.join(CAPTCHA_DIR, fname), 'wb') as f:
        f.write(_render_captcha_image(text))
    # 相对路径，答案代码会拼 'http://exercise.kingname.info/' + captcha_url
    captcha_rel = f'static/captcha/{fname}'
    return render_template('exercise_captcha.html', captcha_url=captcha_rel)


@app.route('/exercise_captcha_check', methods=['POST'])
def captcha_check():
    submitted = (request.form.get('captcha') or '').strip().upper()
    expected = (session.get('captcha') or '').upper()
    if submitted and submitted == expected:
        session.pop('captcha', None)
        return '验证码正确！通关口令：打码不过如此'
    return '验证码错误，请重新打开验证码页面再试'


# -------------------------------------------------------------------
# 第 11 章 —— XPath 练习页（Scrapy）
# -------------------------------------------------------------------
@app.route('/exercise_xpath_1.html')
def xpath_1_page():
    return render_template('exercise_xpath_1.html')


@app.route('/exercise_xpath_2.html')
def xpath_2_page():
    return render_template('exercise_xpath_2.html')


@app.route('/exercise_xpath_3.html')
def xpath_3_page():
    return render_template('exercise_xpath_3.html')


# -------------------------------------------------------------------
# 第 12 章 —— 代理中间件练习：返回访问者 IP，无限翻页
# -------------------------------------------------------------------
def _client_ip() -> str:
    # 支持 nginx 反向代理：优先取 X-Forwarded-For 的第一跳
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.remote_addr or 'unknown'


@app.route('/exercise_middleware_ip', defaults={'page': 1})
@app.route('/exercise_middleware_ip/<int:page>')
def middleware_ip(page):
    return f'当前为第 {page} 页，你的 IP 地址是：{_client_ip()}'


# -------------------------------------------------------------------
# 第 12 章 —— UA 中间件练习：返回 User-Agent，无限翻页
# -------------------------------------------------------------------
@app.route('/exercise_middleware_ua', defaults={'page': 1})
@app.route('/exercise_middleware_ua/<int:page>')
def middleware_ua(page):
    ua = request.headers.get('User-Agent', '')
    return f'当前为第 {page} 页，你的 User-Agent 是：{ua}'


# -------------------------------------------------------------------
# 第 12 章 —— 重试中间件练习
# /exercise_middleware_retry.html 翻页展示页，1-9 页
# /exercise_middleware_retry_backend/param/<i>  POST，date 错了返回"参数错误"
# /exercise_middleware_retry_backend/404/<i>     POST，date 错了跳转 /404.html
# -------------------------------------------------------------------
def _expected_date_for_retry(page: int) -> str:
    """按页数稳定决定服务器期望的 date：奇数页今天，偶数页昨天。

    这样爬虫先用「今天」试，遇到错误再用「昨天」改 body 重试，
    对同一 page 的第二次请求一定能成功——正是书中重试中间件要演示的场景。
    """
    today = datetime.date.today()
    if page % 2 == 0:
        return str(today - datetime.timedelta(days=1))
    return str(today)


@app.route('/exercise_middleware_retry.html')
def middleware_retry_page():
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    page = max(1, min(9, page))
    return render_template(
        'exercise_middleware_retry.html',
        page=page,
        total=9,
        today=str(datetime.date.today()),
    )


@app.route('/exercise_middleware_retry_backend/param/<int:page>', methods=['POST'])
def middleware_retry_param(page):
    data = request.get_json(silent=True) or {}
    date = data.get('date', '')
    if date != _expected_date_for_retry(page):
        return '参数错误'
    return f'第 {page} 页的内容：通关口令第 {page} 页（param 模式）'


@app.route('/exercise_middleware_retry_backend/404/<int:page>', methods=['POST'])
def middleware_retry_404(page):
    data = request.get_json(silent=True) or {}
    date = data.get('date', '')
    if date != _expected_date_for_retry(page):
        return redirect('/404.html', code=302)
    return f'第 {page} 页的内容：通关口令第 {page} 页（404 模式）'


@app.route('/404.html')
def page_404():
    return render_template('404.html'), 200


# -------------------------------------------------------------------
# 入口
# -------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
