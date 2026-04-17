"""逐题回归验证：模拟答案代码里的调用，断言返回符合预期。

只覆盖 HTTP 接口层（不依赖 selenium / scrapy / chromedriver）。
selenium / scrapy 相关题目只检查页面存在性 + 页面含关键字。
"""
import datetime
import json
import os
import re
import sys
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = os.environ.get('EXERCISE_BASE', 'http://127.0.0.1:5000').rstrip('/')

# 给默认 get/post 套一层重试，抵御 HTTPS 网络抖动（EOF、502 等）
_retry = Retry(total=3, backoff_factor=0.5,
               status_forcelist=(502, 503, 504),
               allowed_methods=frozenset(['GET', 'POST']))
_default_session = requests.Session()
_default_session.mount('http://', HTTPAdapter(max_retries=_retry))
_default_session.mount('https://', HTTPAdapter(max_retries=_retry))
requests.get = _default_session.get
requests.post = _default_session.post


def _ok(msg):  print(f'  ✓ {msg}')
def _fail(msg):
    print(f'  ✗ {msg}')
    sys.exit(1)


def test_chapter_4():
    print('[第 4 章] requests GET / POST')
    html = requests.get(f'{BASE}/exercise_requests_get.html').content.decode()
    title = re.search(r'<title>(.*?)<', html, re.S).group(1)
    paragraphs = re.findall(r'<p>(.*?)</p>', html, re.S)
    assert title, 'title 应非空'
    assert len(paragraphs) >= 2, 'p 段落应 >= 2'
    _ok(f'GET title={title!r}, {len(paragraphs)} 段正文')

    data = {'name': 'kingname', 'password': '1234567'}
    r_form = requests.post(f'{BASE}/exercise_requests_post', data=data).json()
    r_json = requests.post(f'{BASE}/exercise_requests_post', json=data).json()
    assert r_form['data']['name'] == 'kingname'
    assert r_json['data']['name'] == 'kingname'
    assert r_form['message'] != r_json['message'], 'form 与 json 返回的 message 应不同'
    _ok('POST form / json 两种形式都能正确识别')


def test_chapter_5():
    print('[第 5 章] BeautifulSoup')
    from bs4 import BeautifulSoup
    html = requests.get(f'{BASE}/exercise_bs_1.html').content.decode()
    soup = BeautifulSoup(html, 'html.parser')

    useful = soup.find(class_='useful')
    assert useful, '必须存在 class=useful 容器'
    lis = useful.find_all('li')
    assert len(lis) == 3, 'useful 内必须有 3 个 li'

    info_2 = soup.find(class_='test')
    assert info_2 and '我需要的信息2' in info_2.string, '我需要的信息2 应在 class=test 节点里'

    info_3 = soup.find_all(class_=re.compile('iam'))
    assert info_3, '应有至少一个 class 含 iam 的节点'

    needs = soup.find_all(string=re.compile('我需要'))
    assert len(needs) >= 3, '应该有至少 3 段文本以「我需要」开头'
    _ok('useful/test/iamstrange 结构完整')


def test_chapter_7():
    print('[第 7 章] AJAX + Headers')
    # 7.1 GET backend
    r = requests.get(f'{BASE}/ajax_1_backend').json()
    assert 'code' in r
    _ok(f'ajax_1_backend GET -> {r["code"]!r}')

    # 7.1 POST backend
    r1 = requests.post(f'{BASE}/ajax_1_postbackend', json={'name': '青南', 'age': 24}).json()
    r2 = requests.post(f'{BASE}/ajax_1_postbackend', json={'name': '无名小卒', 'age': 4}).json()
    assert r1['code'] != r2['code'], '不同 name 应返回不同内容'
    _ok(f'ajax_1_postbackend: 青南 -> {r1["code"][:20]}... / 其他 -> {r2["code"][:20]}...')

    # 7.2 fake ajax
    html = requests.get(f'{BASE}/exercise_ajax_2.html').content.decode()
    code_json = re.search("secret = '(.*?)'", html, re.S).group(1)
    code_dict = json.loads(code_json)
    assert '天王盖地虎' in code_dict['code']
    _ok(f'假 AJAX 数据提取 -> {code_dict["code"]!r}')

    # 7.3 chain ajax
    page = requests.get(f'{BASE}/exercise_ajax_3.html').content.decode()
    secret_2 = re.search("secret_2 = '(.*?)'", page, re.S).group(1)
    secret_1 = requests.get(f'{BASE}/ajax_3_backend').json()['code']
    final = requests.post(f'{BASE}/ajax_3_postbackend', json={
        'name': '青南', 'age': 24,
        'secret1': secret_1, 'secret2': secret_2,
    }).json()
    assert final.get('success') is True, f'串联 AJAX 最终应该 success, got {final}'
    _ok(f'串联 AJAX 最终 -> {final["code"]!r}')

    # 乱写 secret
    bad = requests.post(f'{BASE}/ajax_3_postbackend', json={
        'name': 'x', 'age': 24, 'secret1': '123', 'secret2': '456',
    }).json()
    assert bad.get('success') is False
    # 不写 secret
    missing = requests.post(f'{BASE}/ajax_3_postbackend', json={'name': 'x', 'age': 24}).json()
    assert missing.get('success') is False
    _ok('错误的 secret / 缺失的 secret 均能被拒绝')

    # 7.4 ajax login
    r = requests.post(f'{BASE}/ajax_4_backend',
                      json={'username': 'kingname', 'password': 'genius'}).json()
    assert r.get('success') is True, f'正确凭据应登录成功, got {r}'
    r_bad = requests.post(f'{BASE}/ajax_4_backend',
                          json={'username': 'kingname', 'password': 'wrong'}).json()
    assert r_bad.get('success') is False
    _ok('AJAX 登录 kingname/genius 通过，错误密码被拒')

    # 7.5 advanced ajax
    r = requests.post(f'{BASE}/ajax_5_backend',
                      headers={'ReqTime': str(int(time.time() * 1000))},
                      json={'sum': '6'}).json()
    assert r.get('success') is True, f'正确 ReqTime + sum=6 应通过, got {r}'
    r_old = requests.post(f'{BASE}/ajax_5_backend',
                          headers={'ReqTime': '1000000000000'},
                          json={'sum': '6'}).json()
    assert r_old.get('success') is False, '过期 ReqTime 应被拒'
    r_sum = requests.post(f'{BASE}/ajax_5_backend',
                          headers={'ReqTime': str(int(time.time() * 1000))},
                          json={'sum': '7'}).json()
    assert r_sum.get('success') is False, 'sum != 6 应被拒'
    _ok('advanced_ajax 时间戳容差 + sum 校验通过')

    # 7.6 headers
    # 有正确 anhao 的
    r = requests.get(f'{BASE}/exercise_headers_backend', headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X)',
        'anhao': 'kingname',
        'Referer': f'{BASE}/exercise_headers.html',
        'X-Requested-With': 'XMLHttpRequest',
    }).json()
    assert r.get('success') is True, f'正确 headers 应通过, got {r}'
    # 没有 anhao 的
    r_bad = requests.get(f'{BASE}/exercise_headers_backend', headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': f'{BASE}/exercise_headers.html',
        'X-Requested-With': 'XMLHttpRequest',
    }).json()
    assert r_bad.get('success') is False
    # 只有 UA 没有别的
    r_only_ua = requests.get(f'{BASE}/exercise_headers_backend',
                             headers={'User-Agent': 'Mozilla/5.0'}).json()
    assert r_only_ua.get('success') is False
    _ok('headers 练习：完整头过，缺 anhao 被拒，只有 UA 被拒')

    # 7.7 selenium-style：只验证页面结构
    html = requests.get(f'{BASE}/exercise_advanced_ajax.html').content.decode()
    assert '<div class="content"' in html or "class='content'" in html
    _ok('exercise_advanced_ajax.html 含 class=content 占位 div')


def test_chapter_8():
    print('[第 8 章] 登录 + 验证码')
    # 8.1 form login
    session = requests.Session()
    before = session.get(f'{BASE}/exercise_login_success').text
    assert 'name="username"' in before, '未登录访问成功页应返回登录页'
    _ok('未登录访问 login_success 返回登录页')

    r = session.post(f'{BASE}/exercise_login', data={
        'username': 'kingname', 'password': 'genius', 'rememberme': 'Yes',
    }, allow_redirects=False)
    assert r.status_code == 302, f'登录成功应 302, got {r.status_code}'
    _ok(f'登录成功，返回 302 -> {r.headers.get("Location")}')

    after = session.get(f'{BASE}/exercise_login_success').text
    assert '通关口令' in after, '登录后应看到通关口令'
    _ok('登录后 login_success 显示通关口令')

    # 8.2 captcha
    session = requests.Session()
    import lxml.html
    html = session.get(f'{BASE}/exercise_captcha.html').content
    selector = lxml.html.fromstring(html)
    cap_url = selector.xpath('//img/@src')[0]
    assert cap_url.startswith('static/captcha/'), f'img src 应为相对路径, got {cap_url!r}'
    img = requests.get(f'{BASE}/' + cap_url).content
    assert img[:4] == b'\x89PNG', 'captcha 应是 PNG'

    # 拿到正确答案（此时用同一个 session，但答案存在 Flask session 里）
    # 无法从 client 读到答案，所以用错误答案测试
    r_bad = session.post(f'{BASE}/exercise_captcha_check', data={'captcha': 'XXXX'})
    assert '错误' in r_bad.text
    _ok('验证码图片下载正常，错误答案被拒')


def test_chapter_11():
    print('[第 11 章] XPath')
    import lxml.html
    # 11.1
    sel = lxml.html.fromstring(requests.get(f'{BASE}/exercise_xpath_1.html').content)
    names = sel.xpath('//li[@class="name"]/text()')
    prices = sel.xpath('//li[@class="price"]/text()')
    assert names == ['无人机', '火箭炮', '国产电影特效库']
    assert prices == ['1亿', '100万', '5毛']
    _ok('xpath_1: 3 个商品 3 个价格')

    # 11.2
    sel = lxml.html.fromstring(requests.get(f'{BASE}/exercise_xpath_2.html').content)
    items = sel.xpath('//ul[@class="item"]')
    assert len(items) == 3
    fire = items[1]
    assert fire.xpath('li[@class="name"]/text()') == ['火箭炮']
    assert fire.xpath('li[@class="price"]/text()') == []
    _ok('xpath_2: 火箭炮缺价格，先抓大再抓小适用')

    # 11.3
    sel = lxml.html.fromstring(requests.get(f'{BASE}/exercise_xpath_3.html').content)
    rows = sel.xpath('//div[@class="person_table"]/table/tbody/tr')
    assert len(rows) == 5, f'应 5 行, got {len(rows)}'
    first = rows[0].xpath('td/text()')
    assert first == ['费言', '20', '9999', '1234567']
    _ok('xpath_3: 5 行 4 列表格结构完整')


def test_chapter_12():
    print('[第 12 章] 中间件')
    # 12.1 IP
    r = requests.get(f'{BASE}/exercise_middleware_ip').text
    assert '你的 IP' in r
    r2 = requests.get(f'{BASE}/exercise_middleware_ip/10').text
    assert '第 10 页' in r2
    _ok('middleware_ip 支持翻页并返回 IP')

    # 12.2 UA
    r = requests.get(f'{BASE}/exercise_middleware_ua',
                     headers={'User-Agent': 'TestBot/1.0'}).text
    assert 'TestBot/1.0' in r
    r2 = requests.get(f'{BASE}/exercise_middleware_ua/5',
                      headers={'User-Agent': 'AnotherUA'}).text
    assert '第 5 页' in r2 and 'AnotherUA' in r2
    _ok('middleware_ua 支持翻页并回显 UA')

    # 12.3 retry param —— 服务器随机要今天或昨天
    today = str(datetime.date.today())
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))

    # 重试循环：今天不行就用昨天
    successes = 0
    for i in range(1, 10):
        url = f'{BASE}/exercise_middleware_retry_backend/param/{i}'
        for date_try in (today, yesterday):
            r = requests.post(url, json={'date': date_try})
            if '参数错误' not in r.text:
                successes += 1
                break
    assert successes == 9, f'9 页都应最多 2 次重试即可成功, got {successes}'
    _ok(f'retry/param: 9 页全部在 today/yesterday 重试下通过')

    # 12.4 retry 404：失败时 302 跳 /404.html
    r = requests.post(f'{BASE}/exercise_middleware_retry_backend/404/1',
                      json={'date': '1999-01-01'}, allow_redirects=False)
    assert r.status_code in (302, 301), f'错误 date 应被 302 跳转, got {r.status_code}'
    assert '/404.html' in r.headers.get('Location', '')
    _ok('retry/404: 错误 date 被 302 跳转到 /404.html')


def main():
    # 等服务启动
    for _ in range(20):
        try:
            if requests.get(BASE, timeout=1).status_code < 500:
                break
        except requests.RequestException:
            time.sleep(0.3)
    else:
        _fail('服务未就绪')

    test_chapter_4()
    test_chapter_5()
    test_chapter_7()
    test_chapter_8()
    test_chapter_11()
    test_chapter_12()
    print('\n全部回归通过 ✅')


if __name__ == '__main__':
    main()
