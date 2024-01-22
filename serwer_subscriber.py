#!/usr/bin/env python3

import sqlite3
from datetime import datetime

import paho.mqtt.client as mqtt

# The broker name or IP address.
broker = "localhost"

# subscribed title
topic = "server"

# The MQTT client.
client = mqtt.Client()

# Database name
database_name = "gate_system.db"


def assert_card_authorised(card_uid: str) -> bool:
    connention = sqlite3.connect(database_name)
    cursor = connention.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM registered_uids WHERE uid = ?",
                   (card_uid,))
    result = cursor.fetchone()[0] > 0
    connention.commit()
    connention.close()
    return result


def is_person_inside(card_uid: str) -> bool:
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    cursor.execute(f"SELECT exit_time FROM scan_times WHERE uid = ? ORDER BY enter_time DESC LIMIT 1", (card_uid,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result is not None and result[0] is None


def save_entrance(card_uid: str) -> None:
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO scan_times (uid, enter_time, exit_time) VALUES (?, ?, NULL)",
                   (card_uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    cursor.close()
    conn.close()


def save_exit(card_uid: str) -> None:
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    query = (
        "UPDATE scan_times "
        "SET exit_time = ? "
        "WHERE uid = ? AND enter_time = (SELECT MAX(enter_time) FROM scan_times WHERE uid = ?)"
    )
    cursor.execute(query,
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), card_uid, card_uid))

    conn.commit()
    cursor.close()
    conn.close()


def get_duration_inside(card_uid: str) -> int:
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT enter_time, exit_time FROM scan_times WHERE uid = ? ORDER BY enter_time DESC LIMIT 1",
        (card_uid,)
    )
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result and result[1] is not None:
        enter_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
        exit_time = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S')
        duration_seconds = (exit_time - enter_time).total_seconds()
        return int(duration_seconds)
    else:
        return 0


def send_no_pass(gate_sender_topic: str):
    client.publish(gate_sender_topic, "no_pass", )


def send_pass(gate_sender_topic: str):
    client.publish(gate_sender_topic, "pass", )


def send_pass_for_exit_gate(gate_sender_topic: str, card_uid: str):
    duration_inside = get_duration_inside(card_uid)
    client.publish(gate_sender_topic, f"pass&{duration_inside}", )


def handle_enter_gate(gate_sender_topic: str, card_uid: str) -> None:
    if not assert_card_authorised(card_uid):
        print(f"[INFO] The card of uid {card_uid} is not authorised")
        send_no_pass(gate_sender_topic)
        return
    if is_person_inside(card_uid):
        print(f"[INFO] The card of uid {card_uid} is already inside")
        send_no_pass(gate_sender_topic)
        return
    print(f"[INFO] The card of uid {card_uid} can be let in")
    save_entrance(card_uid)
    send_pass(gate_sender_topic)


def handle_exit_gate(gate_sender_topic: str, card_uid: str) -> None:
    if not is_person_inside(card_uid):
        print(f"[INFO] The card of uid {card_uid} is not inside")
        send_no_pass(gate_sender_topic)
        return
    print(f"[INFO] The card of uid {card_uid} can be let out")
    save_exit(card_uid)
    send_pass_for_exit_gate(gate_sender_topic, card_uid)


def process_message(client, userdata, message):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    print("[INFO] Received new message")
    if len(message_decoded) != 3:
        print("[ERROR] Message is not in correct pattern")
        return
    gate_sender_topic = message_decoded[0]
    gate_type = message_decoded[1]
    card_uid = message_decoded[2]

    if gate_type == "enter":
        print("[INFO] Message is from enter gate")
        handle_enter_gate(gate_sender_topic, card_uid)
        return

    if gate_type == "exit":
        print("[INFO] Message is from exit gate")
        handle_exit_gate(gate_sender_topic, card_uid)
        return

    print("[WARN] Message is from unknown gate type")


def connect_to_broker() -> None:
    client.connect(broker)
    client.on_message = process_message
    client.loop_start()
    client.subscribe(topic)


def disconnect_from_broker() -> None:
    client.loop_stop()
    client.disconnect()


def run_receiver() -> None:
    connect_to_broker()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("[INFO] End")
    disconnect_from_broker()


if __name__ == "__main__":
    run_receiver()
