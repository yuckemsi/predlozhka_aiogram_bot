import sqlite3 as sq

async def db_connect() -> None:
    global db, cur

    db = sq.connect("predlozhka.db") # соединение с базой данных, если бд нет, то файл создастся
    cur = db.cursor()

    users_query = '''
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, 
            tg_id INTEGER NOT NULL, 
            first_name TEXT
            );
            '''
    admins_query = '''
            CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY, 
            tg_id INTEGER NOT NULL,
            first_name TEXT,
            FOREIGN KEY (tg_id) REFERENCES users (tg_id),
            FOREIGN KEY (first_name) REFERENCES users (first_name)
            );
            '''
    posts_query = '''
            CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            tg_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            first_name TEXT,
            media_id TEXT, 
            caption TEXT,
            type INT,
            FOREIGN KEY (tg_id) REFERENCES users (tg_id),
            FOREIGN KEY (channel_id) REFERENCES channels (tg_id),
            FOREIGN KEY (first_name) REFERENCES users (first_name),
            FOREIGN KEY (type) REFERENCES types (id)
            );
            '''
    banlist_query = '''
            CREATE TABLE IF NOT EXISTS banlist (
            id INTEGER PRIMARY KEY, 
            tg_id INTEGER NOT NULL,
            first_name TEXT,
            FOREIGN KEY (tg_id) REFERENCES users (tg_id), 
            FOREIGN KEY (first_name) REFERENCES users (first_name)
            );
            '''
    channels_query = '''
            CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY, 
            tg_id TEXT NOT NULL, 
            channel_name TEXT NOT NULL
            );
            '''
    post_types_query = '''
            CREATE TABLE IF NOT EXISTS types (
            id INTEGER PRIMARY KEY,
            name TEXT
            );
    '''
    cur.execute(users_query)
    cur.execute(admins_query)  
    cur.execute(posts_query)
    cur.execute(banlist_query)
    cur.execute(channels_query)
    cur.execute(post_types_query)

    types = [['text'], ['photo'], ['video']]
    cur.executemany('INSERT INTO types(name) VALUES(?)', (types))
    
    db.commit()
# ЮЗЕР ЗАПРОСЫ
async def set_user(tg_id: int, first_name='') -> None:
    user = cur.execute("SELECT * FROM users WHERE tg_id = (?)", (tg_id,)).fetchone()

    if not user:
        cur.execute('INSERT INTO users(tg_id, first_name) VALUES (?, ?)', (tg_id, first_name))

        db.commit()

async def check_username(tg_id: int, first_name: str):
    name = cur.execute("SELECT first_name FROM users WHERE tg_id = (?)", (tg_id,)).fetchone()

    if name != first_name:
        cur.execute('UPDATE users SET first_name = (?) WHERE tg_id = (?)', (first_name, tg_id))
        db.commit()
        return True
    else:
        return False

async def check_ban(tg_id: int):
    user = cur.execute("SELECT * FROM banlist WHERE tg_id = (?)", (tg_id,)).fetchone()

    if not user:
        return False
    else:
        return True

async def ban_user(tg_id: int):
    user = cur.execute("SELECT * FROM banlist WHERE tg_id = (?)", (tg_id, )).fetchone()

    if not user:
        cur.execute("INSERT INTO banlist(tg_id) VALUES (?)", (tg_id,))
        db.commit()
        return False
    else:
        return True

async def unban_user(tg_id: int):
    user = cur.execute("SELECT * FROM banlist WHERE tg_id = (?)", (tg_id, )).fetchone()

    if not user:
        return False
    else:
        cur.execute('DELETE FROM banlist WHERE tg_id = (?)', (tg_id,))
        db.commit()
        return True

async def banlist():
    bans = cur.execute('SELECT * FROM banlist').fetchall()
    db.commit()
    return bans

# ПОСТ ЗАПРОСЫ
async def create_post(tg_id: int, channel_id: int, first_name: str, caption: str, post_type: int, media_id='',):
    if not media_id:
        cur.execute('INSERT INTO posts(tg_id, channel_id, type, first_name, caption) VALUES(?, ?, ?, ?, ?)', (tg_id, channel_id, post_type, first_name, caption))
    elif len(media_id) > 2:
        cur.execute('INSERT INTO posts(tg_id, channel_id, type, first_name, caption, media_id) VALUES(?, ?, ?, ?, ?, ?)', (tg_id, channel_id, post_type, first_name, caption, media_id))
    else:
        return 'Недостаточно данных для создания поста'
    db.commit()

async def delete_post(post_id: int):
    cur.execute('DELETE FROM posts WHERE id = (?)', (post_id,))
    db.commit()

async def get_all_posts():
    posts = cur.execute('SELECT * FROM posts').fetchall()
    db.commit()
    return posts

async def get_post_id(post_id: int):
    post = cur.execute("SELECT id FROM posts WHERE id = (?)", (post_id,)).fetchone()
    db.commit()
    return post

async def get_post(post_id: int):
    post = cur.execute("SELECT * FROM posts WHERE id = (?)", (post_id,)).fetchone()
    db.commit()
    return post

async def delete_user_posts(tg_id: int):
    cur.execute('DELETE FROM posts WHERE tg_id = (?)', (tg_id,))
    db.commit()
# АДМИН ЗАПРОСЫ
async def add_admin(tg_id: int, first_name: str):
    user = cur.execute("SELECT * FROM admins WHERE tg_id = (?)", (tg_id,)).fetchone()

    if not user:
        cur.execute("INSERT INTO admins(tg_id, first_name) VALUES (?, ?)", (tg_id, first_name))
        db.commit()
        return True
    else:
        return False

async def delete_admin(tg_id: int):
    user = cur.execute("SELECT * FROM admins WHERE tg_id = (?)", (tg_id,)).fetchone()

    if not user:
        return False
    else:
        cur.execute('DELETE FROM admins WHERE tg_id = (?)', (tg_id,))
        db.commit()
        return True

async def check_admin(tg_id: int):
    user = cur.execute("SELECT * FROM admins WHERE tg_id = (?)", (tg_id,)).fetchone()
    db.commit()

    if not user:
        return False
    else:
        return True
# КАНАЛ ЗАПРОСЫ
async def add_channel(tg_id: int, channel_name: str):
    channel = cur.execute("SELECT * FROM channels WHERE tg_id = (?)", (tg_id,)).fetchone()

    if not channel:
        cur.execute("INSERT INTO channels(tg_id, channel_name) VALUES (?, ?)", (tg_id, channel_name))
        db.commit()

async def delete_channel(channel_id: int):
    cur.execute('DELETE FROM channels WHERE tg_id = (?)', (channel_id,))
    db.commit()

async def get_channel(channel_id: int):
    channel = cur.execute('SELECT * FROM channels WHERE tg_id = (?)', (channel_id,)).fetchone()
    db.commit()
    return channel

async def all_channels():
    channels = cur.execute('SELECT * FROM channels').fetchall()
    db.commit()
    return channels
