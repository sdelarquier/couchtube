#!/usr/bin/env python
# coding=utf8
from app import app
# app.config['USE_X_SENDFILE'] = False
app.run(host='0.0.0.0', debug=True)