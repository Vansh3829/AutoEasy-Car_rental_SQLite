import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Database Connection Functions
# -----------------------------
def get_db_connection():
    return sqlite3.connect("car_rental.db")

def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    if fetch:
        result = cursor.fetchall()
        conn.close()
        return result
    conn.commit()
    conn.close()

# -----------------------------
# Initialize Database Tables
# -----------------------------
def init_db():
    execute_query("""
        CREATE TABLE IF NOT EXISTS Cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            model TEXT,
            year INTEGER,
            availability INTEGER
        )
    """)
    execute_query("""
        CREATE TABLE IF NOT EXISTS Rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER,
            rental_date DATE,
            FOREIGN KEY(car_id) REFERENCES Cars(id)
        )
    """)

init_db()

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🚗 Car Rental Management System - AutoEasy")
st.write(
    "An easy-to-use platform for managing car rentals, customer details, and rental transactions, "
    "while providing data-driven insights for better business decisions."
)

menu = ["Home", "Manage Cars", "Manage Rentals", "View Insights"]
choice = st.sidebar.selectbox("Menu", menu)

# -----------------------------
# Manage Cars Section
# -----------------------------
if choice == "Manage Cars":
    st.subheader("Manage Cars")
    option = st.selectbox("Choose an action", ["Add Car", "View Cars", "Update Car", "Delete Car"])

    if option == "Add Car":
        brand = st.text_input("Brand")
        model = st.text_input("Model")
        year = st.number_input("Year", min_value=1990, max_value=2030, step=1)
        status = st.selectbox("Availability", ["Available", "Not Available"])

        if st.button("Add Car"):
            if brand and model:
                execute_query(
                    "INSERT INTO Cars (brand, model, year, availability) VALUES (?, ?, ?, ?)",
                    (brand, model, year, 1 if status == "Available" else 0)
                )
                st.success("✅ Car added successfully!")
            else:
                st.warning("Please enter both brand and model.")

    elif option == "View Cars":
        cars = execute_query("SELECT * FROM Cars", fetch=True)
        if cars:
            # Fixed: removed extra column name "x"
            df = pd.DataFrame(cars, columns=["ID", "Brand", "Model", "Year", "Availability"])
            df["Availability"] = df["Availability"].map({1: "Available", 0: "Not Available"})
            st.dataframe(df)
        else:
            st.info("No cars found in the database.")

    elif option == "Update Car":
        car_id = st.number_input("Enter Car ID to Update", min_value=1, step=1)
        new_status = st.selectbox("New Status", ["Available", "Not Available"])
        if st.button("Update Car"):
            execute_query("UPDATE Cars SET availability=? WHERE id=?",
                          (1 if new_status == "Available" else 0, car_id))
            st.success("✅ Car status updated successfully!")

    elif option == "Delete Car":
        car_id = st.number_input("Enter Car ID to Delete", min_value=1, step=1)
        if st.button("Delete Car"):
            execute_query("DELETE FROM Cars WHERE id=?", (car_id,))
            st.success("🗑️ Car deleted successfully!")

# -----------------------------
# Manage Rentals Section
# -----------------------------
elif choice == "Manage Rentals":
    st.subheader("Manage Rentals")
    action = st.selectbox("Choose an action", ["Rent Car"])

    if action == "Rent Car":
        car_id = st.number_input("Car ID", min_value=1, step=1)
        rental_date = st.date_input("Rent Date")

        if st.button("Rent Car"):
            available = execute_query("SELECT availability FROM Cars WHERE id=?", (car_id,), fetch=True)
            if available and available[0][0] == 1:
                execute_query("INSERT INTO Rentals (car_id, rental_date) VALUES (?, ?)", (car_id, rental_date))
                execute_query("UPDATE Cars SET availability=0 WHERE id=?", (car_id,))
                st.success("🚘 Car rented successfully!")
            else:
                st.error("❌ Car not available or invalid Car ID!")

# -----------------------------
# View Insights Section
# -----------------------------
elif choice == "View Insights":
    st.subheader("📊 Rental Insights")

    # Most Rented Cars by Brand
    rentals = execute_query("""
        SELECT brand, COUNT(*) 
        FROM Rentals 
        JOIN Cars ON Rentals.car_id = Cars.id 
        GROUP BY brand
    """, fetch=True)

    if rentals:
        df = pd.DataFrame(rentals, columns=["Brand", "Total Rentals"])
        fig, ax = plt.subplots()
        ax.bar(df["Brand"], df["Total Rentals"], color="skyblue")
        plt.xlabel("Car Brand")
        plt.ylabel("Total Rentals")
        plt.title("Most Rented Cars by Brand")
        st.pyplot(fig)
    else:
        st.info("No rental data available.")

    # Monthly Rental Trends
    st.subheader("📅 Monthly Rentals")
    monthly_rentals = execute_query("""
        SELECT strftime('%m', rental_date) AS month, COUNT(*) 
        FROM Rentals 
        GROUP BY month 
        ORDER BY month
    """, fetch=True)

    if monthly_rentals:
        df_months = pd.DataFrame(monthly_rentals, columns=["Month", "Total Rentals"])
        df_months["Month"] = df_months["Month"].astype(int)

        fig2, ax2 = plt.subplots()
        ax2.bar(df_months["Month"], df_months["Total Rentals"], color="lightgreen")
        plt.xlabel("Month")
        plt.ylabel("Total Rentals")
        plt.title("Monthly Rental Trends")
        plt.xticks(range(1, 13),
                   ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        st.pyplot(fig2)
    else:
        st.info("No monthly rental data available.")
