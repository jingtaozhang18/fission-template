# -*- coding: utf-8 -*-
from flask import request as flask_request
import json
from flask import g


def main():
    #  打日志
    # g.logger.info()

    #  打点
    # metric name 为埋点的名称
    # labels 为埋点的标签信息，为字典结构
    # g.metric_handler.counter("metric name", labels, 1)  # 通常用于统计频率信息等
    # g.metric_handler.gauge("metric name", labels, 1)  # 通常用于持续计数等

    return json.dumps(flask_request.json)
