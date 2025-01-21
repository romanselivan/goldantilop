# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

# Токены и идентификаторы
ADMIN_ID_1 = int(os.getenv('ADMIN_ID_1'))
ADMIN_ID_2 = int(os.getenv('ADMIN_ID_2'))
ADMIN_IDS = [os.getenv('ADMIN_ID_1'), os.getenv('ADMIN_ID_2')]
BOT_TOKEN = os.getenv('BOT_TOKEN')
G_SHEET_CRED = os.getenv('G_SHEET_CRED')
G_SHEET_ID = os.getenv('G_SHEET_ID')

# Параметры кэширования
CACHE_TTL = timedelta(minutes=10)
CACHE_UPDATE_INTERVAL = timedelta(hours=1)

# Названия листов в Google Sheets
USERS_SHEET = 'Users'
RATES_SHEET = 'Rates'
REQUESTS_SHEET = 'Requests'
ANALYTICS_SHEET = 'Analytics'

# Статусы пользователей и заявок
class UserStatus:
    ADMIN = 'admin'
    ACTIVE = 'active'
    PENDING = 'pending'
    BAN = 'ban'

# Константы состояний
class UserState:
     MAIN_MENU = 'main_menu'
     ADMIN_MENU = 'admin_menu'
     WAITING_REFERRAL = 'waiting_referral'

class RequestStatus:
    CHECK = 'check'
    RUN = 'run'
    DONE = 'done'
    CANCEL = 'cancel'
    CHECK_TEXT = "на проверке"
    RUN_TEXT = "в работе"
    DONE_TEXT = "выполнено"
    CANCEL_TEXT = "отмена"

# class States(Enum):
#     START = 'start'
#     MAIN_MENU = 'main_menu'
#     ADMIN_MENU = 'admin_menu'
#     CHOOSING_SOURCE = 'choosing_source'
#     CHOOSING_TARGET = 'choosing_target'
#     ENTERING_AMOUNT = 'entering_amount'
#     CONFIRMING_EXCHANGE = 'confirming_exchange'
#     WAITING_REFERRAL = 'waiting_referral'
#     WAITING_FOR_HELP_ACTION = 'waiting_for_help_action'
#     WRITING_TO_ADMIN = 'writing_to_admin'
#     WAITING_FOR_COMPLETION_MESSAGE = 'waiting_for_completion_message'

# Названия полей в таблицах
class UserFields:
    USER_ID = 'USER_ID'
    USERNAME = 'USERNAME'
    USER_STATUS = 'USER_STATUS'
    USER_STATE = 'USER_STATE'
    BALANCE = 'BALANCE'
    REFERRAL1_ID = 'REFERRAL1_ID'
    REFERRAL1_USERNAME = 'REFERRAL1_USERNAME'
    REFERRAL1_STATUS = 'REFERRAL1_STATUS'
    REFERRAL2_ID = 'REFERRAL2_ID'
    REFERRAL2_USERNAME = 'REFERRAL2_USERNAME'
    REFERRAL2_STATUS = 'REFERRAL2_STATUS'
    RATING = 'RATING'
    REFERRAL1_MESSAGE_ID = 'REFERRAL1_MESSAGE_ID'
    REFERRAL2_MESSAGE_ID = 'REFERRAL2_MESSAGE_ID'
    LAST_ACTIVITY = 'LAST_ACTIVITY'

class RateFields:
    SOURCE_CURRENCY = 'SOURCE_CURRENCY'
    TARGET_CURRENCY = 'TARGET_CURRENCY'
    RATE = 'RATE'
    MIN_AMOUNT = 'MIN_AMOUNT'
    LAST_UPDATED = 'Last_Updated'
    TEZ_PERCENT = 'Tez%'

class RequestFields:
    REQUEST_ID = 'REQUEST_ID'
    USER_ID = 'USER_ID'
    USERNAME = 'USERNAME'
    SOURCE_CURRENCY = 'SOURCE_CURRENCY'
    TARGET_CURRENCY = 'TARGET_CURRENCY'
    AMOUNT = 'AMOUNT'
    RESULT = 'RESULT'
    STATUS = 'STATUS'
    CREATED_AT = 'CREATED_AT'
    UPDATED_AT = 'UPDATED_AT'

class AnalyticsFields:
    METRIC = 'METRIC'
    VALUE = 'VALUE'
    LAST_UPDATED = 'LAST_UPDATED'

# Локализация сообщений и текстов интерфейса
class Messages:
    # 🌀 Общие сообщения
    USER_WELCOME = """Я – Золотая Антилопа 🐾
Превращаю материю в энергию ✨

Прихожу только к добрым и честным людям, которые готовы поручиться друг за друга 🤝
Мы все здесь по собственному желанию и личной рекомендации.
        
Дзинь! 💫"""

    ERROR = "⚡ Что-то пошло не так. Пробуй снова или взывай к верховным силам."
    MAIN_MENU_TEXT = "✨"
    MAIN_MENU_ACTION_MESSAGE = "✨"
    CRITICAL_ERROR = "⚠️ Перегрев реальности. Антилопа уже знает."
    UNEXPECTED_ERROR = "🌫️ Туманная ошибка. Попробуй позже."
    ERROR_NO_REQUEST_ID = "👁 Слетали цифры. Посчитай сначала."

    HELP_TEXT = """Как тут все устроено:

✨ Я объединяю запросы круга друзей, оптимизирую потоки и создаю лучшие условия.

С кэшем работаю по Барселоне и Москве. Другие города по запросу (пиши, помогу – везде друзья).

Все считай, проверяй, если устраивает – жми "Мне ок, меняемся 🤝" и мне придет твой запрос.
Я всё быстро проверю (минут 5-20 обычно) и напишу в личку, чтобы обменяться реквизитами или договориться о встрече, если кэш.

Я стремлюсь к лучшим условиям для нас. Знаешь как сделать выгоднее? Пиши, я в долгу не останусь.
        
Для обратной связи жми 'Написать Антилопе'.
        
Дзинь! 💫"""  # Текст справки для пользователей
    
    CURRENT_EXCHANGE_RATES = "📊 Курс энергии текущего цикла:\n\n" # Заголовок для списка курсов обмена

    # 💡 Сообщения для пользователей
    SET_USERNAME = "👁️ Без имени = без племени. Создай @username в настройках Telegram и возвращайся."
    USER_BANNED = "Антилопа ушла в джунгли. Дзинь! 💫"
    UNKNOWN_STATUS = "🔮 Состояние неизвестно. Обратись к оракулу."

    CHOOSE_SOURCE_CURRENCY = "Выбирай свои монеты:"  # При выборе исходной валюты для обмена
    CHOOSE_TARGET_CURRENCY = "Выберай мои:"  # При выборе целевой валюты для обмена
    SOURCE_AND_TARGET_CURRENCY = "У тебя {source_currency}. Вот что есть у меня, выбирай:" # Сообщение после выбора исходной валюты, при выборе целевой валюты
    EXCHANGE_RATE_NOT_FOUND = "🌑 Тени скрывают курс для {source_currency} ➡️ {target_currency}. Начни заново." # Сообщение, если курс обмена не найден
    ENTER_EXCHANGE_AMOUNT = "За твои {source_currency} я даю свои {target_currency}.\nНапиши сколько (мин {min_amount:,} {source_currency}):" # Сообщение для ввода суммы обмена
    INVALID_AMOUNT = "🌪️ Это число не обладает гармонией. Пробуй снова."  # Сообщение при вводе некорректной суммы
    ENTER_AMOUNT = "Напиши сколько (мин {min_amount:,} {currency}):"  # При вводе суммы для обмена
    EXCHANGE_RESULT = "✨ За {amount:,} {source_currency} я дам тебе {result:,} {target_currency}.\nКурс: 1 {source_currency} = {rate:.4f} {target_currency}."  # Результат расчета обмена
    CONFIRM_EXCHANGE = "Меняем?"  # Запрос подтверждения обмена
    EXCHANGE_CONFIRMED = "Я все проверю и вернусь, подожди немного. Дзинь! 💫"  # После подтверждения обмена
    REQUEST_ACCEPTED = "Заявка 🆔 {request_id} в работе. Напишу в личку обсудить детали."  # Когда админ принимает заявку
    MINIMUM_AMOUNT_ERROR = "Минимум: {min_amount:,} {currency}.\nПопробуйте снова."  # При вводе суммы меньше минимальной
    OPERATION_CANCELLED = "Все вернулось на круги своя."  # Сообщение при отмене текущей операции
    REQUEST_CREATION_ERROR = "🌌 Энергии не сошлись. Попробуй снова." # Сообщение об ошибке при создании заявки
    REQUEST_ALREADY_CREATED = "🌟 Заявка уже в пути. Доверяй процессу." # Сообщение при повторной отправке той же заявки
    EXCHANGE_RATE_FORMAT = "1 {source} = {rate:.3f} {target} (мин: {min_amount:,})\n" # Отображение строк курсов

    # Форма заявки
    REQUEST_FORMAT = "🆔: {request_id}\n📆: {date} – {status_text}\n💰 {amount} {source_currency} ➡️ {result} {target_currency}"
    ADMIN_REQUEST_FORMAT = "👤 @{username}\n" + REQUEST_FORMAT

    # Сообщения для заявок
    NO_REQUESTS = "💤 Всё чисто. Никаких заявок."  # Когда у пользователя нет активных заявок
    REQUEST_CANCELLED = "🚮 Как скажешь."  # При отмене заявки пользователем
    REQUEST_REJECTED = "Отменяю заявку 🆔 {request_id}. Начни сначала."  # Когда админ отклоняет заявку
    REQUEST_STATUS_CHANGED = "🔄 Статус заявки 🆔 {request_id} теперь {status}." # Сообщение о изменении статуса заявки
    USER_CANCELLED_REQUEST = "Пользователь отменил заявку 🆔 {request_id}"  # Уведомление админу об отмене заявки пользователем
    CANNOT_CANCEL_REQUEST = "Пока отменить нельзя, скоро я отвечу."  # При попытке отменить заявку в работе
    ENTER_REJECTION_MESSAGE = "✍️ Напиши причину:"
    ADMIN_REQUEST_REJECTED = "Заявка отменена, пользователь в курсе."
    REQUEST_REJECTED = "Твоя заявка 🆔 {request_id} отклонена: {message}"
    REQUEST_COMPLETED = "🆔 {request_id} выполнена 🎉" # Когда админ завершает заявку
    REQUEST_REJECTED_WITH_REASON = "Мне пришлось отменить заявку 🆔 {request_id}.\nПричина: {reason}"

    # Сообщения для админов
    ADMIN_WELCOME = "✨ Привет, мой дург, оракул!"  # Заголовок панели администратора
    ADMIN_MENU_MESSAGE = "✨"  # Приглашение выбрать действие в панели администратора
    ADMIN_REQUEST_CANCELLED = "Заявка 🆔 {request_id} отменена."  # Уведомление админу об отмене заявки пользователем
    ENTER_COMPLETION_MESSAGE = "✍️ Напиши причину:"  # Запрос сообщения при завершении заявки
    ADMIN_REQUEST_COMPLETED = "Заявка отменена, пользователь в курсе."  # Подтверждение завершения заявки
    NO_COMPLETED_REQUESTS = "Нет выполненных заявок." # Когда у админа нет завершенных заявок
    COMPLETED_REQUESTS_HEADER = "Выполненные заявки:\n\n" # Заголовок для списка завершенных заявок
    WRITE_TO_ADMIN_PROMPT = "О чем ты хотел поведать? Пиши:" # Когда можно написать сообщение для Антилопы в меню Помощь

    # Сообщения для функции show_friends
    ALL_USERS = "Всего пользователей: {total}\n\n"  # Показывает общее количество пользователей
    ACTIVE_USERS_HEADER = "Активные пользователи:\n"  # Заголовок для списка активных пользователей
    ACTIVE_USER_INFO = "@{username} - Рейтинг: {rating}, Баланс: {balance}\n"  # Информация о каждом активном пользователе

    # Сообщения для аналитики
    ANALYTICS_HEADER = "Аналитика по обменам:\n"  # Заголовок аналитики
    TOTAL_USERS = "Всего пользователей: {total_users}\n"  # Общее количество пользователей
    TOTAL_EXCHANGES = "Всего обменов: {total_exchanges}\n"  # Общее количество обменов
    AVERAGE_EXCHANGE_VOLUME = "Средний объем обмена: {average_volume:,}\n"  # Средний объем обмена
    MOST_POPULAR_PAIR = "Самая популярная валютная пара: {pair}\n"  # Самая популярная валютная пара
    NO_DATA = "Нет данных"  # Сообщение при отсутствии данных

    # Сообщения Антилопе из меню Помощь
    UNKNOWN_USER = "Неизвестный пользователь."  # При отправке сообщения от неизвестного пользователя
    USER_MESSAGE_PREFIX = "📜 Сообщение от пользователя:"  # Префикс сообщения от пользователя
    MESSAGE_SENT_TO_ADMIN = "📜 Сообщение отправлено Антилопе."  # Подтверждение отправки сообщения администратору

    # Сообщения для реферальной системы
    ENTER_REFERRAL = "Кто из общих друзей может за тебя поручиться? Я спрошу у него, пиши @username:"  # Запрос первого реферала
    ENTER_SECOND_REFERRAL = "Ждем... Пока друг не подтвердил, можешь указать еще одного:"  # Запрос второго реферала
    WAITING_REFERRAL_CONFIRMATION = "Ждем ответа друзей..."  # Ожидание подтверждения от рефералов
    INVALID_REFERRAL_FORMAT = "Пиши в формате @username"  # При неверном формате ввода реферала
    SELF_REFERRAL_ERROR = "Ты не можешь поручиться за самого себя, иначе начнётся петля Мёбиуса ♾️"  # При попытке указать себя рефералом
    DUPLICATE_REFERRAL = "Его уже спросила. Кого еще спросить? Пиши @username:"  # При попытке повторно ввести того же реферала
    ERROR_REFERRAL = "Что-то пошло не так. Попробуй снова."  # При ошибке добавления реферала
    UNKNOWN_REFERRAL = "Такого не знаю. Попробуй еще:"  # Когда введенный реферал не найден в системе
    REFERRAL_REQUEST_SENT = "Я спрошу у @{username}. Подожди немного."  # Подтверждение отправки запроса реферала
    REFERRAL_CONFIRMATION_REQUEST = "{username} говорит, что ты можешь поручиться за него. Что делаем?"  # Запрос подтверждения реферала
    REFERRAL_NOT_EXIST = "Ошибка: пользователь не найден."  # При попытке добавить несуществующего пользователя
    REFERRAL_APPROVE = "Отлично, @{username} теперь с нами!"  # Подтверждение реферала
    REFERRAL_REJECT = "Ну и правильно, нам нужны только надеждые друзья."  # Отклонение реферала
    REFERRAL_BAN = "Заблокировала @{username}. Спасибо за бдительность!"  # Подтверждение блокировки реферала    
    ACCOUNT_ACTIVATED = "🎉 За тебя поручился @{username}. Добро пожаловать!" # Подтверждение активации учетной записи
    ACCOUNT_BANNED = "Антилопа ушла в джунгли. Дзинь! 💫" # При блокировке учетной записи

# Тексты для кнопок и клавиатур
class ButtonTexts:
    MY_REQUESTS = "📜 Мои заявки"
    CALCULATE_EXCHANGE = "🧮 Посчитать и поменять"
    VIEW_RATES = "📈 Смотреть курсы"
    HELP = "✉️ Информация"
    FRIENDS = "👥 Друзья"
    REQUESTS = "🔄 Заявки"
    COMPLETED_REQUESTS = "🏁 Завершенные заявки"
    ANALYTICS = "📊 Аналитика"
    EXCHANGE = "Мне ок, меняемся 🤝"
    RECALCULATE = "🔁 Посчитать заново"
    CANCEL_REQUEST = "❌ Отменить заявку"
    ACCEPT_REQUEST = "✅ Принять"
    REJECT_REQUEST = "❌ Отклонить"
    COMPLETE_REQUEST = "🏁 Завершить"
    CANCEL = "✋ Отмена"
    BACK_TO_MENU = "🔙 Обратно в меню"
    WRITE_TO_ADMIN = "✍️ Написать Антилопе"
    CONFIRM_REFERRAL = "✅ Свои, запускаем!"
    DOUBT_REFERRAL = "🤔 Не готов поручиться"
    BAN_USER = "🚫 Таких точно в бан!"

# Функция для проверки, является ли пользователь администратором
def is_admin(user_id: str) -> bool:
    return user_id in ADMIN_IDS
