# 部署说明

## 本地快速启动

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python app.py   # 监听 127.0.0.1:5000
```

打开 <http://127.0.0.1:5000/> 即可看到入口页。

## 生产部署（Docker，推荐）

```bash
# 1. 拉代码到服务器
ssh kingname@34.150.3.217
git clone https://github.com/kingname/crawler_book_exercise.git exercise_app
cd exercise_app

# 2. （可选）设置 session 签名密钥
echo "FLASK_SECRET_KEY=$(openssl rand -hex 32)" > .env

# 3. 构建并启动
docker compose up -d --build

# 4. 验证容器健康
docker compose ps
curl http://127.0.0.1:5000/

# 5. 更新 nginx 反代并 reload
sudo cp exercise.kingname.info.conf /etc/nginx/sites-available/
sudo nginx -t && sudo systemctl reload nginx
```

容器绑定 `127.0.0.1:5000`，只接受宿主机流量，nginx 反代承担 TLS。
验证码图片是容器内的临时文件，超过 10 分钟自动清理，无需持久化卷。

更新代码：

```bash
cd ~/exercise_app
git pull
docker compose up -d --build
```

## 传统部署（systemd + gunicorn，备选）

### 1. 上传代码到服务器

```bash
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='SourceCodeOfBook' \
    --exclude='book_text' --exclude='regression_test.py' --exclude='extract_docx.py' \
    ./ kingname@exercise.kingname.info:/home/kingname/exercise/
```

### 2. 创建虚拟环境并装依赖

```bash
ssh kingname@exercise.kingname.info
cd /home/kingname/exercise
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt gunicorn
```

### 3. 安装 systemd 服务

```bash
sudo mkdir -p /var/log/exercise
sudo chown kingname /var/log/exercise
sudo cp exercise.service /etc/systemd/system/exercise.service
sudo systemctl daemon-reload
sudo systemctl enable --now exercise.service
sudo systemctl status exercise.service
```

### 4. 更新 nginx 配置

```bash
sudo cp exercise.kingname.info.conf /etc/nginx/sites-available/
sudo nginx -t && sudo systemctl reload nginx
```

现在 <https://exercise.kingname.info/> 应该能看到题目目录页。

## 回归测试

本地启动 Flask 后：

```bash
python3 regression_test.py
```

如果全部打 ✓ 且末尾 `全部回归通过 ✅`，说明所有题目的接口契约与书中答案代码对得上。

## 题目清单

| 章 | URL | 说明 |
|---|---|---|
| 4 | `/exercise_requests_get.html` | 静态 HTML，含 title + 2 段 p |
| 4 | `/exercise_requests_post` | POST，同时支持 form / json |
| 5 | `/exercise_bs_1.html` | BS4 练习（useful/test/iamstrange 结构） |
| 7 | `/exercise_ajax_1.html` + `/ajax_1_backend` + `/ajax_1_postbackend` | GET + POST 基础异步 |
| 7 | `/exercise_ajax_2.html` | 假异步（源码里嵌 JSON） |
| 7 | `/exercise_ajax_3.html` + `/ajax_3_backend` + `/ajax_3_postbackend` | 串联异步（secret1/secret2） |
| 7 | `/exercise_ajax_4.html` + `/ajax_4_backend` | AJAX 登录（kingname/genius） |
| 7 | `/exercise_advanced_ajax.html` + `/ajax_5_backend` | ReqTime（30s 容差）+ sum=6 |
| 7 | `/exercise_headers.html` + `/exercise_headers_backend` | 校验 UA / anhao / Referer / XHR |
| 8 | `/exercise_login.html` + `/exercise_login` + `/exercise_login_success` | 表单登录 + Session + 302 |
| 8 | `/exercise_captcha.html` + `/exercise_captcha_check` | 图片验证码 |
| 11 | `/exercise_xpath_1.html` \| `2` \| `3` | XPath 三道题 |
| 12 | `/exercise_middleware_ip[/N]` | 返回访问 IP，无限翻页 |
| 12 | `/exercise_middleware_ua[/N]` | 返回 UA，无限翻页 |
| 12 | `/exercise_middleware_retry_backend/param/<i>` | date 错返回"参数错误" |
| 12 | `/exercise_middleware_retry_backend/404/<i>` | date 错 302 跳 /404.html |

## 维护

- 验证码图片落在 `static/captcha/`，超过 10 分钟会被自动清理（在每次访问验证码页面时触发）
- 如果需要回到"维护中"占位页，把 `index_maintenance.html` 重命名成 `index.html` 即可（首页走的是 nginx 直接提供静态文件）
