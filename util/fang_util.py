#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from retrying import retry

from util.log import logger

# 请求头部
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:73.0) Gecko/20100101 Firefox/73.0'}
# 默认超时时间，单位秒
default_timeout = 300


@retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=5000)
def post(url: str, data: dict, timeout=default_timeout):
    """
    发送POST请求
    :param url: 请求地址
    :param data: 参数
    :param timeout: 超时时间
    :return: 返回Response对象，请求失败时返回HttpRequestException异常
    """
    try:
        response = requests.post(url,
                                 headers=headers,
                                 data=data,
                                 timeout=timeout)
        if not response.status_code == 200:
            raise HttpRequestException('url={}，status_code {} 状态异常'.format(url, response.status_code))
        return response
    except Exception as e:
        logger.error('发送POST请求失败，url={}，{}'.format(url, e.args))
        raise HttpRequestException(e)


def post_with_decode(url: str, data: dict, decode: str, timeout=default_timeout):
    """
    发送POST请求
    :param url: 请求地址
    :param data: 参数
    :param decode: 编码
    :param timeout: 超时时间
    :return: 解码后的文本，当请求失败时抛出HttpRequestException异常
    """
    response = post(url=url, data=data, timeout=timeout)
    return response.text.encode(response.encoding).decode('gbk')


@retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=5000)
def get(url: str, timeout=default_timeout, **kwargs):
    """
    发送GET请求
    :param url: 请求地址
    :param timeout: 超时时间
    :param kwargs: 参数
    :return: Response对象，当请求失败时抛出HttpRequestException异常
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout, params=kwargs.get('params'))
        if not response.status_code == 200:
            raise HttpRequestException('url={}，status_code {} 状态异常'.format(url, response.status_code))
        return response
    except Exception as e:
        logger.error('发送GET请求失败，url={}，{}'.format(url, e.args))
        raise HttpRequestException(e)


def get_with_decode(url: str, decode: str, timeout=default_timeout, **kwargs):
    """
    发送GET请求
    :param url: 请求地址
    :param decode: 解码
    :param timeout: 超时时间
    :param kwargs: 请求参数
    :return: 解码后的文本字符串，当请求失败时抛出HttpRequestException异常
    """
    response = get(url=url, timeout=timeout, **kwargs)
    return response.text.encode(response.encoding).decode(decode)


class HttpRequestException(Exception):
    pass
