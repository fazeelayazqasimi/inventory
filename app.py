import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

DATA_FILE = "inventory_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"products": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def dashboard():
    st.markdown("## 📊 Dashboard")
    data = load_data()

    # Date filter
    start_date = st.date_input("From Date")
    end_date = st.date_input("To Date")

    # Convert the input dates to string format for comparison
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Filter history data based on selected dates
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
        st.warning("If IMEIs are provided, the count should match the quantity.")
        return

    if st.button("Add Product"):
        data = load_data()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing = next((p for p in data["products"] if p["product_name"] == product_name), None)

        if existing:
            existing["qty"] += qty
            existing["IMEI"].extend(imeis)
            existing["history"].append({
                "action": "In", "qty": qty, "IMEI": imeis, "date": now
            })
        else:
            data["products"].append({
                "product_name": product_name,
                "qty": qty,
                "IMEI": imeis,
                "date_added": now,
                "history": [{"action": "In", "qty": qty, "IMEI": imeis, "date": now}]
            })
        save_data(data)
        st.success("Product added successfully!")
        
def remove_product():
    st.markdown("## ➖ Remove Product")
    data = load_data()
    product_names = [p["product_name"] for p in data["products"] if p["qty"] > 0]

    if not product_names:
        st.info("No products available to remove.")
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
            "action": "Out", "qty": qty, "IMEI": selected_imeis, "date": now
        })
        save_data(data)
        st.success("Product removed successfully!")

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
                    records.append({
                        "Product": p["product_name"],
                        "Action": h["action"],
                        "Qty": h["qty"],
                        "IMEIs": ", ".join(h["IMEI"]),
                        "Date": h["date"],
                        "Remaining Qty": p["qty"]
                    })
        if records:
            df = pd.DataFrame(records)
            st.dataframe(df.sort_values(by="Date", ascending=False))
        else:
            st.info("No history found for selected dates.")

def main():
    st.set_page_config(page_title="📦 Inventory System", layout="wide")
    st.markdown("""
        
    """, unsafe_allow_html=True)

    st.title("📦 Inventory Management System")
    menu = ["Dashboard", "Add Product", "Remove Product", "History"]
    choice = st.sidebar.selectbox("Select Action", menu)

    if choice == "Dashboard":
        dashboard()
    elif choice == "Add Product":
        add_product()
    elif choice == "Remove Product":
        remove_product()
    elif choice == "History":
        history_section()

if __name__ == "__main__":
    main()
