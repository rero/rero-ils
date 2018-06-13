#!/bin/bash
# -*- coding: utf-8 -*-
echo "Building version: $1"
source /reroils/reroils/bin/activate && \
cd reroils/src && \
git clone https://github.com/rero/reroils-app.git && \
cd reroils-app
pip install git+https://github.com/rero/reroils-data.git#egg=reroils-data
pip install .[all]
