# -*- coding: UTF-8 -*-
# Copyright (c) 2023 ZianTT
import json
import os
import threading
import time

import kdl

import requests
from loguru import logger

from api import BilibiliHyg
from globals import *

import inquirer

from i18n import i18n

common_project_id = [
    {"name": "上海·BilibiliWorld 2024", "id": 85939},
    {"name": "上海·BILIBILI MACRO LINK 2024", "id": 85938}
]

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
        logger.error(i18n["zh"]["data_error"])
        if os.path.exists("share.json"):
            logger.info(i18n["zh"]["migrate_share"])
            with open("share.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                save(data)
            os.remove("share.json")
            os.remove("data")
        else:
            data = {}
            os.remove("data")
        logger.info(i18n["zh"]["has_destroyed"])
    return data

def run(hyg):
    if hyg.config["mode"] == 'direct':
        while True:
            if hyg.try_create_order():
                if "hunter" not in hyg.config:
                    hyg.sdk.capture_message("Pay success!")
                    logger.success(i18n["zh"]["pay_success"])
                    return
                else:
                    hyg.config['hunter'] += 1
                    save(hyg.config)
                    logger.success(i18n["zh"]["hunter_prompt"].format(hyg.config['hunter']))
    elif hyg.config["mode"] == 'detect':
        while 1:
            hyg.risk = False
            if hyg.risk:
                status = -1
            status, clickable = hyg.get_ticket_status()
            if status == 2 or clickable:
                if status == 1:
                    logger.warning("喵，现在还不能买票呢喵~要不晚点再回来看看喵？")
                elif status == 3:
                    logger.warning("票已经卖完了喵")
                elif status == 5:
                    logger.warning("现在是不可售喵，也许过会儿就会公布了喵！")
                elif status == 102:
                    logger.warning("这个演出已经卖完票了，主人好像来晚了喵...")
                while True:
                    if hyg.try_create_order():
                        if "hunter" not in hyg.config:
                            hyg.sdk.capture_message("Pay success!")
                            logger.success("入场券GET☆DAZE")
                            return
                        else:
                            hyg.config['hunter'] += 1
                            save(hyg.config)
                            logger.success(f"主人，你也就抢了区区{hyg.config['hunter']}张票喵")
                break
            elif status == 1:
                logger.warning("喵，现在还不能买票呢喵~要不晚点再回来看看喵？")
            elif status == 3:
                logger.warning("票已经卖完了喵")
            elif status == 4:
                logger.warning("票已经卖完了喵")
            elif status == 5:
                logger.warning("现在是不可售喵，也许过会儿就会公布了喵！")
            elif status == 6:
                logger.error("这张票好像是免费的喵，还用得着本喵出场吗喵~")
                sentry_sdk.capture_message("Exit by in-app exit")
                return
            elif status == 8:
                logger.warning("看上去没票了喵...但是本喵闻到了余票的味道~")

            elif status == -1:
                continue
            else:
                logger.error("本喵发现了一条主人没告诉我的状态喵...B站告诉我是这个" + str(status))
            time.sleep(hyg.config["status_delay"])
    elif hyg.config["mode"] == 'time':
        logger.info("根据主人的设定，现在是定时抢票模式喵！")
        logger.info("本喵会帮你看着的喵...")
        while hyg.get_time() < hyg.config["time"]-60:
            time.sleep(10)
            logger.info(f"好困...怎么还有{hyg.config['time'] - get_time():.2f}秒啊喵呜..")
        logger.info("本喵闻到了票的味道！马上开始喵！")# Heads up, the wheels are spinning...
        while True:
            if hyg.get_time() >= hyg.config["time"]:
                break
        while True:
            if hyg.try_create_order():
                if "hunter" not in hyg.config:
                    hyg.sdk.capture_message("Pay success!")
                    logger.success("入场券GET☆DAZE")
                    return
                else:
                    hyg.config['hunter'] += 1
                    save(hyg.config)
                    logger.success(f"主人，你也就抢了区区{hyg.config['hunter']}张票喵")


def main():
    easter_egg = False
    logger.info(i18n["zh"]["start_up"])
    global uid
    try:
        version, sentry_sdk = init()
        session = requests.session()

        check_update(version)

        config = load_config()
        headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/618.1.15.10.15 (KHTML, like Gecko) Mobile/21F90 BiliApp/77900100 os/ios model/iPhone 15 mobi_app/iphone build/77900100 osVer/17.5.1 network/2 channel/AppStore c_locale/zh-Hans_CN s_locale/zh-Hans_CH disable_rcmd/0",
                "Cookie": config["cookie"],
        }
        if "user-agent" in config:
            headers["User-Agent"] = config["user-agent"]
        session = requests.Session()
        if "mode" not in config:
            mode_str = prompt([inquirer.List("mode", message=i18n["zh"]["choose_mode"], choices=[
                i18n["zh"]["mode_time"], i18n["zh"]["mode_direct"], i18n["zh"]["mode_detect"]
            ], default=i18n["zh"]["mode_time"])])["mode"]
            if mode_str == i18n["zh"]["mode_direct"]:
                config["mode"] = 'direct'
                logger.info(i18n["zh"]["mode_direct_on"])
            elif mode_str == i18n["zh"]["mode_detect"]:
                config["mode"] = 'detect'
                logger.info(i18n["zh"]["mode_detect_on"])
            else:
                config["mode"] = 'time'
                logger.info(i18n["zh"]["mode_time_on"])
        if "status_delay" not in config and config["mode"] == 'detect':
            config["status_delay"] = float(prompt([
                inquirer.Text(
                    "status_delay",
                    message=i18n["zh"]["input_status_delay"],
                    default="0.2",
                    validate=lambda _, x: float(x) >= 0
                )])["status_delay"])
        if "proxy" not in config:
            choice = prompt([inquirer.List("proxy", message=i18n["zh"]["input_is_use_proxy"], choices=[i18n["zh"]["yes"], i18n["zh"]["no"]], default=i18n["zh"]["no"])])["proxy"]
            if choice == i18n["zh"]["yes"]:
                while True:
                    config["proxy_auth"] = prompt([
                        inquirer.Text("proxy_auth", message=i18n["zh"]["input_proxy"],validate=lambda _, x: len(x.split(" ")) == 3)
                    ])["proxy_auth"].split(" ")
                    config["proxy_channel"] = prompt([
                        inquirer.Text("proxy_channel", message=i18n["zh"]["input_proxy_channel"], validate=lambda _, x: x.isdigit())
                    ])["proxy_channel"]
                    config["proxy"] = True
                    break
            else:
                config["proxy"] = False
        kdl_client = None
        if config["proxy"] == True:
            auth = kdl.Auth(config["proxy_auth"][0], config["proxy_auth"][1])
            kdl_client = kdl.Client(auth)
            session.proxies = {
                "http": config["proxy_auth"][2],
                "https": config["proxy_auth"][2],
            }
            if config["proxy_channel"] != "0":
                headers["kdl-tps-channel"] = config["proxy_channel"]
            session.keep_alive = False
            session.get("https://show.bilibili.com")
            logger.info(
                i18n["zh"]["test_proxy"].format(kdl_client.tps_current_ip(sign_type="hmacsha1"))
            )
        if "again" not in config:
            choice = prompt([inquirer.List("again", message=i18n["zh"]["input_is_allow_again"], choices=[i18n["zh"]["yes"], i18n["zh"]["no"]], default=i18n["zh"]["yes"])])["again"]
            if choice == i18n["zh"]["no"]:
                config["again"] = False
            else:
                config["again"] = True
        if (
            "project_id" not in config
            or "screen_id" not in config
            or "sku_id" not in config
            or "pay_money" not in config
            or "id_bind" not in config
        ):
            while True:
                logger.info(i18n["zh"]["common_project_id"])
                for i in range(len(common_project_id)):
                    logger.info(
                        common_project_id[i]["name"]
                        + " id: "
                        + str(common_project_id[i]["id"])
                    )
                if len(common_project_id) == 0:
                    logger.info(i18n["zh"]["empty"])
                config["project_id"] = prompt([
                    inquirer.Text("project_id", message=i18n["zh"]["input_project_id"], validate=lambda _, x: x.isdigit())
                ])["project_id"]
                url = (
                    "https://show.bilibili.com/api/ticket/project/getV2?version=134&id="
                    + config["project_id"]
                )
                response = session.get(url, headers=headers)
                if response.status_code == 412:
                    logger.error(i18n["zh"]["not_handled_412"])
                    if config["proxy"]:
                        logger.info(
                            i18n["zh"]["manual_change_ip"].format(
                                kdl_client.change_tps_ip(sign_type="hmacsha1")
                            )
                        )
                        session.close()
                response = response.json()
                if response["errno"] == 3:
                    logger.error(i18n["zh"]["project_id_not_found"])
                    continue
                if response["data"] == {}:
                    logger.error(i18n["zh"]["server_no_response"])
                    continue
                if response["data"]["is_sale"] == 0:
                    logger.info(i18n["zh"]["project_name"].format(response["data"]["name"]))
                    logger.error(i18n["zh"]["not_salable"])
                    continue
                break
            logger.info(i18n["zh"]["project_name"].format(response["data"]["name"]))
            config["id_bind"] = response["data"]["id_bind"]
            config["is_paper_ticket"] = response["data"]["has_paper_ticket"]
            screens = response["data"]["screen_list"]
            screen_id = prompt([
                inquirer.List("screen_id", message="请告诉本喵你要去哪一天喵", choices=[f"{i}. {screens[i]['name']}" for i in range(len(screens))])
            ])["screen_id"].split(".")[0]
            logger.info("场次：" + screens[int(screen_id)]["name"])
            tickets = screens[int(screen_id)]["ticket_list"]  # type: ignore
            sku_id = prompt([
                inquirer.List("sku_id", message="请告诉本喵你有多少钱喵", choices=[f"{i}. {tickets[i]['desc']} {tickets[i]['price']/100}元" for i in range(len(tickets))])
            ])["sku_id"].split(".")[0]
            logger.info("票档：" + tickets[int(sku_id)]["desc"])
            config["screen_id"] = str(screens[int(screen_id)]["id"])
            config["sku_id"] = str(tickets[int(sku_id)]["id"])
            config["pay_money"] = str(tickets[int(sku_id)]["price"])
            config["ticket_desc"] = str(tickets[int(sku_id)]["desc"])
            config["time"] = int(tickets[int(sku_id)]["saleStart"])
            if tickets[int(sku_id)]["discount_act"] is not None:
                logger.info(f"这个活动好像有优惠喵！ID {tickets[int(sku_id)]['discount_act']['act_id']}")
                config["act_id"] = tickets[int(sku_id)]["discount_act"]["act_id"]
                config["order_type"] = tickets[int(sku_id)]["discount_act"]["act_type"]
            else:
                config["order_type"] = "1"
            if config["is_paper_ticket"]:
                if response["data"]["express_free_flag"]:
                    config["express_fee"] = 0
                else:
                    config["express_fee"] = response["data"]["express_fee"]
                url = "https://show.bilibili.com/api/ticket/addr/list"
                resp_ticket = session.get(url, headers=headers)
                if resp_ticket.status_code == 412:
                    logger.error(i18n["zh"]["not_handled_412"])
                    if config["proxy"]:
                        logger.info(
                            i18n["zh"]["manual_change_ip"].format(
                                kdl_client.change_tps_ip(sign_type="hmacsha1")
                            )
                        )
                        session.close()
                addr_list = resp_ticket.json()["data"]["addr_list"]
                if len(addr_list) == 0:
                    logger.error("本喵还不知道你住在哪里呢喵，打开B站添加一个喵！")
                else:
                    addr = prompt([
                        inquirer.List("addr", message="告诉本喵你的地址喵", choices=[{"name": f"{i}. {addr_list[i]['prov']+addr_list[i]['city']+addr_list[i]['area']+addr_list[i]['addr']} {addr_list[i]['name']} {addr_list[i]['phone']}", "value": i} for i in range(len(addr_list))])
                    ])["addr"].split(".")[0]
                    addr = addr_list[int(addr)]
                    logger.info(
                        f"已选择收货地址：{addr['prov']+addr['city']+addr['area']+addr['addr']} {addr['name']} {addr['phone']}"
                    )
                    config["deliver_info"] = json.dumps(
                        {
                            "name": addr["name"],
                            "tel": addr["phone"],
                            "addr_id": addr["addr"],
                            "addr": addr["prov"]
                            + addr["city"]
                            + addr["area"]
                            + addr["addr"],
                        },
                        ensure_ascii=False,
                    )
            logger.debug(
                "您的screen_id 和 sku_id 和 pay_money 分别为："
                + config["screen_id"]
                + " "
                + config["sku_id"]
                + " "
                + config["pay_money"]
            )
            logger.debug("您的开始销售时间为：" + str(config["time"]))
        if config["id_bind"] != 0 and ("buyer_info" not in config):
            url = "https://show.bilibili.com/api/ticket/buyer/list"
            response = session.get(url, headers=headers)
            if response.status_code == 412:
                logger.error(i18n["zh"]["not_handled_412"])
            buyer_infos = response.json()["data"]["list"]
            config["buyer_info"] = []
            if len(buyer_infos) == 0:
                logger.error("主人的信息也要瞒着我吗？打开B站添加一下喵~")
            else:
                multiselect = True
            if config["id_bind"] == 1:
                logger.info("这个漫展只能一个人去喵...")
                multiselect = False
            if multiselect:
                buyerids = prompt([
                    inquirer.Checkbox(
                        "buyerids",
                        message="请选择购票人",
                        choices=[f"{i}. {buyer_infos[i]['name']} {buyer_infos[i]['personal_id']} {buyer_infos[i]['tel']}" for i in range(len(buyer_infos))],
                        validate=lambda _, x: len(x) > 0
                    )
                ])["buyerids"]
                buyerids = [int(i.split(".")[0]) for i in buyerids]
                config["buyer_info"] = []
                female = False
                male = False
                for select in buyerids:
                    config["buyer_info"].append(
                        buyer_infos[int(select)]
                    )  # type: ignore
                    # type: ignore
                    logger.info(
                        "已选择购票人" + buyer_infos[int(select)]["name"] + " " + buyer_infos[int(select)]["personal_id"] + " " + buyer_infos[int(select)]["tel"]
                    )
                    if int(buyer_infos[int(select)]["personal_id"][16]) % 2 == 0:
                        female = True
                    else:
                        male = True
                if easter_egg:
                    if len(buyerids) == 1:
                        logger.info("你好像只有一个人喵，好孤单喵")
                    else:
                        if male and female:
                            logger.error("主人是和对象一起去的吗喵？不要抛弃本喵喵...")
                        elif male and not female:
                            logger.error("喵！主人是南通吗？")
                            if len(buyerids) == 4:
                                logger.error("喵喵喵！？这么多人陪主人去看漫展喵？")
                        elif female and not male:
                            logger.error("喵！主人是女铜吗？")
            else:
                index = prompt([
                    inquirer.List("index", message="请选择购票人", choices=[f"{i}. {buyer_infos[i]['name']} {buyer_infos[i]['personal_id']} {buyer_infos[i]['tel']}" for i in range(len(buyer_infos))])
                ])["index"]
                config["buyer_info"].append(buyer_infos[int(index.split(".")[0])])
                logger.info("已选择购票人" + config["buyer_info"][0]["name"] + " " + config["buyer_info"][0]["personal_id"] + " " + config["buyer_info"][0]["tel"])
            if "count" not in config:
                config["count"] = len(config["buyer_info"])
            config["buyer_info"] = json.dumps(config["buyer_info"])
        if config["id_bind"] == 0 and (
            "buyer" not in config or "tel" not in config
        ):
            logger.info("请告诉本喵主人的信息喵！")
            config["buyer"] = input("联系人姓名：")
            config["tel"] = prompt([
                inquirer.Text("tel", message="联系人手机号", validate=lambda _, x: len(x) == 11)
            ])["tel"]
            if "count" not in config:
                config["count"] = prompt([
                    inquirer.Text("count", message="请输入票数", default="1",validate=lambda _, x: x.isdigit() and int(x) > 0)
                ])["count"]
        if config["is_paper_ticket"]:
            if config["express_fee"] == 0:
                config["all_price"] = int(config["pay_money"]) * int(
                    config["count"]
                )
                logger.info(
                    f"共 {config['count']} 张 {config['ticket_desc']} 票，单张价格为 {int(config['pay_money'])/100}，纸质票，邮费免去，总价为{config['all_price'] / 100}"
                )
            else:
                config["all_price"] = (
                    int(config["pay_money"]) * int(config["count"])
                    + config["express_fee"]
                )
                logger.info(
                    f"共 {config['count']} 张 {config['ticket_desc']} 票，单张价格为 {int(config['pay_money'])/100}，纸质票，邮费为 {config['express_fee'] / 100}，总价为{config['all_price'] / 100}"
                )
        else:
            config["all_price"] = int(config["pay_money"]) * int(
                config["count"]
            )
            logger.info(
                f"共 {config['count']} 张 {config['ticket_desc']} 票，单张价格为 {int(config['pay_money'])/100}，总价为{config['all_price'] / 100}"
            )
        save(config)
        sentry_sdk.capture_message("config complete")
        BHYG = BilibiliHyg(config, sentry_sdk, kdl_client, session)
        run(BHYG)
    except KeyboardInterrupt:
        logger.info("你手动打断了本喵的工作喵，本喵会记住你的喵")
        return
    except Exception as e:
        track = sentry_sdk.capture_exception(e)
        logger.exception("本喵出现错误了喵...：" + str(e))
        logger.error("虽然不懂错误追踪ID是什么喵，但是开发者说可以提供给他喵：" + str(track))
        return
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("你手动打断了本喵的工作喵，本喵会记住你的喵")
    from sentry_sdk import Hub
    client = Hub.current.client
    if client is not None:
        client.close(timeout=2.0)
    logger.info("算了喵，主人可以关闭窗口了喵（或者本喵会在15秒后自动退下的喵）")
    try:
        time.sleep(15)
    except KeyboardInterrupt:
        pass
