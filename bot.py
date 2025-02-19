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
def post_to_vk(text, photo_urls=None):
    try:
        # Заменяем "@freelogistics" на "@freelogistics1"
        if "@freelogistics" in text:
            text = text.replace("@freelogistics", "@freelogistics1")
            print("✅ Заменено '@freelogistics' на '@freelogistics1'")

        vk_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
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


# Функция для публикации поста в ВКонтакте с прикрепленными фото (используется токен группы)
def post_to_vk(text, photo_urls=None):
    try:
        # Заменяем "@freelogistics" на "@freelogistics1"
        if "@freelogistics" in text:
            text = text.replace("@freelogistics", "@freelogistics1")
            print("✅ Заменено '@freelogistics' на '@freelogistics1'")

        vk_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
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
    offset = 0  # Начальное значение offset
    posts = {}

    while True:
        updates = await bot.get_updates(offset=offset)
        if not updates:
            break  # Если обновлений больше нет, выходим из цикла

        for update in updates:
            if update.channel_post and update.channel_post.chat.id == int(TELEGRAM_CHANNEL_ID):
                message: Message = update.channel_post
                message_date = message.date.date()

                # Проверяем, что пост еще не был обработан
                if message_date == today and message.message_id not in posts:
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

                    # Собираем все фотографии из поста (используем только самую большую версию)
                    if message.photo:
                        # Используем последний элемент в списке (самая большая версия)
                        largest_photo = message.photo[-1]
                        file_info = await bot.get_file(largest_photo.file_id)
                        photo_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_info.file_path}"
                        photos.append(photo_url)

                    # Группируем посты по их ID
                    posts[message.message_id] = {"text": text, "photos": photos}

                # Обновляем offset
                offset = update.update_id + 1

    # Возвращаем список постов
    return list(posts.values())


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
