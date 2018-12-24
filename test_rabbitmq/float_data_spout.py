# -*- coding: utf-8 -*-
# @Date	: 2018-3-19
# @Author  : liuhy
# @Desc    : receive float_data from rabbitmq
from pika import BlockingConnection, ConnectionParameters
from pika.exceptions import ConnectionClosed
from pyleus.storm import Spout
import logging, pika

log = logging.getLogger('spout')


class FloatDataSpout(Spout):
    # OUTPUT_FIELDS，表示你要输出几个参数，如果list中有一个，tuple只能输出一个参数，格式一定要统一，不然会报错
    OUTPUT_FIELDS = ['items']

    def initialize(self):
        # self.m2m_conn = BlockingConnection(ConnectionParameters(host='192.168.64.137', port=5672))
        # self.channel = self.m2m_conn.channel()
        # self.queue_name = 'storm'
        # result = self.channel.queue_declare(queue=self.queue_name)
        # self.log('queue name is :%s' % self.queue_name)
        # log.debug('queue name is :%s' % self.queue_name)
        # # self.channel.basic_qos(prefetch_count=1)
        # self.channel.queue_bind(exchange="float_data", queue=self.queue_name, routing_key="float_data")

        rabbitmq_url = 'amqp://guest:guest@192.168.64.137:5672/%2F'
        parameters = pika.URLParameters(rabbitmq_url)
        connection = pika.BlockingConnection(parameters)
        self.channel = connection.channel()
        self.queue_name = 'storm'
        result = self.channel.queue_declare(queue=self.queue_name)
        # self.channel.exchange_declare(exchange=self.queue_name, type='fanout')
        self.channel.queue_bind(exchange="float_data", queue=self.queue_name, routing_key="float_data")

    def call_back(self, ch, method, properties, body, data):
        log.debug('1 argument, %s' % ch)
        log.debug('2 argument, %s' % method)
        log.debug('3 argument, %s' % properties)
        log.debug('4 is:%s' % body)
        log.debug('5 is:%s' % data)
        self.log(body)
        self.emit((body,), )

    def next_tuple(self):

        try:
            # self.channel.basic_consume(self.call_back, queue=self.queue_name, no_ack=True)
            method_frame, _, data = self.channel.basic_get(queue=self.queue_name, no_ack=False)
            # self.log(method_frame)
            # self.log(_)
            if data:
                self.log('i want %s' %data)
                self.emit((data,))
        except ConnectionClosed, e:
            pass
        # try:
        #     method_frame, _, data = self.channel.basic_get(queue=self.queue_name, no_ack=False)  # noqa
        #     if method_frame and data:
        #         self.channel.basic_ack(method_frame.delivery_tag)
        #         self.emit((data,))
        # except ConnectionClosed, e:
        #     print e


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='/tmp/spout.log',
        format="%(message)s",
        filemode='a',
    )
    FloatDataSpout().run()
