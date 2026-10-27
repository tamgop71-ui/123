import aiomysql
import json

class Database:
    def __init__(self, config):
        self.config = config
        self.pool = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(**self.config)

    async def get_user(self, peer_id: int, user_id: int, super_ids: list):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE peer_id = %s AND user_id = %s",
                    (peer_id, user_id)
                )
                res = await cur.fetchone()
                if not res:
                    is_super = 1 if user_id in super_ids else 0
                    await cur.execute(
                        "INSERT INTO users (peer_id, user_id, is_super) VALUES (%s, %s, %s)",
                        (peer_id, user_id, is_super)
                    )
                    return {
                        "peer_id": peer_id, "user_id": user_id, "role": 0, 
                        "is_super": is_super, "warns": 0, "is_banned": 0, 
                        "nickname": None, "experience": 0, "reputation": 0
                    }
                if user_id in super_ids and not res["is_super"]:
                    await cur.execute("UPDATE users SET is_super = 1 WHERE user_id = %s", (user_id,))
                    res["is_super"] = 1
                return res

    async def set_role(self, peer_id: int, user_id: int, role: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (peer_id, user_id, role) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE role = %s",
                    (peer_id, user_id, role, role)
                )

    async def set_super(self, user_id: int, is_super: bool):
        val = 1 if is_super else 0
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE users SET is_super = %s WHERE user_id = %s", (val, user_id))

    async def add_warn(self, peer_id: int, user_id: int, reason: str, given_by: int) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (peer_id, user_id, warns) VALUES (%s, %s, 1) "
                    "ON DUPLICATE KEY UPDATE warns = warns + 1",
                    (peer_id, user_id)
                )
                await cur.execute(
                    "INSERT INTO warns_history (peer_id, user_id, reason, given_by) VALUES (%s, %s, %s, %s)",
                    (peer_id, user_id, reason, given_by)
                )
                await cur.execute("SELECT warns FROM users WHERE peer_id = %s AND user_id = %s", (peer_id, user_id))
                res = await cur.fetchone()
                return res[0]

    async def remove_warn(self, peer_id: int, user_id: int) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET warns = GREATEST(0, warns - 1) WHERE peer_id = %s AND user_id = %s",
                    (peer_id, user_id)
                )
                await cur.execute("SELECT warns FROM users WHERE peer_id = %s AND user_id = %s", (peer_id, user_id))
                res = await cur.fetchone()
                return res[0] if res else 0

    async def set_ban(self, peer_id: int, user_id: int, is_banned: bool):
        val = 1 if is_banned else 0
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (peer_id, user_id, is_banned) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE is_banned = %s",
                    (peer_id, user_id, val, val)
                )

    async def set_nickname(self, peer_id: int, user_id: int, nick: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (peer_id, user_id, nickname) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE nickname = %s",
                    (peer_id, user_id, nick, nick)
                )

    async def add_exp(self, peer_id: int, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (peer_id, user_id, experience) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE experience = experience + %s",
                    (peer_id, user_id, amount, amount)
                )

    async def change_rep(self, peer_id: int, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (peer_id, user_id, reputation) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE reputation = reputation + %s",
                    (peer_id, user_id, amount, amount)
                )

    async def get_top_exp(self, peer_id: int, limit: int = 10):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT user_id, experience, nickname FROM users WHERE peer_id = %s ORDER BY experience DESC LIMIT %s",
                    (peer_id, limit)
                )
                return await cur.fetchall()

    async def get_staff(self, peer_id: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT user_id, role, is_super, nickname FROM users WHERE peer_id = %s AND (role > 0 OR is_super = 1) ORDER BY role DESC",
                    (peer_id,)
                )
                return await cur.fetchall()
