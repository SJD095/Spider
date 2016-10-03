#!/usr/bin/python
# -*- coding: UTF-8 -*-

#SDCS of SYSU   Victor Sun
#2016-10-02     szy@sunzhongyang.com

import gzip
import re
import os
import sys
import time
import threading
import http.cookiejar
import urllib.request
import urllib.parse
import json

#人人网登陆URL
url = 'http://www.renren.com/PLogin.do'

header = {
    'Connection': 'Keep-Alive',
    'Accept': 'text/html, application/xhtml+xml, */*',
    'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.renren.com',
    'AllowAutoRedirect': 'false',
    'DNT': '1'
}

PostDict = {
        'email': None,
        'password': None,
        'autoLogin': 'true',
        "origURL": "http://www.renren.com/home",
        "domain": "renren.com",
        "key_id": "1",
        "captcha_type": "web_login"
}

#创建一个Opener, 自动处理Cookies
def buildOpener(head):
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    opener = urllib.request.build_opener(pro)
    header = []
    for key, value in head.items():
        elem = (key, value)
        header.append(elem)
    opener.addheaders = header
    urllib.request.install_opener(opener)

#解压数据
def ungzip(data):
    try:
        data = gzip.decompress(data)
    except:
        pass
    return data

#获取图片
def getPhotos(albumName, albumId):
    global ownerId, currentCount, NumberOfPhoto, OthersCount
    if os.path.exists(albumName):
        downloadDir = albumName + os.sep
    else:
        downloadDir = 'others' + os.sep

    AlbumLink = 'http://photo.renren.com/photo/'+ownerId+'/album-'+albumId+'/v7'
    AlbumPage=ungzip(urllib.request.urlopen(AlbumLink).read()).decode(encoding='UTF-8')
    PhotoIdRe = re.compile(r'"photoId":"(\d*?)",')
    if re.search(PhotoIdRe, AlbumPage) == None:
        print('Maybe album ' + albumName + ' is secret')
        return

    photoId = re.search(PhotoIdRe, AlbumPage).group(1)

    #获取含有所有图片URL的网址
    finalLink = 'http://photo.renren.com/photo/'+ownerId+'/photo-'+photoId+'/v7'
    finalPage=ungzip(urllib.request.urlopen(finalLink).read()).decode(encoding='UTF-8')
    photoLinkRe = re.compile(r'"largeurl":"(.*?)",')

    #去除重复的首张相片
    photoLinkList = re.findall(photoLinkRe, finalPage)[1:]

    #下载每一张图片
    for i,j in enumerate(photoLinkList):
        time.sleep(1)
        if j.count('\\')>0:
            j = j.replace('\\','')
        currentCount += 1;
        print(str(currentCount) + '/' + str(NumberOfPhoto) + ' ' + albumName + ' ' + j + '\n')
        try:
            if downloadDir == 'others' + os.sep:
                OthersCount += 1
                urllib.request.urlretrieve(j, downloadDir+'%d.jpg' % OthersCount)
            else:
                urllib.request.urlretrieve(j, downloadDir+'%d.jpg' % i)
        except BaseException:

            #如果下载出现错误，则在log中记录发生错误的图片的URL
            log = open("log.txt", "a", encoding='utf-8')
            log.write(j + '\n')
            log.close()
            print(str(currentCount) + ' ' + albumName + ' ' + j + ' ' + 'error')

            #中断五秒后继续开始
            time.sleep(5)
            continue

#获得日志列表
def getBlogData(id = 0):
    data = {
            'categoryId': 0,
            'curpage': id,
            }
    return urllib.parse.urlencode(data)

#从日志列表下载日志
def getBlogs(BlogsList):
    global ownerId

    #新建日志文件夹
    os.mkdir('Blogs')
    os.chdir('Blogs')
    basicBlogUrl = 'http://blog.renren.com/blog/' + ownerId + '/'
    for items in BlogsList:
        BlogUrl = basicBlogUrl + str(int(items[1]))
        req=urllib.request.Request(BlogUrl)
        HtmlObj=urllib.request.urlopen(req)
        PageData = HtmlObj.read()
        BlogPage = ungzip(PageData).decode(encoding='UTF-8')

        #通过正则表达式确定正文内容
        BlogContentRe = re.compile(r'<div class="blogDetail-text">(\n[\s\S]*)(<!--上一篇、下一篇-->)')
        BlogContent = re.findall(BlogContentRe, BlogPage)

        #以HTML形式将日志写入文件
        try:
            text = open(items[0] + '.html', 'w', encoding='utf-8')
            content = '<p>' + items[2] + '</p>\n'+ str(BlogContent[0][0]).replace('\\n', '')
            text.write(content)
            text.close()
            print(items[0] + ' have been successfuly downloaded')
        except BaseException:
            print('some error occured in Blog ' + items[0])

    #将目录切换回根目录
    os.chdir(RootPath)

#获取状态列表
def getStatusData(PageNumber):
    global ownerId
    data = {
            'userId' : ownerId,
            'curpage' : PageNumber
            }
    return urllib.parse.urlencode(data)

#保存状态到文件
def saveStatus(StatuList):
    page = open('Status.html', 'a', encoding='utf-8')
    for items in StatuList:

        #转发的状态
        if 'rootContent' in items:
            statu = items['dtime'] + '<br />' + items['content'] + '<br />' + items['rootContent'] + '<br /><br />'

        #原创的状态
        else:
            statu = items['dtime'] + '<br />' + items['content'] + '<br /><br /><br />'
        page.write(statu)

    print('one page of status have been downloaded')
    page.close()

#获取用户昵称
def getInfo(Id):
    global name

    InfoLink = 'http://www.renren.com/' + Id + '/profile?v=info_timeline'
    req=urllib.request.Request(InfoLink)
    HtmlObj=urllib.request.urlopen(req)
    PageData = HtmlObj.read()
    InfoPage = ungzip(PageData).decode(encoding='UTF-8')

    InfoRe = re.compile(r'<title>([\s\S]*?)</title>')
    InfoContent = re.findall(InfoRe, InfoPage)

    name = InfoContent[0]
    print(InfoContent)

#构造opener
buildOpener(header)

#登陆
while True:
    try:
        PostDict['email'] = input("请输入您的人人网账号： ").strip()
        PostDict['password'] = input("请输入您的账号密码： ").strip()
        postData = urllib.parse.urlencode(PostDict).encode()
        req = urllib.request.Request(url, postData)

        #登陆首页
        HtmlObj=urllib.request.urlopen(req)
    except:
        print("登陆账号或密码不正确！请重新输入！")
    else:
        print('正在登陆人人网服务器获取相册及相片信息，请稍等...\n')
        break

#获取用户ID
#ownerId=HtmlObj.geturl()[22:]
ownerId='587377841'

name = ''
getInfo(ownerId)

#新建并切换到目录
if name != '':
    try:
        os.mkdir(name)
        os.chdir(name)
    except BaseException:
        os.mkdir('RenRen')
        os.chdir('RenRen')
else:
    os.mkdir('RenRen')
    os.chdir('RenRen')

#获取当前路径
RootPath = os.getcwd()

#获取全部状态
StatusLink = 'http://status.renren.com/GetSomeomeDoingList.do'
PageNumber = 0
os.mkdir('Status')
os.chdir('Status')

PageUrl = StatusLink + '?' + getStatusData(PageNumber)
req=urllib.request.Request(PageUrl)
HtmlObj=urllib.request.urlopen(req)
PageData = HtmlObj.read()
StatusListPage = ungzip(PageData).decode(encoding='UTF-8')

#将JSON格式的状态信息转换为字典
StatusDict = json.loads(StatusListPage)
StatusList = StatusDict['doingArray']

#读取下一页的状态
while len(StatusList) != 0:
    saveStatus(StatusList)
    PageNumber += 1
    PageUrl = StatusLink + '?' + getStatusData(PageNumber)
    req=urllib.request.Request(PageUrl)
    HtmlObj=urllib.request.urlopen(req)
    PageData = HtmlObj.read()
    StatusListPage = ungzip(PageData).decode(encoding='UTF-8')
    StatusDict = json.loads(StatusListPage)
    StatusList = StatusDict['doingArray']

os.chdir(RootPath)

#获取全部日志

BlogsLink = 'http://blog.renren.com/blog/' + ownerId + '/blogs?'
PageNumber = 0
BlogIds = []

PageUrl = BlogsLink + getBlogData(PageNumber)
req=urllib.request.Request(PageUrl)
HtmlObj=urllib.request.urlopen(req)
PageData = HtmlObj.read()
BlogsListPage = ungzip(PageData).decode(encoding='UTF-8')
print(BlogsListPage)
BlogsDict = json.loads(BlogsListPage)

#下载每一页的日志
while len(BlogsDict['data']) != 0:
    for items in BlogsDict['data']:
            BlogIds.append((items['title'], items['id'], items['createTime']))
    PageNumber += 1
    PageUrl = BlogsLink + getBlogData(PageNumber)
    req=urllib.request.Request(PageUrl)
    HtmlObj=urllib.request.urlopen(req)
    PageData = HtmlObj.read()
    BlogsListPage = ungzip(PageData).decode(encoding='UTF-8')
    BlogsDict = json.loads(BlogsListPage)

getBlogs(BlogIds)

#获取全部照片

albumsLink = 'http://photo.renren.com/photo/'+ownerId+'/albumlist/v7#'

tag = True
cnt = 0

while tag and cnt < 60:
    tag = False

    req = urllib.request.Request(albumsLink)
    HtmlObj = urllib.request.urlopen(req)
    data = HtmlObj.read()

    #获取相册首页代码
    AlbumsPage = ungzip(data).decode(encoding='UTF-8')

    #正则 获取相册名
    albumsNameRe = re.compile('"albumName":"(.*?)","albumId"') #重复元字符后加？表示：匹配的非贪婪模式
    AlbumsList = re.findall(albumsNameRe,AlbumsPage)
    print(AlbumsList)

    #如果相册名字中包含 \\u (unicode未正常转码) 则跳出此循环，然后重新请求一次。
    for i in AlbumsList:
        if i.count('\\u') > (cnt / 3):
            cnt += 1
            tag = True
            break

#正则 获取相册ID
AlbumsIdRe = re.compile(r'"albumId":"(.*?)","ownerId"')
AlbumsId = re.findall(AlbumsIdRe,AlbumsPage)

#正则 获取每个相册的相片数量
PhotoCountRe = re.compile(r'"photoCount":(\d*?),')
PhotoCount = re.findall(PhotoCountRe, AlbumsPage)

print(AlbumsList)
print(PhotoCount)

#初始相片总数
NumberOfPhoto = 0
for i in PhotoCount:
    NumberOfPhoto += int(i)

#从AlbumsList和AlbumsId中剔除相片数为0的项，从而避免下载异常
for i in PhotoCount:
    if i == '0':
        index = PhotoCount.index(i)

        #标记非法的相册
        AlbumsList[index] = 'illegal'
        AlbumsId[index] = 'illegal'
        PhotoCount[index] = '-1'

ListId = []
for album, ids in zip(AlbumsList, AlbumsId):
    if album != 'illegal':

        #避免相册名为类似'......'格式而导致文件夹无法被创建的情况
        if album.find('.', 0) != -1:
            album = '(' + album + ')'
        ListId.append((album, ids))

print(ListId);

tmp_count = 2;
tmp_list = []

#创建相册文件夹
os.mkdir('Photo')
os.chdir('Photo')
os.mkdir('others')

#避免重名相册
for album, ids in ListId:
    if album not in tmp_list:
        tmp_list.append(album)
        try:
            os.mkdir(album)
        except BaseException:
            print('make direction ' + album + ' failed')
            album = 'illegal'

    else:
        tmp_count += 1;
        album += str(tmp_count)
        tmp_list.append(album)
        try:
            os.mkdir(album)
        except BaseException:
            print('make direction ' + album + ' failed')
            album = 'illegal'

currentCount = 0;
OthersCount = 0

#下载每张照片
for i, j in ListId:
    if i != 'illegal':
        getPhotos(i, j)

#重新下载之前下载失败的图片到others文件夹中
if os.path.exists(log.txt):
    log = open("log.txt", "r")
    LogContent = log.read()
    urls = LogContent.split('\n')

    for url in urls:
        try:
            OthersCount += 1
            urllib.request.urlretrieve(url, 'others'+ os.sep + str(OthersCount) + '.jpg' )
        except BaseException:
            print(url + ' downloaded failed')
