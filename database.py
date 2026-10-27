import aiomysql

class Database:
    def __init__(self, config):
        self.config = config
        self.pool = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(**self.config)

    async def get_user(self, peer_id: int, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM users WHERE peer_id = %s AND user_id = %s",
                    (peer_id, user_id)
                )
                res = await cur.fetchone()
                if not res:
                    await cur.execute(
                        "INSERT INTO users (peer_id, user_id) VALUES (%s, %s)",
                        (peer_id, user_id)
                    )
                    return {"peer_id": peer_id, "user_id": user_id, "role": 0, "warns": 0, "is_banned": 0}
                return res

    async def set_role(self, peer_id: int, user_id: int, role: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (peer_id, user_id, role) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE role = %s",
                    (peer_id, user_id, role, role)
                )

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
                await cur.execute(
                    "SELECT warns FROM users WHERE peer_id = %s AND user_id = %s",
                    (peer_id, user_id)
                )
                res = await cur.fetchone()
                return res[0]

    async def remove_warn(self, peer_id: int, user_id: int) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET warns = GREATEST(0, warns - 1) WHERE peer_id = %s AND user_id = %s",
                    (peer_id, user_id)
                )
                await cur.execute(
                    "SELECT warns FROM users WHERE peer_id = %s AND user_id = %s",
                    (peer_id, user_id)
                )
                res = await cur.fetchone()
                return res[0] if res else 0

    async def set_ban(self, peer_id: int, user_id: int, is_banned: bool):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                b_val = 1 if is_banned else 0
                await cur.execute(
                    "INSERT INTO users (peer_id, user_id, is_banned) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE is_banned = %s",
                    (peer_id, user_id, b_val, b_val)
                )
