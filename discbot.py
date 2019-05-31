import discord
import random
import asyncio
import youtube_dl
from datetime import timedelta
import os

pybot = discord.Client()

ydl = youtube_dl.YoutubeDL({
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'logtostderr': False,
    'noplaylist': True,
    'nocheckcertificate': True,
    'restrictfilenames': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320'}]
})

swears = {'bitch': 'floozy',
          'fuck': 'intercourse',
          'pussy': 'female reproductive organ',
          'damnit': 'darnit',
          'damn': 'darn',
          'shit': 'doo doo',
          'bastard': 'illegitimate son',
          'cock': 'male reproductive organ',
          'dick': 'male reproductive organ',
          'cunt': 'female reproductive organ',
          'faggot': 'gay',
          'fag': 'gay',
          'porn': 'adult movie',
          'suck': 'oral',
          'tits': 'breasts',
          'tit': 'breast',
          'piss': 'pee',
          'handjob': 'self-pleasuring'}

commands = ['about', 'passage', 'image', 'soft_ban', 'airhorn', 'sadhorn', 'stop', 'hello', 'soft_ban_voice', 'bulk_del', 'quote', 'play', 'volume', 'pause', 'resume', 'queue', 'skip', 'next', 'create_secret']

sermons = []

voice_bans = asyncio.Queue()

voice_clients = {}

channel_playlist = {}

owners_list = {}

skip_votes = {}

with open('sermons.txt', 'r') as f:
    sermons = eval(f.read())


def index_of(string: str, substring: str):
    index_aux = None
    index_substring = 0
    indexes = ()
    num_spaces = 0
    num_letters = 0
    triggered = False

    for i in range(len(string)):
        if string[i].lower() == substring[index_substring].lower():
            index_aux = i
            num_letters += 1
            triggered = True

            if i < len(string) - 1:
                if string[i + 1].lower() != substring[index_substring].lower():
                    index_substring += 1
            elif string[i].lower() == substring[index_substring].lower():
                index_substring += 1

        elif not 97 <= ord(string[i].lower()) <= 122 and triggered:
            num_spaces += 1
        else:
            index_substring = 0
            num_spaces = 0
            index_aux = None
            triggered = False

        if index_substring == len(substring):
            index_substring = 0
            tup_aux = ((index_aux - (num_letters - 1 + num_spaces), index_aux + 1),)
            begin = tup_aux[0][0]

            if not 97 <= ord(string[begin - 1].lower()) <= 122 or begin == 0:
                indexes += tup_aux

    return indexes


def censor(text: str, swear: str, clean: str):
    text_aux = text

    for begin, end in index_of(text, swear):
        text_aux = text_aux.replace(text[begin:end], clean)

    return text_aux


def get_username(id_u):

    men = str(id_u)
    men = men.replace('<', '').replace('>', '').replace('@', '')

    return str(pybot.get_user(int(men)))


async def timer_ban(timer, member, *channels):
    if len(channels) == 1:
        await channels[0].set_permissions(member, read_messages=True, send_messages=False)
        await channels[0].send(member.mention + ' has been soft banned from this channel for ' + str(timer) + ' minute(s)!', delete_after=5)
        await asyncio.sleep(timer * 60)
        await channels[0].set_permissions(member, read_messages=True, send_messages=True)
        await channels[0].send(member.mention + ' can now send messages to this channel!', delete_after=5)
    else:
        for c in channels:
            await c.set_permissions(member, read_messages=True, send_messages=False)
            await c.send(member.mention + ' has been soft banned from all channels for ' + str(timer) + ' minute(s)!', delete_after=5)

        await asyncio.sleep(timer * 60)

        for c in channels:
            await c.set_permissions(member, read_messages=True, send_messages=True)
            await c.send(member.mention + ' can now send messages to all channels!', delete_after=5)


async def play_audio(message, audio_name):
    voice = message.author.voice
    if not voice:
        await message.channel.send('You must be connected to a voice channel!', delete_after=5)
    else:
        if voice.channel in [vc.channel for vc in pybot.voice_clients]:
            await message.channel.send('I\'m already playing audio on your channel!', delete_after=5)
            return
        vc = await voice.channel.connect()
        audio = discord.FFmpegPCMAudio(audio_name + '.mp3', options='-hide_banner -loglevel quiet')
        vc.play(audio)
        while vc.is_playing():
            await asyncio.sleep(0.7)
        vc.stop()
        audio.cleanup()
        await vc.disconnect()


async def timer_ban_voice(member, message, timer):
    sinners = None

    for vc in message.channel.guild.voice_channels:
        if vc.name == 'Sinners':
            sinners = vc
        else:
            await vc.set_permissions(member, connect=False)

    await voice_bans.put(member)

    for tc in [c for c in message.channel.guild.channels if isinstance(c, discord.TextChannel)]:
        await tc.send('User ' + member.mention + ' has been voice soft banned for ' + str(timer) + ' minute(s)!\nRedirected to Sinners channel. If '
                                                                                                   'there are no more banned users Sinners channel will be deleted!', delete_after=5)
    if not sinners:
        sinners = await message.channel.guild.create_voice_channel('Sinners')

    if member.voice:
        await member.move_to(sinners)

    await asyncio.sleep(timer * 60)

    if member.voice:
        channel_aux = await message.channel.guild.create_voice_channel('lel')
        await member.move_to(channel_aux)
        await channel_aux.delete()

    for vc in message.channel.guild.voice_channels:
        if vc.name != 'lel':
            await vc.set_permissions(member, connect=True)

    await voice_bans.get()

    if voice_bans.empty():
        await sinners.delete()

    for tc in [c for c in message.channel.guild.channels if isinstance(c, discord.TextChannel)]:
        await tc.send(member.mention + ' voice ban has been lifted!', delete_after=5)


async def get_audio(vid_name: str, loop=None):
    try:
        vid_name = 'https://www.youtube.com/results?search_query=' + vid_name if vid_name.find('watch?v=') == -1 else vid_name

        loop = loop or asyncio.get_event_loop()

        info = await loop.run_in_executor(None, lambda: ydl.extract_info(vid_name, download=False))

        link = ''

        if 'entries' in info:
            link = info['entries'][0]
        else:
            link = info

        duration = link['duration']

        title = link['title']

        for f in link['formats']:
            if f['ext'] == 'webm':
                link = f['url']
                break

        audio = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(link, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -t ' + str(duration), options='-hide_banner -loglevel quiet'))

    except discord.ClientException:
        return await get_audio(vid_name, pybot.loop)

    return audio, title


@pybot.event
async def on_ready():
    print('Christian bot bitches!')
    print('API version:', discord.__version__)
    app_info = await pybot.application_info()
    await pybot.change_presence(status=discord.Status.online, activity=discord.Game(name='True Believers Unite F*** google! Made by '+ str(app_info.owner) +'\nBeta Build...'))


@pybot.event
async def on_message(message):
    if message.author.mention == pybot.user.mention and message.type == discord.MessageType.pins_add:
        await message.delete()
        return
    elif message.author.mention == pybot.user.mention:
        return
    elif len(message.content) == 0:
        return
    elif str(message.channel.category) != 'Bot' and message.content.find('create_secret') == -1 and message.content.find('soft_ban') == -1 and message.content.find('soft_ban_voice') == -1 and message.content.find('bulk_del') == -1:
        return

    is_command = False

    if message.content[0] == '!':
        command = message.content[1:len(message.content)]
        if command.split(' ')[0].lower() in commands:
            is_command = True
            if command.lower().find('about') != -1:
                split = command.split(' ')
                size = len(split)
                if size == 1:
                    if str(message.author.mention) != message.channel.guild.owner.mention:
                        await message.channel.send(str(message.author.mention) + ' is gay.\nGays burn in hell!')
                    else:
                        await message.channel.send(str(message.author.mention) + ' is the greatest man alive.\n'
                                                                                 'He will be my driving force when Judgement Day arrives!')
                elif size == 2:
                    if split[1] != message.channel.guild.owner.mention:
                        await message.channel.send(split[1] + ' is gay\nGays burn in hell!')
                    else:
                        await message.channel.send(split[1] + ' is the greatest man alive.\n'
                                                              'He will be my driving force when Judgement Day arrives!')
            elif command.lower() == 'passage':
                await message.channel.send(sermons[random.randint(0, len(sermons) - 1)])
            elif command.lower().find('image') != -1:
                with open('Crusades.jpg', 'rb') as pic:
                    await message.channel.send('Glory to Christ!:crossed_swords::cross:', file=discord.File(pic))
            elif command.split(' ')[0].lower() == 'soft_ban'.lower():
                if get_username(message.channel.guild.owner.mention) != get_username(message.author.mention):
                    await message.channel.send('You are not the owner of this server ' + message.author.mention + ', you filthy non-believer', delete_after=5)
                else:
                    split = command.split(' ')
                    size = len(split)
                    if size != 4:
                        await message.channel.send('Incorrect soft_ban format!\nSend channel name, then mention the user and then the ban time in minutes(up to 1 hour).\nSeparate the parameters with spaces', delete_after=5)
                    else:
                        if split[1].lower() not in [x.name.lower() for x in message.channel.guild.channels] and split[1].lower() != 'all'.lower():
                            await message.channel.send('That channel does not exist on this server!', delete_after=5)
                        else:
                            if split[2] not in [x.mention for x in message.channel.members]:
                                await message.channel.send('That user is not in that channel or he cannot se it!', delete_after=5)
                            else:
                                _member = None
                                for x in message.channel.members:
                                    if x.mention == split[2]:
                                        _member = x
                                        break
                                if split[1].lower() != 'all':
                                    _channel = None
                                    for y in message.channel.guild.channels:
                                        if y.name == split[1]:
                                            _channel = y
                                            break
                                    await timer_ban(float(split[3]), _member, _channel)
                                else:
                                    await timer_ban(float(split[3]), _member, *[x for x in message.channel.guild.channels if isinstance(x, discord.TextChannel)])
            elif command.lower().find('airhorn') != -1:
                await play_audio(message, 'air_horn(club sample)')
            elif command.lower().find('sadhorn') != -1:
                await play_audio(message, 'sadhorn')
            elif command.lower().find('hello') != -1:
                await play_audio(message, 'hello_boys')
            elif command.lower().find('stop') != -1:
                v_channel = message.author.voice
                if not v_channel:
                    await message.channel.send('You aren\'t connected to a voice channel!')
                else:
                    voice_client = None
                    if v_channel.channel.name not in voice_clients.keys():
                        await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                    elif owners_list[v_channel.channel.name] != message.author.mention:
                        await message.channel.send('You are not the creator of the playlist!', delete_after=5)
                    else:
                        voice_client = voice_clients[v_channel.channel.name]

                        while not channel_playlist[v_channel.channel.name].empty():
                            await channel_playlist[v_channel.channel.name].get()

                        voice_client.stop()

            elif command.split(' ')[0].lower() == 'soft_ban_voice'.lower():
                if get_username(message.channel.guild.owner.mention) != get_username(message.author.mention):
                    await message.channel.send('You are not the owner of this server ' + message.author.mention + ', you filthy non-believer', delete_after=5)
                else:
                    split = command.split(' ')
                    size = len(split)

                    if size != 3:
                        await message.channel.send('Incorrect soft_ban_voice format!\nCorrect format:\n!soft_ban <user_mention> <ban_time_in_minutes(up to 1 hour)>', delete_after=5)
                    else:
                        if split[1] not in [m.mention for m in message.channel.guild.members]:
                            await message.channel.send('That user doesn\'t appear to be in this server!', delete_after=5)
                        else:
                            member = None

                            for m in message.channel.guild.members:
                                if m.mention == split[1]:
                                    member = m

                            await timer_ban_voice(member, message, float(split[2]))
            elif command.lower().find('bulk_del') != -1:
                if message.channel.guild.owner.mention != message.author.mention:
                    await message.channel.send('You are not the owner of this server, ' + message.author.mention + ' you filthy non-believer!', delete_after=5)
                else:
                    split = command.split(' ')
                    size = len(split)
                    await message.delete()
                    if size == 2:
                        await message.channel.delete_messages(await message.channel.history(limit=int(split[1])).flatten())
                    elif size == 3:
                        history_list = await message.channel.history(limit=int(split[1]) + int(split[2])).flatten()
                        await message.channel.delete_messages(history_list[int(split[2]):])
                    else:
                        await message.channel.send('Incorrect bulk_del format\nCorrect format:\n!bulk_dek <number_of_messages_to_delete(from bottom to top)> <number_of_messages to keep, counting_from_the_bottom_if_you_skip_this_parameter_it_counts_from_the_last_message>', delete_after=5)
            elif command.lower().find('quote') != -1:
                split = command.split(' ')
                size = len(split)

                if size != 2:
                    await message.channel.send('Wrong format!\nCorrect Format: !quote <msg_id>', delete_after=5)
                else:
                    text_channels = [c for c in message.channel.guild.channels if isinstance(c, discord.TextChannel)]

                    for c in text_channels:
                        try:
                            target_msg = await c.fetch_message(int(split[1]))
                        except discord.NotFound:
                            continue
                        else:
                            correct_date = target_msg.created_at + timedelta(hours=1)
                            date = str(correct_date)

                            await message.delete()

                            msg = await pybot.wait_for('message', check=lambda m: m.author == message.author)

                            if msg.content.lower() == '?cancel':
                                await msg.delete()
                                return

                            await message.channel.send(target_msg.author.mention + ' ' + date[:len(date) - 10].replace(' ', ' às ') + ' em ' + target_msg.channel.mention +'\n```' + target_msg.content + '```\n' + get_username(message.author.mention) + ':\n' + msg.content)
                            await msg.delete()
                            break

            elif command.lower().find('play') != -1:
                split = command.split(' ')

                song_name = ' '.join(split[1:len(split)])

                size = len(split)

                if size == 1:
                    await message.channel.send('Wrong format!\nCorrect Format: !play <song_you_want_ie_youtube_search>', delete_after=5)
                else:
                    voice = message.author.voice
                    if not voice:
                        await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                    elif voice.channel.name in voice_clients.keys():
                        await message.channel.send('I\'m already playing audio on your channel!', delete_after=5)
                    else:
                        vc = await voice.channel.connect()

                        try:
                            wait_message = await message.channel.send('Connecting to YouTube, this may take awhile!')
                            voice_clients[voice.channel.name] = vc
                            playlist = asyncio.Queue()
                            owners_list[voice.channel.name] = message.author.mention
                            channel_playlist[voice.channel.name] = playlist
                            audio_title = await get_audio(song_name, pybot.loop)
                            await playlist.put(audio_title)
                            await wait_message.delete()

                            messages = []

                            while not playlist.empty():
                                audio = await playlist.get()

                                if len(messages) == 0:
                                    for tc in [c for c in message.channel.guild.channels if isinstance(c, discord.TextChannel) and str(c.category) == 'Bot']:
                                        start_msg = await tc.send('```css\nHere we go muthafuckas!!\nNow Playing in ' + vc.channel.name + ' -> ' + audio[1] + '```')
                                        messages.append(start_msg)
                                        await start_msg.pin()
                                else:
                                    for m in messages:
                                        await m.edit(content='```css\nHere we go muthafuckas!!\nNow Playing in ' + vc.channel.name + ' -> ' + audio[1] + '```')

                                vc.play(audio[0])

                                while vc.is_playing() or vc.is_paused():
                                    await asyncio.sleep(1)

                                audio[0].cleanup()

                            for m in messages:
                                await m.delete()

                            messages.clear()

                            try:
                                voice_clients.pop(voice.channel.name)
                                channel_playlist.pop(voice.channel.name)
                                owners_list.pop(voice.channel.name)
                            except KeyError:
                                pass

                        except IndexError:
                            await wait_message.delete()
                            await message.channel.send('Couldn\'t find requested video, I\'m afraid :S!\nTry to type your search keywords in a clearer fashion!', delete_after=5)

                        finally:
                            await vc.disconnect()

            elif command.lower().find('volume') != -1:
                split = command.split(' ')
                size = len(split)

                if size != 2:
                    await message.channel.send('Wrong format!\nCorrect format: !volume <0_to_100_just_like_a_stereo>', delete_after=5)
                else:
                    try:
                        volume = int(split[1])
                        if not 0 <= volume <= 100:
                            await message.channel.send('Wrong volume size range!\nSize Range <= 0 range <= 100', delete_after=5)
                        else:
                            voice = message.author.voice

                            if not voice:
                                await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                            elif voice.channel.name not in voice_clients.keys():
                                await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                            else:
                                voice_clients[voice.channel.name].source.volume = volume / 100

                    except ValueError:
                        await message.channel.send('Second parameter must be a number from 0 to 100!', delete_after=5)
            elif command.lower() == 'pause'.lower():
                voice = message.author.voice

                if not voice:
                    await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                elif voice.channel.name not in voice_clients.keys():
                    await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                else:
                    voice_clients[voice.channel.name].pause()
            elif command.lower() == 'resume'.lower():
                voice = message.author.voice

                if not voice:
                    await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                elif voice.channel.name not in voice_clients.keys():
                    await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                else:
                    voice_clients[voice.channel.name].resume()
            elif command.lower().find('queue') != -1:
                split = command.split(' ')

                song_name = ' '.join(split[1:len(split)])

                size = len(split)

                if size == 1:
                    await message.channel.send('Wrong format!\nCorrect Format: !queue <song_you_want_ie_youtube_search>', delete_after=5)
                else:
                    voice = message.author.voice

                    if not voice:
                        await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                    elif voice.channel.name not in voice_clients.keys():
                        await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                    else:
                        queue_message = await message.channel.send('Enqueueing!')
                        try:
                            audio = await get_audio(song_name)
                            await channel_playlist[voice.channel.name].put(audio)

                            for tc in [c for c in message.channel.guild.channels if isinstance(c, discord.TextChannel)]:
                                await tc.send('```css\n*@' + get_username(message.author.mention) + ' has queued -> ' + audio[1] + ' into the playlist*```', delete_after=5)

                        except KeyError:
                            pass
                        except IndexError:
                            await message.channel.send('Couldn\'t find requested video, I\'m afraid :S!\nTry to type your search keywords in a clearer fashion!', delete_after=5)
                        finally:
                            await queue_message.delete()

            elif command.lower() == 'skip'.lower():
                voice = message.author.voice

                if not voice:
                    await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                elif voice.channel.name not in voice_clients.keys():
                    await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                elif owners_list[voice.channel.name] == message.author.mention:
                    voice_clients[voice.channel.name].stop()
                else:
                    await message.channel.send('You are not the creator of the playlist!', delete_after=5)
            elif command.lower() == 'next'.lower():
                voice = message.author.voice

                if not voice:
                    await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                elif voice.channel.name not in voice_clients.keys():
                    await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                else:
                    queue_aux = asyncio.Queue()

                    playlist = channel_playlist[voice.channel.name]

                    if playlist.empty():
                        await message.channel.send('```css\n[No more songs left after this :/ \nYou can add more songs to the playlist with !queue command].```', delete_after=5)
                        return

                    while not playlist.empty():
                        await queue_aux.put(await playlist.get())

                    next_song = await queue_aux.get()

                    await playlist.put(next_song)

                    while not queue_aux.empty():
                        await playlist.put(await queue_aux.get())

                    await message.channel.send('```css\n("Next song in ' + voice.channel.name + ' -> ' + next_song[1] + ')"```', delete_after=5)
            elif command.lower().find('create_secret') != -1:
                split = command.split(' ')
                size = len(split)
                if size != 3:
                    await message.channel.send('Wrong format!\nCorrect Format: !create_secret <channel_name_no_spaces> <Role_which_users_must_have>')
                elif str(message.author.top_role).lower() == 'Admin'.lower():
                    guild = message.channel.guild

                    try:
                        cat = [x for x in guild.categories if str(x) == 'Bot'][0]
                    except IndexError:
                        cat = None

                    cat = cat or await guild.create_category('Bot')

                    target_role = [x for x in guild.roles if str(x) == split[2]][0]
                    overs = {x: discord.PermissionOverwrite(read_messages=False) for x in guild.roles if str(x) != split[2]}
                    overs[target_role] = discord.PermissionOverwrite(read_messages=True)

                    await cat.create_text_channel(split[1], overwrites=overs)
                else:
                    await message.channel.send('Fuck Off non-believer!', delete_after=5)
        if not is_command:
            await message.channel.send('I\'m not that enlightened!', delete_after=5)
    else:
        msg = message.content
        new_msg = msg
        for x in swears.keys():
            if len(index_of(new_msg, x)) == 0:
                continue
            else:
                new_msg = censor(new_msg, x, swears[x])
        if new_msg != msg:
            await message.delete()
            await message.channel.send('Absolutely no swearing! This is a christian channel.\n'
                                       'Here let me fix that for you, ' + get_username(message.author.mention) + ':\n'
                                       '```' + new_msg + '```')


@pybot.event
async def on_message_delete(message):
    has_swears = False

    for s in swears.keys():
        if len(index_of(message.content, s)) != 0:
            has_swears = True
            break

    if has_swears or message.author.mention == pybot.user.mention:
        return


@pybot.event
async def on_raw_bulk_message_delete(payload):
    await pybot.get_channel(payload.channel_id).send(str(len(payload.message_ids)) + ' messages have been deleted!', delete_after=10)


@pybot.event
async def on_voice_state_update(member, before, after):
    if not before.channel:
        return

    if member.mention == pybot.user.mention:
        try:
            while not channel_playlist[before.channel.name].empty():
                await channel_playlist[before.channel.name].get()
            voice_clients.pop(before.channel.name)
        except KeyError:
            pass

    if len(before.channel.members) == 1 and before.channel.members[0].name == pybot.user.name:
        for vc in pybot.voice_clients:
            if vc.channel.name == before.channel.name:
                await vc.disconnect()
                break


@pybot.event
async def on_guild_channel_delete(channel):
    if not isinstance(channel, discord.VoiceChannel):
        return

    for vc in pybot.voice_clients:
        if vc.channel == channel:
            vc.disconnect()
            break


pybot.run(str(os.environ.get('BOT_TOKEN')))
