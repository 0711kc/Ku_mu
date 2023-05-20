import discord
from discord.ext import commands
from youtube_dl import YoutubeDL
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from discord.utils import get
from discord import Embed, FFmpegPCMAudio
from discord.ui import Button, View, Select
import bs4
import asyncio
from urllib import request
import requests


#channel = open("channel", "r").readline() # 채널 ID 가져오기
token = open("token","r").readline()      # 디스코드 봇의 토큰 가져오기

bot = commands.Bot(command_prefix='%',intents=discord.Intents.all())
client = discord.Client(intents = discord.Intents.default())

user = []       # 유저가 입력한 노래 정보
musictitle = [] # 가공한 정보의 노래 제목
song_queue = [] # 가공한 정보의 노래 링크
musicnow = []   # 현재 출력되는 노래
#username = []   # 노래를 입력한 사용자 이름

bot_musics = ["즐거운", "신나는", "활기찬", "슬픈", "가슴 아픈", "눈물겨운", "잔잔한", "어두운", "지루한", "졸린", "빠른"]

# 봇이 사용할 버튼 목록
bt_play = Button(label="재생/일시정지", emoji="⏯️", style = discord.ButtonStyle.green)
bt_skip = Button(label="넘어가기", emoji="⏭️", style = discord.ButtonStyle.green)
bt_show = Button(label="대기열", emoji="📶", style = discord.ButtonStyle.green)
bt_reset = Button(label="대기열 초기화", emoji="❌", style = discord.ButtonStyle.green)
bt_leave = Button(label="내보내기", emoji="🚫", style = discord.ButtonStyle.green)

# 상태 메시지 변경하는 함수
async def bot_presence(musics):
    while not client.is_closed():
        for m in musics:
            await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name=str(m + " 노래")))
            await asyncio.sleep(210) # 바뀌는 시간 초 단위 설정

@bot.event
async def on_ready():
    global ch
    ch = bot.get_channel(1105793581391810654)

    # 재생/일시정지 버튼 callback 함수
    async def callback_play(interaction):
        if vc.is_playing():
            vc.pause()
            await ch.send(embed = discord.Embed(title= "일시정지", description = musicnow[0] + "을(를) 일시정지 했습니다.", color = 0x00ff00))
        else:
            try:
                vc.resume()
            except:
                await ch.send("재생하고 있는 노래가 없습니다.")
            else:
                await ch.send(embed = discord.Embed(title= "다시재생", description = musicnow[0]  + "을(를) 다시 재생했습니다.", color = 0x00ff00))
        await interaction.response.defer()

    # 넘어가기 버튼 callback 함수
    async def callback_skip(interaction):
        try:
            vc.pause()
            YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            await ch.send(embed = discord.Embed(title= "넘어가기", description = musicnow[0]  + "을(를) 종료했습니다.", color = 0x00ff00))
            play_next()
        except:
            pass
        await interaction.response.defer()

    # 대기열 초기화 버튼 callback 함수
    async def callback_reset(interaction):
        ex = len(musicnow) - len(user)
        del user[:]
        del musictitle[:]
        del song_queue[:]
        while True:
            try:
                del musicnow[ex]
            except:
                break
        await ch.send(embed = discord.Embed(title= "목록초기화", description = """목록이 정상적으로 초기화되었습니다. 이제 노래를 등록해볼까요?""", color = 0x00ff00))
        await interaction.response.defer()

    # 퇴장 버튼 callback 함수
    async def callback_leave(interaction):
        await bot.voice_clients[0].disconnect()
        await interaction.response.defer()

    # 대기열 목록 확인 버튼 callback 함수
    async def callback_show(interaction):
        if len(musictitle) == 0:
            await ch.send("아직 아무노래도 등록하지 않았어요.")
        else:
            global Text
            Text = ""
            for i in range(len(musictitle)):
                Text = Text + "\n" + str(i + 1) + ". " + str(musictitle[i])
                
            await ch.send(embed = discord.Embed(title= "노래목록", description = Text.strip(), color = 0x00ff00))
        await interaction.response.defer()

    bt_play.callback = callback_play
    bt_skip.callback = callback_skip
    bt_reset.callback = callback_reset
    bt_leave.callback = callback_leave
    bt_show.callback = callback_show

    view = View(timeout=None)
    view.add_item(bt_play)
    view.add_item(bt_skip)
    view.add_item(bt_show)
    view.add_item(bt_reset)
    view.add_item(bt_leave)

    await ch.send(embed = discord.Embed(title='메뉴 선택하기',description="원하시는 버튼을 클릭해주세요", colour=discord.Colour.blue()), view=view)
    
    print("크뮤 봇이 실행되었습니다.")
    await bot_presence(bot_musics)

@bot.event
async def on_message(ctx):
    if ctx.author.bot: return None
    
    try:
        topic = ctx.channel.topic
    except:
        pass

    if topic is not None and '#주크박스' in topic:
        #노래봇이 음성 채널에 접속
        if ctx.author.voice is None:
            await ctx.channel.send("음성 채널에 접속 후 이용해주세요.")
            return
        else:
            try:
                global vc
                vc = await ctx.author.voice.channel.connect()
            except:
                await vc.move_to(ctx.author.voice.channel)

        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


        if len(musicnow) == 0:      # 재생하고 있는 노래가 없는 경우

            if 'https://www.youtube.com/' in str(ctx.content):
                print("URL 실행됨\n")
                result, URLTEST = url_music(ctx.content)
            else:
                result, URLTEST = title(ctx.content)
                print("title 실행됨\n")
            
            if result is None:
                return

            vc.play(discord.FFmpegPCMAudio(URLTEST,**FFMPEG_OPTIONS), after=lambda e: play_next())

            await ch.send(embed = discord.Embed(title= "노래 재생", description = "현재 " + result + "을(를) 재생하고 있습니다.", color = 0x00ff00))
        
        else:     # 재생하고 있는 노래가 있는 경우

            if 'https://www.youtube.com/' in ctx.content:
                result, URLTEST = url_music(ctx.content)
            else:
                result, URLTEST = title(ctx.content)

            if result is None:
                return
            
            user.append(ctx.content)
            song_queue.append(URLTEST)
            await ctx.channel.send(result + "를 재생목록에 추가했어요!")

    await bot.process_commands(ctx)

# 제목을 입력받고 링크와 이름을 반환하는 함수
def title(msg):

    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}

    options = webdriver.ChromeOptions()
    options.add_argument("headless")

    chromedriver_dir = r"C:\Users\0711k\Desktop\code\chromedriver_win32\chromedriver.exe"
    driver = webdriver.Chrome(chromedriver_dir, options = options)

    driver.get("https://www.youtube.com/results?search_query="+msg+"+lyrics")

    source = driver.page_source
    bs = bs4.BeautifulSoup(source, 'lxml')

    try:
        entire = bs.find_all('a', {'id': 'video-title'})
        entireNum = entire[0]
        entireText = entireNum.text.strip()
        musicnow.append(entireText)
        musictitle.append(entireText)

        musicurl = entireNum.get('href')
        url = 'https://www.youtube.com'+musicurl

        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['formats'][0]['url']

        driver.quit()
        return entireText, URL
    except:
        return None, None
    
# URL을 입력받고 링크와 이름을 반환하는 함수
def url_music(msg):
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}

    options = webdriver.ChromeOptions()
    options.add_argument("headless")

    chromedriver_dir = r"C:\Users\0711k\Desktop\code\chromedriver_win32\chromedriver.exe"
    driver = webdriver.Chrome(chromedriver_dir, options = options)

    driver.get(msg)

    source = driver.page_source

    bs = bs4.BeautifulSoup(source, 'html.parser')

    try:
        title = bs.select_one('meta[itemprop="name"][content]')['content']
        
        musicnow.append(title)
        musictitle.append(title)
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(msg, download=False)
        URL = info['formats'][0]['url']

        driver.quit()
        print(title,("\n"), URL)
        return title, URL
    except:
        return None, None

def play_next():
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    
    if len(musicnow) > 1:       # 대기열에 노래가 존재하는 경우
        try:
            del musicnow[0]
            URL = song_queue[0]
            del user[0]
            del musictitle[0]
            del song_queue[0]
            vc.play(discord.FFmpegPCMAudio(URL,**FFMPEG_OPTIONS), after=lambda e: play_next())
        except:
            pass
    elif len(musicnow) == 1:
        try:
            del musictitle[0]
            del musicnow[0]
            bot.loop.create_task(vc.disconnect())
        except:
            pass

def URLPLAY(sTitle, url):
    YDL_OPTIONS = {'format': 'bestaudio','noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    if len(musictitle) == 0:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['formats'][0]['url']
        vc.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        musictitle.append(sTitle)
        musicnow.append(sTitle)
    else:
        result, URLTEST = title(sTitle)
        musictitle.append(result)
        musicnow.append(result)
        song_queue.append(URLTEST)
        user.append(sTitle)

@bot.command()
async def 지금노래(ctx):
    if not vc.is_playing():
        await ctx.send("지금은 노래가 재생되지 않네요..")
    else:
        await ctx.send(embed = discord.Embed(title = "지금노래", description = "현재 " + musicnow[0] + "을(를) 재생하고 있습니다.", color = 0x00ff00))

bot.run(token)