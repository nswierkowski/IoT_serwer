#!/usr/bin/env python3

import os
import sqlite3


def create_database():
    if os.path.exists("gate_system.db"):
        os.remove("gate_system.db")
        print("An old database removed.")
    connection = sqlite3.connect("gate_system.db")
    cursor = connection.cursor()
    cursor.execute(""" CREATE TABLE scan_times (
        uid text,
        enter_time text,
        exit_time text
    )""")
    cursor.execute(""" CREATE TABLE registered_uids (
            uid text
        )""")
    connection.commit()
    connection.close()
    print("The new database created.")


if __name__ == "__main__":
    create_database()
