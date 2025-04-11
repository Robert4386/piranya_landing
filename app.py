from flask import Flask, jsonify, render_template
import feedparser
import requests
import re
from dateutil import parser as date_parser
import locale
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# Конфигурация
BACKGROUNDS_FOLDER = 'static/backgrounds'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Устанавливаем русскую локаль
try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'ru_RU')
    except:
        pass  # для Windows

def get_background_image():
    if os.path.exists(BACKGROUNDS_FOLDER):
        for filename in os.listdir(BACKGROUNDS_FOLDER):
            if filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
                return f'backgrounds/{filename}'
    return None

def extract_image_from_summary(summary):
    match = re.search(r'<img[^>]+src="([^">]+)"', summary)
    return match.group(1) if match else None

@app.route('/')
def index():
    bg_image = get_background_image()
    return render_template('index.html', bg_image=bg_image)

@app.route('/news')
def get_news():
    feed_url = 'https://rsshub.app/telegram/channel/piranyaz'
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.text)

        posts = []
        for entry in feed.entries:
            title = entry.get('title', '').strip()
            summary = entry.get('summary', entry.get('description', '')).strip()

            if not summary and re.match(r'^(Tue|Mon|Wed|Thu|Fri|Sat|Sun),', title):
                continue

            pub_date = entry.get('published', '')
            try:
                parsed_date = date_parser.parse(pub_date)
                formatted_date = parsed_date.strftime('%-d %B %Y, %H:%M')
            except:
                formatted_date = ''

            posts.append({
                'title': title,
                'summary': summary,
                'link': entry.link,
                'image': extract_image_from_summary(summary),
                'date': formatted_date
            })

        return jsonify(posts[:7])

    except Exception as e:
        print(f"Ошибка при загрузке RSS: {e}")
        return jsonify([])

@app.route('/articles')
def get_articles():
    feed_url = 'https://rsshub.app/telegram/channel/piranyaz'
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.text)

        articles = []
        for entry in feed.entries:
            summary = entry.get('summary', entry.get('description', '')).strip()
            links = re.findall(r'https://telegra\.ph/[^\s"<>]+', summary)
            for link in links:
                try:
                    article_html = requests.get(link, timeout=5).text
                    soup = BeautifulSoup(article_html, 'html.parser')
                    title = soup.title.string.strip()
                    image = soup.find('img')
                    image_url = image['src'] if image else None

                    articles.append({
                        'title': title,
                        'link': link,
                        'image': image_url
                    })
                except Exception as e:
                    print(f'Ошибка при обработке статьи {link}: {e}')
                    continue

        return jsonify(articles)

    except Exception as e:
        print(f"Ошибка при загрузке статей: {e}")
        return jsonify([])

if __name__ == '__main__':
    os.makedirs(BACKGROUNDS_FOLDER, exist_ok=True)
    app.run(debug=True)
