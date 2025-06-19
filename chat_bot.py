import os
import uuid

from dotenv import find_dotenv, load_dotenv
from langchain_gigachat.chat_models import GigaChat
from langchain_core.runnables import RunnableConfig

load_dotenv(find_dotenv())

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
    
    print("=" * 50)
    print("Чат с инженером-строителем (GigaChat)")
    print("Для выхода введите 'выход' или 'exit'")
    print("=" * 50)
    
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
                "content": "ответь приветственно",
                "attachments": 
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
    chat_with_gigachat()