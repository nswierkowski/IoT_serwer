import re
import sqlite3
from datetime import datetime, timedelta


def stats():
    work_time_statistics("today")
    work_time_statistics("this_week")
    work_time_statistics("this_month")


def seconds_to_hours_minutes(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return hours, minutes


def calculate_statistics(uid_input, start_date, end_date):
    connection = sqlite3.connect("gate_system.db")
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT enter_time, exit_time FROM scan_times WHERE uid = (?)", (uid_input,))
        results = cursor.fetchall()

        total_time_difference = 0
        entry_count = 0

        for entry, exit in results:
            entry_time = datetime.strptime(entry, "%Y-%m-%d %H:%M:%S")
            if exit is not None:
                exit_time = datetime.strptime(exit, "%Y-%m-%d %H:%M:%S")
            else:
                exit_time = datetime.now()

            if start_date <= entry_time.date() <= end_date:
                time_difference = exit_time - entry_time
                total_time_difference += time_difference.total_seconds()
                entry_count += 1

        if entry_count > 0:
            avg_time_difference = total_time_difference / entry_count
            avg_hours, avg_minutes = seconds_to_hours_minutes(avg_time_difference)
            return avg_hours, avg_minutes, entry_count

        return 0, 0, 0

    except sqlite3.Error as e:
        print("Błąd", e, e.with_traceback())
        return 0, 0, 0

    finally:
        connection.close()


def work_time_statistics(period):
    today = datetime.now().date()

    if period == "today":
        start_date = today
        end_date = today
    elif period == "this_week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "this_month":
        start_date = today.replace(day=1)
        end_date = today.replace(day=30)
    else:
        print("Nieprawidłowy okres.")
        return

    connection = sqlite3.connect("gate_system.db")
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT DISTINCT uid FROM registered_uids")
        uids = cursor.fetchall()

        for uid in uids:
            uid = uid[0]
            avg_hours, avg_minutes, entry_count = calculate_statistics(uid, start_date, end_date)

            if entry_count > 0:
                print(f"Statystyki dla pracownika o UID {uid} w okresie {start_date} - {end_date}:")
                print(f"Średni czas pracy dziennie: {int(avg_hours)}h {int(avg_minutes)}min")
                print(f"Średnia dzienna ilość wejść: {entry_count}")
                print("\n")

    except sqlite3.Error as e:
        print("Błąd przy próbie pobrania danych z bazy danych:", e)

    finally:
        connection.close()


def work_time():
    uid_input = input("Podaj uid użytkownika: ")
    connection = sqlite3.connect("gate_system.db")
    cursor = connection.cursor()

    try:
        today = datetime.now().date()

        cursor.execute("SELECT enter_time, exit_time FROM scan_times WHERE uid = ?", (uid_input,))
        results = cursor.fetchall()

        total_time_difference = 0
        entrance_counter = 0

        for entry, exit in results:
            entry_time = datetime.strptime(entry, "%Y-%m-%d %H:%M:%S")  # sprawdzic jak to jest zapisywane w bazce
            if exit is not None:
                exit_time = datetime.strptime(exit, "%Y-%m-%d %H:%M:%S")  # to też
            else:
                exit_time = datetime.now()

            if entry_time.date() == today:
                entrance_counter += 1
                time_difference = exit_time - entry_time
                total_time_difference += time_difference.total_seconds()

        total_hours, total_minutes = seconds_to_hours_minutes(total_time_difference)
        print(f"Czas pracy dzisiaj: {int(total_hours)}h {int(total_minutes)}min")
        print(f"Liczba zarejestrowanych wejść: {entrance_counter}")

    except sqlite3.Error as e:
        print("Błąd", e)

    finally:
        connection.close()


def add_random_values():
    connection = sqlite3.connect("gate_system.db")
    cursor = connection.cursor()
    cursor.execute("INSERT INTO scan_times VALUES (?,?,?)", ("[23, 23, 23, 23, 23]", "2024-01-23 10:01:23", None))
    connection.commit()
    connection.close()


def unregister():
    uid_input = input("Podaj uid użytkownika: ")
    connection = sqlite3.connect("gate_system.db")
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM registered_uids WHERE uid=(?)", (uid_input,))
        connection.commit()
    except sqlite3.Error as e:
        print("Błąd przy próbie usunięcia UID z bazy danych")
    finally:
        connection.close()


def register():
    uid = input("Podaj uid użytkownika: ")
    if check_is_uid_valid(uid):
        connection = sqlite3.connect("gate_system.db")
        cursor = connection.cursor()
        cursor.execute("INSERT INTO registered_uids (uid) VALUES (?)", (uid,))
        connection.commit()
        connection.close()
    else:
        print("Niepoprawne uid. Przyjmowany format: [N, N, N, N, N]")


def show_registered_uid(registered_uids: list) -> None:
    print('\nregistered_uids')
    for i, uid in enumerate(registered_uids):
        print(f'{i + 1}.{uid[0]}')
    print("\n")


def print_single_record_from_scan_times(i, scan_time) -> None:
    if scan_time[1] and scan_time[2]:
        print(f'{i + 1}.  {scan_time[0]}  {scan_time[1]}  {scan_time[2]}')
    elif scan_time[1] and (not scan_time[2]):
        print(f'{i + 1}.  {scan_time[0]}  {scan_time[1]}  {" " * 14}{scan_time[2]}')
    elif (not scan_time[1]) and scan_time[2]:
        print(f'{i + 1}.  {scan_time[0]}  {" " * 14}{scan_time[1]}  {scan_time[2]}')
    else:
        print(f'{i + 1}.  {scan_time[0]}  {" " * 14}{scan_time[1]}  {" " * 14}{scan_time[2]}')


def show_scan_times(scan_times: list) -> None:
    print('\nscan_times')
    print(f'lp. {" " * 8} uid {" " * 10} enter_time {" " * 10} exit_time')
    for i, scan_time in enumerate(scan_times):
        print_single_record_from_scan_times(i, scan_time)
    print("\n")


def get_registered_uid() -> None:
    connection = sqlite3.connect("gate_system.db")
    cursor = connection.cursor()
    cursor.execute("SELECT uid FROM registered_uids")
    registered_uids = cursor.fetchall()
    connection.commit()
    connection.close()
    show_registered_uid(registered_uids)


def get_scan_times() -> None:
    connection = sqlite3.connect("gate_system.db")
    cursor = connection.cursor()
    cursor.execute("SELECT uid, enter_time, exit_time FROM scan_times")
    scan_times = cursor.fetchall()
    connection.commit()
    connection.close()
    show_scan_times(scan_times)


def show_menu():
    print("1 - zarejestruj nowego użytkownika")
    print("2 - wyrejestruj użytkownika")
    print("3 - czas pracy użytkownika")
    print("4 - statystyki użytkownika")
    print("5 - zaprezentuj uid zarejestrowane")
    print("6 - zaprezentuj tabele dotyczącą czasu")
    print("7 - zamknij aplikacje")
    choice = input("Podaj opcję:\n")
    if choice == '1':
        register()
    elif choice == '2':
        unregister()
    elif choice == '3':
        work_time()
    elif choice == '4':
        stats()
    elif choice == '5':
        get_registered_uid()
    elif choice == '6':
        get_scan_times()
    elif choice == '7':
        return False
    else:
        print("Zła opcja")
    return True


def check_is_uid_valid(uid):
    pattern = re.compile(r'\[\d{1,3}, \d{1,3}, \d{1,3}, \d{1,3}, \d{1,3}\]')
    return pattern.match(uid)


def main():
    while show_menu():
        pass
