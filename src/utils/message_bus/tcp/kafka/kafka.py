#!/usr/bin/env python3

"""
 ****************************************************************************
 Filename:          kafka.py
 Description:       Producer and Consumer implementaion for kafka module.
 Creation Date:     06/08/2020
 Author:            Pawan Kumar Srivastava
 Do NOT modify or remove this copyright and confidentiality notice!
 Copyright (c) 2001 - $Date: 2015/01/14 $ Seagate Technology, LLC.
 The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 Portions are also trade secret. Any use, duplication, derivation, distribution
 or disclosure of this code, for any reason, not expressly authorized is
 prohibited. All other rights are expressly reserved by Seagate Technology, LLC.
 ****************************************************************************
"""
from eos.utils.message_bus.comm import Channel, Comm
from confluent_kafka import Producer, Consumer, KafkaException
from eos.utils.message_bus.error import SendError, ConnectionEstError,MsgFetchError, \
    OperationSuccessful
import uuid
from eos.utils.log import Log
import time
from eos.utils.message_bus.tcp.kafka import const

class KafkaProducerChannel(Channel):
    """
    Represents kafka producer channel for communication.
    """

    def __init__(self, **kwargs):
        Channel.__init__(self)
        self._hosts = kwargs.get("hosts")
        self._client_id = kwargs.get("client_id")
        self._retry_counter = kwargs.get("retry_counter", 5)
        self._topic = None
        self._channel = None

    def get_topic(self):
        return self._topic

    def set_topic(self, topic):
        if topic:
            self._topic = topic

    def init(self):
        """
        Initialize the object usinf configuration params passed.
        Establish connection with Kafka broker.
        """
        self._channel = None
        retry_count = 0
        try:
            while self._channel is None and int(self._retry_counter) > retry_count:
                self.connect()
                if self._channel is None:
                    Log.warn(f"message bus producer connection Failed. Retry Attempt: {retry_count+1}" \
                        f" in {2**retry_count} seconds")
                    time.sleep(2**retry_count)
                    retry_count += 1
                else:
                    Log.debug(f"message bus producer connection is Initialized."\
                    f"Attempts:{retry_count+1}")
        except Exception as ex:
            Log.error(f"message bus producer initialization failed. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus broker. {ex}")

    def connect(self):
        """
        Initiate the connection with Kafka broker and open the
        necessary communication channel.
        """
        try:
            conf = {'bootstrap.servers': str(self._hosts),
                    'request.required.acks' : 'all',
                    'max.in.flight.requests.per.connection': 1,
                    'client.id': self._client_id,
                    'transactional.id': uuid.uuid4(),
                    'enable.idempotence' : True}
            self._channel = Producer(conf)
            self._channel.init_transactions()
        except Exception as ex:
            Log.error(f"Unable to connect to message bus broker. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus broker. {ex}")

    @classmethod
    def disconnect(self):
        raise Exception('recv not implemented for Kafka producer Channel')

    @classmethod
    def recv(self, message=None):
        raise Exception('recv not implemented for Kafka producer Channel')

    def channel(self):
        return self._channel

    def send(self, message):
        """
        Publish the message to kafka broker topic.
        """
        try:
            if self._channel is not None:
                self._channel.begin_transaction()
                self._channel.produce(self._topic, message)
                self._channel.commit_transaction()
                Log.info(f"Message Published to Topic: {self._topic},"\
                    f"Msg Details: {message}")
        except KafkaException as e:
            if e.args[0].retriable():
                """Retriable error, try again"""
                self.send(message)
            elif e.args[0].txn_requires_abort():
                """
                Abort current transaction, begin a new transaction,
                and rewind the consumer to start over.
                """
                self._channel.abort_transaction()
                self.send(message)
                #TODO
                #rewind_consumer_offsets...()
            else:
                """Treat all other errors as fatal"""
                Log.error(f"Failed to publish message to topic : {self._topic}. {e}")
                raise SendError(f"Unable to send message to message bus broker. {e}")

    @classmethod
    def recv_file(self, remote_file, local_file):
        raise Exception('recv_file not implemented for Kafka producer Channel')

    @classmethod
    def send_file(self, local_file, remote_file):
        raise Exception('send_file not implemented for Kafka producer Channel')

    @classmethod
    def acknowledge(self, delivery_tag=None):
        raise Exception('send_file not implemented for Kafka producer Channel')

class KafkaConsumerChannel(Channel):
    """
    Represents kafka consumer channel for communication.
    """

    def __init__(self, **kwargs):
        Channel.__init__(self)
        self._hosts = kwargs.get("hosts")
        self._group_id = kwargs.get("group_id")
        self._consumer_name = kwargs.get("consumer_name")
        self._retry_counter = kwargs.get("retry_counter", 5)

    def init(self):
        """
        Initialize the object usinf configuration params passed.
        Establish connection with message bus broker.
        """
        self._channel = None
        retry_count = 0
        try:
            while self._channel is None and int(self._retry_counter) > retry_count:
                self.connect()
                if self._channel is None:
                    Log.warn(f"message bus consumer connection Failed. Retry Attempt: {retry_count+1}" \
                        f" in {2**retry_count} seconds")
                    time.sleep(2**retry_count)
                    retry_count += 1
                else:
                    Log.debug(f"message bus consumer connection is Initialized."\
                    f"Attempts:{retry_count+1}")
        except Exception as ex:
            Log.error(f"message bus consumer initialization failed. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus broker. {ex}")

    def connect(self):
        """
        Initiate the connection with Kafka broker and open the
        necessary communication channel.
        """
        try:
            conf = {'bootstrap.servers': str(self._hosts),
                    'group.id' : self._group_id,
                    'group.instance.id' : self._consumer_name,
                    'isolation.level' : 'read_committed',
                    'enable.auto.commit' : False}
            self._channel = Consumer(conf)
            Log.info(f"message bus consumer Channel initialized. Group : {self._group_id}")
        except Exception as ex:
            Log.error(f"Unable to connect to message bus broker. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus broker. {ex}")

    @classmethod
    def disconnect(self):
        raise Exception('recv not implemented for Kafka consumer Channel')

    @classmethod
    def recv(self, message=None):
        raise Exception('recv not implemented for Kafka consumer Channel')

    def channel(self):
        return self._channel

    @classmethod
    def send(self, message):
        raise Exception('send not implemented for Kafka consumer Channel')

    @classmethod
    def recv_file(self, remote_file, local_file):
        raise Exception('recv_file not implemented for Kafka consumer Channel')

    @classmethod
    def send_file(self, local_file, remote_file):
        raise Exception('send_file not implemented for Kafka consumer Channel')

    @classmethod
    def acknowledge(self, delivery_tag=None):
        raise Exception('send_file not implemented for Kafka consumer Channel')

class KafkaProducerComm(Comm):
    def __init__(self, **kwargs):
        Comm.__init__(self)
        self._outChannel = KafkaProducerChannel(**kwargs)

    def init(self):
        self._outChannel.init()

    def send_message_list(self, message: list, **kwargs):
        if self._outChannel is not None:
            self._outChannel.set_topic(kwargs.get(const.TOPIC))
            for msg in message:
                self.send(msg)
            return OperationSuccessful("Successfully sent messages.")
        else:
            Log.error("Unable to connect to Kafka broker.")
            raise ConnectionEstError("Unable to connect to message bus broker.")


    def send(self, message, **kwargs):
        self._outChannel.send(message)

    @classmethod
    def acknowledge(self):
        raise Exception('acknowledge not implemented for KafkaProducer Comm')

    @classmethod
    def stop(self):
        raise Exception('stop not implemented for KafkaProducer Comm')

    @classmethod
    def recv(self, callback_fn=None, message=None, **kwargs):
        raise Exception('recv not implemented for KafkaProducer Comm')

    @classmethod
    def disconnect(self):
        raise Exception('disconnect not implemented for KafkaProducer Comm')

    @classmethod
    def connect(self):
        raise Exception('connect not implemented for KafkaProducer Comm')

class KafkaConsumerComm(Comm):
    def __init__(self, **kwargs):
        Comm.__init__(self)
        self._inChannel = KafkaConsumerChannel(**kwargs)

    def init(self):
        self._inChannel.init()

    @classmethod
    def send_message_list(self, message: list, **kwargs):
        raise Exception('send_message_list not implemented for KafkaConsumer Comm')

    @classmethod
    def send(self, message, **kwargs):
        raise Exception('send not implemented for KafkaConsumer Comm')

    @classmethod
    def acknowledge(self):
        if self._inChannel is not None:
            self._inChannel.commit()
            return OperationSuccessful("Commit operation successfull.")
        else:
            Log.error("Unable to connect to message bus broker.")
            raise ConnectionEstError("Unable to connect to message bus broker.")

    @classmethod
    def stop(self):
        raise Exception('stop not implemented for KafkaConsumer Comm')

    def recv(self, callback_fn=None, message=None, **kwargs):
        if self._inChannel is not None:
            self._inChannel.channel().subscribe(kwargs.get(const.TOPIC))
            msg = self._inChannel.channel().poll(1.0)
            if msg is None:
                Log.warn("No message fetched from kafka broker.")
                return msg
            if msg.error():
                Log.error(f"Fetching message from kafka broker failed. {msg.error()}")
                raise MsgFetchError(f"No message fetched from kafka broker. {msg.error()}")
            Log.info(f"Received message: {msg.value().decode('utf-8')}")
        else:
            Log.error("Unable to connect to message bus broker.")
            raise ConnectionEstError("Unable to connect to message bus broker.")
        return msg.value().decode('utf-8')

    @classmethod
    def disconnect(self):
        if self._inChannel is not None:
            self._inChannel.close()
            return OperationSuccessful("Close operation successfull.")
        else:
            Log.error("Unable to connect to message bus broker.")
            raise ConnectionEstError("Unable to connect to message bus broker.")

    @classmethod
    def connect(self):
        raise Exception('connect not implemented for KafkaConsumer Comm')
