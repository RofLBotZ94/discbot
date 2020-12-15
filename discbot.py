import discord
import random
import asyncio
import youtube_dl
from datetime import datetime, timedelta, timezone
from aiohttp import ClientSession, FormData, ServerConnectionError
from iso3166 import countries
import json
import os
import aiofiles
import math
import pandas
import functools
import re


pybot = discord.Client()

ydl = youtube_dl.YoutubeDL({
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'logtostderr': False,
    'noplaylist': True,
    'nocheckcertificate': True,
    'restrictfilenames': True
})

meme_map = {
    'snow': 61579,
    'drake': 181913649,
    'distracted': 112126428,
    'pigeon': 100777631,
    'exit': 124822590,
    'surprised': 155067746,
    'doge': 8072285,
    'bill': 56225174,
    'parker': 53764,
    'safe': 161865971,
    'seagull': 114585149,
    'changemymind': 129242436,
    'womancat': 188390779,
    'scroll': 123999232,
    'kill': 135678846,
    'buttons': 87743020,
    'boardroom': 1035805,
    'skeleton': 4087833,
    'toystory': 91538330,
    'trump': 91545132,
    'argument': 134797956,
    'therock': 21735,
    'futurama': 61520,
    'neverland': 6235864,
    'prezalert': 157978092,
    'morpheus': 100947,
    'sparta': 195389,
    'goodfellas': 47235368,
    'brain': 93895088,
    'fairygodparents': 3218037,
    'eddie': 89370399,
    'carroof': 142921050,
    'grindgears': 356615,
    'npc': 154434126,
    'droids': 1373425,
    'ramsay': 496570,
    'bollywood': 970155,
    'justpretending': 250004520
}

commands = {
    'ping': 'Bot Latency',
    'about': 'Find something about someone',
    'passage': 'Bible passage lol',
    'image': 'Crusades',
    'soft_ban': 'Soft ban someone from a text channel',
    'airhorn': 'Airhorn (voice)',
    'sadhorn': 'Airhorn but sad (voice)',
    'stop': 'Stop RofLSpawN in the middle of an audio play (voice)',
    'hello': 'Undertaker WWE (voice)',
    'bom_flash': 'Whistle in approval (voice)',
    'mau_flash': 'Whistle in disapproval (voice)',
    'soft_ban_voice': 'Soft ban someone from a voice channel',
    'bulk_del': 'Delete several messages',
    'bulk_del_s': 'Delete several messages (archive)',
    'quote': 'Quote someone',
    'play': 'Create a playlist of songs (voice)',
    'volume': 'Set the playlist volume (voice)',
    'pause': 'Pause the current song in the playlist (voice)',
    'resume': 'Resume the current song in the playlist (voice)',
    'queue': 'Add a song to the playlist (voice)',
    'skip': 'Skip to the next song in the playlist (voice)',
    'create_secret': 'Create a channel for a specific role',
    'delete_role': 'Delete a Role',
    'memes': 'Create a meme from a template or fetch a created meme',
    'acnh': 'Extract an excel file with items from the supplied category, of the video game Animal Crossing: New Horizons',
    'help': 'List all commands / Learn more about a specific command',
    'sacrifice': 'LOL',
    'corona': 'Track the most up to date COVID-19 numbers around the world'
}

voice_bans = {}

voice_clients = {}

channel_playlist = {}

owners_list = {}

channel_volume = {}

deleted_message_cache = {}

history_channel_messages = {}
history_channel_timers = {}

with open('sermons.txt', 'r') as f:
    sermons = eval(f.read())


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
        if discord.utils.get(pybot.voice_clients, guild=message.guild):
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

    voice_bans[message.channel.guild.id] = asyncio.Queue()

    await voice_bans[message.channel.guild.id].put(member)

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

    await voice_bans[message.channel.guild.id].get()

    if voice_bans[message.channel.guild.id].empty():
        await sinners.delete()

    for tc in [c for c in message.channel.guild.channels if isinstance(c, discord.TextChannel)]:
        await tc.send(member.mention + ' voice ban has been lifted!', delete_after=5)


async def bulk_del(channel, msgs_to_del, msgs_to_ignore=0, save=False):
    history_list = [{x.id: [await y.to_file() for y in x.attachments]} async for x in channel.history(limit=msgs_to_del + msgs_to_ignore)][msgs_to_ignore:]

    if save:
        deleted_message_cache[str(channel)] = history_list[::-1]

    await channel.purge(limit=msgs_to_del + msgs_to_ignore, check=lambda m: m.id in [list(x.keys())[0] for x in history_list])


async def get_audio(vid_name: str, loop=None, vol: float = 0.5):
    try:
        loop = loop or asyncio.get_event_loop()
        info = await loop.run_in_executor(None, functools.partial(ydl.extract_info, vid_name, download=False))

        link = info['entries'][0] if 'entries' in info else info
        duration = link['duration']
        title = link['title']
        image = link['thumbnail']

        for f in link['formats']:
            if f['ext'] == 'webm':
                link = f['url']
                break

        audio = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(link, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -t ' + str(duration), options='-hide_banner -loglevel quiet'), volume=vol)

    except Exception:
        await asyncio.sleep(5)
        return await get_audio(vid_name, pybot.loop)
 
    return audio, title, image


async def next_song(voice):
    if not voice:
        return
    elif voice.channel.name not in voice_clients.keys():
        return
    else:
        queue_aux = asyncio.Queue()

        playlist = channel_playlist[voice.channel.name]

        if playlist.empty():
            return 'No more songs left!', 'https://cdn4.iconfinder.com/data/icons/icocentre-free-icons/137/f-check_256-512.png'

        next_s = await playlist.get()

        while not playlist.empty():
            await queue_aux.put(await playlist.get())

        await playlist.put(next_s)

        while not queue_aux.empty():
            await playlist.put(await queue_aux.get())

        return next_s[1], next_s[2]


async def meme_service(message: discord.Message, name: str, *boxes):
    boxes = boxes[:1] + (boxes[1:] * 4) if name == 'justpretending' else boxes
    async with ClientSession() as session:
        try:
            form = FormData()
            form.add_field('template_id', meme_map[name])
            form.add_field('username', 'RofLSpawN')
            form.add_field('password', 'ConadaTia')
            form.add_field('text0', 'whatever')
            form.add_field('text1', 'dafuq')
        except KeyError:
            await message.channel.send(f'The meme \"{name}\" does not exist!', delete_after=5)
        else:
            for i, text in enumerate(boxes):
                form.add_field('boxes[%s][text]' % i, text.upper())

            async with session.post('https://api.imgflip.com/caption_image', data=form) as response:
                response = json.loads(await response.read())

                if response['success']:
                    image_url = response['data']['url']
                else:
                    raise ServerConnectionError(response['error_message'])

            async with session.get(image_url) as response:
                extension = response.headers['CONTENT-TYPE'].split('/')[1]
                async with aiofiles.open(f'C:\\ProgramData\\ASUS\\ASUS Live Update\\Temp\\image.{extension}', 'wb') as pic:
                    await pic.write(await response.read())

            with open(f'C:\\ProgramData\\ASUS\\ASUS Live Update\\Temp\\image.{extension}', 'rb') as pic:
                await message.channel.send(f'Created by {message.author}:', file=discord.File(pic))

            await message.delete()


async def datamine_animal_crossings(message: discord.Message, category: str = 'All'):
    categories = ['Tools', 'Housewares', 'Wall-mounted', 'Wallpaper,_rugs_and_flooring', 'Equipment', 'Other']
    category = category.replace(' ', '_')
    files = []

    async def mine_category(category: str):
        data = await pybot.loop.run_in_executor(None, pandas.read_html, f'https://animalcrossing.fandom.com/wiki/DIY_recipes/{category}')
        await pybot.loop.run_in_executor(None, functools.partial(data[0].to_excel, f'datamine_acnh_{category}.xlsx', index=False))
        with open(f'datamine_acnh_{category}.xlsx', 'rb') as f:
            return discord.File(f)

    if category not in categories and category != 'All':
        await message.channel.send(f'{category} is not a valid category!', delete_after=5)
    else:
        try:
            index = categories.index(category)
        except ValueError:
            index = -1
        finally:
            categories = categories if index == -1 else [categories[index]]
            for cat in categories:
                files.append(pybot.loop.create_task(mine_category(cat)))

            await message.channel.send(files=await asyncio.gather(*files))


async def covid(country: str = 'global'):
    async with ClientSession() as session:
        async with session.get('https://api.covid19api.com/summary') as response:
            response = json.loads(await response.read())
            if country == 'global':
                glob = {'Country': 'Global :map:'}
                glob.update(response['Global'])
                ret = [re.sub(r'([A-Z])', r' \1',
                              k).strip() + f': {"{:,}".format(v) if isinstance(v, int) else v}\n' for k, v
                       in glob.items()]
                return ''.join(ret)
            else:
                name = countries.get(country.upper()).alpha2
                for c in response['Countries']:
                    if c['CountryCode'] == name:
                        c['Country'] = f'{c["Country"]} :flag_{c["CountryCode"].lower()}:'
                        ret = [re.sub(r'([A-Z])', r' \1',
                                      k).strip() + f': {"{:,}".format(v) if isinstance(v, int) else v}\n' for k, v
                               in c.items()]
                        del ret[1:3], ret[len(ret) - 2:]
                        return ''.join(ret)


async def command_description(message: discord.Message, command: str):
    embed = None
    rofl_mention = pybot.user.mention
    if command.lower() == 'ping':
        embed = discord.Embed.from_dict({
            'title': '!ping command',
            'description': f'This command allows you to check {rofl_mention}\'s latency',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': f'{rofl_mention}\'s latency value in milliseconds'
                },
                {
                    'name': 'Example:',
                    'value': '!ping'
                },
                {
                    'name': 'Considerations:',
                    'value': 'None'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'about':
        embed = discord.Embed.from_dict({
            'title': '!about command',
            'description': 'This command allows you to get someones description',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<User mention> (optional)'
                },
                {
                    'name': 'Returns:',
                    'value': 'A description about the user associated with the supplied <User Mention>'
                },
                {
                    'name': 'Example (no arguments):',
                    'value': '!about'
                },
                {
                    'name': 'Example (with a <User Mention>):',
                    'value': '!about @some_username'
                },
                {
                    'name': 'Considerations:',
                    'value': 'If no argument is supplied to the command it will describe you! Are you sure you want to do this?'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'passage':
        embed = discord.Embed.from_dict({
            'title': '!passage command',
            'description': 'This command allows to get a random bible passage',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': 'A bible passage'
                },
                {
                    'name': 'Example:',
                    'value': '!passage'
                },
                {
                    'name': 'Considerations:',
                    'value': 'None'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'image':
        embed = discord.Embed.from_dict({
            'title': '!image command',
            'description': 'This command allows you the see a picture of crusaders',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': 'An image of crusaders'
                },
                {
                    'name': 'Example:',
                    'value': '!image'
                },
                {
                    'name': 'Considerations:',
                    'value': 'None'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'airhorn':
        embed = discord.Embed.from_dict({
            'title': '!airhorn command',
            'description': 'This command allows you to play an airhorn sound',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': f'The sound of an airhorn played by {rofl_mention} in your Voice Channel'
                },
                {
                    'name': 'Example:',
                    'value': '!airhorn'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} cannot be already playing audio'
                             ' in your Voice Channel!\n\nIn case he happens to be playing audio in your Channel, '
                             'you need to wait until he\'s through playing!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'sadhorn':
        embed = discord.Embed.from_dict({
            'title': '!sadhorn command',
            'description': 'This command allows you to play an airhorn sound with a sad tone to it',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': f'The sound of an airhorn with a sad tone to it played by {rofl_mention} in your Voice Channel'
                },
                {
                    'name': 'Example:',
                    'value': '!sadhorn'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} cannot be already playing audio'
                             ' in your Voice Channel!\n\nIn case he happens to be playing audio in your Channel, '
                             'you need to wait until he\'s through playing!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'hello':
        embed = discord.Embed.from_dict({
            'title': '!hello command',
            'description': 'This command allows you to play a soundbite from the WWE\'s Undertaker,'
                           ' saying \"Hello Boys!\"',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': 'A soundbite form the Undertaker saying \"Hello Boys!\" '
                             f'played by {rofl_mention} in your Voice Channel'
                },
                {
                    'name': 'Example:',
                    'value': '!hello'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} cannot be already playing audio'
                             ' in your Voice Channel!\n\nIn case he happens to be playing audio in your Channel, '
                             'you need to wait until he\'s through playing!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'bom_flash':
        embed = discord.Embed.from_dict({
            'title': '!bom_flash command',
            'description': 'This command allows you to play the sound of a whistle in a tone of approval',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': f'The sound of a whistle in a tone of approval played by {rofl_mention} in your Voice Channel'
                },
                {
                    'name': 'Example:',
                    'value': '!bom_flash'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} cannot be already playing audio'
                             ' in your Voice Channel!\n\nIn case he happens to be playing audio in your Channel, '
                             'you need to wait until he\'s through playing!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'mau_flash':
        embed = discord.Embed.from_dict({
            'title': '!mau_flash command',
            'description': 'This command allows you to play the sound of a whistle in a tone of disapproval',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': f'The sound of a whistle in a tone of disapproval played by {rofl_mention} in your Voice Channel'
                },
                {
                    'name': 'Example:',
                    'value': '!mau_flash'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} cannot be already playing audio'
                             ' in your Voice Channel!\n\nIn case he happens to be playing audio in your Channel, '
                             'you need to wait until he\'s through playing!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'stop':
        embed = discord.Embed.from_dict({
            'title': '!stop command',
            'description': f'This command allows you to stop {rofl_mention}\'s current sound '
                           'from playing in your Voice Channel',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': f'Stops {rofl_mention} from playing audio in your Channel by making him leave the Channel'
                },
                {
                    'name': 'Example:',
                    'value': '!stop'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} must be currently playing audio '
                             'in your Voice Channel!\n\nIn case he happens to be playing a song from a music queue, only'
                             ' the music queue\'s owner is able to use this command to stop the music queue'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'skip':
        embed = discord.Embed.from_dict({
            'title': '!skip command',
            'description': 'This command allows you to skip to the next song from your Voice Channel\'s music queue',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': 'The next song in the music queue from your Voice Channel'
                },
                {
                    'name': 'Example:',
                    'value': '!skip'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} must be currently playing a music'
                             ' queue in your Voice Channel!\n\nIn case there are no more songs left, after the current '
                             'song, then the music queue will be stopped'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'pause':
        embed = discord.Embed.from_dict({
            'title': '!pause command',
            'description': 'This command allows you to pause the current song playing '
                           'in your Voice Channel\'s music queue',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': 'Pauses the current song from your Voice Channel\'s music queue'
                },
                {
                    'name': 'Example:',
                    'value': '!pause'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} must be currently playing a music'
                             ' queue in your Voice Channel!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'resume':
        embed = discord.Embed.from_dict({
            'title': '!resume command',
            'description': 'This command allows you to resume playing the currently paused song '
                           'in your Voice Channel\'s music queue',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': 'None'
                },
                {
                    'name': 'Returns:',
                    'value': 'Resumes playing the currently paused song from your Voice Channel\'s music queue'
                },
                {
                    'name': 'Example:',
                    'value': '!resume'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel and {rofl_mention} must be currently playing a music'
                             ' queue in your Voice Channel!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'soft_ban':
        embed = discord.Embed.from_dict({
            'title': '!soft_ban command',
            'description': 'This command allows you to soft ban a specific user from a Text Channel, '
                           'for a definite period of time',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Target Text Channel Name> <User Mention of the targeted user> '
                             '<Ban Time in minutes> (up to an hour)'
                },
                {
                    'name': 'Returns:',
                    'value': f'{rofl_mention} banning the supplied user, '
                             'from the supplied Text Channel, for the supplied time in minutes!'
                },
                {
                    'name': 'Example (soft ban from a single Text Channel for 2 minutes):',
                    'value': '!soft_ban channel_name @some_user 2'
                },
                {
                    'name': 'Example (soft ban from all Text Channels for 30 seconds):',
                    'value': '!soft_ban all @some_user 1/2'
                },
                {
                    'name': 'Considerations:',
                    'value': 'You must be a server administrator to use this command, and the targeted user, '
                             'must be able to currently see the supplied Text Channel!\n\nPlease keep in mind that this'
                             ' command will have no effect on a user that is currently a server administrator'
                             ', due to the way that Discord handles the administrator permission, as they bypass all'
                             ' restrictions applied to them. You should be careful as to whom '
                             'you give the administrator permission!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'soft_ban_voice':
        embed = discord.Embed.from_dict({
            'title': '!soft_ban_voice command',
            'description': 'This command allows you to soft ban a specific user from all Voice Channel in the server, '
                           'for a definite period of time',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<User Mention of the targeted user> <Ban Time in minutes> (up to an hour)'
                },
                {
                    'name': 'Returns:',
                    'value': f'{rofl_mention} banning the supplied user, '
                             'from all Voice Channels, for the supplied time in minutes!\n'
                             'Also he creates a Voice Channel called \"Sinners\", '
                             'that the voice soft banned users can join!'
                },
                {
                    'name': 'Example (soft ban from all Voice Channels for 10 minutes):',
                    'value': '!soft_ban_voice @some_user 10'
                },
                {
                    'name': 'Considerations:',
                    'value': 'You must be a server administrator to use this command!\n\nOnce there are no more voice '
                             'soft banned users, the \"Sinners\" Voice Channel will be deleted!\n\n'
                             'Please keep in mind that this command will have no effect on a user '
                             'that is currently a server administrator, due to the way '
                             'that Discord handles the administrator permission, as they bypass all'
                             ' restrictions applied to them. You should be careful as to whom '
                             'you give the administrator permission!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'quote':
        embed = discord.Embed.from_dict({
            'title': '!quote command',
            'description': 'This command allows you to quote a message and reply to it',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Target Message Id>'
                },
                {
                    'name': 'Returns:',
                    'value': f'A message written by {rofl_mention} with the quoted message and a mention from the user '
                             'that wrote the quoted message, with your reply below it!'
                },
                {
                    'name': 'Example:',
                    'value': '!quote <Target Message Id>Hit \"Enter\" and write your reply'
                },
                {
                    'name': 'Considerations:',
                    'value': 'In case you enter the command and you change your mind about replying, use \"?cancel\" '
                             'to cancel your reply!\n\nIn order to easily get a message id follow these steps:\nGo To '
                             'User Settings => Appearance (Behaviour for mobile clients) => Scroll down to ADVANCED '
                             '(Chat Behaviour for mobile clients) => Turn on Developer Mode. Now go to the message '
                             'you want to quote, go to it\'s options and you should be able to see the \"Copy ID\" '
                             'option, click it and paste it to the command!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'bulk_del':
        embed = discord.Embed.from_dict({
            'title': '!bulk_del command',
            'description': 'This command allows you to bulk delete a number of messages counting from the bottom',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Number of Messages> <Number of Messages to ignore counting from the bottom> (optional)'
                },
                {
                    'name': 'Returns:',
                    'value': 'The supplied number of messages deleted from the channel, where the command was invoked!'
                },
                {
                    'name': 'Example (delete the last 10 messages):',
                    'value': '!bulk_del 10'
                },
                {
                    'name': 'Example (delete the last 10 messages, ignoring the first two):',
                    'value': '!bulk_del 10 - 2'
                },
                {
                    'name': 'Considerations:',
                    'value': 'You must be a server administrator to use this command!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'bulk_del_s':
        embed = discord.Embed.from_dict({
            'title': '!bulk_del_s command',
            'description': 'This command allows you to bulk delete a number of messages counting from the bottom '
                           'saving them in an archive channel!',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Number of Messages> <Number of Messages to ignore counting from the bottom> (optional)'
                },
                {
                    'name': 'Returns:',
                    'value': 'The supplied number of messages deleted from the channel, where the command was invoked, '
                             'redirecting them to the \"arquivo\" Text Channel'
                },
                {
                    'name': 'Example (delete and save the last 10 messages):',
                    'value': '!bulk_del_s 10'
                },
                {
                    'name': 'Example (delete and save the last 10 messages, ignoring the first two):',
                    'value': '!bulk_del_s 10 - 2'
                },
                {
                    'name': 'Considerations:',
                    'value': 'You must be a server administrator to use this command!\n\nIn case your server does not have'
                             f' a\"Bot\" Category Channel with a Text Channel \"arquivo\" inside, {rofl_mention}'
                             ' will create it for you! This is done in order to contain the output of some '
                             'commands to the Channels in that category, to avoid spamming the other channels!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'play':
        embed = discord.Embed.from_dict({
            'title': '!play command',
            'description': 'This command allows you to create a music queue on your Voice Channel, with'
                           ' the song you supplied',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Song Name like a youtube search or a link from a youtube video>'
                },
                {
                    'name': 'Returns:',
                    'value': f'A music queue created by {rofl_mention} playing the song you supplied,'
                             ' assigning it to you as the owner!'
                },
                {
                    'name': 'Example:',
                    'value': '!play alice in chains man in the box'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel, and {rofl_mention} cannot be currently playing any'
                             ' other audio on your Channel!\n\nThe song is being mined from Youtube so type it as you'
                             ' would in the Youtube search bar. Also take in consideration that you can also '
                             f' copy paste a Youtube video link instead of the song name, and {rofl_mention} will extract it '
                             ' significantly faster from Youtube. It may be less practical but it works better!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'queue':
        embed = discord.Embed.from_dict({
            'title': '!queue command',
            'description': 'This command allows you to add a song to your Voice Channel\'s music queue',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Song Name like a youtube search or a link from a youtube video>'
                },
                {
                    'name': 'Returns:',
                    'value': f'{rofl_mention} adds the song you supplied to the command, to your Voice Channel\'s music queue'
                },
                {
                    'name': 'Example:',
                    'value': '!queue alice in chains angry chair'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel, and {rofl_mention} has to be currently playing a'
                             ' music queue on your Channel!\n\nThe song is being mined from Youtube so type it as you'
                             ' would in the Youtube search bar. Also take in consideration that you can also '
                             f' copy paste a Youtube video link instead of the song name, and {rofl_mention} will extract it '
                             ' significantly faster from Youtube. It may be less practical but it works better!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'volume':
        embed = discord.Embed.from_dict({
            'title': '!volume command',
            'description': 'This command allows you to set the volume of the music queue in your Voice Channel',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Volume value between 0-100>'
                },
                {
                    'name': 'Returns:',
                    'value': f'{rofl_mention} sets the volume of the music queue in your Voice Channel, to the one supplied '
                             'in the command'
                },
                {
                    'name': 'Example:',
                    'value': '!volume 75'
                },
                {
                    'name': 'Considerations:',
                    'value': f'You must be connected to a Voice Channel, and {rofl_mention} has to be currently playing a'
                             ' music queue on your Channel!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'create_secret':
        embed = discord.Embed.from_dict({
            'title': '!create_secret command',
            'description': 'This command allows you to create a Text Channel that\'s only visible to a specific role',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Channel name> <Role Name>'
                },
                {
                    'name': 'Returns:',
                    'value': 'A new channel under the \"Bot\" Category Channel with the name you supplied and only '
                             'visible to the role you supplied'
                },
                {
                    'name': 'Example: (Specific role)',
                    'value': '!create_secret foo Admin'
                },
                {
                    'name': 'Example: (Everyone can see the Channel)',
                    'value': '!create_secret foo @everyone'
                },
                {
                    'name': 'Considerations:',
                    'value': 'You must be a server administrator to use this command!\n\n'
                             'Please keep in mind that users with the administrator permission or associated to a role '
                             'that has the administrator permission will still be able to see the Channel, due to the way '
                             'that Discord handles the administrator permission, as they bypass all'
                             ' restrictions applied to them. You should be careful as to whom '
                             'you give the administrator permission!\n\n'
                             'In case your server does not have'
                             f' a\"Bot\" Category Channel, {rofl_mention} will create it for you with the created '
                             'Text Channel inside! This is done in order to contain the output of some '
                             'commands to the Channels in that category, to avoid spamming the other channels!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'delete_role':
        embed = discord.Embed.from_dict({
            'title': '!delete_role command',
            'description': 'This command allows you to delete a specific role from your server',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Role Name>'
                },
                {
                    'name': 'Returns:',
                    'value': f'{rofl_mention} will delete the role you supplied to the command'
                },
                {
                    'name': 'Example:',
                    'value': '!delete_role Admin'
                },
                {
                    'name': 'Considerations:',
                    'value': 'You must be a server administrator to use this command!\n\n'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'memes':
        embed = discord.Embed.from_dict({
            'title': '!memes command',
            'description': 'This command allows you to create a meme from a template or fetch an already created meme',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<Template> (optional) <Text you wish to put on the template separated by commas, '
                             'per text box on the Template> (optional)'
                },
                {
                    'name': 'Returns:',
                    'value': f'{rofl_mention} will provide you with an already created meme, or create a meme for you based '
                             'on a template and the text boxes you supplied.'
                },
                {
                    'name': 'Example: (fetch a meme)',
                    'value': '!memes'
                },
                {
                    'name': 'Example: (create a meme)',
                    'value': '!memes distracted wall, trump, mexicans'
                },
                {
                    'name': 'Example: (same meme but with middle text box empty)',
                    'value': '!memes distracted wall, , mexicans'
                },
                {
                    'name': 'Considerations:',
                    'value': 'In case you\'d like to create a meme with some empty text boxes just leave a whitespace '
                             'in it\'s place (check above example)!\n\nSome memes have more text boxes than others, '
                             'they range between 2-5, so if you happen to supply too many text boxes for a template, '
                             f'don\'t worry it will still work, but {rofl_mention} will ignore the ones that are in excess, '
                             ' starting from the right. So if for example, you supply an excess of two text boxes, '
                             f'{rofl_mention} will ignore two text boxes counting from the right!\n\nMany thanks to '
                             '[Imgflip:copyright:](https://imgflip.com/) for making their [API](https://api.imgflip.com/) '
                             f'available for free to the public! {rofl_mention} appreciates it!'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })
    elif command.lower() == 'corona':
        embed = discord.Embed.from_dict({
            'title': '!corona command',
            'description': 'This command return the most up to date stats on COVID-19 around the world, presented in a table like fashion',
            'thumbnail': {
                'url': str(pybot.user.avatar_url),
                'height': 10,
                'width': 10
            },
            'color': discord.Color.blurple().value,
            'fields': [
                {
                    'name': 'Arguments:',
                    'value': '<country> (optional)'
                },
                {
                    'name': 'Returns:',
                    'value': f'{rofl_mention} will provide you with the information concerning COVID-19 of the country of your choice.'
                             ' If you don\'t provide a country, all countries will be listed!'
                },
                {
                    'name': 'Example: All countries',
                    'value': '!corona'
                },
                {
                    'name': 'Example: (specific country)',
                    'value': '!corona Portugal'
                },
                {
                    'name': 'Example: (same as above but with the country code, instead of the country name)',
                    'value': '!corona pt'
                },
                {
                    'name': 'Considerations:',
                    'value': 'None'
                }
            ],
            'timestamp': datetime.now().replace(microsecond=0).isoformat(),
            'footer': {
                'text': str(message.author),
                'icon_url': str(message.author.avatar_url)
            }
        })

    await message.channel.send(embed=embed)


@pybot.event
async def on_ready():
    print('RoflSpawn bitches!')
    print('API version:', discord.__version__)
    app_info = await pybot.application_info()
    await pybot.change_presence(status=discord.Status.online, activity=discord.Game(name='!help | Made by ' + str(app_info.owner)))


@pybot.event
async def on_message(message: discord.Message):
    if message.content.lower().find('culha') != -1:
        await message.add_reaction(':culha:633338461964992534')
    if message.author.display_name == 'am2g':
        await message.add_reaction('🐸')
        await message.add_reaction(':torta:635479359645286428')
    if message.author.mention == pybot.user.mention and message.type == discord.MessageType.pins_add:
        await message.delete()
        return
    elif message.author.mention == pybot.user.mention:
        return
    elif len(message.content) == 0:
        return

    if message.content[0] == '!':
        command = message.content[1:]
        if command.split(' ')[0].lower() in commands.keys():
            if command.lower().startswith('about'):
                split = command.split(' ')
                size = len(split)
                if size == 1:

                    if str(message.author) == str((await pybot.application_info()).owner):
                        await message.channel.send('My dad!')
                    elif str(message.author.mention) != message.channel.guild.owner.mention:
                        await message.channel.send(str(message.author.mention) + ' is gay.\nGays burn in hell!')
                    else:
                        await message.channel.send(str(message.author.mention) + ' is the greatest man alive.\n'
                                                                                 'He will be my driving force when Judgement Day arrives!')
                elif size == 2:

                    if split[1].replace('!', '') == str((await pybot.application_info()).owner.mention):
                        await message.channel.send('My dad!')
                    elif split[1].replace('!', '') != message.channel.guild.owner.mention:
                        await message.channel.send(split[1] + ' is gay\nGays burn in hell!')
                    else:
                        await message.channel.send(split[1] + ' is the greatest man alive.\n'
                                                              'He will be my driving force when Judgement Day arrives!')
            elif command.lower() == 'passage':
                await message.channel.send(random.choice(sermons))
            elif command.lower().startswith('image'):
                with open('Crusades.jpg', 'rb') as pic:
                    await message.channel.send('Glory to Christ!:crossed_swords::cross:', file=discord.File(pic))
            elif command.lower().startswith('soft_ban'):
                if not message.author.top_role.permissions.administrator:
                    await message.channel.send('You are not the owner of this server ' + message.author.mention + ', you filthy non-believer', delete_after=5)
                else:
                    split = command.split(' ')
                    size = len(split)
                    if size != 4:
                        await message.channel.send('Incorrect soft_ban format!\nSend channel name, then mention the user and then the ban time in minutes(up to 1 hour).\nSeparate the parameters with spaces', delete_after=5)
                    else:
                        if split[1].lower() not in [x.name.lower() for x in message.channel.guild.channels] and split[1].lower() != 'all'.lower():
                            await message.channel.send('That channel does not exist in this server!', delete_after=5)
                        else:
                            if split[2].replace('!', '') not in [x.mention for x in message.channel.members]:
                                await message.channel.send('That user is not in that channel or he cannot see it!', delete_after=5)
                            else:
                                _member = None
                                for x in message.channel.members:
                                    if x.mention == split[2].replace('!', ''):
                                        _member = x
                                        break
                                if split[1].lower() != 'all':
                                    _channel = None
                                    for y in message.channel.guild.channels:
                                        if y.name == split[1]:
                                            _channel = y
                                            break
                                    await timer_ban(eval(split[3]), _member, _channel)
                                else:
                                    await timer_ban(eval(split[3]), _member, *[x for x in message.channel.guild.channels if isinstance(x, discord.TextChannel)])
            elif command.lower() == 'airhorn':
                await play_audio(message, 'air_horn(club sample)')
            elif command.lower() == 'sadhorn':
                await play_audio(message, 'sadhorn')
            elif command.lower() == 'hello':
                await play_audio(message, 'hello_boys')
            elif command.lower() == 'bom_flash':
                await play_audio(message, 'bom_flash')
            elif command.lower() == 'mau_flash':
                await play_audio(message, 'mau_flash')
            elif command.lower() == 'stop':
                v_channel = message.author.voice
                if not v_channel:
                    await message.channel.send('You aren\'t connected to a voice channel!')
                else:
                    if v_channel.channel.name not in voice_clients.keys():
                        await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                    elif owners_list[v_channel.channel.name] != message.author:
                        await message.channel.send('You are not the creator of the playlist!', delete_after=5)
                    else:
                        voice_client = voice_clients[v_channel.channel.name]

                        while not channel_playlist[v_channel.channel.name].empty():
                            await channel_playlist[v_channel.channel.name].get()

                        voice_client.stop()

            elif command.lower().startswith('soft_ban_voice'):
                if not message.author.top_role.permissions.administrator:
                    await message.channel.send('You are not the admin of this server ' + message.author.mention + ', you filthy non-believer', delete_after=5)
                else:
                    split = command.split(' ')
                    size = len(split)

                    if size != 3:
                        await message.channel.send('Incorrect soft_ban_voice format!\nCorrect format:\n!soft_ban <user_mention> <ban_time_in_minutes(up to 1 hour)>', delete_after=5)
                    else:
                        if split[1].replace('!', '') not in [m.mention for m in message.channel.guild.members]:
                            await message.channel.send('That user doesn\'t appear to be in this server!', delete_after=5)
                        else:
                            member = None

                            for m in message.channel.guild.members:
                                if m.mention == split[1].split('!', ''):
                                    member = m

                            await timer_ban_voice(member, message, eval(split[2]))
            elif command.lower().startswith('bulk_del'):
                if not message.author.top_role.permissions.administrator:
                    await message.channel.send('You are not the admin of this server, ' + message.author.mention + ' you filthy non-believer!', delete_after=5)
                else:
                    split = command.split(' ')
                    size = len(split)
                    await message.delete()
                    if size == 2:
                        await bulk_del(message.channel, int(split[1]))
                    elif size == 4:
                        await bulk_del(message.channel, int(split[1]), msgs_to_ignore=int(split[3]))
                    else:
                        await message.channel.send(
                            'Incorrect bulk_del format\nCorrect format:\n!bulk_dek <number_of_messages_to_delete(from bottom to top)> - <number_of_messages to keep, counting_from_the_bottom_if_you_skip_this_parameter_it_starts counting_from_the_last_message>',
                            delete_after=5)
            elif command.lower().startswith('bulk_del_s'):
                if not message.author.top_role.permissions.administrator:
                    await message.channel.send(
                        'You are not the admin of this server, ' + message.author.mention + ' you filthy non-believer!',
                        delete_after=5)
                else:
                    split = command.split(' ')
                    size = len(split)
                    await message.delete()
                    if size == 2:
                        await bulk_del(message.channel, int(split[1]), save=True)
                    elif size == 4:
                        await bulk_del(message.channel, int(split[1]), msgs_to_ignore=int(split[3]), save=True)
                    else:
                        await message.channel.send(
                            'Incorrect bulk_del_s format\nCorrect format:\n!bulk_dek <number_of_messages_to_delete(from bottom to top)> <number_of_messages to keep, counting_from_the_bottom_if_you_skip_this_parameter_it_counts_from_the_last_message>',
                            delete_after=5)
            elif command.lower().startswith('quote'):
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

                            await message.channel.send(target_msg.author.mention + ' ' + date[:len(date) - 10].replace(' ', ' às ') + ' em ' + target_msg.channel.mention +'\n```' + target_msg.content + '```\n' + str(message.author) + ':\n' + msg.content)
                            await msg.delete()
                            break

            elif command.lower().startswith('play'):
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
                            channel_playlist[voice.channel.name] = playlist
                            owners_list[voice.channel.name] = message.author
                            channel_volume[voice.channel.name] = 0.5
                            audio_title = await get_audio(song_name, pybot.loop)
                            await playlist.put(audio_title)
                            await wait_message.delete()

                            messages = []

                            while not playlist.empty():
                                audio = await playlist.get()

                                if len(messages) == 0:
                                    for tc in [c for c in message.channel.guild.channels if
                                               isinstance(c, discord.TextChannel) and str(c.category) == 'Bot']:
                                        embed = discord.Embed.from_dict({'title': 'Music Queue',
                                                                         'description': 'Audio information for ' + vc.channel.name,
                                                                         'author': {
                                                                             'name': owners_list[voice.channel.name].name,
                                                                             'icon_url': str(owners_list[voice.channel.name].avatar_url)
                                                                         },
                                                                         'image': {
                                                                             'url': audio[2],
                                                                             'height': 25,
                                                                             'width': 25
                                                                         },
                                                                         'thumbnail': {
                                                                             'url': str(message.channel.guild.icon_url),
                                                                             'height': 10,
                                                                             'width': 10
                                                                         },
                                                                         'color': discord.Color.red().value,
                                                                         'fields': [
                                                                             {
                                                                                 'name': 'Song Name:',
                                                                                 'value': audio[1],
                                                                                 'inline': True
                                                                             },
                                                                             {
                                                                                 'name': 'Volume:',
                                                                                 'value': str(math.ceil(audio[0].volume * 100)) + '%',
                                                                                 'inline': True
                                                                             }
                                                                         ],
                                                                         'timestamp': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                                                                         'footer': {
                                                                             'text': 'Next Song: \n' + (await next_song(voice))[0],
                                                                             'icon_url': (await next_song(voice))[1]
                                                                         }
                                                                         })
                                        start_msg = await tc.send(embed=embed)
                                        messages.append(start_msg)
                                        await start_msg.pin()
                                else:
                                    for m in messages:
                                        embed = m.embeds[0]
                                        embed.set_field_at(0, name='Song Name:', value=audio[1], inline=True)
                                        embed.set_image(url=audio[2])
                                        _new, thumb = await next_song(voice)
                                        embed.set_footer(text='Next Song: \n' + _new, icon_url=thumb)
                                        await m.edit(embed=embed)

                                audio[0].volume = channel_volume[voice.channel.name] if audio[0].volume != channel_volume[voice.channel.name] else audio[0].volume
                                vc.play(audio[0])

                                while vc.is_playing() or vc.is_paused():
                                    if embed.footer.text.split('\n')[1] == 'No more songs left!' and not playlist.empty():
                                        _new, thumb = await next_song(voice)
                                        for m in messages:
                                            embed = m.embeds[0]
                                            embed.set_footer(text='Next Song: \n' + _new, icon_url=thumb)
                                            await m.edit(embed=embed)
                                    elif embed.fields[1].value != str(math.ceil(audio[0].volume * 100)) + '%':
                                        for m in messages:
                                            embed = m.embeds[0]
                                            embed.set_field_at(1, name='Volume:', value=str(math.ceil(audio[0].volume * 100)) + '%')
                                            await m.edit(embed=embed)
                                    await asyncio.sleep(1)

                                audio[0].cleanup()

                            for m in messages:
                                await m.delete()

                            messages.clear()

                            try:
                                voice_clients.pop(voice.channel.name)
                                channel_playlist.pop(voice.channel.name)
                                owners_list.pop(voice.channel.name)
                            except (KeyError, AttributeError):
                                pass

                        except IndexError:
                            await wait_message.delete()
                            await message.channel.send('Couldn\'t find requested video, please try to type your search text in clearer fashion!', delete_after=5)

                        finally:
                            await vc.disconnect()
            elif command.lower().startswith('volume'):
                split = command.split(' ')
                size = len(split)

                if size != 2:
                    await message.channel.send('Wrong format!\nCorrect format: !volume <0_to_100_just_like_a_stereo>', delete_after=5)
                else:
                    try:
                        volume = int(split[1])
                        if not 0 <= volume <= 100:
                            await message.channel.send('Wrong volume size range!\nSize Range: 0 <= range <= 100', delete_after=5)
                        else:
                            voice = message.author.voice

                            if not voice:
                                await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                            elif voice.channel.name not in voice_clients.keys():
                                await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                            else:
                                voice_clients[voice.channel.name].source.volume = channel_volume[voice.channel.name] = volume / 100

                    except ValueError:
                        await message.channel.send('Second parameter must be a number from 0 to 100!', delete_after=5)
            elif command.lower() == 'pause':
                voice = message.author.voice

                if not voice:
                    await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                elif voice.channel.name not in voice_clients.keys():
                    await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                else:
                    voice_clients[voice.channel.name].pause()
            elif command.lower() == 'resume':
                voice = message.author.voice

                if not voice:
                    await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                elif voice.channel.name not in voice_clients.keys():
                    await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                else:
                    voice_clients[voice.channel.name].resume()
            elif command.lower().startswith('queue'):
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
                            audio = await get_audio(song_name, pybot.loop, channel_volume[voice.channel.name])
                            await channel_playlist[voice.channel.name].put(audio)

                            for tc in [c for c in message.channel.guild.channels if isinstance(c, discord.TextChannel) and str(c.category) == 'Bot']:
                                await tc.send('```css\n*' + str(message.author) + ' has queued -> ' + audio[1] + ' into the playlist*```', delete_after=5)

                        except KeyError:
                            pass
                        except IndexError:
                            await message.channel.send('Couldn\'t find requested video, I\'m afraid :S!\nTry to type your search keywords in a clearer fashion!', delete_after=5)
                        finally:
                            await queue_message.delete()

            elif command.lower() == 'skip':
                voice = message.author.voice

                if not voice:
                    await message.channel.send('You be must connected to a voice channel!', delete_after=5)
                elif voice.channel.name not in voice_clients.keys():
                    await message.channel.send('I\'m not playing audio on your channel right now!', delete_after=5)
                elif owners_list[voice.channel.name] == message.author:
                    voice_clients[voice.channel.name].stop()
                else:
                    await message.channel.send('You are not the creator of the playlist!', delete_after=5)
            elif command.lower().startswith('create_secret'):
                split = command.split(' ')
                size = len(split)
                if size != 3:
                    await message.channel.send('Wrong format!\nCorrect Format: !create_secret <channel_name_no_spaces> <Role_which_users_must_have>')
                elif message.author.top_role.permissions.administrator:
                    guild = message.channel.guild

                    try:
                        cat = [x for x in guild.categories if str(x) == 'Bot'][0]
                    except IndexError:
                        cat = None

                    cat = cat or await guild.create_category('Bot')

                    target_role = [x for x in guild.roles if str(x) == split[2]][0]
                    overs = {x: discord.PermissionOverwrite(read_messages=False) for x in guild.roles if str(x) != split[2] and split[2] != '@everyone'}
                    overs[target_role] = discord.PermissionOverwrite(read_messages=True)

                    await cat.create_text_channel(split[1], overwrites=overs)
                else:
                    await message.channel.send('Fuck Off non-believer!', delete_after=5)
            elif command.lower() == 'ping':
                await message.channel.send('Pong! %s ms' % round(pybot.latency * 1000))
            elif command.lower().startswith('delete_role'):
                split = command.split(' ')
                split = [split[0], ' '.join(split[1:])]
                size = len(split)
                if size != 2:
                    await message.channel.send('Wrong delete_role format!\nCorrect format: !delete_role <roleName>', delete_after=5)
                elif not message.author.top_role.permissions.administrator:
                    await message.channel.send('You do not have the permission to use this command, filthy non-believer!', delete_after=5)
                else:
                    for r in message.channel.guild.roles:
                        if str(r) == split[1]:
                            await r.delete()
            elif command.lower().startswith('memes'):
                split = command.split(' ')
                size = len(split)
                if size > 1:
                    try:
                        await meme_service(message, split[1], *(' '.join(split[2:]).split(', ')))
                    except ServerConnectionError as sce:
                        await message.channel.send(f'Something went wrong with the API!\n\"{str(sce)}\"', delete_after=10)
                else:
                    memes_dir = 'D:\\memes'
                    chosen = random.choice(os.listdir(memes_dir))

                    with open(memes_dir + '\\' + chosen, 'rb') as meme:
                        embed = discord.Embed.from_dict({
                            'title': 'Here you go %s, sadistic fuck' % message.author.display_name,
                            'image': {'url': 'attachment://' + chosen},
                            'color': discord.Color.green().value})
                        await message.channel.send(embed=embed, file=discord.File(meme))
            elif command.lower().startswith('acnh'):
                split = command.split(' ')
                if len(split) > 1:
                    await datamine_animal_crossings(message, ' '.join(split[1:]))
                else:
                    await datamine_animal_crossings(message)
            elif command.lower().startswith('corona'):
                split = ' '.join(command.split(' ')[1:])
                if split != '':
                    returned = await covid(split)
                else:
                    returned = await covid()
                await message.channel.send(returned)
            elif command.lower().startswith('help'):
                split = command.split(' ')
                if len(split) == 1:
                    embed = discord.Embed.from_dict({
                        'title': 'Here\'s a list of all the commands',
                        'description': 'To find more about a specific command, type \"!help <command>\"',
                        'thumbnail': {
                            'url': str(pybot.user.avatar_url),
                            'height': 10,
                            'width': 10
                        },
                        'fields': [{'name': v, 'value': k, 'inline': True} for k, v in commands.items() if k != 'help'],
                        'color': discord.Color.orange().value,
                        'timestamp': datetime.now().replace(microsecond=0).isoformat(),
                        'footer': {
                            'text': str(message.author),
                            'icon_url': str(message.author.avatar_url)
                        }
                    })
                    await message.channel.send(embed=embed)
                else:
                    await command_description(message, split[1])
            elif command.lower() == 'sacrifice':
                offerings = [x.mention for x in message.channel.members if x.mention != pybot.user.mention]
                await message.channel.send(f'{offerings[random.randrange(0, len(offerings))]}\nSorry m8, you da chicken!')

        else:
            await message.channel.send('I\'m not that enlightened!', delete_after=5)


@pybot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    await on_message(after) if after is not None else await on_message(before)


@pybot.event
async def on_message_delete(message):

    channel_ch = message.channel

    channel = str(channel_ch)

    if channel not in deleted_message_cache.keys():
        return

    if channel not in history_channel_messages.keys():
        history_channel_messages[channel] = deleted_message_cache[channel]
        deleted_message_cache.pop(channel)
        history_channel_timers[channel] = 2 * 60

        while history_channel_timers[channel] != 0:
            timer = history_channel_timers[channel]

            timer -= 1

            history_channel_timers[channel] = timer

            await asyncio.sleep(1)

        await channel_ch.send('The last ' + str(len(history_channel_messages[channel])) + ' messages have been arquived!')

        try:
            bot = [x for x in channel_ch.guild.categories if str(x) == 'Bot'][0]
        except IndexError:
            bot = None

        bot = bot or await channel_ch.guild.create_category('Bot')

        try:
            archive = [x for x in bot.text_channels if str(x) == 'arquivo'][0]
        except IndexError:
            archive = None

        archive = archive or await bot.create_text_channel('arquivo')

        current_author = None

        for message in history_channel_messages[channel]:

            for m, attachs in message.items():

                if current_author != m.author:
                    date = m.created_at + timedelta(hours=1)
                    header = '```css\n' + str(m.author) + ' em ' + str(date)[:len(str(date)) - 10].replace(' ', ' às ') + ' em #' + str(m.channel) + ':```\n'
                else:
                    header = ''

                sent = await archive.send(header + m.content, files=attachs)

                for reaction in m.reactions:
                    await sent.add_reaction(reaction.emoji)

                current_author = m.author

        history_channel_messages.pop(channel)
        history_channel_timers.pop(channel)

    else:
        history_channel_timers[channel] = 2 * 60
        messages = history_channel_messages[channel]
        _new = deleted_message_cache[channel] + messages
        deleted_message_cache.pop(channel)
        history_channel_messages[channel] = _new


@pybot.event
async def on_raw_bulk_message_delete(payload: discord.RawBulkMessageDeleteEvent):

    channel_ch = pybot.get_channel(payload.channel_id)

    channel = str(channel_ch)

    if channel not in deleted_message_cache.keys():
        return

    if channel not in history_channel_messages.keys():
        history_channel_messages[channel] = deleted_message_cache[channel]
        deleted_message_cache.pop(channel)
        history_channel_timers[channel] = 2 * 60

        while history_channel_timers[channel] != 0:
            timer = history_channel_timers[channel]

            timer -= 1

            history_channel_timers[channel] = timer

            await asyncio.sleep(1)

        await channel_ch.send('The last ' + str(len(history_channel_messages[channel])) + ' messages have been arquived!')

        try:
            bot = [x for x in channel_ch.guild.categories if str(x) == 'Bot'][0]
        except IndexError:
            bot = None

        bot = bot or await channel_ch.guild.create_category('Bot')

        try:
            archive = [x for x in bot.text_channels if str(x) == 'arquivo'][0]
        except IndexError:
            archive = None

        archive = archive or await bot.create_text_channel('arquivo')

        current_author = None

        for message in history_channel_messages[channel]:

            for m, attachs in message.items():

                if current_author != m.author:
                    date = m.created_at + timedelta(hours=1)
                    header = '```css\n' + str(m.author) + ' em ' + str(date)[:len(str(date)) - 10].replace(' ', ' às ') + ' em #' + str(m.channel) + ':```\n'
                else:
                    header = ''

                sent = await archive.send(header + m.content, files=attachs)

                for reaction in m.reactions:
                    await sent.add_reaction(reaction.emoji)

                current_author = m.author

        history_channel_messages.pop(channel)
        history_channel_timers.pop(channel)

    else:
        history_channel_timers[channel] = 2 * 60
        messages = history_channel_messages[channel]
        _new = deleted_message_cache[channel] + messages
        deleted_message_cache.pop(channel)
        history_channel_messages[channel] = _new


@pybot.event
async def on_member_remove(member: discord.Member):
    await member.guild.system_channel.send(str(member) + ' has left the server!!\nFuck him! Who needs him anyway?\n:rage:')


@pybot.event
async def on_voice_state_update(member, before, after):
    if not before.channel:
        return

    if member.mention == pybot.user.mention:
        try:
            voice_clients.pop(before.channel.name)
            channel_playlist.pop(before.channel.name)
            owners_list.pop(before.channel.name)
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


@pybot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if (str(payload.emoji) == '🐸' or str(payload.emoji) == '<:torta:635479359645286428>') and payload.user_id == pybot.user.id:
        await (await pybot.get_channel(payload.channel_id).fetch_message(payload.message_id)).add_reaction(payload.emoji)

pybot.run('NTcyMjMyMjkyOTI4NTg1NzUx.XPCD3w.t0rEhyZw9yVWg1YHQNbeGVk97EA')

# :trap:594276902425067550
