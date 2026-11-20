
import sqlite3
from pathlib import Path


class ConversationMemory:
    def __init__(self, max_exchanges=10):
        self.max_exchanges = max_exchanges

        # Store the database inside the JARVIS project.
        project_dir = Path(__file__).resolve().parent
        data_dir = project_dir / "data"
        data_dir.mkdir(exist_ok=True)

        self.db_path = data_dir / "jarvis_memory.db"

        self._create_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_database(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def add_exchange(self, user_message, assistant_response):
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO conversations (role, content)
                VALUES (?, ?)
                """,
                [
                    ("user", str(user_message)),
                    ("assistant", str(assistant_response))
                ]
            )

    def get_messages(self):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM (
                    SELECT id, role, content
                    FROM conversations
                    ORDER BY id DESC
                    LIMIT ?
                )
                ORDER BY id ASC
                """,
                (self.max_exchanges * 2,)
            ).fetchall()

        return [
            {"role": role, "content": content}
            for role, content in rows
        ]

    def clear(self):
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM conversations"
            )

    def count_messages(self):
        with self._connect() as connection:
            result = connection.execute(
                "SELECT COUNT(*) FROM conversations"
            ).fetchone()

        return result[0]


if __name__ == "__main__":
    memory = ConversationMemory()

    print("JARVIS Persistent Memory Test")
    print("Database:", memory.db_path)
    print("Saved messages:", memory.count_messages())

    for message in memory.get_messages():
        print(message)
