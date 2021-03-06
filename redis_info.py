# -*- coding:utf-8 -*-
"""

modules for redis info parse

"""

import json
import os
import time

import paramiko
import redis
import logging


class RedisInfo(object):
    """
    redis info

    """

    RETRY_TIMES = 3

    INFO_KEY = [

        # ---- server :
        'redis_version',
        'uptime_in_seconds',
        'uptime_in_days',


        # ---- memory
        'used_memory',
        'used_memory_rss',
        'mem_fragmentation_ratio',
        'total_system_memory',

        # ---- Stats :
        'total_connections_received',
        'total_commands_processed',
        'instantaneous_ops_per_sec',

        'total_net_input_bytes',
        'total_net_output_bytes',
        'instantaneous_input_kbps',
        'instantaneous_output_kbps',

        'rejected_connections',

        'expired_keys',
        'evicted_keys',
        'keyspace_hits',
        'keyspace_misses',

        # ---- clients :
        'connected_clients',
        'blocked_clients',

        # ---- Keyspace

        # total_keys

        # ---- commandstats

    ]

    def __init__(self, host="localhost", port=6379, password=""):

        self.host = host
        self.port = port
        self.password = password

        self.monitor_info = None  # dict: storage monitor information

        self._redis_client = None
        # self._auth_init()

        self.redis_connection_init()

    def redis_connection_init(self):
        # connection init
        try:
            pool = redis.ConnectionPool(host=self.host, port=self.port, db=0,
                                        password=self.password)
            self._redis_client = redis.Redis(connection_pool=pool)
            RETRY_TIMES = 3
        except Exception as ex:
            logging.error(ex)
        finally:
            if RETRY_TIMES > 0:
                RETRY_TIMES = RETRY_TIMES - 1
                self.redis_connection_init()

    def _auth_init_from_env(self):
        # redis auth info
        self.host = str(os.environ['REDIS_ADDRESS'])
        self.port = int(os.environ['REDIS_PORT'])
        self.password = str(os.environ['REDIS_PASSWORD'])

    def rdb_info(self, section="Stats"):
        # get stats from redis server
        info = self._redis_client.info(section)    # redis info
        return info

    @staticmethod
    def state(f):
        format_unit = f"{f:.2f}"
        return format_unit

    @staticmethod
    def get_cpu():
        # system cpu info
        num = 0
        with open('/proc/cpuinfo') as fd:
            for line in fd:
                if line.startswith('processor'):
                    num += 1
                if line.startswith('model name'):
                    cpu_model = line.split(':')[1].strip().split()
                    cpu_model = cpu_model[0] + ' ' + cpu_model[2] + ' ' + cpu_model[-1]
        cpu_info = f"CPU : cpu_num : {num}   cpu_model : {cpu_model}"
        return cpu_info

    @staticmethod
    def get_memory():
        # system memory info
        #   kb : return GB
        with open('/proc/meminfo') as fd:
            for line in fd:
                if line.startswith('MemTotal'):
                    mem = int(line.split()[1].strip())
                    break

        mem_info = f'MemTotal: {mem / 1024 / 1024 :.2f} GB'
        return mem_info

    def get_qps_tps(self):
        # tps  total_commands_processed : <Sampling interval>
        # https://github.com/me115/cppset/blob/master/redisTPS/main.cpp

        sec_start = time.time()
        cmd_num_start = self.rdb_info()['total_commands_processed']
        time.sleep(1)
        sec_end = time.time()
        info = self.rdb_info()
        cmd_num_end = info['total_commands_processed']
        qps = info['instantaneous_ops_per_sec']

        tps = (cmd_num_end - cmd_num_start) / (sec_end-sec_start)

        return qps, tps

    def log_show(self):
        #  log process
        pass

    def poll(self):
        """
        performance index
        :return: all info of INFO_KEY
        """
        db_info = {}
        for keyname, value in self.rdb_info().items():

            if keyname in self.INFO_KEY:
                db_info[keyname] = value

        self.output_info(db_info)

    def output_info(self, monitor_info):
        # output data
        pass

    def json_info(self, section="all"):
        """
        get section info from redis
        :param section:
        :return: json data
        """
        data = self.rdb_info(section)
        json_data = json.dumps(data)
        return json_data


def main():
    info = RedisInfo()
    json_info = info.json_info()
    print(json_info)


if __name__ == '__main__':
    main()
