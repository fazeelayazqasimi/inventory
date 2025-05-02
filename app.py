import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

USER_FILE = "users.json"
DATA_FILE = "inventory_data.json"
NOTIF_FILE = "notifications.json"

# ---------------- Utility Functions ---------------- #

def load_users():
    if not os.path.exists(USER_FILE):
        return {"users": []}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"products": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_notifications():
    if not os.path.exists(NOTIF_FILE):
        return {"notifications": []}
    with open(NOTIF_FILE, "r") as f:
        return json.load(f)

def save_notifications(notifs):
    with open(NOTIF_FILE, "w") as f:
        json.dump(notifs, f, indent=4)

def add_notification(message):
    notifs = load_notifications()
    notifs["notifications"].append({
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_notifications(notifs)

def clear_notifications():
    save_notifications({"notifications": []})

# ---------------- Login & Signup ---------------- #

def login_signup():
    st.title("🔐 Login / Signup")
    action = st.radio("Choose Action", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    users = load_users()

    if action == "Login":
        if st.button("Login"):
            user = next((u for u in users["users"] if u["username"] == username and u["password"] == password), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user.get("role", "user")
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials!")

    else:
        if st.button("Signup"):
            if any(u["username"] == username for u in users["users"]):
                st.warning("Username already exists!")
            else:
                users["users"].append({"username": username, "password": password, "role": "user"})
                save_users(users)
                st.success("Signup successful! Please login.")

# ---------------- Inventory Functionalities ---------------- #

def dashboard():
    st.markdown("## 📊 Dashboard")
    data = load_data()

    start_date = st.date_input("From Date")
    end_date = st.date_input("To Date")

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    filtered_data = [p for p in data["products"] if any(
        start_date_str <= h["date"][:10] <= end_date_str for h in p["history"])]

    total_in = sum(h["qty"] for p in filtered_data for h in p["history"] if h["action"] == "In")
    total_out = sum(h["qty"] for p in filtered_data for h in p["history"] if h["action"] == "Out")
    total_remaining = sum(p["qty"] for p in filtered_data)

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total In Qty", total_in)
    col2.metric("📤 Total Out Qty", total_out)
    col3.metric("📈 Remaining Qty", total_remaining)

    rows = []
    for p in filtered_data:
        rows.append({
            "Product Name": p["product_name"],
            "Remaining Qty": p["qty"],
            "IMEI Count": len(p["IMEI"]),
            "Date Added": p["date_added"]
        })
    st.dataframe(pd.DataFrame(rows))

def add_product():
    st.markdown("## ➕ Add Product")
    product_name = st.text_input("Product Name")
    qty = st.number_input("Quantity", min_value=1, step=1)
    imei_input = st.text_area("Enter IMEIs (optional - comma-separated)")
    imeis = [i.strip() for i in imei_input.split(",") if i.strip()]

    if imeis and len(imeis) != qty:
        st.warning("If IMEIs are provided, count must match quantity.")
        return

    if st.button("Add Product"):
        data = load_data()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing = next((p for p in data["products"] if p["product_name"] == product_name), None)

        entry = {
            "action": "In",
            "qty": qty,
            "IMEI": imeis,
            "date": now,
            "by": st.session_state.username
        }

        if existing:
            existing["qty"] += qty
            existing["IMEI"].extend(imeis)
            existing["history"].append(entry)
        else:
            data["products"].append({
                "product_name": product_name,
                "qty": qty,
                "IMEI": imeis,
                "date_added": now,
                "history": [entry]
            })

        save_data(data)
        add_notification(f"{st.session_state.username} added {qty} x {product_name}")
        st.success("Product added successfully!")

def remove_product():
    st.markdown("## ➖ Remove Product")
    data = load_data()
    product_names = [p["product_name"] for p in data["products"] if p["qty"] > 0]

    if not product_names:
        st.info("No products available.")
        return

    selected = st.selectbox("Select Product", product_names)
    product = next(p for p in data["products"] if p["product_name"] == selected)

    if product["IMEI"]:
        selected_imeis = st.multiselect("Select IMEIs to remove", product["IMEI"])
        qty = len(selected_imeis)
    else:
        qty = st.number_input("Enter quantity to remove", min_value=1, max_value=product["qty"], step=1)
        selected_imeis = []

    if st.button("Remove"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if product["IMEI"]:
            for i in selected_imeis:
                product["IMEI"].remove(i)

        product["qty"] -= qty
        product["history"].append({
            "action": "Out",
            "qty": qty,
            "IMEI": selected_imeis,
            "date": now,
            "by": st.session_state.username
        })
        save_data(data)
        add_notification(f"{st.session_state.username} removed {qty} x {selected}")
        st.success("Product removed!")

def history_section():
    st.markdown("## 📅 History")
    data = load_data()
    start = st.date_input("From Date")
    end = st.date_input("To Date")

    if st.button("🔍 Filter History"):
        records = []
        for p in data["products"]:
            for h in p["history"]:
                if start.strftime("%Y-%m-%d") <= h["date"][:10] <= end.strftime("%Y-%m-%d"):
                    record = {
                        "Product": p["product_name"],
                        "Action": h["action"],
                        "Qty": h["qty"],
                        "IMEIs": ", ".join(h["IMEI"]),
                        "Date": h["date"],
                        "Remaining Qty": p["qty"]
                    }
                    if st.session_state.role == "admin":
                        record["By"] = h.get("by", "N/A")
                    records.append(record)

        if records:
            df = pd.DataFrame(records)
            st.dataframe(df.sort_values(by="Date", ascending=False))
        else:
            st.info("No records found.")

def notification_center():
    st.markdown("## 🔔 Notifications")
    notifs = load_notifications()

    if notifs["notifications"]:
        for i, n in enumerate(reversed(notifs["notifications"]), 1):
            st.markdown(f"**{i}.** {n['message']} — _{n['timestamp']}_")
        if st.button("🧹 Clear All Notifications"):
            clear_notifications()
            st.success("Notifications cleared!")
            st.rerun()
    else:
        st.info("No notifications.")

# ---------------- Main App ---------------- #

def main():
    st.set_page_config(page_title="📦 Inventory System", layout="wide")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_signup()
        return

    st.sidebar.title(f"👋 Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    notifs = load_notifications()
    notif_count = len(notifs["notifications"])

    menu = ["Dashboard", "Add Product", "Remove Product", "History"]
    if st.session_state.role == "admin":
        menu.append(f"Notifications ({notif_count})")

    choice = st.sidebar.selectbox("Select Action", menu)

    st.title("📦 Salamtec Inventory System")

    if choice == "Dashboard":
        dashboard()
    elif choice == "Add Product":
        add_product()
    elif choice == "Remove Product":
        remove_product()
    elif choice == "History":
        history_section()
    elif "Notifications" in choice:
        notification_center()

if __name__ == "__main__":
    main()
