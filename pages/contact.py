import streamlit as st

st.set_page_config(page_title="Contact Us - LIG Visualization Tool", layout="wide")

st.title("Contact Us")
st.markdown("""
We'd love to hear from you! Reach out for support, feedback, or inquiries about the LIG Visualization Tool.

- **Email**: support@ligviz.com
- **Phone**: +91 123 456 7890
- **Address**: 123 Innovation Hub, Bengaluru, Karnataka, India

For payment-related issues, please include your email and transaction ID.
""")

st.subheader("Contact Form")
with st.form("contact_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message")
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.success("Thank you for your message! We'll respond soon.")
        