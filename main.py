import requests
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from bs4 import BeautifulSoup


def get_rank():
    target = "https://ctfd.iseal.ac.cn/scoreboard"
    req = requests.get(target, verify=False)
    soup = BeautifulSoup(req.text, "lxml")

    table = soup.find("table", class_="table")

    data = []

    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        rank = row.find("th").get_text(strip=True)
        username = cols[0].get_text(strip=True)
        score = cols[1].get_text(strip=True)
        data.append({
            "排名": int(rank),
            "用户名": username,
            "分数": int(score)
        })

    # 拼接为字符串
    result_lines = [f"{item['排名']:>2} | {item['用户名']:<20} | {item['分数']}" for item in data]
    result = "\n".join(result_lines)

    return result


@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("rank")
    async def helloworld(self, event: AstrMessageEvent):
        """get iseal-ctf rank"""  # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。

        msg = get_rank()

        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(msg)  # 发送一条纯文本消息

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
