import streamlit as st

st.title("Streamlit test")
v = st.slider("Velocity (m/s)", 10, 100, 80)
q = 0.5 * 1.225 * v**2
st.metric("Dynamic pressure", f"{q:,.0f} Pa")
