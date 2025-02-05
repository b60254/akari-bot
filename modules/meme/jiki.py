import traceback

from bs4 import BeautifulSoup

from config import Config
from core.elements import Url
from core.logger import Logger
from core.utils import get_url


async def jiki(term: str):
    '''查询小鸡百科。

    :param term: 需要查询的term。
    :returns: 查询结果。'''
    try:
        api = 'https://jikipedia.com/search?phrase=' + term
        webrender = Config('web_render')
        if webrender:
            api = webrender + 'source?url=' + api
        html = await get_url(api, 200)
        Logger.debug(html)
        bs = BeautifulSoup(html, 'html.parser')
        result = bs.select_one('[data-index="0"]')
        title_ele = result.select_one(
            'a.title-container.block.title-normal')
        content_ele = result.select_one('.lite-card-content')

        title = title_ele.get_text()
        link = title_ele.get('href')
        content = content_ele.get_text()

        results = bs.select('.lite-card').__len__()
        count = str(result) if results < 15 else '15+'
        return f'[小鸡百科]（{count}个结果）：{title}\n{content}\n{str(Url(link))}'
    except Exception:
        traceback.print_exc()
        return '[小鸡百科] 查询出错。'
