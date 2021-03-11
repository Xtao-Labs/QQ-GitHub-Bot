#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author         : yanyongyu
@Date           : 2021-03-11 16:04:44
@LastEditors    : yanyongyu
@LastEditTime   : 2021-03-11 16:53:10
@Description    : None
@GitHub         : https://github.com/yanyongyu
"""
__author__ = "yanyongyu"

from . import BaseModel


class License(BaseModel):
    key: str
    name: str
    spdx_id: str
    url: str
    node_id: str
