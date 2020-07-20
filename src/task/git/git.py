#!/usr/bin/env python3
# coding=utf-8
import requests
import random
import json
import time
import csv
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GithubCrawl:
    def __init__(self, git_host, git_api_host, user_name, password, keyword, api_token):
        self.git_host = git_host
        self.git_api_host = git_api_host
        self.user_name = user_name
        self.password = password
        self.keyword = keyword
        self.api_token = api_token
        self.user_agent_list = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]

        # 初始化一些必要的参数
        self.login_headers = {
            "Referer": 'https://' + git_host + '/',
            "Host": git_host,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
        }

        self.logined_headers = {
            "Referer": 'https://' + git_host + '/login',
            "Host": "github.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
        }

        self.login_url = 'https://' + git_host +'/login'
        self.post_url = 'https://' + git_host +'/session'
        self.session = requests.Session()

    def ua_headers(self):
        ua = random.choice(self.user_agent_list)  # 随机选用ua
        headers = {
            'Connection': 'close',  # 关闭长链接
            "User-Agent": ua,
            'Authorization': self.api_token
            # 'Content-Type': 'application/json',
            # 'Accept': 'application/json'
        }
        return headers

    def parse_loginpage(self):
        # 对登陆页面进行爬取，获取token值
        html = self.session.get(url=self.login_url, headers=self.login_headers, verify=False, timeout=5)
        soup = BeautifulSoup(html.text, "lxml")
        self.token = soup.find("input", attrs={"name": "authenticity_token"}).get("value")
        return self.token
    # 获得了登陆的一个参数

    def login(self):
        # 传进必要的参数，然后登陆
        post_data = {
            "commit": "Sign in",
            "utf8": "✓",
            "authenticity_token": self.parse_loginpage(),
            "login": self.user_name,
            "password": self.password
        }
        logined_html = self.session.post(url=self.post_url, data=post_data, headers=self.logined_headers, verify=False)
        if logined_html.status_code == 200:
            project_list = self.parse_keyword()
            return project_list

    def parse_keyword(self):
        # 解析登陆以后的页面，筛选出包含这个关键字的python代码
        user_repositorys = set()  # 集合用来存放作者名和库名
        project_list = list()
        try:
            for i in range(1):
                #url = "https://{git_host}/search?l=Python&p={id}&q={keyword}&type=Code".format(git_host=self.git_host, id=i + 1, keyword=self.keyword)  # 循环的爬取页面信息
                url = "https://{git_host}/search?p={id}&q={keyword}&type=Code".format(git_host=self.git_host,
                                                                                               id=i + 1,
                                                                                               keyword=self.keyword)  # 循环的爬取页面信息
                resp = self.session.get(url=url, headers=self.login_headers, verify=False)
                soup = BeautifulSoup(resp.text, 'lxml')
                for m in soup.find_all('a', class_='link-gray'):
                    item = str(m.get('href')).strip('/')

                    if item:
                        user_repositorys.add(item)
        except Exception as e:
            print(e)
        if len(user_repositorys) > 0:
            for user_repository in user_repositorys:
                user = user_repository.split('/')[0]
                project_info = self.get_results(user_repository, user)
                if project_info:
                    project_list.append(project_info)
                time.sleep(5)
        return project_list

    def get_results(self, repository, user):  # 用Github的官方API V3版本爬取数据，解析json
        #url = "https://{git_api_host}/search/code?q={keyword}+in:file+language:python+repo:{w}"\
            #.format(git_api_host=self.git_api_host, w=repository, keyword=self.keyword)  # 只是搜索语言为python的代码
        url = "https://{git_api_host}/search/code?q={keyword}+in:file+repo:{w}" \
            .format(git_api_host=self.git_api_host, w=repository, keyword=self.keyword)  # 只是搜索含有关键字的代码
        attempts = 0
        success = False
        headers = self.ua_headers()
        result_dict = dict()
        while attempts < 3 and not success:
            try:
                ret = requests.get(url, headers=headers, verify=False)
                result = json.loads(ret.text)
                result_dict['user'] = user
                result_dict['project_url'] = 'https://' + self.git_host + '/' + repository
                result_dict['match_num'] = result['total_count']
                file_path_list = list()
                for item in result['items']:
                    file_path = item['html_url']
                    file_path_list.append(file_path)
                    # fork = item["repository"]["fork"]
                result_dict['file_path_list'] = file_path_list
                success = True
            except Exception as e:
                attempts += 1
                print("获取失败: %s," % e, "重试三次")
                time.sleep(30)
                if attempts == 3:
                    break
        return result_dict


if __name__ == "__main__":
    x = GithubCrawl('git_host', 'git_api_host', 'user_name', 'password', 'keyword', 'api_token')
    x.login()