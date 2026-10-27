import asyncio
import re
from vk_api.vk_api import VkApiGroup
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import VK_TOKEN, DB_CONFIG
from database import Database

db = Database(DB_CONFIG)
vk_session = VkApiGroup(token=VK_TOKEN)
vk = vk_session.get_api()

def extract_user_id(event):
    if 'reply_message' in event.obj.message:
        return event.obj.message['reply_message']['from_id']
    text = event.obj.message.get('text', '')
    match = re.search(r'\[id(\d+)\|', text)
    if match:
        return int(match.group(1))
    return None

def send_msg(peer_id, text):
    try:
        vk.messages.send(
            peer_id=peer_id,
            message=text,
            random_id=0
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

async def main():
    await db.connect()
    print("Успешное подключение к внешней базе данных MySQL!")
    
    group_info = vk.groups.getById()[0]
    group_id = group_info['id']
    
    longpoll = VkBotLongPoll(vk_session, group_id)
    print("Бот модерации бесед запущен!")

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.obj.message
            peer_id = msg['peer_id']
            from_id = msg['from_id']
            text = msg.get('text', '').strip()

            if peer_id < 2000000000:
                continue

            user_data = await db.get_user(peer_id, from_id)
            if user_data and user_data['is_banned']:
                try:
                    vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=from_id)
                except Exception:
                    pass
                continue

            if text.startswith('/'):
                args = text.split()
                cmd = args[0].lower()

                if cmd == '/role':
                    if user_data['role'] < 2:
                        send_msg(peer_id, "⛔ У вас недостаточно прав (нужен уровень 2+).")
                        continue
                    
                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя (ответом или через @mention).")
                        continue
                    
                    try:
                        new_role = int(args[-1])
                        if new_role < 0 or new_role > 3:
                            raise ValueError
                    except ValueError:
                        send_msg(peer_id, "⚠️ Укажите корректную роль от 0 до 3.")
                        continue

                    if new_role >= user_data['role']:
                        send_msg(peer_id, "⛔ Вы не можете выдать роль равную или выше вашей!")
                        continue

                    await db.set_role(peer_id, target_id, new_role)
                    send_msg(peer_id, f"✅ Пользователю [id{target_id}|Участнику] присвоена роль Уровня {new_role}.")

                elif cmd == '/warn':
                    if user_data['role'] < 1:
                        send_msg(peer_id, "⛔ Команда доступна Модераторам [1]+.")
                        continue

                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Ответьте на сообщение или упомяните нарушителя.")
                        continue

                    reason = " ".join(args[1:]) if len(args) > 1 else "Нарушение правил"
                    warns_count = await db.add_warn(peer_id, target_id, reason, from_id)

                    if warns_count >= 3:
                        await db.set_ban(peer_id, target_id, True)
                        try:
                            vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
                            send_msg(peer_id, f"⛔ Пользователь [id{target_id}|Участник] получил 3/3 варнов и забанен!")
                        except Exception:
                            send_msg(peer_id, f"⚠️ Выдан 3-й варн, но не удалось кикнуть пользователя.")
                    else:
                        send_msg(peer_id, f"⚠️ Выдан варн [id{target_id}|Участнику] ({warns_count}/3). Причина: {reason}")

                elif cmd == '/unwarn':
                    if user_data['role'] < 1:
                        send_msg(peer_id, "⛔ Недостаточно прав.")
                        continue

                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue

                    warns_count = await db.remove_warn(peer_id, target_id)
                    send_msg(peer_id, f"✅ С пользователя [id{target_id}|Участник] снят варн. Текущие варны: {warns_count}/3")

                elif cmd == '/kick':
                    if user_data['role'] < 1:
                        send_msg(peer_id, "⛔ Недостаточно прав.")
                        continue

                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue

                    target_data = await db.get_user(peer_id, target_id)
                    if target_data['role'] >= user_data['role']:
                        send_msg(peer_id, "⛔ Вы не можете кикнуть участника с равными или высшими правами!")
                        continue

                    try:
                        vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
                        send_msg(peer_id, f"👞 Пользователь [id{target_id}|Участник] исключён.")
                    except Exception:
                        send_msg(peer_id, "❌ Ошибка при попытке исключить пользователя.")

                elif cmd == '/ban':
                    if user_data['role'] < 2:
                        send_msg(peer_id, "⛔ Команда доступна Администраторам [2]+.")
                        continue

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
                    if user_data['role'] < 2:
                        send_msg(peer_id, "⛔ Команда доступна Администраторам [2]+.")
                        continue

                    target_id = extract_user_id(event)
                    if not target_id:
                        send_msg(peer_id, "⚠️ Укажите пользователя.")
                        continue

                    await db.set_ban(peer_id, target_id, False)
                    send_msg(peer_id, f"✅ Пользователь [id{target_id}|Участник] разбанен.")

                elif cmd in ['/profile', '/myrole']:
                    role_names = {0: "Участник", 1: "Модератор", 2: "Администратор", 3: "Создатель"}
                    send_msg(
                        peer_id,
                        f"👤 Профиль [id{from_id}|Участника]:\n"
                        f"🔹 Роль: {role_names.get(user_data['role'], 'Участник')} (Уровень {user_data['role']})\n"
                        f"⚠️ Предупреждения: {user_data['warns']}/3\n"
                        f"🚫 Статус бана: {'Да' if user_data['is_banned'] else 'Нет'}"
                    )

if __name__ == '__main__':
    asyncio.run(main())
