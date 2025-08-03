import streamlit as st
import pandas as pd
import mysql.connector

# App title
st.title("Real Estate Valuation App")

# Database config
config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'unix_socket': '/Applications/MAMP/tmp/mysql/mysql.sock',
    'database': 'AppliedDatabaseTechnologyFinalProject',
    'raise_on_warnings': False
}

# Connect to MySQL
@st.cache_resource
def get_connection():
    return mysql.connector.connect(**config)

conn = get_connection()

# Sidebar: Table viewer
st.sidebar.header("Table Viewer")
table = st.sidebar.selectbox("Select a table to preview", ["Properties", "Sales", "Regional_Prices", "Neighbors"])
query = f"SELECT * FROM {table} LIMIT 20"
df = pd.read_sql(query, conn)
st.subheader(f"Preview of {table} table")
st.dataframe(df)

# Section: Undervalued property explorer
st.subheader("Explore Undervalued Properties")

# Dropdown for ZIP code (optional filter)
zip_query = "SELECT DISTINCT zip_code FROM Properties ORDER BY zip_code"
zip_options = pd.read_sql(zip_query, conn)['zip_code'].tolist()
zip_options.insert(0, "All ZIP Codes")
selected_zip = st.selectbox("Filter by ZIP code", zip_options)

# Dropdown for available months
date_query = "SELECT DISTINCT date FROM Regional_Prices ORDER BY date DESC"
date_options = pd.read_sql(date_query, conn)['date'].astype(str).tolist()
selected_date = st.selectbox("Select Month", date_options)

# Construct query based on ZIP filter
if selected_zip == "All ZIP Codes":
    undervalued_query = f"""
    SELECT p.property_id, p.zip_code, p.lat, p.lon, p.valuation, r.avg_price,
           ROUND((r.avg_price - p.valuation) / r.avg_price * 100, 2) AS undervalued_percent
    FROM Properties p
    JOIN Regional_Prices r ON p.zip_code = r.zip_code
    WHERE r.date = '{selected_date}' AND p.valuation < r.avg_price
    LIMIT 100
    """
else:
    undervalued_query = f"""
    SELECT p.property_id, p.zip_code, p.lat, p.lon, p.valuation, r.avg_price,
           ROUND((r.avg_price - p.valuation) / r.avg_price * 100, 2) AS undervalued_percent
    FROM Properties p
    JOIN Regional_Prices r ON p.zip_code = r.zip_code
    WHERE r.date = '{selected_date}' AND p.zip_code = '{selected_zip}' AND p.valuation < r.avg_price
    LIMIT 100
    """

undervalued_df = pd.read_sql(undervalued_query, conn)

# Display the full undervalued table
st.write(f"Undervalued properties for {selected_zip} on {selected_date}:")
st.dataframe(undervalued_df)

# Multiselect for filtering specific rows on right-side map
selected_ids = st.multiselect(
    "Select properties to highlight (by Property ID):",
    options=undervalued_df['property_id'].tolist(),
    default=undervalued_df['property_id'].tolist()
)

filtered_df = undervalued_df[undervalued_df['property_id'].isin(selected_ids)]

# Display side-by-side maps
left_col, right_col = st.columns(2)

with left_col:
    st.markdown("**Map: All undervalued properties**")
    if not undervalued_df.empty:
        st.map(undervalued_df[['lat', 'lon']])
    else:
        st.info("No properties to display.")

with right_col:
    st.markdown("**Map: Selected properties only**")
    if not filtered_df.empty:
        st.map(filtered_df[['lat', 'lon']])
    else:
        st.info("No selected properties to display.")
