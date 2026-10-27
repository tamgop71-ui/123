import asyncio
import re
import json
import random
from vk_api.vk_api import VkApiGroup
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import VK_TOKEN, DB_CONFIG, SUPER_ADMIN_IDS
from database import Database

db = Database(DB_CONFIG)
vk_session = VkApiGroup(token=VK_TOKEN)
vk = vk_session.get_api()

# Загрузка вопросов для тестов/викторины из questions.json
try:
    with open("questions.json", "r", encoding="utf-8") as f:
        QUESTIONS = json.load(f)
except Exception:
    QUESTIONS = []

# Иерархия 8 уровней команд (0..7)
COMMAND_LEVELS = {
    # Уровень 0 - Обычный пользователь
    '/help': 0, '/id': 0, '/stats': 0, '/top': 0, '/q': 0, '/premium': 0,
    '/bonus': 0, '/transfer': 0, '/duel': 0, '/guess': 0, '/cmd': 0,
    '/chatid': 0, '/chats': 0, '/report': 0, '/rep': 0, '/exam': 0,

    # Уровень 1 - Младший Модератор
    '/kick': 1, '/mute': 1, '/warn': 1, '/clear': 1, '/staff': 1,
    '/olist': 1, '/getnick': 1, '/snick': 1, '/rnick': 1, '/nlist': 1,
    '/check': 1, '/scan': 1, '/invited': 1, '/setaccess': 1, '/delaccess': 1,

    # Уровень 2 - Модератор
    '/unmute': 2, '/unwarn': 2, '/mutelist': 2, '/warnlist': 2,

    # Уровень 3 - Старший Модератор / Администратор
    '/ban': 3, '/unban': 3, '/kickmenu': 3, '/banlist': 3,
    '/timeout': 3, '/zov': 3, '/inactive': 3,

    # Уровень 4 - Глобальный Админ
    '/gkick': 4, '/gban': 4, '/gunban': 4, '/gmute': 4, '/gunmute': 4,
    '/gwarn': 4, '/gunwarn': 4, '/gsnick': 4, '/grnick': 4, '/gzov': 4,

    # Уровень 5 - Спец. Администратор
    '/skick': 5, '/sban': 5, '/sunban': 5, '/ssnick': 5, '/srnick': 5,
    '/szov': 5, '/chat': 5, '/antitag': 5, '/pin': 5, '/unpin': 5,

    # Уровень 6 - Зам. Владельца
    '/demote': 6, '/resetnick': 6, '/resetaccess': 6, '/chatlimit': 6,
    '/rename': 6, '/notif': 6, '/purge': 6, '/ignore': 6, '/unignore': 6,
    '/ignorelist': 6, '/gsetaccess': 6, '/gdelaccess': 6, '/ssetaccess': 6, '/sdelaccess': 6,

    # Уровень 7 - Создатель / Владелец беседы
    '/creategroup': 7, '/delgroup': 7, '/mygroups': 7, '/levelname': 7,
    '/resetlevel': 7, '/async': 7, '/delasync': 7, '/bind': 7, '/unbind': 7,
    '/bindlist': 7, '/filter': 7, '/filteradd': 7, '/filterdel': 7,
    '/listasync': 7, '/editlevel': 7, '/giveowner': 7, '/settings': 7, '/import': 7
}

ROLE_NAMES = {
    0: "Пользователь",
    1: "Младший Модератор",
    2: "Модератор",
    3: "Старший Модератор",
    4: "Администратор",
    5: "Глобальный Админ",
    6: "Зам. Владельца",
    7: "Создатель Беседы"
}

def send_msg(peer_id, text):
    try:
        vk.messages.send(peer_id=peer_id, message=text, random_id=0)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def extract_user_id(event):
    if 'reply_message' in event.obj.message:
        return event.obj.message['reply_message']['from_id']
    text = event.obj.message.get('text', '')
    match = re.search(r'\[id(\d+)\|', text)
    if match:
        return int(match.group(1))
    return None

async def main():
    await db.connect()
    print("Бот успешно подключился к MySQL базе данных 127.0.0.1!")
    
    group_info = vk.groups.getById()[0]
    group_id = group_info['id']
    longpoll = VkBotLongPoll(vk_session, group_id)
    print("Бот модерации бесед с 8 уровнями и СУПЕР-доступом полностью запущен!")

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.obj.message
            peer_id = msg['peer_id']
            from_id = msg['from_id']
            text = msg.get('text', '').strip()

            if peer_id < 2000000000:
                continue

            user_data = await db.get_user(peer_id, from_id, SUPER_ADMIN_IDS)

            # Автоматический кик забаненных пользователей
            if user_data['is_banned'] and not user_data['is_super']:
                try:
                    vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=from_id)
                except Exception:
                    pass
                continue

            if text.startswith('/'):
                args = text.split()
                cmd = args[0].lower()

                # --- Супер-Команды Владельца / Разработчика ---
                if cmd == '/sdev':
                    if not user_data['is_super']:
                        send_msg(peer_id, "⛔ Команда доступна только Разработчику / Владельцу бота!")
                        continue
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя (ответом или через @mention).")
                        continue
                    await db.set_super(target_id, True)
                    send_msg(peer_id, f"👑 Пользователю [id{target_id}|Участнику] выдан СУПЕР-ДОСТУП! Ему доступны абсолютно все команды.")
                    continue

                if cmd == '/unsdev':
                    if not user_data['is_super']:
                        send_msg(peer_id, "⛔ Команда доступна только Разработчику / Владельцу бота!")
                        continue
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue
                    await db.set_super(target_id, False)
                    send_msg(peer_id, f"🛡️ У пользователя [id{target_id}|Участник] аннулирован СУПЕР-ДОСТУП.")
                    continue

                # --- Проверка прав по иерархии ---
                required_level = COMMAND_LEVELS.get(cmd)
                if required_level is not None:
                    # СУПЕР-ДОСТУП обходит абсолютно любые ограничения
                    if not user_data['is_super'] and user_data['role'] < required_level:
                        send_msg(peer_id, f"⛔ Команда {cmd} требует Уровень {required_level} ({ROLE_NAMES.get(required_level, 'Админ')})! Ваш уровень: {user_data['role']}.")
                        continue

                # --- Команды бота ---
                if cmd == '/help':
                    user_lvl = "СУПЕР-АДМИН 👑" if user_data['is_super'] else f"Уровень {user_data['role']} ({ROLE_NAMES.get(user_data['role'])})"
                    send_msg(peer_id, f"📄 Ваш статус: {user_lvl}\n\nИспользуйте доступные команды вашего уровня (0–7). Для изменения прав используйте /setaccess.")

                elif cmd in ['/id', '/stats']:
                    target_id = extract_user_id(event) or from_id
                    t_data = await db.get_user(peer_id, target_id, SUPER_ADMIN_IDS)
                    role_str = "👑 СУПЕР-АДМИН" if t_data['is_super'] else f"Уровень {t_data['role']} ({ROLE_NAMES.get(t_data['role'])})"
                    send_msg(
                        peer_id,
                        f"📊 Профиль [id{target_id}|Пользователя]:\n"
                        f"🔹 Роль: {role_str}\n"
                        f"⭐ Опыт: {t_data['experience']}\n"
                        f"🏆 Репутация: {t_data['reputation']}\n"
                        f"⚠️ Предупреждения: {t_data['warns']}/3\n"
                        f"🚫 Бан: {'Да' if t_data['is_banned'] else 'Нет'}"
                    )

                elif cmd == '/setaccess':
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue
                    try:
                        new_lvl = int(args[-1])
                        if new_lvl < 0 or new_lvl > 7:
                            raise ValueError
                    except ValueError:
                        send_msg(peer_id, "⚠️ Укажите уровень от 0 до 7 (Пример: /setaccess 3).")
                        continue

                    if not user_data['is_super'] and new_lvl >= user_data['role']:
                        send_msg(peer_id, "⛔ Вы не можете выдать уровень равный или выше вашего собственного!")
                        continue

                    await db.set_role(peer_id, target_id, new_lvl)
                    send_msg(peer_id, f"✅ Пользователю [id{target_id}|Участник] установлен {new_lvl} Уровень прав ({ROLE_NAMES.get(new_lvl)}).")

                elif cmd == '/delaccess':
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue
                    await db.set_role(peer_id, target_id, 0)
                    send_msg(peer_id, f"✅ У пользователя [id{target_id}|Участник] сброшены права до 0 уровня.")

                elif cmd == '/kick':
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue
                    t_data = await db.get_user(peer_id, target_id, SUPER_ADMIN_IDS)
                    if not user_data['is_super'] and t_data['role'] >= user_data['role']:
                        send_msg(peer_id, "⛔ Нельзя исключить пользователя с равным или высоким уровнем!")
                        continue
                    try:
                        vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
                        send_msg(peer_id, f"👞 Пользователь [id{target_id}|Участник] исключен из беседы.")
                    except Exception:
                        send_msg(peer_id, "❌ Ошибка при исключении. Проверьте права бота в беседе!")

                elif cmd == '/warn':
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue
                    reason = " ".join(args[1:]) if len(args) > 1 else "Нарушение правил"
                    warns_cnt = await db.add_warn(peer_id, target_id, reason, from_id)
                    if warns_cnt >= 3:
                        await db.set_ban(peer_id, target_id, True)
                        try:
                            vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
                            send_msg(peer_id, f"⛔ Пользователь [id{target_id}|Участник] получил 3/3 варнов и забанен!")
                        except Exception:
                            send_msg(peer_id, f"⚠️ Выдан 3-й варн, но не удалось исключить пользователя.")
                    else:
                        send_msg(peer_id, f"⚠️ Пользователю [id{target_id}|Участник] выдан варн ({warns_cnt}/3). Причина: {reason}")

                elif cmd == '/unwarn':
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue
                    w_cnt = await db.remove_warn(peer_id, target_id)
                    send_msg(peer_id, f"✅ С пользователя [id{target_id}|Участник] снят варн. Текущие варны: {w_cnt}/3.")

                elif cmd == '/ban':
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue
                    await db.set_ban(peer_id, target_id, True)
                    try:
                        vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
                    except Exception:
                        pass
                    send_msg(peer_id, f"⛔ Пользователь [id{target_id}|Участник] забанен.")

                elif cmd == '/unban':
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue
                    await db.set_ban(peer_id, target_id, False)
                    send_msg(peer_id, f"✅ Пользователь [id{target_id}|Участник] разбанен.")

                elif cmd == '/staff':
                    staff_list = await db.get_staff(peer_id)
                    if not staff_list:
                        send_msg(peer_id, "📋 В беседе нет пользователей с повышенными правами.")
                        continue
                    lines = ["📋 Администрация беседы:"]
                    for s in staff_list:
                        r_str = "👑 СУПЕР-АДМИН" if s['is_super'] else f"Lvl {s['role']} ({ROLE_NAMES.get(s['role'])})"
                        lines.append(f"• [id{s['user_id']}|Участник] — {r_str}")
                    send_msg(peer_id, "\n".join(lines))

                elif cmd == '/exam':
                    if not QUESTIONS:
                        send_msg(peer_id, "❓ Вопросы для экзамена не загружены.")
                        continue
                    q = random.choice(QUESTIONS)
                    opts = "\n".join([f"{idx+1}. {o}" for idx, o in enumerate(q['options'])])
                    send_msg(peer_id, f"📝 Вопрос экзамена/теста:\n{q['question']}\n\nВарианты ответов:\n{opts}")

if __name__ == '__main__':
    asyncio.run(main())
