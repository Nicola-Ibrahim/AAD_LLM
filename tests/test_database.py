from shared.infra.database import Database


def test_file_database_keeps_wal_and_sqlite_connection_settings(tmp_path):
    database = Database(f"sqlite:///{tmp_path / 'audit.db'}")

    try:
        with database.engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA journal_mode").scalar_one() == "wal"
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one() == 60_000
            assert connection.exec_driver_sql("PRAGMA synchronous").scalar_one() == 1
    finally:
        database.dispose()


def test_memory_database_skips_wal_but_keeps_connection_settings():
    database = Database("sqlite:///:memory:")

    try:
        with database.engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one() == 60_000
            assert connection.exec_driver_sql("PRAGMA synchronous").scalar_one() == 1
    finally:
        database.dispose()
