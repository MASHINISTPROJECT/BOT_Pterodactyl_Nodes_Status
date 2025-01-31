import discord
from discord.ext import tasks
import requests
from discord import Embed
from datetime import datetime
import asyncio
from requests.exceptions import RequestException

TOKEN = 'YOUR_TOKEN_BOTS'
LOG_CHANNEL_ID = [] # id канала для логов (замените: [] на id вашего канала)
STATUS_CHANNEL_ID = [] # id канала для статусов нод (замените: [] на id вашего канала)

# Активируем intents
intents = discord.Intents.default()
intents.messages = True

client = discord.Client(intents=intents)

NODES = [
    {'name': 'name_node', 'url': 'http://127.0.0.1:8888'} # Замените ip и port на ваши реальные данные
    {'name': 'name_node', 'url': 'http://127.0.0.1:8888'}
    # Добавь столько сколько у вас нод и даже больше
]

def log(level, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{now}] [{level}] {message}"
    return log_message


async def send_log_message(level, message):
    log_message = log(level, message)
    log_channel = client.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"```\n{log_message}\n```")
    else:
        print(f"Log Error: Channel not found: {log_message}")


@client.event
async def on_ready():
    print(f'Мы вошли как {client.user}')
    await send_log_message("INFO", "Бот запущен!")
    check_status.start()


status_messages = {}
error_counts = {}


@tasks.loop(minutes=1)
async def check_status():
    status_channel = client.get_channel(STATUS_CHANNEL_ID)
    if status_channel:
        await send_log_message("INFO", "Начинаю проверку статуса нод")
        for node in NODES:
            embed, error = await get_node_status_embed(node['name'], node['url'])
            if embed:
                if node['name'] in status_messages:
                     message = status_messages[node['name']]
                     await message.edit(embed=embed)
                else:
                    message = await status_channel.send(embed=embed)
                    status_messages[node['name']] = message
            
            if error:
               await handle_node_error(node, error)
        await send_log_message("INFO", "Проверка статуса нод завершена")
    else:
        await send_log_message("FATAL", f"Канал {STATUS_CHANNEL_ID} не найден")

async def handle_node_error(node, error):
    node_name = node['name']
    if node_name not in error_counts:
         error_counts[node_name] = 0

    error_counts[node_name] += 1
    if error_counts[node_name] == 1:
        message = f"Не удалось проверить статус ноды {node_name}: {error}\n@Ping staff {node_name}: NODE IS CORRUPTED"
        await send_log_message("WARN", message)
    elif error_counts[node_name] == 2:
         message = f"Не удалось проверить статус ноды {node_name} во второй раз: {error}\n@Ping staff {node_name}: NODE IS CORRUPTED"
         await send_log_message("WARN", message)
    elif error_counts[node_name] >= 3:
        message = f"[NODE]: WARNING! NODE {node_name} IS CORRUPTED, error: {error}"
        await send_log_message("FATAL", message)


async def get_node_status_embed(name, url):
    try:
        response = requests.get(f'{url}/status', timeout=10)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        status = data.get('status', 'Неизвестно')
        cpu_usage = data.get('cpu_usage', 'Неизвестно')
        ram_usage = data.get('ram_usage', 'Неизвестно')
        disk_usage = data.get('disk_usage', 'Неизвестно')

        embed = Embed(title=f"Статус ноды: {name}", color=0x00ff00)
        embed.add_field(name="Статус", value=status, inline=False)
        embed.add_field(name="Загруженность CPU", value=f"{cpu_usage}%", inline=False)
        embed.add_field(name="Загруженность RAM", value=f"{ram_usage}%", inline=False)
        embed.add_field(name="Загруженность диска", value=f"{disk_usage}%", inline=False)
        return embed, None
    except RequestException as e:
        embed = Embed(title=f"Статус ноды: {name}", color=0xff0000) # красный цвет для offline
        embed.add_field(name="Статус", value="offline", inline=False)
        embed.add_field(name="Загруженность CPU", value="error", inline=False)
        embed.add_field(name="Загруженность RAM", value="error", inline=False)
        embed.add_field(name="Загруженность диска", value="error", inline=False)
        return embed, e
    except Exception as e:
        embed = Embed(title=f"Статус ноды: {name}", color=0xff0000)
        embed.add_field(name="Статус", value="offline", inline=False)
        embed.add_field(name="Загруженность CPU", value="error", inline=False)
        embed.add_field(name="Загруженность RAM", value="error", inline=False)
        embed.add_field(name="Загруженность диска", value="error", inline=False)
        return embed, e

client.run(TOKEN)