#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import os
import threading
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor

from lxml import etree

from util.fang_util import get
from util.fang_util import get_with_decode
from util.fang_util import logger
from util.fang_util import post

"""西安新房用户评论爬虫"""


class UserCommentSpider(object):
    # 传入几就是第几页
    INDEX_PAGE_URL = 'https://xian.newhouse.fang.com/house/s/b9{}/?ctm=1.xian.xf_search.page.1'

    def name(self):
        return '西安新房用户评论爬虫'

    def fetch_index_page_size(self):
        """
        获取高新区新房共有几页，目前一页显示20条
        """
        # 获取首页返回的html文本
        index_html_text = get_with_decode(url=self.INDEX_PAGE_URL.format(1), decode='gbk')
        # 使用xpath解析获取共多少页
        html_tree = etree.HTML(index_html_text)
        total_elements_list = html_tree.xpath('//div[@id="sjina_C01_47"]/ul/li/b/text()')
        record_total = ''.join(total_elements_list).strip()
        total_split = str(int(record_total) / 20).split('.')
        if total_split[1] == '0':
            return int(total_split[0])
        else:
            return int(total_split[0]) + 1

    def get_house_info_by_page(self, page):
        """
        获取当前页面所有房屋的信息和详情链接
        :param page: 当前是第几页
        :return: 房屋信息列表，元组（标题，详情链接）
        """
        all_house = []
        current_page_html = get_with_decode(url=self.INDEX_PAGE_URL.format(page), decode='gbk')
        html_tree = etree.HTML(current_page_html)
        # 找到当前页面下标题对应的所有的a连接
        a_from_title = html_tree.xpath('//div[@class="nlcd_name"]/a')
        for a in a_from_title:  # 开始循环进入详情页
            title = ''.join(a.xpath('text()')).strip()
            domain = ''.join(a.xpath('@href')).strip()
            all_house.append((title, f'https:{domain}'))
        return all_house

    def get_house_id(self, detail_url: str):
        """
        获取房屋ID，进入评论页面需要
        :param detail_url: 详情页面链接
        :return: 房屋ID
        """
        response = get(url=detail_url)
        response_text = response.text
        detail_html = etree.HTML(response_text)
        mobile_agent_content = ''.join(detail_html.xpath('//meta[@name="mobile-agent"]/@content')).strip()
        house_id = mobile_agent_content.split('/')[5].strip('.htm')
        return house_id

    def worker(self, page: str):
        """
        核心任务函数
            1.获取当前页面所有的链接
            2.根据链接获取到房屋ID
            3.根据房屋ID构造出评论页面并进行数据获取
            4.保存评论信息
        :param page: 当前是第几页
        """
        houses_info = self.get_house_info_by_page(page)
        logger.info('{} 当前页面[{}]所有房屋信息{}'.format(threading.current_thread().getName(), page, houses_info))

        # 开启线程池，每个页面有多少个连接就开多少个
        with ThreadPoolExecutor(max_workers=len(houses_info), thread_name_prefix='page_all_houses') as exe:
            for house_info in houses_info:
                future = exe.submit(self.get_house_id, detail_url=house_info[1])
                # 增强回调函数
                future.add_done_callback(functools.partial(self.house_id_handler_callback, house_info=house_info))

    @staticmethod
    def house_id_handler_callback(future: Future, **kwargs):
        house_info = kwargs['house_info']
        title = house_info[0].replace('/', '_')
        detail_url = house_info[1]
        house_id = future.result()
        logger.info('{} 当前标题[{}] 房屋ID {}'.format(threading.current_thread().getName(), house_info,
                                                 house_id))
        # 现获取评论总数，然后一次性取全部评论
        dianping_url = f'{detail_url}/house/ajaxrequest/dianpingList_201501.php'
        logger.info('开始获取{}点评总数，点评链接：{}，house_id={}'.format(title, dianping_url, house_id))
        response = post(url=dianping_url,
                        data={'city': '西安', 'dianpingNewcode': house_id, 'ifjiajing': 0, 'tid': '', 'page': 1,
                              'pagesize': 1,
                              'starnum': 0, 'shtag': -1, 'rand': 0.8865550224456968})

        count = response.json().get('count')
        logger.info('开始获取{}点评 ，house_id={}，评论数={}，开始抓取所有评论'.format(title, house_id, count))

        response = post(url=dianping_url,
                        data={'city': '西安', 'dianpingNewcode': house_id, 'ifjiajing': 0, 'tid': '', 'page': 1,
                              'pagesize': count,
                              'starnum': 0, 'shtag': -1, 'rand': 0.8865550224456968})
        comment_list = response.json().get('list')
        write_usage_list = []
        for comment in comment_list:
            # 组装写入文件每行的内容
            formated_comment = comment.get('content').strip().replace('<br/>', '')
            write_usage = '[{0}]|[{1}]|[{2}]|{3}\n'.format(comment.get('user_id'), comment.get('username'),
                                                           comment.get('create_time'),
                                                           formated_comment)
            write_usage_list.append(write_usage)
        folder = os.path.join(os.getcwd(), 'fang_comments')
        if not os.path.exists(folder):
            os.mkdir(folder)
        with open(f'{folder}/{title}_[评论{count}条].txt', 'w') as f:
            f.writelines(write_usage_list)


def start():
    ucs = UserCommentSpider()
    page_total = ucs.fetch_index_page_size()
    logger.info('西安新房共有{}页'.format(page_total))
    # 开始循环每页所有房子
    with ThreadPoolExecutor(max_workers=page_total, thread_name_prefix='every_page') as executor:
        for current_page in range(1, page_total + 1):
            executor.submit(ucs.worker, page=current_page)
