from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os


def get_rank_image(url="http://192.168.1.16:8000/scoreboard") -> bytes:
    """
    从 CTFd 榜单页面抓取排行榜并生成图片，返回图片字节流 (bytes)
    """
    try:
        req = requests.get(url, verify=False, timeout=10)
    except Exception as e:
        return b""

    soup = BeautifulSoup(req.text, "lxml")
    table = soup.find("table", class_="table")

    if not table:
        return b""

    data = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        rank = row.find("th").get_text(strip=True)
        username = cols[0].get_text(strip=True)
        score = cols[1].get_text(strip=True)
        data.append((int(rank), username, int(score)))

    if not data:
        return b""

    # ========== 生成图片 ==========
    title = "排行榜"
    font_path = "C:/Windows/Fonts/msyh.ttc"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

    font_size = 32
    line_height = 50
    margin = 50
    bg_color = (245, 245, 245)
    text_color = (30, 30, 30)

    font = ImageFont.truetype(font_path, font_size)
    title_font = ImageFont.truetype(font_path, font_size + 10)

    width = 800
    height = margin * 2 + line_height * (len(data) + 2)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 标题
    try:
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_w = title_bbox[2] - title_bbox[0]
    except AttributeError:
        title_w, _ = draw.textsize(title, font=title_font)

    draw.text(((width - title_w) / 2, margin // 2), title, font=title_font, fill=(0, 0, 0))

    # 表头
    header_y = margin + 30
    draw.text((margin, header_y), "排名", font=font, fill=text_color)
    draw.text((margin + 100, header_y), "昵称", font=font, fill=text_color)
    draw.text((margin + 500, header_y), "分数", font=font, fill=text_color)

    # 绘制数据
    y = header_y + line_height
    for rank, name, score in data:
        if rank == 1:
            color = (255, 215, 0)
        elif rank == 2:
            color = (192, 192, 192)
        elif rank == 3:
            color = (205, 127, 50)
        else:
            color = text_color

        draw.text((margin, y), str(rank), font=font, fill=color)
        draw.text((margin + 100, y), str(name), font=font, fill=color)
        draw.text((margin + 500, y), str(score), font=font, fill=color)
        y += line_height

    # 保存到字节流
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()


def get_rank(target="http://192.168.1.16:8000/scoreboard"):
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


@register("get-iseal-ctf-rank", "le", "iseal-ctf", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    @filter.command("black_switch")
    async def my_switch(self, event: AstrMessageEvent):

        token = "ctfd_ee743880fb2a711d8bb91ba5f1e6557e608b1fe6337477c966915ca36c2b9f28"
        headers = {"Authorization": f"Token {token}"}

        res = requests.get("http://192.168.1.16:8000/scoreboard/")
        if res.status_code == 404:
            payload = {"challenge_visibility": "private", "account_visibility": "public", "score_visibility": "public",
                       "registration_visibility": "public"}

            requests.patch("http://192.168.1.16:8000/api/v1/configs", headers=headers, json=payload)
            yield event.plain_result("关闭黑灯")
            return

        else:
            payload = {"challenge_visibility": "private", "account_visibility": "public", "score_visibility": "hidden",
                       "registration_visibility": "public"}

            requests.patch("http://192.168.1.16:8000/api/v1/configs", headers=headers, json=payload)
            yield event.plain_result("开启黑灯")
            return

    @filter.command("rank")
    async def helloworld(self, event: AstrMessageEvent):
        """get iseal-ctf rank"""  # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。

        res = requests.get("http://192.168.1.16:8000/scoreboard/")
        if res.status_code == 404:
            yield event.plain_result("黑灯咯，玩一会吧")
            return

        img_bytes = get_rank_image()
        if img_bytes:
            with open("/tmp/ranking.png", "wb") as f:
                f.write(img_bytes)

        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.image_result("/tmp/ranking.png")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
