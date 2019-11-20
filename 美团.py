import requests
import time
import re
import csv
import random
from lxml import etree
from fake_useragent import UserAgent


def create_csv():
    '''
    创建 csv 并写入头信息
    :return:
    '''
    with open(r'zhuhai_meishi.csv','w+',encoding='utf-8',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['餐厅名','种类','地址','评分','人均','链接'])


def get_html(url):
    '''
    下载 html 页面
    :return:
    '''
    count = 0  # 计数
    while True:
        headers = {
            'User-Agent': UserAgent().random,
            'cookie' : '你的'
        }
        proxies = get_proxy() # 获得代理 ip
        try: # 使用代理后有时会连接失败
            response = s.get(url, headers=headers,proxies=proxies)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                return response
            else:
                count += 1  # 请求失败 + 1
                if count == 3:  # 失败 3 次休息 2 秒后返回空
                    time.sleep(2)
                    return
                continue
        except:
            pass


def get_proxy():
    '''
    阿布云代理：https://center.abuyun.com/
    获得代理
    :return:
    '''
    # 代理服务器
    proxyHost = "http-dyn.abuyun.com"
    proxyPort = "9020"

    # 代理隧道验证信息
    proxyUser = 'HYR4XR990DK7QU9D'
    proxyPass = '199DCF7B4246B823'

    proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        "host": proxyHost,
        "port": proxyPort,
        "user": proxyUser,
        "pass": proxyPass,
    }

    proxies = {
        "http": proxyMeta,
        "https": proxyMeta,
    }
    return proxies


def get_kind_url(response):
    '''
    提取各类美食的链接以 [(美食种类,链接)。。。] 返回
    :param response:
    :return:
    '''
    html = etree.HTML(response.text)
    # 提取了所有分类标签包括了，种类，区域，人数
    links = html.xpath('//ul[@class="more clear"]/li/a/@href')
    kinds = html.xpath('//ul[@class="more clear"]/li/a/text()')
    # 从标签中提取出种类，链接，以 [(美食种类,链接)。。。] 保存
    ls = []
    for kind,link in zip(kinds,links):
        if kind == '单人餐': # 只需要美食种类，其他区域，人数过滤
            break
        ls.append((kind,link))

    return ls


def get_info(data):
    '''
    提取数据逻辑
    :param data: (美食种类,此种类的第一页链接)
    :return:
    '''
    kind = data[0]
    link = data[1]

    # 因为不知道每种种类有多少页，直到爬到最后一页的下一页为空后，跳出循环
    p = 1  # 起始为第一页，用来翻页的
    print('正在爬取' + kind + '类美食')
    while True:
        url = link + 'pn' + str(p) + '/'
        response = get_html(url)
        s.cookies = response.cookies
        # 用来测试是否被反爬的，链接较长，说明是验证码的链接
        if len(response.url) > 42:
            print(kind + '类的' + str(p) + '页被反爬！正在重试。。')
            continue
        if response == None: # 请求失败跳过
            p += 1
            continue
        infos = get_data(response)
        if list(infos) == []: # 当提取最后一页的下一页为空，跳出
            break
        for info in infos: # 写入每一条信息
            write_to_csv(info,kind)
        time.sleep(1 + random.random())
        p += 1
    print(kind + '美食类已爬完!!!\n')


def get_data(response):
    '''
    提取数据
    :param response:
    :return:
    '''
    # 店家 id
    poiIds = re.findall('"poiId":(.*?),',response.text,re.S)
    # 提取到 id 后，构造每家的美团链接
    poiIdurls = []
    for poiId in poiIds:
        url = 'https://www.meituan.com/meishi/{}/'
        url = url.format(str(poiId))
        poiIdurls.append(url)
    # 店名
    titles = re.findall('"title":"(.*?)"',response.text,re.S)
    titles = titles[20:] # 剔除冗余信息
    # 人均
    avgPrices = re.findall('"avgPrice":(.*?),',response.text,re.S)
    # 评分
    avgScores = re.findall('"avgScore":(.*?),',response.text,re.S)
    # 地址
    addresses = re.findall('"address":"(.*?)"',response.text,re.S)

    return list(zip(titles,addresses,avgScores,avgPrices,poiIdurls))


def write_to_csv(info,kind):
    '''
    写入 csv 文件
    :param data:
    :return:
    '''
    # 把种类插入到第二个位置
    info = list(info)
    info.insert(1,kind)
    info[3] = info[3].replace('}','').replace(']','')
    info[4] = info[4].replace('}', '').replace(']', '')
    with open('zhuhai_meishi.csv','a+',encoding='utf-8',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(info)


if __name__ == '__main__':
    # 创建 csv
    create_csv()
    # 创建 session 会话
    s = requests.session()
    # 起始 url
    url = 'https://zh.meituan.com/meishi/'
    response = get_html(url)
    # 保存 cookie
    s.cookies = response.cookies
    # 从起始 url 的响应中提取各类美食的链接以 [(美食种类,链接)。。。] 返回
    data = get_kind_url(response)
    # 把 “代金券” 种类过滤掉
    data = data[1:]
    # 从每种种类的食物链接翻页提取信息
    for da in data:
        get_info(da)


