# 导入所需的库
import json
import subprocess
import traceback
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import aiohttp
import langid

import openai
import pygame
from bilibili_api import live, sync

# 读取配置文件信息
with open("config.json", "r", encoding='utf-8') as jsonfile:
    config_data = json.load(jsonfile)

# 设置会话初始值
session_config = {'msg': [{"role": "system", "content": config_data['chatgpt']['preset']}]}
sessions = {}
current_key_index = 0

# 配置 OpenAI API 和 Bilibili 直播间 ID
openai.api_base = config_data["api"]  # https://chat-gpt.aurorax.cloud/v1 https://api.openai.com/v1
room_id = config_data["room_display_id"]

# 初始化 Bilibili 直播间和 TTS 语音
room = live.LiveDanmaku(room_id)
tts_voice = config_data["tts_voice"]

# 配置文件对应的讲话人
speakers = {
    "\u7279\u522b\u5468 Special Week (Umamusume Pretty Derby)": 0,
    "\u65e0\u58f0\u94c3\u9e7f Silence Suzuka (Umamusume Pretty Derby)": 1,
    "\u4e1c\u6d77\u5e1d\u738b Tokai Teio (Umamusume Pretty Derby)": 2,
    "\u4e38\u5584\u65af\u57fa Maruzensky (Umamusume Pretty Derby)": 3,
    "\u5bcc\u58eb\u5947\u8ff9 Fuji Kiseki (Umamusume Pretty Derby)": 4,
    "\u5c0f\u6817\u5e3d Oguri Cap (Umamusume Pretty Derby)": 5,
    "\u9ec4\u91d1\u8239 Gold Ship (Umamusume Pretty Derby)": 6,
    "\u4f0f\u7279\u52a0 Vodka (Umamusume Pretty Derby)": 7,
    "\u5927\u548c\u8d64\u9aa5 Daiwa Scarlet (Umamusume Pretty Derby)": 8,
    "\u5927\u6811\u5feb\u8f66 Taiki Shuttle (Umamusume Pretty Derby)": 9,
    "\u8349\u4e0a\u98de Grass Wonder (Umamusume Pretty Derby)": 10,
    "\u83f1\u4e9a\u9a6c\u900a Hishi Amazon (Umamusume Pretty Derby)": 11,
    "\u76ee\u767d\u9ea6\u6606 Mejiro Mcqueen (Umamusume Pretty Derby)": 12,
    "\u795e\u9e70 El Condor Pasa (Umamusume Pretty Derby)": 13,
    "\u597d\u6b4c\u5267 T.M. Opera O (Umamusume Pretty Derby)": 14,
    "\u6210\u7530\u767d\u4ec1 Narita Brian (Umamusume Pretty Derby)": 15,
    "\u9c81\u9053\u592b\u8c61\u5f81 Symboli Rudolf (Umamusume Pretty Derby)": 16,
    "\u6c14\u69fd Air Groove (Umamusume Pretty Derby)": 17,
    "\u7231\u4e3d\u6570\u7801 Agnes Digital (Umamusume Pretty Derby)": 18,
    "\u9752\u4e91\u5929\u7a7a Seiun Sky (Umamusume Pretty Derby)": 19,
    "\u7389\u85fb\u5341\u5b57 Tamamo Cross (Umamusume Pretty Derby)": 20,
    "\u7f8e\u5999\u59ff\u52bf Fine Motion (Umamusume Pretty Derby)": 21,
    "\u7435\u7436\u6668\u5149 Biwa Hayahide (Umamusume Pretty Derby)": 22,
    "\u91cd\u70ae Mayano Topgun (Umamusume Pretty Derby)": 23,
    "\u66fc\u57ce\u8336\u5ea7 Manhattan Cafe (Umamusume Pretty Derby)": 24,
    "\u7f8e\u666e\u6ce2\u65c1 Mihono Bourbon (Umamusume Pretty Derby)": 25,
    "\u76ee\u767d\u96f7\u6069 Mejiro Ryan (Umamusume Pretty Derby)": 26,
    "\u96ea\u4e4b\u7f8e\u4eba Yukino Bijin (Umamusume Pretty Derby)": 28,
    "\u7c73\u6d74 Rice Shower (Umamusume Pretty Derby)": 29,
    "\u827e\u5c3c\u65af\u98ce\u795e Ines Fujin (Umamusume Pretty Derby)": 30,
    "\u7231\u4e3d\u901f\u5b50 Agnes Tachyon (Umamusume Pretty Derby)": 31,
    "\u7231\u6155\u7ec7\u59ec Admire Vega (Umamusume Pretty Derby)": 32,
    "\u7a3b\u8377\u4e00 Inari One (Umamusume Pretty Derby)": 33,
    "\u80dc\u5229\u5956\u5238 Winning Ticket (Umamusume Pretty Derby)": 34,
    "\u7a7a\u4e2d\u795e\u5bab Air Shakur (Umamusume Pretty Derby)": 35,
    "\u8363\u8fdb\u95ea\u8000 Eishin Flash (Umamusume Pretty Derby)": 36,
    "\u771f\u673a\u4f36 Curren Chan (Umamusume Pretty Derby)": 37,
    "\u5ddd\u4e0a\u516c\u4e3b Kawakami Princess (Umamusume Pretty Derby)": 38,
    "\u9ec4\u91d1\u57ce\u5e02 Gold City (Umamusume Pretty Derby)": 39,
    "\u6a31\u82b1\u8fdb\u738b Sakura Bakushin O (Umamusume Pretty Derby)": 40,
    "\u91c7\u73e0 Seeking the Pearl (Umamusume Pretty Derby)": 41,
    "\u65b0\u5149\u98ce Shinko Windy (Umamusume Pretty Derby)": 42,
    "\u4e1c\u5546\u53d8\u9769 Sweep Tosho (Umamusume Pretty Derby)": 43,
    "\u8d85\u7ea7\u5c0f\u6eaa Super Creek (Umamusume Pretty Derby)": 44,
    "\u9192\u76ee\u98de\u9e70 Smart Falcon (Umamusume Pretty Derby)": 45,
    "\u8352\u6f20\u82f1\u96c4 Zenno Rob Roy (Umamusume Pretty Derby)": 46,
    "\u4e1c\u701b\u4f50\u6566 Tosen Jordan (Umamusume Pretty Derby)": 47,
    "\u4e2d\u5c71\u5e86\u5178 Nakayama Festa (Umamusume Pretty Derby)": 48,
    "\u6210\u7530\u5927\u8fdb Narita Taishin (Umamusume Pretty Derby)": 49,
    "\u897f\u91ce\u82b1 Nishino Flower (Umamusume Pretty Derby)": 50,
    "\u6625\u4e4c\u62c9\u62c9 Haru Urara (Umamusume Pretty Derby)": 51,
    "\u9752\u7af9\u56de\u5fc6 Bamboo Memory (Umamusume Pretty Derby)": 52,
    "\u5f85\u517c\u798f\u6765 Matikane Fukukitaru (Umamusume Pretty Derby)": 55,
    "\u540d\u5c06\u6012\u6d9b Meisho Doto (Umamusume Pretty Derby)": 57,
    "\u76ee\u767d\u591a\u4f2f Mejiro Dober (Umamusume Pretty Derby)": 58,
    "\u4f18\u79c0\u7d20\u8d28 Nice Nature (Umamusume Pretty Derby)": 59,
    "\u5e1d\u738b\u5149\u73af King Halo (Umamusume Pretty Derby)": 60,
    "\u5f85\u517c\u8bd7\u6b4c\u5267 Matikane Tannhauser (Umamusume Pretty Derby)": 61,
    "\u751f\u91ce\u72c4\u675c\u65af Ikuno Dictus (Umamusume Pretty Derby)": 62,
    "\u76ee\u767d\u5584\u4fe1 Mejiro Palmer (Umamusume Pretty Derby)": 63,
    "\u5927\u62d3\u592a\u9633\u795e Daitaku Helios (Umamusume Pretty Derby)": 64,
    "\u53cc\u6da1\u8f6e Twin Turbo (Umamusume Pretty Derby)": 65,
    "\u91cc\u89c1\u5149\u94bb Satono Diamond (Umamusume Pretty Derby)": 66,
    "\u5317\u90e8\u7384\u9a79 Kitasan Black (Umamusume Pretty Derby)": 67,
    "\u6a31\u82b1\u5343\u4ee3\u738b Sakura Chiyono O (Umamusume Pretty Derby)": 68,
    "\u5929\u72fc\u661f\u8c61\u5f81 Sirius Symboli (Umamusume Pretty Derby)": 69,
    "\u76ee\u767d\u963f\u5c14\u4e39 Mejiro Ardan (Umamusume Pretty Derby)": 70,
    "\u516b\u91cd\u65e0\u654c Yaeno Muteki (Umamusume Pretty Derby)": 71,
    "\u9e64\u4e38\u521a\u5fd7 Tsurumaru Tsuyoshi (Umamusume Pretty Derby)": 72,
    "\u76ee\u767d\u5149\u660e Mejiro Bright (Umamusume Pretty Derby)": 73,
    "\u6a31\u82b1\u6842\u51a0 Sakura Laurel (Umamusume Pretty Derby)": 74,
    "\u6210\u7530\u8def Narita Top Road (Umamusume Pretty Derby)": 75,
    "\u4e5f\u6587\u6444\u8f89 Yamanin Zephyr (Umamusume Pretty Derby)": 76,
    "\u771f\u5f13\u5feb\u8f66 Aston Machan (Umamusume Pretty Derby)": 80,
    "\u9a8f\u5ddd\u624b\u7eb2 Hayakawa Tazuna (Umamusume Pretty Derby)": 81,
    "\u5c0f\u6797\u5386\u5947 Kopano Rickey (Umamusume Pretty Derby)": 83,
    "\u5947\u9510\u9a8f Wonder Acute (Umamusume Pretty Derby)": 85,
    "\u79cb\u5ddd\u7406\u4e8b\u957f President Akikawa (Umamusume Pretty Derby)": 86,
    "\u7dbe\u5730 \u5be7\u3005 Ayachi Nene (Sanoba Witch)": 87,
    "\u56e0\u5e61 \u3081\u3050\u308b Inaba Meguru (Sanoba Witch)": 88,
    "\u690e\u8449 \u7d2c Shiiba Tsumugi (Sanoba Witch)": 89,
    "\u4eee\u5c4b \u548c\u594f Kariya Wakama (Sanoba Witch)": 90,
    "\u6238\u96a0 \u61a7\u5b50 Togakushi Touko (Sanoba Witch)": 91,
    "\u4e5d\u6761\u88df\u7f57 Kujou Sara (Genshin Impact)": 92,
    "\u82ad\u82ad\u62c9 Barbara (Genshin Impact)": 93,
    "\u6d3e\u8499 Paimon (Genshin Impact)": 94,
    "\u8352\u6cf7\u4e00\u6597 Arataki Itto (Genshin Impact)": 96,
    "\u65e9\u67da Sayu (Genshin Impact)": 97,
    "\u9999\u83f1 Xiangling (Genshin Impact)": 98,
    "\u795e\u91cc\u7eeb\u534e Kamisato Ayaka (Genshin Impact)": 99,
    "\u91cd\u4e91 Chongyun (Genshin Impact)": 100,
    "\u6d41\u6d6a\u8005 Wanderer (Genshin Impact)": 102,
    "\u4f18\u83c8 Eula (Genshin Impact)": 103,
    "\u51dd\u5149 Ningguang (Genshin Impact)": 105,
    "\u949f\u79bb Zhongli (Genshin Impact)": 106,
    "\u96f7\u7535\u5c06\u519b Raiden Shogun (Genshin Impact)": 107,
    "\u67ab\u539f\u4e07\u53f6 Kaedehara Kazuha (Genshin Impact)": 108,
    "\u8d5b\u8bfa Cyno (Genshin Impact)": 109,
    "\u8bfa\u827e\u5c14 Noelle (Genshin Impact)": 112,
    "\u516b\u91cd\u795e\u5b50 Yae Miko (Genshin Impact)": 113,
    "\u51ef\u4e9a Kaeya (Genshin Impact)": 114,
    "\u9b48 Xiao (Genshin Impact)": 115,
    "\u6258\u9a6c Thoma (Genshin Impact)": 116,
    "\u53ef\u8389 Klee (Genshin Impact)": 117,
    "\u8fea\u5362\u514b Diluc (Genshin Impact)": 120,
    "\u591c\u5170 Yelan (Genshin Impact)": 121,
    "\u9e7f\u91ce\u9662\u5e73\u85cf Shikanoin Heizou (Genshin Impact)": 123,
    "\u8f9b\u7131 Xinyan (Genshin Impact)": 124,
    "\u4e3d\u838e Lisa (Genshin Impact)": 125,
    "\u4e91\u5807 Yun Jin (Genshin Impact)": 126,
    "\u574e\u8482\u4e1d Candace (Genshin Impact)": 127,
    "\u7f57\u838e\u8389\u4e9a Rosaria (Genshin Impact)": 128,
    "\u5317\u6597 Beidou (Genshin Impact)": 129,
    "\u73ca\u745a\u5bab\u5fc3\u6d77 Sangonomiya Kokomi (Genshin Impact)": 132,
    "\u70df\u7eef Yanfei (Genshin Impact)": 133,
    "\u4e45\u5c90\u5fcd Kuki Shinobu (Genshin Impact)": 136,
    "\u5bb5\u5bab Yoimiya (Genshin Impact)": 139,
    "\u5b89\u67cf Amber (Genshin Impact)": 143,
    "\u8fea\u5965\u5a1c Diona (Genshin Impact)": 144,
    "\u73ed\u5c3c\u7279 Bennett (Genshin Impact)": 146,
    "\u96f7\u6cfd Razor (Genshin Impact)": 147,
    "\u963f\u8d1d\u591a Albedo (Genshin Impact)": 151,
    "\u6e29\u8fea Venti (Genshin Impact)": 152,
    "\u7a7a Player Male (Genshin Impact)": 153,
    "\u795e\u91cc\u7eeb\u4eba Kamisato Ayato (Genshin Impact)": 154,
    "\u7434 Jean (Genshin Impact)": 155,
    "\u827e\u5c14\u6d77\u68ee Alhaitham (Genshin Impact)": 156,
    "\u83ab\u5a1c Mona (Genshin Impact)": 157,
    "\u59ae\u9732 Nilou (Genshin Impact)": 159,
    "\u80e1\u6843 Hu Tao (Genshin Impact)": 160,
    "\u7518\u96e8 Ganyu (Genshin Impact)": 161,
    "\u7eb3\u897f\u59b2 Nahida (Genshin Impact)": 162,
    "\u523b\u6674 Keqing (Genshin Impact)": 165,
    "\u8367 Player Female (Genshin Impact)": 169,
    "\u57c3\u6d1b\u4f0a Aloy (Genshin Impact)": 179,
    "\u67ef\u83b1 Collei (Genshin Impact)": 182,
    "\u591a\u8389 Dori (Genshin Impact)": 184,
    "\u63d0\u7eb3\u91cc Tighnari (Genshin Impact)": 186,
    "\u7802\u7cd6 Sucrose (Genshin Impact)": 188,
    "\u884c\u79cb Xingqiu (Genshin Impact)": 190,
    "\u5965\u5179 Oz (Genshin Impact)": 193,
    "\u4e94\u90ce Gorou (Genshin Impact)": 198,
    "\u8fbe\u8fbe\u5229\u4e9a Tartalia (Genshin Impact)": 202,
    "\u4e03\u4e03 Qiqi (Genshin Impact)": 207,
    "\u7533\u9e64 Shenhe (Genshin Impact)": 217,
    "\u83b1\u4f9d\u62c9 Layla (Genshin Impact)": 228,
    "\u83f2\u8c22\u5c14 Fishl (Genshin Impact)": 230,
    "User": 999,
    "\u4f0a\u5361\u6d1b\u65af": 1000,
    "\u89c1\u6708\u695a\u539f": 1001,
    "\u4e94\u6708\u7530\u6839\u7f8e\u9999\u5b50": 1002,
    "\u6a31\u4e95\u667a\u6811": 1003,
    "\u59ae\u59c6\u8299": 1004,
    "\u963f\u65af\u7279\u857e\u4e9a": 1005,
    "\u6a31\u4e95\u667a\u5b50": 1006,
    "\u5b88\u5f62\u82f1\u56db\u90ce": 1007
}

# 请求VITS接口获取合成后的音频路径
async def get_data(character="ikaros", language="日语", text="こんにちわ。", speed=1):
    # API地址
    API_URL = 'http://127.0.0.1:7860' + '/run/predict/'

    data_json = {
        "fn_index":0,
        "data":[
            "こんにちわ。",
            "ikaros",
            "日本語",
            1
        ],
        "session_hash":"mnqeianp9th"
    }

    if language == "中文" or language == "汉语":
        data_json["data"] = [text, character, "简体中文", speed]
    elif language == "英文" or language == "英语":
        data_json["data"] = [text, character, "English", speed]
    else:
        data_json["data"] = [text, character, "日本語", speed]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=API_URL, json=data_json) as response:
                result = await response.read()
                # print(result)
                ret = json.loads(result)
        return ret
    except Exception as e:
        print(e)
        return None

def chat(msg, sessionid):
    """
    ChatGPT 对话函数
    :param msg: 用户输入的消息
    :param sessionid: 当前会话 ID
    :return: ChatGPT 返回的回复内容
    """
    try:
        # 获取当前会话
        session = get_chat_session(sessionid)

        # 将用户输入的消息添加到会话中
        session['msg'].append({"role": "user", "content": msg})

        # 添加当前时间到会话中
        session['msg'][1] = {"role": "system", "content": "current time is:" + get_bj_time()}

        # 调用 ChatGPT 接口生成回复消息
        message = chat_with_gpt(session['msg'])

        # 如果返回的消息包含最大上下文长度限制，则删除超长上下文并重试
        if message.__contains__("This model's maximum context length is 4096 token"):
            del session['msg'][2:3]
            del session['msg'][len(session['msg']) - 1:len(session['msg'])]
            message = chat(msg, sessionid)

        # 将 ChatGPT 返回的回复消息添加到会话中
        session['msg'].append({"role": "assistant", "content": message})

        # 输出会话 ID 和 ChatGPT 返回的回复消息
        print("会话ID: " + str(sessionid))
        print("ChatGPT返回内容: ")
        print(message)

        # 返回 ChatGPT 返回的回复消息
        return message

    # 捕获异常并打印堆栈跟踪信息
    except Exception as error:
        traceback.print_exc()
        return str('异常: ' + str(error))


# 获取北京时间
def get_bj_time():
    """
    获取北京时间
    :return: 当前北京时间，格式为 '%Y-%m-%d %H:%M:%S'
    """
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)  # 获取当前 UTC 时间
    SHA_TZ = timezone(
        timedelta(hours=8),
        name='Asia/Shanghai',
    )
    beijing_now = utc_now.astimezone(SHA_TZ)  # 将 UTC 时间转换为北京时间
    fmt = '%Y-%m-%d %H:%M:%S'
    now_fmt = beijing_now.strftime(fmt)
    return now_fmt


def get_chat_session(sessionid):
    """
    获取指定 ID 的会话，如果不存在则创建一个新的会话
    :param sessionid: 会话 ID
    :return: 指定 ID 的会话
    """
    sessionid = str(sessionid)
    if sessionid not in sessions:
        config = deepcopy(session_config)
        config['id'] = sessionid
        config['msg'].append({"role": "system", "content": "current time is:" + get_bj_time()})
        sessions[sessionid] = config
    return sessions[sessionid]


def chat_with_gpt(messages):
    """
    使用 ChatGPT 接口生成回复消息
    :param messages: 上下文消息列表
    :return: ChatGPT 返回的回复消息
    """
    global current_key_index
    max_length = len(config_data['openai']['api_key']) - 1

    try:
        if not config_data['openai']['api_key']:
            return "请设置Api Key"
        else:
            # 判断是否所有 API key 均已达到速率限制
            if current_key_index > max_length:
                current_key_index = 0
                return "全部Key均已达到速率限制,请等待一分钟后再尝试"
            openai.api_key = config_data['openai']['api_key'][current_key_index]

        # 调用 ChatGPT 接口生成回复消息
        resp = openai.ChatCompletion.create(
            model=config_data['chatgpt']['model'],
            messages=messages
        )
        resp = resp['choices'][0]['message']['content']

    # 处理 OpenAIError 异常
    except openai.OpenAIError as e:
        if str(e).__contains__("Rate limit reached for default-gpt-3.5-turbo") and current_key_index <= max_length:
            current_key_index = current_key_index + 1
            print("速率限制，尝试切换key")
            return chat_with_gpt(messages)
        elif str(e).__contains__(
                "Your access was terminated due to violation of our policies") and current_key_index <= max_length:
            print("请及时确认该Key: " + str(openai.api_key) + " 是否正常，若异常，请移除")

            # 判断是否所有 API key 均已尝试
            if current_key_index + 1 > max_length:
                return str(e)
            else:
                print("访问被阻止，尝试切换Key")
                current_key_index = current_key_index + 1
                return chat_with_gpt(messages)
        else:
            print('openai 接口报错: ' + str(e))
            resp = "openai 接口报错: " + str(e)

    return resp


@room.on('DANMU_MSG')
async def on_danmaku(event):
    """
    处理直播间弹幕事件
    :param event: 弹幕事件数据
    """
    content = event["data"]["info"][1]  # 获取弹幕内容
    user_name = event["data"]["info"][2][1]  # 获取发送弹幕的用户昵称

    # 判断弹幕是否以句号或问号结尾，如果是则进行回复
    if content.endswith("。") or content.endswith("？") or content.endswith("?"):
        # 获取当前用户的会话
        session = get_chat_session(str(user_name))

        # 输出当前用户发送的弹幕消息
        print(f"[{user_name}]: {content}")

        # 调用 ChatGPT 接口生成回复消息
        prompt = f"{content}"
        response = chat(prompt, session)

        # 输出 ChatGPT 返回的回复消息
        print(f"[AI回复{user_name}]：{response}")

        # 使用 Edge TTS 生成回复消息的语音文件
        # cmd = f'edge-tts --voice {tts_voice} --text "{content}{response}" --write-media output.mp3'
        # subprocess.run(cmd, shell=True)

        character = "ikaros"
        # character = "妮姆芙"
        language = "日语"
        text = "こんにちわ。"
        speed = 1

        text = response

        # 语言检测 一个是语言，一个是概率
        language, score = langid.classify(text)

        # 自定义语言名称（需要匹配请求解析）
        language_name_dict = {"en": "英语", "zh": "中文", "jp": "日语"}  

        if language in language_name_dict:
            language = language_name_dict[language]
        else:
            language = "日语"  # 无法识别出语言代码时的默认值

        # print("language=" + language)

        # 调用接口合成语音
        data_json = await get_data(character, language, text, speed)
        # print(data_json)

        name = data_json["data"][1]["name"]
        # command = 'mpv.exe -vo null ' + name  # 播放音频文件
        # subprocess.run(command, shell=True)  # 执行命令行指令

        # 将 AI 回复记录到日志文件中
        with open("./log.txt", "a", encoding="utf-8") as f:
            f.write(f"[AI回复{user_name}]：{response}\n")

        # 播放生成的语音文件
        pygame.mixer.init()
        # pygame.mixer.music.load('output.mp3')
        pygame.mixer.music.load(name)

        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()


# 启动 Bilibili 直播间连接
sync(room.connect())