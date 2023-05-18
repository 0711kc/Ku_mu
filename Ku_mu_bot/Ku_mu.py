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
import time
from urllib import request

channel = open("channel", "r").readline() # 디스코드 봇이 전달할 메시지의 채널 ID 가져오기
token = open("token","r").readline()      # 디스코드 봇의 토큰 가져오기

bot = commands.Bot(command_prefix='%',intents=discord.Intents.all())
client = discord.Client(intents = discord.Intents.default())

user = [] #유저가 입력한 노래 정보
musictitle = [] #가공한 정보의 노래 제목
song_queue = [] #가공한 정보의 노래 링크
musicnow = []   #현재 출력되는 노래

userF = []
userFlist = []
allplaylist = []

# 봇이 사용할 버튼 목록
button1 = Button(label="재생/일시정지", emoji="⏯️", style = discord.ButtonStyle.green)
button2 = Button(label="넘어가기", emoji="⏭️", style = discord.ButtonStyle.green)
button3 = Button(label="대기열 초기화", emoji="❌", style = discord.ButtonStyle.green)
button4 = Button(label="내보내기", emoji="🚫", style = discord.ButtonStyle.green)

@bot.event
async def on_ready():
    ch = bot.get_channel(channel)

    print("크뮤 봇이 실행되었습니다.")
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name="즐겁게 노래"))

    async def button_callback1(interaction):
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

    async def button_init(interaction):
        if not vc.is_playing():
            await ch.send("재생하고 있는 노래가 없습니다.")
        else:
            await ch.send("대기열에 노래가 없습니다.")
        await interaction.response.defer()

    async def button_callback3(interaction):
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

    async def button_callback4(interaction):
        await bot.voice_clients[0].disconnect()
        await interaction.response.defer()

    button1.callback = button_callback1
    button2.callback = button_init
    button3.callback = button_callback3
    button4.callback = button_callback4

    view = View(timeout=None)
    view.add_item(button1)
    view.add_item(button2)
    view.add_item(button3)
    view.add_item(button4)

    await ch.send(embed = discord.Embed(title='메뉴 선택하기',description="원하시는 버튼을 클릭해주세요", colour=discord.Colour.blue()), view=view)

@bot.event
async def on_message(ctx):
    if ctx.author.bot: return None
    topic = ctx.channel.topic
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

        YDL_OPTIONS = {'format': 'bestaudio','noplaylist':'True'}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


        if len(musicnow)<1: #노래가 추가되어 있지 않은 경우
            options = webdriver.ChromeOptions()
            options.add_argument("headless")

            chromedriver_dir = r"C:\Users\0711k\Desktop\code\chromedriver_win32\chromedriver.exe"
            driver = webdriver.Chrome(chromedriver_dir, options = options)

            if not 'https://' in ctx.content:
                driver.get("https://www.youtube.com/results?search_query="+ctx.content+"+lyrics")
            else:
                driver.get(ctx.content)
            
            source = driver.page_source
            bs = bs4.BeautifulSoup(source, 'lxml')
            if not 'https://' in ctx.content:
                entire = bs.find_all('a', {'id': 'video-title'})
                entireNum = entire[0]
                entireText = entireNum.text.strip()
                musicurl = entireNum.get('href')
                url = 'https://www.youtube.com'+musicurl
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
            else:
                entire = bs.find_all('yt-formatted-string', class_="style-scope ytd-watch-metadata")
                entireNum = entire[0]
                entireText = entireNum.text.strip()
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(ctx.content, download=False)
            
            driver.quit()
            musicnow.insert(0, entireText)

            URL = info['formats'][0]['url']
            vc.play(discord.FFmpegPCMAudio(URL,**FFMPEG_OPTIONS), after=lambda e:play_next(ctx))

            await ctx.channel.send(embed = discord.Embed(title= "노래 재생", description = "현재 " + musicnow[0] + "을(를) 재생하고 있습니다.", color = 0x00ff00))
        else:
            user.append(ctx.content)
            result, URLTEST = title(ctx.content)
            song_queue.append(URLTEST)
            await ctx.channel.send(result + "를 재생목록에 추가했어요!")

            async def button_callback2(interaction):
                vc.stop()
                YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
                FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                await ctx.channel.send(embed = discord.Embed(title= "넘어가기", description = musicnow[0]  + "을(를) 종료했습니다.", color = 0x00ff00))
                URL = song_queue[1]
                vc.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), after=lambda e: play_next(ctx)) 
                await interaction.response.defer()
        
            button2.callback = button_callback2
    entire = None
    await bot.process_commands(ctx)

@bot.command()
async def 공지(ctx, *, message=None):
    if ctx.author.bot: return None
    topic = ctx.channel.topic
    if topic is not None and '#뉴알파서버' in topic:
        embed = discord.Embed(title="뉴-알파서버", description=message, color=0x00ff00)

        thread = ctx.guild.get_thread()
        await thread.send (embed=embed)

@bot.command()
async def on(ctx):
    if ctx.author.bot: return None
    topic = ctx.channel.topic
    if topic is not None and '#뉴알파서버' in topic:
        await bot.change_presence(status=discord.Status.online, activity=discord.Game("🌐서버가 온라인 상태입니다....."))
        print("디스코드 봇 상태 메시지가 온라인으로 변경되었습니다.")

@bot.command()
async def off(ctx):
    if ctx.author.bot: return None
    topic = ctx.channel.topic
    if topic is not None and '#뉴알파서버' in topic:
        await bot.change_presence(status=discord.Status.online, activity=discord.Game("🚫서버가 오프라인 상태입니다....."))
        print("디스코드 봇 상태 메시지가 오프라인으로 변경되었습니다.")

@bot.command()
async def 나가(ctx):
    try:
        await bot.voice_clients[0].disconnect()
    except:
        await ctx.send("이미 그 채널에 속해있지 않아요.")

@bot.command()
async def 일시정지(ctx):
    if vc.is_playing():
        vc.pause()
        await ctx.send(embed = discord.Embed(title= "일시정지", description = musicnow[0] + "을(를) 일시정지 했습니다.", color = 0x00ff00))
    else:
        await ctx.send("지금 노래가 재생되지 않네요.")

@bot.command()
async def 다시재생(ctx):
    try:
        vc.resume()
    except:
         await ctx.send("지금 노래가 재생되지 않네요.")
    else:
         await ctx.send(embed = discord.Embed(title= "다시재생", description = musicnow[0]  + "을(를) 다시 재생했습니다.", color = 0x00ff00))

@bot.command()
async def 노래끄기(ctx):
    if vc.is_playing():
        vc.stop()
        await ctx.send(embed = discord.Embed(title= "노래끄기", description = musicnow[0]  + "을(를) 종료했습니다.", color = 0x00ff00))
    else:
        await ctx.send("지금 노래가 재생되지 않네요.")

def title(msg):
    global music

    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    options = webdriver.ChromeOptions()
    options.add_argument("headless")

    chromedriver_dir = r"C:\Users\0711k\Desktop\code\chromedriver_win32\chromedriver.exe"
    driver = webdriver.Chrome(chromedriver_dir, options = options)
    driver.get("https://www.youtube.com/results?search_query="+msg+"+lyrics")
    source = driver.page_source
    bs = bs4.BeautifulSoup(source, 'lxml')
    entire = bs.find_all('a', {'id': 'video-title'})
    entireNum = entire[0]
    music = entireNum.text.strip()
    
    musictitle.append(music)
    musicnow.append(music)
    test1 = entireNum.get('href')
    url = 'https://www.youtube.com'+test1
    with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
    URL = info['formats'][0]['url']

    driver.quit()
    
    return music, URL

def play(ctx):
    global vc
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    URL = song_queue[0]
    del user[0]
    del musictitle[0]
    del song_queue[0]
    vc = get(bot.voice_clients, guild=ctx.guild)
    if not vc.is_playing():
        vc.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), after=lambda e: play_next(ctx)) 

def play_next(ctx):
    if len(musicnow) - len(user) >= 2:
        for i in range(len(musicnow) - len(user) - 1):
            del musicnow[0]
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    if len(user) >= 1:
        if not vc.is_playing():
            del musicnow[0]
            URL = song_queue[0]
            del user[0]
            del musictitle[0]
            del song_queue[0]
            vc.play(discord.FFmpegPCMAudio(URL,**FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
    else:
        if not vc.is_playing():
            client.loop.create_task(vc.disconnect())

@bot.command()
async def 대기열추가(ctx, *, msg):
    user.append(ctx.content)
    result, URLTEST = title(ctx.content)
    song_queue.append(URLTEST)
    await ctx.channel.send(result + "를 재생목록에 추가했어요!")

@bot.command()
async def 대기열삭제(ctx, *, number):
    try:
        ex = len(musicnow) - len(user)
        del user[int(number) - 1]
        del musictitle[int(number) - 1]
        del song_queue[int(number)-1]
        del musicnow[int(number)-1+ex]
            
        await ctx.send("대기열이 정상적으로 삭제되었습니다.")
    except:
        if len(list) == 0:
            await ctx.send("대기열에 노래가 없어 삭제할 수 없어요!")
        else:
            if len(list) < int(number):
                await ctx.send("숫자의 범위가 목록개수를 벗어났습니다!")
            else:
                await ctx.send("숫자를 입력해주세요!")

@bot.command()
async def 목록(ctx):
    if len(musictitle) == 0:
        await ctx.send("아직 아무노래도 등록하지 않았어요.")
    else:
        global Text
        Text = ""
        for i in range(len(musictitle)):
            Text = Text + "\n" + str(i + 1) + ". " + str(musictitle[i])
            
        await ctx.send(embed = discord.Embed(title= "노래목록", description = Text.strip(), color = 0x00ff00))

@bot.command()
async def 목록초기화(ctx):
    try:
        ex = len(musicnow) - len(user)
        del user[:]
        del musictitle[:]
        del song_queue[:]
        while True:
            try:
                del musicnow[ex]
            except:
                break
        await ctx.send(embed = discord.Embed(title= "목록초기화", description = """목록이 정상적으로 초기화되었습니다. 이제 노래를 등록해볼까요?""", color = 0x00ff00))
    except:
        await ctx.send("아직 아무노래도 등록하지 않았어요.")

@bot.command()
async def 목록재생(ctx):

    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    
    if len(user) == 0:
        await ctx.send("아직 아무노래도 등록하지 않았어요.")
    else:
        if len(musicnow) - len(user) >= 1:
            for i in range(len(musicnow) - len(user)):
                del musicnow[0]
        if not vc.is_playing():
            play(ctx)
        else:
            await ctx.send("노래가 이미 재생되고 있어요!")

@bot.command()
async def 지금노래(ctx):
    if not vc.is_playing():
        await ctx.send("지금은 노래가 재생되지 않네요..")
    else:
        await ctx.send(embed = discord.Embed(title = "지금노래", description = "현재 " + musicnow[0] + "을(를) 재생하고 있습니다.", color = 0x00ff00))

@bot.command()
async def 멜론차트(ctx):
    if not vc.is_playing():
        
        options = webdriver.ChromeOptions()
        options.add_argument("headless")

        global entireText
        YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            
        chromedriver_dir = r"C:\Users\0711k\Desktop\code\chromedriver_win32\chromedriver.exe"
        driver = webdriver.Chrome(chromedriver_dir, options = options)
        driver.get("https://www.youtube.com/results?search_query=멜론차트")
        source = driver.page_source
        bs = bs4.BeautifulSoup(source, 'lxml')
        entire = bs.find_all('a', {'id': 'video-title'})
        entireNum = entire[0]
        entireText = entireNum.text.strip()
        musicurl = entireNum.get('href')
        url = 'https://www.youtube.com'+musicurl 

        driver.quit()

        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['formats'][0]['url']
        await ctx.send(embed = discord.Embed(title= "노래 재생", description = "현재 " + entireText + "을(를) 재생하고 있습니다.", color = 0x00ff00))
        vc.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
    else:
        await ctx.send("이미 노래가 재생 중이라 노래를 재생할 수 없어요!")

def URLPLAY(sTitle, url):
    YDL_OPTIONS = {'format': 'bestaudio','noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    if not vc.is_playing():
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['formats'][0]['url']
        vc.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        musictitle.append(sTitle)
        musicnow.append(sTitle)
    else:
        result, URLTEST = title(sTitle)
        song_queue.append(URLTEST)
        user.append(sTitle)

@bot.command()
async def 정밀검색(ctx, msg):
    Text = ""
    global rinklist
    rinklist = [0,0,0,0,0]

    global vc
    vc = await ctx.author.voice.channel.connect()

    YDL_OPTIONS = {'format': 'bestaudio','noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    
    options = webdriver.ChromeOptions()
    options.add_argument("headless")

    chromedriver_dir = r"C:\Users\0711k\Desktop\code\chromedriver_win32\chromedriver.exe"
    driver = webdriver.Chrome(chromedriver_dir, options = options)
    driver.get("https://www.youtube.com/results?search_query="+msg)

    source = driver.page_source
    bs = bs4.BeautifulSoup(source, 'lxml')
    entire = bs.find_all('a', {'id': 'video-title'})
    driver.quit()

    select = Select(
        min_values = 1,
        max_values = 4,
        placeholder = "재생하고 싶은 영상을 선택해주세요."
    )

    for i in range(0, 4):
        entireNum = entire[i]
        entireText = entireNum.text.strip()  # 영상제목
        test1 = entireNum.get('href')  # 하이퍼링크
        rinklist[i] = 'https://www.youtube.com'+test1
        Text = Text + str(i+1)+'번째 영상' + entireText +'\n링크 : '+ rinklist[i] + '\n'
        select.append_option(discord.SelectOption(label = str(i+1) + '번째 영상', description = entireText))
    
    await ctx.channel.send(embed = discord.Embed(title= "검색한 영상들입니다.", description = Text.strip(), color = 0x00ff00))

    async def my_callback(interaction):
        if '1번째 영상' in select.values:
            URLPLAY(entire[0].text.strip(), rinklist[0])
            await ctx.channel.send(entire[0].text.strip() + "를 재생목록에 추가했어요!\n" + rinklist[0])
        if '2번째 영상' in select.values:
            URLPLAY(entire[1].text.strip(), rinklist[1])
            await ctx.channel.send(entire[1].text.strip() + "를 재생목록에 추가했어요!\n" + rinklist[1])
        if '3번째 영상' in select.values:
            URLPLAY(entire[2].text.strip(), rinklist[2])
            await ctx.channel.send(entire[2].text.strip() + "를 재생목록에 추가했어요!\n" + rinklist[2])
        if '4번째 영상' in select.values:
            URLPLAY(entire[3].text.strip(), rinklist[3])
            await ctx.channel.send(entire[3].text.strip() + "를 재생목록에 추가했어요!\n" + rinklist[3])
        await interaction.response.defer()
            
    select.callback = my_callback
    view = View()
    view.add_item(select)

    await ctx.channel.send(view = view)


@bot.command()
async def 즐겨찾기(ctx):
    global Ftext
    Ftext = ""
    correct = 0
    global Flist
    for i in range(len(userF)):
        if userF[i] == str(ctx.message.author.name): #userF에 유저정보가 있는지 확인
            correct = 1 #있으면 넘김
    if correct == 0:
        userF.append(str(ctx.message.author.name)) #userF에다가 유저정보를 저장
        userFlist.append([]) #유저 노래 정보 첫번째에 유저이름을 저장하는 리스트를 만듬.
        userFlist[len(userFlist)-1].append(str(ctx.message.author.name))
        
    for i in range(len(userFlist)):
        if userFlist[i][0] == str(ctx.message.author.name):
            if len(userFlist[i]) >= 2: # 노래가 있다면
                for j in range(1, len(userFlist[i])):
                    Ftext = Ftext + "\n" + str(j) + ". " + str(userFlist[i][j])
                titlename = str(ctx.message.author.name) + "님의 즐겨찾기"
                embed = discord.Embed(title = titlename, description = Ftext.strip(), color = 0x00ff00)
                embed.add_field(name = "목록에 추가\U0001F4E5", value = "즐겨찾기에 모든 곡들을 목록에 추가합니다.", inline = False)
                embed.add_field(name = "플레이리스트로 추가\U0001F4DD", value = "즐겨찾기에 모든 곡들을 새로운 플레이리스트로 저장합니다.", inline = False)
                Flist = await ctx.send(embed = embed)
                await Flist.add_reaction("\U0001F4E5")
                await Flist.add_reaction("\U0001F4DD")
            else:
                await ctx.send("아직 등록하신 즐겨찾기가 없어요.")



@bot.command()
async def 즐겨찾기추가(ctx, *, msg):
    correct = 0
    for i in range(len(userF)):
        if userF[i] == str(ctx.message.author.name): #userF에 유저정보가 있는지 확인
            correct = 1 #있으면 넘김
    if correct == 0:
        userF.append(str(ctx.message.author.name)) #userF에다가 유저정보를 저장
        userFlist.append([]) #유저 노래 정보 첫번째에 유저이름을 저장하는 리스트를 만듦.
        userFlist[len(userFlist)-1].append(str(ctx.message.author.name))

    for i in range(len(userFlist)):
        if userFlist[i][0] == str(ctx.message.author.name):
            
            options = webdriver.ChromeOptions()
            options.add_argument("headless")

            chromedriver_dir = r"D:\Discord_Bot\chromedriver.exe"
            driver = webdriver.Chrome(chromedriver_dir, options = options)
            driver.get("https://www.youtube.com/results?search_query="+msg+"+lyrics")
            source = driver.page_source
            bs = bs4.BeautifulSoup(source, 'lxml')
            entire = bs.find_all('a', {'id': 'video-title'})
            entireNum = entire[0]
            music = entireNum.text.strip()

            driver.quit()

            userFlist[i].append(music)
            await ctx.send(music + "(이)가 정상적으로 등록되었어요!")



@bot.command()
async def 즐겨찾기삭제(ctx, *, number):
    correct = 0
    for i in range(len(userF)):
        if userF[i] == str(ctx.message.author.name): #userF에 유저정보가 있는지 확인
            correct = 1 #있으면 넘김
    if correct == 0:
        userF.append(str(ctx.message.author.name)) #userF에다가 유저정보를 저장
        userFlist.append([]) #유저 노래 정보 첫번째에 유저이름을 저장하는 리스트를 만듦.
        userFlist[len(userFlist)-1].append(str(ctx.message.author.name))

    for i in range(len(userFlist)):
        if userFlist[i][0] == str(ctx.message.author.name):
            if len(userFlist[i]) >= 2: # 노래가 있다면
                try:
                    del userFlist[i][int(number)]
                    await ctx.send("정상적으로 삭제되었습니다.")
                except:
                     await ctx.send("입력한 숫자가 잘못되었거나 즐겨찾기의 범위를 초과하였습니다.")
            else:
                await ctx.send("즐겨찾기에 노래가 없어서 지울 수 없어요!")

bot.run(token)