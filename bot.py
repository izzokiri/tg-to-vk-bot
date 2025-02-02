import os
import vk_api
import requests
from datetime import datetime
from dotenv import load_dotenv

# Загружаем токен из .env
load_dotenv()
VK_TOKEN = os.getenv("VK_TOKEN")  # Токен из настроек группы
GROUP_ID = os.getenv("VK_GROUP_ID")  # ID группы ВКонтакте (без "-"!)


# Функция для получения курса юаня
def get_yuan_rate():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["Valute"]["CNY"]["Value"]
    except Exception as e:
        print(f"Ошибка при получении курса: {e}")
        return None


# Функция для публикации поста в группу
def post_to_vk():
    rate = get_yuan_rate()
    if rate is None:
        print("❌ Не удалось получить курс юаня!")
        return

    today_date = datetime.now().strftime("%d.%m.%Y")

    rate_200 = rate + 0.8
    rate_2000 = rate + 0.7
    rate_6000 = rate + 0.6

    # Формируем сообщение
    message = (
        f"🇨🇳 Актуальный курс на {today_date}:\n"
        f"От 200¥ - {rate_200:.2f}₽\n"
        f"От 2000¥ - {rate_2000:.2f}₽\n"
        f"От 6000¥ - {rate_6000:.2f}₽"
    )

    # Авторизация в ВК
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()

    # Публикация поста
    try:
        vk.wall.post(owner_id=f"-{GROUP_ID}", message=message, from_group=1)
        print("✅ Пост успешно опубликован в группу!")
    except Exception as e:
        print(f"❌ Ошибка при публикации поста: {e}")


# Запуск публикации
if __name__ == "__main__":
    post_to_vk()
