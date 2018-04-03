#! /usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging

from src.crawler import run
from src.storage import S
from src.utils import get_default_arg_parser


async def main(root_hash: str, reset: bool=False, **kwargs):
    S.set_io_loop(asyncio.get_event_loop())
    if reset:
        await S.drop_all()
    await S.add_video_hash(root_hash)
    await run(**kwargs)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)

    parser = get_default_arg_parser()
    parser.add_argument('root_hash', action='store', type=str, help='start video hash')
    args = parser.parse_args()

    ioloop = asyncio.new_event_loop()
    ioloop.run_until_complete(main(**args.__dict__))
    ioloop.close()
