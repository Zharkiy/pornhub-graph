import asyncio
from pyppeteer import launch


async def main():
    browser = await launch()
    page = await browser.newPage()
    for i in range(0, 20):
        resp = await page.goto('https://www.pornhub.com/view_video.php?viewkey=ph5a7f1ba584481', timeout=10 * 1000)
        await page.waitForSelector('head > title', timeout=10 * 1000)
        response_content = await resp.text()
        print(len(response_content))
    await browser.close()


if __name__ == '__main__':
    ioloop = asyncio.new_event_loop()
    ioloop.run_until_complete(main())
    ioloop.close()
