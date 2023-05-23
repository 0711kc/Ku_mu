import discord
from discord.ext import commands
from selenium.webdriver.chrome.service import Service
from youtube_dl import YoutubeDL
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from discord.utils import get
from discord import Embed, FFmpegPCMAudio
from discord.ui import Button, View, Select
import bs4
import asyncio
from urllib import request
from webdriver_manager.chrome import ChromeDriverManager


#channel = open("channel", "r").readline() # 채널 ID 가져오기
token = open("token","r").readline()      # 디스코드 봇의 토큰 가져오기

bot = commands.Bot(command_prefix='%',intents=discord.Intents.all())
client = discord.Client(intents = discord.Intents.default())

user = []       # 유저가 입력한 노래 정보
musictitle = [] # 가공한 정보의 노래 제목
song_queue = [] # 가공한 정보의 노래 링크
musicnow = []   # 현재 출력되는 노래
username = []   # 노래를 입력한 사용자 이름
duration = []   # 가공한 정보의 노래 길이
#linkList = []  # 가공한 정보의 유튜브 링크

message_time = 8 # 메세지를 보내고 지우는 시간 간격

bot_musics = ["즐거운", "신나는", "활기찬", "슬픈", "가슴 아픈", "눈물겨운", "잔잔한", "어두운", "지루한", "졸린", "빠른"]

# 봇이 사용할 버튼 목록
bt_play = Button(label="재생/일시정지", emoji="⏯️", style = discord.ButtonStyle.green, row = 0)
bt_skip = Button(label="넘어가기", emoji="⏭️", style = discord.ButtonStyle.green, row = 0)
bt_show = Button(label="대기열", emoji="📶", style = discord.ButtonStyle.green, row = 0)
bt_reset = Button(label="대기열 초기화", emoji="🔁",  row = 1)
bt_leave = Button(label="내보내기", emoji="✖️", style = discord.ButtonStyle.danger, row = 1)
bt_whatSong = Button(label="재생중인 노래", emoji="🎵", style = discord.ButtonStyle.green, row = 0)

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
        await interaction.response.defer()
        if vc.is_playing():
            vc.pause()
            status = await ch.send(embed = discord.Embed(title= "일시정지", description = musicnow[0] + "을(를) 일시정지 했습니다.", color = 0x00ff00))
        else:
            try:
                vc.resume()
            except:
                status = await ch.send("재생하고 있는 노래가 없습니다.")
            else:
                status = await ch.send(embed = discord.Embed(title= "다시재생", description = musicnow[0]  + "을(를) 다시 재생했습니다.", color = 0x00ff00))
        await asyncio.sleep(message_time)
        await status.delete()

    # 넘어가기 버튼 callback 함수
    async def callback_skip(interaction):
        await interaction.response.defer()
        try:
            vc.pause()
            status = await ch.send(embed = discord.Embed(title= "넘어가기", description = username[0] + "님이 신청하신 " + musicnow[0]  + "을(를) 종료했습니다.", color = 0x00ff00))
            await asyncio.sleep(message_time)
            await status.delete()
            play_next()
        except:
            pass

    # 대기열 초기화 버튼 callback 함수
    async def callback_reset(interaction):
        await interaction.response.defer()
        if len(musicnow) > 1:
            del user[:]
            del song_queue[:]
            for i in range(len(musicnow)-1):
                try:
                    del musicnow[1]
                    del musictitle[1]
                except:
                    pass
            status = await ch.send(embed = discord.Embed(title= "목록초기화", description = """목록이 정상적으로 초기화되었습니다. 이제 노래를 등록해볼까요?""", color = 0x00ff00))
        elif len(musicnow) == 1:
            status = await ch.send("대기열에 노래가 존재하지 않습니다.")
        else:
            status = await ch.send("아직 아무 노래도 등록하지 않았어요.")
        await asyncio.sleep(message_time)
        await status.delete()

    # 퇴장 버튼 callback 함수
    async def callback_leave(interaction):
        await interaction.response.defer()
        await bot.voice_clients[0].disconnect()

    # 대기열 목록 확인 버튼 callback 함수
    async def callback_show(interaction):
        await interaction.response.defer()
        if len(musictitle) == 0:
            status = await ch.send("아직 아무 노래도 등록하지 않았어요.")
        else:
            global Text
            for i in range(len(musictitle)):
                if i == 0:
                    Text = "재생중인 노래 : " + str(musictitle[i]) + " | " + str(duration[i]) + "\n신청자 : " + username[i]
                else:
                    Text = Text + "\n" + str(i) + ". " + str(musictitle[i]) + " | " + str(duration[i]) + "\n  신청자 : " + username[i]
                
            status = await ch.send(embed = discord.Embed(title= "노래목록", description = Text.strip(), color = 0x00ff00))
        await asyncio.sleep(message_time)
        await status.delete()

    # 재생 중인 노래 확인 버튼 callback 함수
    async def callback_whatSong(interaction):
        await interaction.response.defer()
        if len(musicnow) == 0:
            status = await ch.send("현재 재생중인 노래가 없습니다.")
        else:
            status = await ch.send(embed = discord.Embed(title= "재생중인 노래", description = str(musictitle[0]) + " | " + str(duration[0]) + "\n신청자 : " + username[0], color = 0x00ff00))
        await asyncio.sleep(message_time)
        await status.delete()

    bt_play.callback = callback_play
    bt_skip.callback = callback_skip
    bt_reset.callback = callback_reset
    bt_leave.callback = callback_leave
    bt_show.callback = callback_show
    bt_whatSong.callback = callback_whatSong

    view = View(timeout=None)
    view.add_item(bt_play)
    view.add_item(bt_skip)
    view.add_item(bt_whatSong)
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
            status = await ctx.channel.send("음성 채널에 접속 후 이용해주세요.")
            await asyncio.sleep(message_time)
            await status.delete()
            return
        else:
            try:
                global vc
                vc = await ctx.author.voice.channel.connect()
                if len(musicnow) > 0:
                    play_next()
            except:
                await vc.move_to(ctx.author.voice.channel)
            

        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        await ctx.delete()
        temp = await ch.send(str(ctx.content) + " 음악을 찾는 중입니다...")

        if len(musicnow) == 0:      # 재생하고 있는 노래가 없는 경우
            if 'https://www.youtube.com/' in str(ctx.content):
                result, URLTEST = url_music(ctx.content)
            else:
                result, URLTEST = title(ctx.content)
            
            if result is None:
                return

            try:
                await temp.delete()
                username.append(str(ctx.author))
                vc.play(discord.FFmpegPCMAudio(URLTEST,**FFMPEG_OPTIONS), after=lambda e: play_next())
            except:
                await temp.delete()
                status = await ch.send(str(ctx.content) + "을(를) 재생하는 과정에서 오류가 발생하였습니다. 다시 입력해주세요.")
                await asyncio.sleep(message_time)
                await status.delete()
                return
            
            status = await ch.send(embed = discord.Embed(title= "노래 재생", description = "현재 " + result + "을(를) 재생하고 있습니다. | " + str(duration[int(len(duration)-1)]) + "\n신청자 : " + username[0], color = 0x00ff00))
            await asyncio.sleep(message_time)
            await status.delete()
        
        else:     # 재생하고 있는 노래가 있는 경우
            if 'https://www.youtube.com/' in ctx.content:
                result, URLTEST = url_music(ctx.content)
            else:
                result, URLTEST = title(ctx.content)

            if result is None:
                status = await ch.send(str(ctx.content) + "을(를) 재생하는 과정에서 오류가 발생하였습니다. 다시 입력해주세요.")
                await asyncio.sleep(message_time)
                await status.delete()
                return
            
            await temp.delete()
            user.append(ctx.content)
            song_queue.append(URLTEST)
            username.append(str(ctx.author))
            #status = await ctx.channel.send(result + "을(를) 재생목록에 추가했어요! 신청자 : " + str(ctx.author))
            status = await ch.send(embed = discord.Embed(title= "대기열 추가", description = result + "을(를) 재생목록에 추가했어요! | " + str(duration[int(len(duration)-1)]) + "\n신청자 : " + str(ctx.author), color = 0x00ff00))
            await asyncio.sleep(message_time)
            await status.delete()

    await bot.process_commands(ctx)

# 제목을 입력받고 링크와 이름을 반환하는 함수
def title(msg):

    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True', 'youtube_include_dash_manifest': False , 'quiet': False, 'default_search': 'ytsearch', 'postprocessor': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]}

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument('--log-level=1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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

        aria = entireNum["aria-label"].split()
        temp_duration = aria[len(aria)-4] + " " + aria[len(aria)-3]
        duration.append(temp_duration)

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
    options.add_argument('--log-level=1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(msg)

    source = driver.page_source

    bs = bs4.BeautifulSoup(source, 'lxml')
    try:
        entire = bs.find_all('span', class_='ytp-time-duration')
        time = entire[0].get_text().split(":")
        if len(time) > 2:
            temp_duration = (time[0] +"시간 " + time[1] + "분")
        else:
            temp_duration = time[0] + "분 " + time[1] + "초"

        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(msg, download=False)
        URL = info['formats'][0]['url']
        title = info.get("title", None)
        musicnow.append(title)
        musictitle.append(title)
        duration.append(temp_duration)

        driver.quit()
        return title, URL
    except:
        return None, None

def play_next():
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    
    if len(musicnow) > 1:       # 대기열에 노래가 존재하는 경우
        try:
            del musicnow[0]
            del username[0]
            del user[0]
            del musictitle[0]
            URL = song_queue[0]
            del song_queue[0]
            vc.play(discord.FFmpegPCMAudio(URL,**FFMPEG_OPTIONS), after=lambda e: play_next())
        except:
            pass
    elif len(musicnow) == 1:
        try:
            del musictitle[0]
            del musicnow[0]
            del username[0]
            bot.loop.create_task(vc.disconnect())
        except:
            pass

@bot.command()
async def 정밀검색(ctx, msg):
    rinklist = [0,0,0,0]              # 검색된 노래의 링크들
    entireText = ["","","",""]       # 검색된 노래의 제목들
    temp_duration = ["","","",""]                # 검색된 노래의 길이들
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument('--log-level=1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.youtube.com/results?search_query="+msg+"+lyrics")

    source = driver.page_source
    bs = bs4.BeautifulSoup(source, 'lxml')
    entire = bs.find_all('a', {'id': 'video-title'})
    
    driver.quit()

    select = Select(
        min_values = 1,
        max_values = 4,
        placeholder = "재생하고 싶은 영상을 선택해주세요."
    )

    embed = discord.Embed(title = "검색한 영상들입니다.", color = 0x00ff00)

    for i in range(0, 4):
        text = ""
        entireNum = entire[i]
        test1 = entireNum.get('href')  # 하이퍼링크
        entireText[i] = entireNum.text.strip()  # 영상제목
        rinklist[i] = 'https://www.youtube.com'+test1
        aria = entire[i]["aria-label"].split()
        for j in aria:
            if "분" in j or "초" in j:
                text = text + j + " "
        temp_duration[i] = text
        embed.add_field(name = str(i+1) + "번째 영상", value = entireText[i] + " | " + temp_duration[i], inline=False)
        embed.add_field(name = "", value = rinklist[i], inline=False)
        select.append_option(discord.SelectOption(label = str(i+1) + '번째 영상', description = entireText[i]))
    
    status1 = await ch.send(embed=embed)

    async def my_callback(interaction):
        await interaction.response.defer()
        text = ""
        count = 0

        if '1번째 영상' in select.values:
            musicnow.append(entireText[0])
            musictitle.append(entireText[0])
            duration.append(temp_duration[0])
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(rinklist[0], download=False)
            URL = info['formats'][0]['url']

            count = count + 1
            text = text + str(count) + ". " + entireText[0] + "\n"
            song_queue.append(URL)
            user.append(msg)
            username.append(str(ctx.author))

        if '2번째 영상' in select.values:
            musicnow.append(entireText[1])
            musictitle.append(entireText[1])
            duration.append(temp_duration[1])
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(rinklist[1], download=False)
            URL = info['formats'][0]['url']

            count = count + 1
            text = text + str(count) + ". " + entireText[1] + "\n"
            song_queue.append(URL)
            user.append(msg)
            username.append(str(ctx.author))

        if '3번째 영상' in select.values:
            musicnow.append(entireText[2])
            musictitle.append(entireText[2])
            duration.append(temp_duration[2])
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(rinklist[2], download=False)
            URL = info['formats'][0]['url']

            count = count + 1
            text = text + str(count) + ". " + entireText[2] + "\n"
            song_queue.append(URL)
            user.append(msg)
            username.append(str(ctx.author))

        if '4번째 영상' in select.values:
            musicnow.append(entireText[3])
            musictitle.append(entireText[3])
            duration.append(temp_duration[3])
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(rinklist[3], download=False)
            URL = info['formats'][0]['url']

            count = count + 1
            text = text + str(count) + ". " + entireText[3] + "\n"
            song_queue.append(URL)
            user.append(msg)
            username.append(str(ctx.author))
        
        await status1.delete()
        await status2.delete()
        status = await ch.send(embed = discord.Embed(title= "추가한 영상들입니다.", description = text.strip(), color = 0x00ff00))
        await asyncio.sleep(message_time)
        await status.delete()


    select.callback = my_callback
    view = View()
    view.add_item(select)

    status2 = await ch.send(view = view)

bot.run(token)