import os
import uuid
import sqlite3
import re
from pymorphy2 import MorphAnalyzer
from datetime import datetime, timedelta, timezone

from dotenv import find_dotenv, load_dotenv
from langchain_gigachat.chat_models import GigaChat
from langchain_core.runnables import RunnableConfig
from telethon import TelegramClient
import asyncio

load_dotenv(find_dotenv())

# --- TELEGRAM PART ---
API_ID = 26369943  # Обычно это числовое значение, а не токен
API_HASH = '5f145bd49336dc4bf33a583a0ea5ecaf'
PHONE = '+79817205750'
CHANNEL_URL = 'https://t.me/+9l5IsAiymJk1MjQy'

DB_PATH = 'ai_zam.db'

# Функция для извлечения фамилий из текста (русские слова с заглавной буквы)
def extract_surnames(text):
    # Ищем слова, разделённые запятыми или пробелами, допускаем строчные буквы
    # Например: 'иванов, петров сидоров' -> ['иванов', 'петров', 'сидоров']
    # Убираем лишние символы, разбиваем по запятым и пробелам
    if not text:
        return []
    # Заменяем запятые на пробелы, разбиваем по пробелам
    words = [w.strip() for w in text.replace(',', ' ').split()]
    # Оставляем только слова из букв (русских)
    surnames = [w for w in words if w.isalpha() and len(w) > 2]
    return surnames

# Функция для морфологического поиска фамилий в staff
def find_staff_matches(surnames):
    morph = MorphAnalyzer()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    matches = []
    for surname in surnames:
        parsed = morph.parse(surname)[0]
        normal_surname = parsed.normal_form.capitalize()
        # Поиск по нормальной форме фамилии
        cursor.execute("SELECT * FROM staff WHERE full_name LIKE ?", (f"%{normal_surname}%",))
        rows = cursor.fetchall()
        for row in rows:
            matches.append(row)
    conn.close()
    return matches

async def get_today_messages_and_parse():
    async with TelegramClient('anon', API_ID, API_HASH) as client:
        entity = await client.get_entity(CHANNEL_URL)
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        messages = []
        async for msg in client.iter_messages(entity, offset_date=None):
            if msg.date < today:
                break
            messages.append(msg)
        if messages:
            print(f'Найдено сообщений за сегодня: {len(messages)}')
            print('\n--- Все сообщения за сегодня ---')
            for m in messages:
                print(f"[{m.date}] {m.text}")
            print('--- Конец списка сообщений ---\n')
            all_surnames = set()
            all_matches = []
            not_found_surnames = set()
            for m in messages:
                surnames = extract_surnames(m.text or "")
                if surnames:
                    print(f"\nСообщение: {m.text}")
                    print('Найденные фамилии:', surnames)
                    all_surnames.update(surnames)
                    matches = find_staff_matches(surnames)
                    found_surnames = set()
                    if matches:
                        print('Совпадения в staff:')
                        for match in matches:
                            print(match)
                            for surname in surnames:
                                parsed = MorphAnalyzer().parse(surname)[0]
                                normal_surname = parsed.normal_form.capitalize()
                                if normal_surname in match[1]:
                                    found_surnames.add(surname)
                        all_matches.extend(matches)
                    else:
                        print('Совпадений не найдено.')
                    not_found = set(surnames) - found_surnames
                    if not_found:
                        not_found_surnames.update(not_found)
            if not all_surnames:
                print('Фамилии не найдены ни в одном сообщении.')
            if not_found_surnames:
                print('\nФамилии, которых нет в базе данных staff:')
                for nf in not_found_surnames:
                    print(nf)
                # Отправляем сообщение в чат
                text = ("Эти фамилии отсутствуют в базе данных. "
                        "Это новые люди или написаны были с ошибкой?\n" + ", ".join(not_found_surnames))
                await client.send_message(entity, text)
        else:
            print('Нет сообщений за сегодня.')

def chat_with_gigachat():
    # Инициализация модели
    model = GigaChat(
        model="GigaChat-2-Max",
        verify_ssl_certs=False,
    )
    
    # Создаем конфигурацию с постоянным thread_id для сохранения контекста беседы
    thread_id = uuid.uuid4().hex
    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    
    # Начальная системная инструкция
    messages = [
        {"role": "system", "content": "ты инженер строитель с 30 летним стажем"}
    ]
    
    
    while True:
        # Получаем ввод пользователя
        user_input = input("\nВы: ")
        
        # Проверяем команду выхода
        if user_input.lower() in ["выход", "exit", "quit", "q"]:
            print("Завершение работы чата...")
            break
        
        # Проверяем, не является ли ввод путем к изображению
       
            
            # Добавляем сообщение с вложением
            messages.append({
                "role": "user", 
                "content": "найди фамилии в чате",
                "attachments": ""
            })
        else:
            # Обычное текстовое сообщение
            messages.append({"role": "user", "content": user_input})
        
        # Отправляем запрос и получаем ответ
        try:
            print("Ожидание ответа...")
            response = model.invoke(messages, config=config)
            
            # Добавляем ответ ассистента в историю сообщений
            messages.append({"role": "assistant", "content": response.content})
            
            # Выводим ответ
            print("\nИнженер: ")
            print(response.content)
            
        except Exception as e:
            print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    print("Получение всех сообщений за сегодня из Telegram-канала и парсинг...")
    asyncio.run(get_today_messages_and_parse())
    print("\n--- Чат с GigaChat ---\n")
    chat_with_gigachat()