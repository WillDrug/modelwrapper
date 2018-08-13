#!/usr/bin/env bash
redis-server $REDIS_CONFIG --dir $REDIS_DATA
python3 start.py