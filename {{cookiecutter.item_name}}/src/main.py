# -*- coding: utf-8 -*-
from flask import request as flask_request
import json

def main():
    return json.dumps(flask_request.json)