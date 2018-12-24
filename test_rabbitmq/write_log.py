# -*- coding: utf-8 -*-
import logging

from pyleus.storm import SimpleBolt

log = logging.getLogger('write_log')


class SplitWordsBolt(SimpleBolt):

    OUTPUT_FIELDS = ["items"] # 定义输出的字段只有一个，名为word

    def process_tuple(self, tup):
        line, = tup.values # 接收到上游的tuple
        log.debug(line)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='/tmp/result.log',
        format="%(message)s",
        filemode='a',
    )
    SplitWordsBolt().run()
