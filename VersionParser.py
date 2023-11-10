from bs4 import BeautifulSoup
import requests

import pandas as pd

import numpy as np

from google_play_scraper import app


# Все категории приложений с сайта RuStore на момент хакатона. Может выгружаться машинно при дальнейшей разработке:
slovar = {'Все приложения': 'https://apps.rustore.ru/',
          'Бизнес-сервисы': 'https://apps.rustore.ru/business',
          'Государственные': 'https://apps.rustore.ru/state',
          'Еда и напитки': 'https://apps.rustore.ru/foodanddrink',
          'Здоровье': 'https://apps.rustore.ru/health',
          'Книги': 'https://apps.rustore.ru/books',
          'Новости и события': 'https://apps.rustore.ru/news',
          'Образ жизни': 'https://apps.rustore.ru/lifestyle',
          'Образование': 'https://apps.rustore.ru/education',
          'Общение': 'https://apps.rustore.ru/social',
          'Объявления и услуги': 'https://apps.rustore.ru/adsandservices',
          'Питомцы': 'https://apps.rustore.ru/pets',
          'Покупки': 'https://apps.rustore.ru/purchases',
          'Полезные инструменты': 'https://apps.rustore.ru/tools',
          'Путешествия': 'https://apps.rustore.ru/travelling',
          'Развлечения': 'https://apps.rustore.ru/entertainment',
          'Родителям': 'https://apps.rustore.ru/parenting',
          'Спорт': 'https://apps.rustore.ru/sport',
          'Ставки и лотереи': 'https://apps.rustore.ru/gambling',
          'Транспорт и навигация': 'https://apps.rustore.ru/transport',
          'Финансы': 'https://apps.rustore.ru/finance'}

# Функция get_versions() принимает на вход URL страницы с сайта RuStore, откуда выгружаются сведения о приложениях. На основе AppID этих приложений, осуществляется их поиск у конкурентов.
# Данные о названиях приложений, appid, версиях приложений на различных платформах сохраняются в датафрейме Pandas


def get_versions(url):

    responseMain = requests.get(url)

    soup = BeautifulSoup(responseMain.content, 'html.parser')

    a_tags = soup.find_all('a')

    urls = [tag.get('href') for tag in a_tags]

    appids = [appid.replace('/app/', '')
              for appid in list(map(str, urls)) if '/app/' in appid]

    res = pd.DataFrame()

    for ind in range(len(appids)):
        res.loc[ind, 'appid'] = appids[ind]
        responseApp = requests.get(
            f'https://apps.rustore.ru/app/{appids[ind]}')
        soup = BeautifulSoup(responseApp.content, 'html.parser')
        res.loc[ind, 'version_rs'] = soup.find_all(
            'p', {'itemprop': 'softwareVersion'})[0].get_text()
        res.loc[ind, 'title_rs'] = soup.find_all(
            'h1', {'itemprop': 'headline'})[0].get_text()
    for ind in res.index:
        responseGP = requests.get(
            f'https://play.google.com/store/apps/details?id={res.loc[ind, "appid"]}')
        responseGS = requests.get(
            f'https://galaxystore.samsung.com/detail/{res.loc[ind, "appid"]}')

        soupGP = BeautifulSoup(responseGP.content, 'html.parser')
        soupGS = BeautifulSoup(responseGS.content, 'html.parser')

        try:
            res.loc[ind, 'title_gp'] = app(
                res.loc[ind, 'appid'],
                lang='ru',
                country='ru'
            )['title']
        except:
            res.loc[ind, 'title_gp'] = np.nan

        try:
            res.loc[ind, 'version_gp'] = app(
                res.loc[ind, 'appid'],
                lang='ru',
                country='ru'
            )['version']
        except:
            res.loc[ind, 'version_gp'] = np.nan

        try:
            res.loc[ind, 'version_gs'] = soupGS.find_all(
                'div', {'class': 'InfoSession_info_version_info__3yNQH'})[0].get_text()
        except:
            res.loc[ind, 'version_gs'] = np.nan

    return res


# Пользователь вводит в консоли название категории с сайта RuStore одной строкой. При доработке можно реализовать парсинг сразу всех категорий. В таком случае, программы будет выполняться медленнее.
cat = input('Введите категорию приложения с сайта RuStore: ')
url = slovar[cat]
# Следующей строкой пользователь вводит количество страниц сайта RuStore данной категории, подлежащих обработке.
num_pages = int(input(
    'Введите количество страниц сайта RuStore для выбранной категории для анализа: '))


# Цикл перебирает каждую страницу, выгружая необходимую информацию о приложениях и их версиях
if len(num_pages) > 1:
    for i in range(2, num_pages + 1):
        if i == 1:
            output = get_versions(f'https://apps.rustore.ru/')
        else:
            pd.concat(output, get_versions(
                f'https://apps.rustore.ru/page-{i}'), axis=0)


# Итоговая таблица сохраняется в файл excel в директории с файлом кода
output.to_excel(f'versions_{cat}.xlsx')
