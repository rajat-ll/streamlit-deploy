# Import python packages
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
# from snowflake.snowpark.context import get_active_session

session = get_active_session()

# Write directly to the app
st.title("Working on deployment")

# query = "SELECT * FROM LL_PROD_RAW_ZONE.PUBLIC.EXTRA_TABLES;"
# df = pd.DataFrame(session.sql(query).collect())
# st.write(df)

st.write("Hello I am Rajat, building a automated streamlit app,making your life easy")


# dept_tables = pd.read_csv('table_dept_mapping.csv')
# st.write(dept_tables)

