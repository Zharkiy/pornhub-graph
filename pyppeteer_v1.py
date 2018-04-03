#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from collections import Counter
import asyncio

from pyppeteer import launch
import lxml.html as l

from storage import S


START_VIDEO_HASH = 'ph59fcf23b6203e'
TIMEOUT = 10
MAX_CONCURRENT_CLIENTS = 1
URL_TEMPLATE = 'https://www.pornhub.com/view_video.php?viewkey=%s'
BATCH_SIZE = 100

_BROWSER = None


def parse_similar_videos(source_html) -> set:
    doc = l.document_fromstring(source_html)
    return {r.get('_vkey') for r in doc.xpath('//ul[@id="relatedVideosCenter"]/li[@_vkey]') if len(r.get('_vkey')) == 15}


async def crawl_many_videos(concurrency: int, video_hashes: set, cnt: Counter=None):
    global _BROWSER
    # todo concurency
    # todo pages pool?
    if _BROWSER is None:
        _BROWSER = await launch()
    if cnt is None:
        cnt = Counter()

    page = await _BROWSER.newPage()
    for current_video in video_hashes:
        relations, title = await crawl_one(current_video, page, cnt)
        if relations:
            for r in relations:
                await S.add_video_hash(r)
            await S.mark_video_as_parsed(current_video, title, relations)
    await page.close()


async def crawl_one(hash: str, page, cnt: Counter) -> tuple:
    out = set()
    title = None
    url = URL_TEMPLATE % hash
    logging.info('fetch %s url', url)
    try:
        resp = await page.goto(url, timeout=TIMEOUT * 1000)
        code = resp.status
        cnt[code] += 1
        logging.info('fetch %s url code %s', url, code)
        if code == 200:
            try:
                title = await page.waitForSelector('head > title', timeout=TIMEOUT * 1000)
                response_content = await resp.text()
                result = parse_similar_videos(response_content)
                if not result:
                    logging.warning('parse %s url: not found hashes', url)
                    cnt['similar_not_found'] += 1
                # elif not title:
                #     logging.warning('parse %s url: not found title', url)
                #     cnt['title_not_found'] += 1
                else:
                    logging.info('parse %s url: found %d hashes', url, len(result))
                    out = out | result
            except Exception as e:
                cnt['exception_parse'] += 1
                logging.warning('parse %s url exception %s', url, type(e))
                logging.exception(e)
    except Exception as e:
        cnt['exception_fetch'] += 1
        logging.warning('fetch %s url exception %s', url, type(e))

    return out, 'todo'


async def run(max_iterations: int=100, reset_db: bool=False):
    S.set_io_loop(asyncio.get_event_loop())
    cnt = Counter()

    if reset_db:
        # todo
        pass

    iter_num = 1
    await S.add_video_hash(START_VIDEO_HASH)

    while iter_num <= max_iterations:
        videos_for_parsing = await S.get_videos_for_parsing(BATCH_SIZE)
        logging.info('start %d crawling iteration (%d videos)', iter_num, len(videos_for_parsing))
        if not len(videos_for_parsing):
            break

        await crawl_many_videos(MAX_CONCURRENT_CLIENTS, videos_for_parsing, cnt)
        logging.info('end %d level crawling (%s)', iter_num, cnt.items())
        iter_num += 1

    logging.info('end with counters %s', cnt.items())
    try:
        await asyncio.sleep(TIMEOUT)
        await _BROWSER.close()
    except:
        pass


if __name__ == '__main__':
    # todo cli args
    # todo reset mode
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    ioloop = asyncio.new_event_loop()
    ioloop.run_until_complete(run())
    ioloop.close()
