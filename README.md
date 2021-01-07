# ha_elec_balance

本插件用于从国家电网智能站上，读取电表余额。

**本插件只能运行在支持 ipv6 的网络上。因为如果通过 ipv4 的 ip 访问国网的网站，是有防抓取保护的。但是通过 ipv6 访问则一切正常。 **

### 环境搭建

由于没有搞定在 ha 的 docker 容器里可用的 chromedriver，因此，获取电表余额的脚本只能在宿主机上跑。
需要在宿主机上搭建运行环境，包括 python3、pip3、chromedriver、selenium、和 pillow
python3 和 pip3 的安装方法不细说了
chromedriver 可以去 chromium 的官网去下载最新版本: https://chromedriver.chromium.org/
如果是树莓派的话，可以通过 apt 安装

```shell
apt-get install chromium-chromedriver
```

然后安装依赖

```
pip3 install selenium pillow
```

去打码狗平台注册一个账号，先充个 1 块钱应该就足够用了: http://www.damagou.top/

然后去国网的网站注册个账号，绑定上家里的智能电表: http://www.95598.cn/member/login.shtml

打开 fetch.py，按照注释，配置好打码狗的用户名密码，和国网的用户名密码

然后就可以在宿主机运行 fetch.py 试试了。

一切顺利的话，打印出以下类似的 log，就说明成功了

```
[2021-01-07 09:07:07] resize window to 1920*1080
[2021-01-07 09:07:11] opened page:  http://www.95598.cn/member/login.shtml
[2021-01-07 09:07:12] ready to recognize captcha
[2021-01-07 09:07:16] begin to request damagou
[2021-01-07 09:07:26] request damagou timeout, retry
[2021-01-07 09:07:28] begin to request damagou
[2021-01-07 09:07:28] got response from damagou
[2021-01-07 09:07:28] recognized captcha: q9on
[2021-01-07 09:07:29] submit login
[2021-01-07 09:07:30] captcha error, attempt to relogin 5 seconds later
[2021-01-07 09:07:37] opened page:  http://www.95598.cn/member/login.shtml
[2021-01-07 09:07:38] ready to recognize captcha
[2021-01-07 09:07:39] begin to request damagou
[2021-01-07 09:07:40] got response from damagou
[2021-01-07 09:07:40] recognized captcha: n6q7
[2021-01-07 09:07:41] submit login
[2021-01-07 09:07:50] login success
[2021-01-07 09:07:55] opened balance page: http://www.95598.cn/95598/per/account/initSmartConsInfo?partNo=PM02001007
[2021-01-07 09:08:05] get balance timeout
[2021-01-07 09:08:07] opened balance page: http://www.95598.cn/95598/per/account/initSmartConsInfo?partNo=PM02001007
[2021-01-07 09:08:17] get balance timeout
[2021-01-07 09:08:18] opened balance page: http://www.95598.cn/95598/per/account/initSmartConsInfo?partNo=PM02001007
[2021-01-07 09:08:28] get balance timeout
[2021-01-07 09:08:29] opened balance page: http://www.95598.cn/95598/per/account/initSmartConsInfo?partNo=PM02001007
[2021-01-07 09:08:39] get balance timeout
[2021-01-07 09:08:42] opened balance page: http://www.95598.cn/95598/per/account/initSmartConsInfo?partNo=PM02001007
[2021-01-07 09:08:45] got balance: 81.8
```

然后需要配置一个 crontab，国网的余额数据据观察是一天才更新一次，所以不用抓取太频繁。我现在是每天早上 7，8，9 点各抓取一次。

```
7 7,8,9 * * * python3 /usr/share/hassio/homeassistant/custom_components/elec_balance/fetch.py 1>>/var/log/elec_balance.log 2>>/var/log/elec_balance_error.log
```

最后，在 ha 里面，添加一条配置

```
sensor:
  - platform: elec_balance
```

大功告成了！
