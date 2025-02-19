import os
import requests
import vk_api
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.types import Message
from aiogram.client.session.aiohttp import AiohttpSession
import datetime

# Загружаем токены из .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # ID канала в формате -100xxxxxxxxxx
VK_GROUP_TOKEN = os.getenv("VK_ACCESS_TOKEN")  # Токен группы ВКонтакте
VK_USER_TOKEN = os.getenv("VK_USER_TOKEN")  # Токен пользователя ВКонтакте
GROUP_ID = os.getenv("VK_GROUP_ID")  # ID группы ВКонтакте (без "-")

# Инициализация бота Telegram
session = AiohttpSession()
bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)


# Функция для загрузки изображения на сервер ВКонтакте (используется токен пользователя)
def upload_photo_to_vk(photo_url):
    try:
        # Скачиваем изображение
        response = requests.get(photo_url)
        if response.status_code == 200:
            # Загружаем изображение на сервер ВКонтакте
            vk_session = vk_api.VkApi(token=VK_USER_TOKEN)
            upload_url = vk_session.method("photos.getWallUploadServer", {"group_id": GROUP_ID})['upload_url']
            files = {'photo': ('photo.jpg', response.content, 'image/jpeg')}
            upload_response = requests.post(upload_url, files=files).json()

            # Сохраняем изображение на сервере ВКонтакте
            save_response = vk_session.method("photos.saveWallPhoto", {
                'photo': upload_response['photo'],
                'server': upload_response['server'],
                'hash': upload_response['hash'],
                'group_id': GROUP_ID
            })
            return f"photo{save_response[0]['owner_id']}_{save_response[0]['id']}"
        else:
            print(f"❌ Ошибка при скачивании изображения: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ошибка при загрузке изображения в ВКонтакте: {e}")
        return None


# Функция для публикации поста в ВКонтакте с прикрепленными фото (используется токен группы)
def post_to_vk(text, photo_urls=None):
    try:
        # Заменяем "@freelogistics" на "@freelogistics1"
        if "@freelogistics" in text:
            text = text.replace("@freelogistics", "@freelogistics1")
            print("✅ Заменено '@freelogistics' на '@freelogistics1'")

        vk_session = vk_api.VkApi(token=VK_ACCESS_TOKEN)
        vk = vk_session.get_api()

        attachments = []
        if photo_urls:
            for photo_url in photo_urls:
                # Загружаем фото на сервер ВКонтакте
                photo_attachment = upload_photo_to_vk(photo_url)
                if photo_attachment:
                    attachments.append(photo_attachment)

        # Публикация поста от имени сообщества
        vk.wall.post(
            owner_id=f"-{GROUP_ID}",  # Отрицательное значение ID сообщества
            message=text,
            attachments=",".join(attachments) if attachments else None,
            from_group=1  # Публикуем от имени группы
        )
        print("✅ Пост успешно опубликован в группу!")
    except Exception as e:
        print(f"❌ Ошибка при публикации поста в ВКонтакте: {e}")


# Функция для получения всех постов за текущий день из Telegram-канала
async def get_today_posts():
    today = datetime.datetime.now().date()
    updates = await bot.get_updates()
    posts = []

    for update in updates:
        if update.channel_post and update.channel_post.chat.id == int(TELEGRAM_CHANNEL_ID):
            message: Message = update.channel_post
            message_date = message.date.date()

            if message_date == today:
                text = message.text or message.caption or ""
                photos = []

                # Извлекаем гиперссылки из текста
                if message.entities:
                    for entity in message.entities:
                        if entity.type == "text_link":  # Гиперссылка
                            url = entity.url
                            link_text = entity.get_text(message.text)  # Текст гиперссылки
                            # Заменяем текст на формат ВКонтакте [ссылка|текст]
                            text = text.replace(link_text, f"[{url}|{link_text}]")

                # Заменяем "@freelogistics" на "@freelogistics1"
                if "@freelogistics" in text:
                    text = text.replace("@freelogistics", "@freelogistics1")
                    print("✅ Заменено '@freelogistics' на '@freelogistics1'")

                if message.photo:
                    largest_photo = message.photo[-1]
                    file_info = await bot.get_file(largest_photo.file_id)
                    photo_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_info.file_path}"
                    photos.append(photo_url)

                posts.append({"text": text, "photos": photos})

    return posts


# Основная функция
async def main():
    posts = await get_today_posts()

    if posts:
        for post in posts:
            if post["photos"]:
                # Публикуем пост с фотографиями, прикрепляя их к посту
                post_to_vk(post["text"], post["photos"])
            else:
                # Публикуем текстовый пост
                post_to_vk(post["text"])
    else:
        print("Нет новых постов для публикации сегодня.")


# Запуск
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
