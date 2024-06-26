# -*- coding: UTF-8 -*-
# Contains global variables


import sys
import os
import json 

import sentry_sdk
from loguru import logger
from sentry_sdk.integrations.loguru import LoggingLevels, LoguruIntegration

from login import *

import inquirer

from utility import utility

def prompt(prompt):
    data = inquirer.prompt(prompt)
    if data is None:
        raise KeyboardInterrupt
    return data

def save(data: dict):
    import base64
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    import machineid
    import json
    key = machineid.id().encode()[:16]
    cipher = AES.new(key, AES.MODE_CBC)
    cipher_text = cipher.encrypt(pad(json.dumps(data).encode("utf-8"), AES.block_size))
    data = base64.b64encode(cipher_text).decode("utf-8")
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    with open("data", "w", encoding="utf-8") as f:
        f.write(iv+"%"+data)
    return

def load() -> dict:
    import base64
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    import machineid
    import json
    key = machineid.id().encode()[:16]
    try:
        with open("data", "r", encoding="utf-8") as f:
            iv, data = f.read().split("%")
            iv = base64.b64decode(iv)
            cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = base64.b64decode(data)
        data = unpad(cipher.decrypt(cipher_text), AES.block_size).decode("utf-8")
        data = json.loads(data)
    except ValueError:
        logger.error("有问题喵！本喵正在删除错误的数据文件喵！")
        if os.path.exists("share.json"):
            logger.info("本喵好像找到了一个分享文件喵，正在恢复数据喵！")
            with open("share.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                save(data)
            os.remove("share.json")
            os.remove("data")
        else:
            data = {}
            os.remove("data")
        logger.info("原数据文件已删除喵！")
    return data

def agree_terms():
    while True:
        agree_prompt = input("欢迎使用抢票喵程序喵，使用前请阅读EULA喵(https://github.com/biliticket/BHYG)。若主人使用时遇到问题，请查阅biliticket文档喵(https://docs.bitf1a5h.eu.org/)\n抢票喵魔改版项目主页(https://github.com/duobuhui/BHYG-Miao/)当前基于0.7.7版本，commits:e7a6aa2\n特别提醒，根据EULA，严禁任何形式通过本软件盈利喵。若您同意本软件EULA，请向本喵承诺：我已阅读并同意EULA，黄牛倒卖狗死妈\n")
        if "同意" in agree_prompt and "死妈" in agree_prompt and "黄牛" in agree_prompt and "不" not in agree_prompt:
            break
        else:
            logger.error("你是不是黄牛派来的卧底喵！必须给本喵承诺喵！")
    with open("agree-terms", "w") as f:
        import machineid
        f.write(machineid.id())
    logger.info("已同意EULA喵")

def init():
    logger.remove(handler_id=0)
    if sys.argv[0].endswith(".py"):
        level = "DEBUG"
        format = "DEBUG MODE | <green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        environment = "development"
        print("WARNING: YOU ARE IN DEBUG MODE")
    else:
        level = "INFO"
        format = "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        environment = "production"
    handler_id = logger.add(
        sys.stderr,
        format=format,
        level=level,  # NOTE: logger level
    )

    if not os.path.exists("agree-terms"):
        agree_terms()
    else:
        with open("agree-terms", "r") as f:
            hwid = f.read()
            import machineid
            if hwid != machineid.id():
                agree_terms()
                with open("agree-terms", "w") as f:
                    f.write(machineid.id())
    version = "v0.7.7"

    sentry_sdk.init(
        dsn="https://9c5cab8462254a2e1e6ea76ffb8a5e3d@sentry-inc.bitf1a5h.eu.org/3",
        release=version,
        profiles_sample_rate=1.0,
        enable_tracing=True,
        integrations=[
            LoguruIntegration(
                level=LoggingLevels.DEBUG.value, event_level=LoggingLevels.CRITICAL.value
            ),
        ],
        sample_rate=1.0,
        environment=environment
    )
    with sentry_sdk.configure_scope() as scope:
        scope.add_attachment(path="data")

    import machineid
    sentry_sdk.set_user({"hwid": machineid.id()[:16]}) 
    return version, sentry_sdk


def check_update(version):
    try:
        import requests
        data = requests.get("https://api.github.com/repos/biliticket/BHYG/releases/latest", headers={"Accept": "application/vnd.github+json"}).json()
        if data["tag_name"] != version:
            
            import platform
            if platform.system() == "Windows":
                name = "BHYG-Windows"
            elif platform.system() == "Linux":
                name = "BHYG-Linux"
            elif platform.system() == "Darwin":
                print(platform.machine())
                if "arm" in platform.machine():
                    name = "BHYG-macOS-Apple_Silicon"
                elif "64" in platform.machine():
                    name = "BHYG-macOS-Intel"
                else:
                    name = "BHYG-macOS"
            else:
                name = "BHYG"
            find = False
            for distribution in data["assets"]:
                if distribution["name"] == name:
                    logger.warning(f"发现原始项目新版本{data['tag_name']}了喵，如果你想体验最新程序，请前往 {distribution['browser_download_url']} 下载喵，大小：{distribution['size']/1024/1024:.2f}MB喵。或者请等待抢票喵作者同步更新喵。")
                    if data['body'] != "":
                        logger.warning(f"这是原始项目的更新说明喵：{data['body']}")
                    find = True
                    break
            if not find:
                logger.warning(f"发现原始项目新版本{data['tag_name']}了喵，请前往{data['html_url']}查看喵。或者请等待抢票喵作者同步更新喵。")
    except:
        logger.warning("更新检查失败了喵，一定是哪里有问题喵！")
    

class HygException(Exception):
    pass


def load_config(): 
    go_utility = False
    if os.path.exists("config.json"):
        logger.info("感谢主人升级到最新版本了喵！现在正在为主人自动迁移旧版本数据喵...")
        if os.path.isdir("data"):
            import shutil
            shutil.rmtree("data")
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            save(config)
        os.remove("config.json")
        logger.info("迁移完成了喵")
    if os.path.exists("share.json"):
        logger.info("本喵好像找到了一个分享文件喵，正在恢复数据喵！")
        with open("share.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            save(config)
        os.remove("share.json")
    if os.path.isdir("data"):
        import shutil
        shutil.rmtree("data")
    if os.path.exists("data"):
        run_info = prompt([
            inquirer.List(
                "run_info",
                message="请选择运行设置喵",
                choices=["延续上次启动所有配置", "保留登录信息重新配置", "全新启动", "进入账户实用工具", "进入账户实用工具（重新登录）"],
                default="延续上次启动所有配置"
            )]
        )["run_info"]
        if run_info == "全新启动":
            logger.info("全新启动，但继承pushplus信息（若有）")
            temp = load()
            config = {}
            if "pushplus" in temp:
                config["pushplus"] = temp["pushplus"]
            if "ua" in temp:
                config["ua"] = temp["pushplus"]
            use_login = False
        elif run_info == "保留登录信息重新配置":
            logger.info("只沿用登录信息")
            temp = load()
            config = {}
            if "gaia_vtoken" in temp:
                config["gaia_vtoken"] = temp["gaia_vtoken"]
            if "ua" in temp:
                config["ua"] = temp["ua"]
            if "cookie" in temp:
                config["cookie"] = temp["cookie"]
            if "pushplus" in temp:
                config["pushplus"] = temp["pushplus"]
            use_login = True
        elif run_info == "延续上次启动所有配置":
            logger.info("使用上次的配置文件")
            config = load()
            use_login = True
        elif run_info == "进入账户实用工具":
            logger.info("进入账户实用工具")
            go_utility = True
            use_login = True
            config = load()
        elif run_info == "进入账户实用工具（重新登录）":
            logger.info("进入账户实用工具（重新登录）")
            go_utility = True
            use_login = False
            config = {}
    else:
        save({})
        config = {}
    import ntplib
    c = ntplib.NTPClient()
    skip = False
    try:
        response = c.request('ntp.sjtu.edu.cn')
    except Exception:
        logger.error("时间同步出现错误了喵，本喵将跳过时间检查喵")
        skip = True
    if skip == False:
        import time
        time_offset = response.offset
        if time_offset > 0.5:
            logger.warning(f"主人的系统时间有：{time_offset:.2f}秒的偏移喵，建议校准时间呢喵")
        config["time_offset"] = time_offset
    else:
        config["time_offset"] = 0
    while True:
            if "cookie" not in config or not use_login:
                config["cookie"] = interactive_login(sentry_sdk)
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/618.1.15.10.15 (KHTML, like Gecko) Mobile/21F90 BiliApp/77900100 os/ios model/iPhone 15 mobi_app/iphone build/77900100 osVer/17.5.1 network/2 channel/AppStore c_locale/zh-Hans_CN s_locale/zh-Hans_CH disable_rcmd/0",
                "Cookie": config["cookie"],
            }
            user = requests.get(
                "https://api.bilibili.com/x/web-interface/nav", headers=headers
            )
            user = user.json()
            if user["data"]["isLogin"]:
                logger.success("主人 " + user["data"]["uname"] + " 登录成功了喵！")
                if user["data"]["vipStatus"] == 1:
                    logger.info(f"主人居然是大会员喵，距离到期还有{(user['data']['vipDueDate']/1000-time.time())/60/60/24:.2f}天喵，好有钱喵！")
                import machineid
                sentry_sdk.set_user(
                    {
                        "username": user["data"]["mid"],
                        "hwid": machineid.id()[:16]
                    }
                )
                if "hunter" in config:
                    logger.success("已启用猎手模式喵")
                    logger.info(f"主人已经用本喵抢到了：{config['hunter']}张喵")  
                save(config)         
                break
            else:
                logger.error("登录失败了喵...")
                use_login = False
                config.pop("cookie")
                save(config)
    if go_utility:
        utility(config)
        return load_config()
    return config
