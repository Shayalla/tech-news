import requests
import parsel
import time
from .database import create_news


# Requisito 1
def fetch(url):
    try:
        response = requests.get(url, timeout=3)
        time.sleep(1)
        if response.status_code == 200:
            return response.text
    except requests.ReadTimeout:
        return None


# Requisito 2
def scrape_novidades(html_content):
    selector = parsel.Selector(html_content)
    return selector.css("h3.tec--card__title a::attr(href)").getall()


# Requisito 3
def scrape_next_page_link(html_content):
    selector = parsel.Selector(html_content)
    return selector.css("div.tec--list > a::attr(href)").get()


# Requisito 4
def scrape_noticia(html_content):
    selector = parsel.Selector(html_content)
    # seletor pego da duvida que o Mauricio Ieiri postou no slack
    # https://trybecourse.slack.com/archives/C01PLFW7347/p1644513640915889
    url = selector.xpath("/html/head/*[@rel='canonical']/@href").get()
    title = selector.css("h1.tec--article__header__title::text").get()
    time = selector.css("div.tec--timestamp__item time::attr(datetime)").get()
    writer = selector.css("div.tec--author__info *:first-child *::text").get()
    # Em busca do seletor correto para o writer peguei desse commit do Marco
    # Galindo:
    # https://github.com/tryber/sd-011-tech-news/pull/22/commits/f1b312eb5385eca938340a185f2a826d291ec407
    shares = selector.css("div.tec--toolbar__item::text").get()
    comments = selector.css("button#js-comments-btn::attr(data-count)").get()
    summary = ''.join(selector.css(
        "div.tec--article__body > p:first-child *::text"
        ).getall())
    sources = list(map(
        str.strip, selector.css("a.tec--badge[target='_blank']::text").getall()
        ))
    categories = list(map(
        str.strip, selector.css("div#js-categories a::text").getall()
        ))

    if not writer:
        writer = selector.css(
            "div.tec--timestamp__item.z--font-bold a::text"
        ).get()
    if writer:
        writer = writer.strip()

    if shares is None:
        shares_count = 0
    else:
        shares_count = int(shares.split()[0])

    return {
        'url': url.strip(),
        'title': title.strip(),
        'timestamp': time.strip(),
        'writer': writer,
        'shares_count': shares_count,
        'comments_count': int(comments),
        'summary': summary.strip(),
        'sources': sources,
        'categories': categories
        }


# Requisito 5
def get_tech_news(amount):
    html_content = fetch("https://www.tecmundo.com.br/novidades")
    links = scrape_novidades(html_content)
    news = []

    while len(links) < amount:
        next_page = scrape_next_page_link(html_content)
        html_content = fetch(next_page)
        new_links = scrape_novidades(html_content)
        links.extend(new_links)

    news = links[0:amount]

    tech_news = []
    for new in news:
        tech_news.append(scrape_noticia(fetch(new)))

    create_news(tech_news)
    return tech_news
