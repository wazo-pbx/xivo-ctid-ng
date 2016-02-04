# -*- coding: utf-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import json

from kombu import Connection
from kombu import Consumer
from kombu import Exchange
from kombu import Producer
from kombu import Queue
from kombu.exceptions import TimeoutError

from .constants import BUS_EXCHANGE_NAME
from .constants import BUS_EXCHANGE_TYPE
from .constants import BUS_URL
from .constants import BUS_QUEUE_NAME


class BusClient(object):

    @classmethod
    def listen_events(cls, routing_key, exchange=BUS_EXCHANGE_NAME):
        exchange = Exchange(exchange, type=BUS_EXCHANGE_TYPE)
        with Connection(BUS_URL) as conn:
            queue = Queue(BUS_QUEUE_NAME, exchange=exchange, routing_key=routing_key, channel=conn.channel())
            queue.declare()
            queue.purge()
            cls.bus_queue = queue

    @classmethod
    def json_events(cls):
        events = []

        def on_event(body, message):
            events.append(json.loads(body))
            message.ack()

        cls._drain_events(on_event=on_event)

        return events

    @classmethod
    def text_events(cls):
        events = []

        def on_event(body, message):
            events.append(body)
            message.ack()

        cls._drain_events(on_event=on_event)

        return events

    @classmethod
    def _drain_events(cls, on_event):
        with Connection(BUS_URL) as conn:
            with Consumer(conn, cls.bus_queue, callbacks=[on_event]):
                try:
                    while True:
                        conn.drain_events(timeout=0.5)
                except TimeoutError:
                    pass

    @classmethod
    def send_event(cls, event, routing_key):
        bus_exchange = Exchange(BUS_EXCHANGE_NAME, type=BUS_EXCHANGE_TYPE)
        with Connection(BUS_URL) as connection:
            producer = Producer(connection, exchange=bus_exchange, auto_declare=True)
            producer.publish(json.dumps(event), routing_key=routing_key)

    @classmethod
    def send_ami_newchannel_event(cls, channel_id):
        cls.send_event({
            'data': {
                'Event': 'Newchannel',
                'Uniqueid': channel_id,
            }
        }, 'ami.Newchannel')

    @classmethod
    def send_ami_newstate_event(cls, channel_id):
        cls.send_event({
            'data': {
                'Event': 'Newstate',
                'Uniqueid': channel_id,
            }
        }, 'ami.Newstate')

    @classmethod
    def send_ami_hangup_event(cls, channel_id):
        cls.send_event({
            'data': {
                'Event': 'Hangup',
                'Uniqueid': channel_id,
                'ChannelStateDesc': 'Up',
                'CallerIDName': 'my-caller-id-name',
                'CallerIDNum': 'my-caller-id-num',
            }
        }, 'ami.Hangup')
