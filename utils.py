import streamlit as st
import razorpay
import requests
import json
import os
from datetime import datetime, timedelta

def get_inr_amount(usd_amount):
    """Convert USD to INR using a fixed exchange rate (update as needed)."""
    exchange_rate = 85.8  # As of June 2025, adjust via API if needed
    return int(usd_amount * exchange_rate)

def track_trial():
    """Track user trials, limited to 50/month for free users."""
    if "razorpay_payment_id" in st.session_state:
        return 0  # Unlimited for premium users
    
    if "trial_count" not in st.session_state:
        st.session_state["trial_count"] = 0
    if "trial_month" not in st.session_state:
        st.session_state["trial_month"] = datetime.now().strftime("%Y-%m")
    
    current_month = datetime.now().strftime("%Y-%m")
    if current_month != st.session_state["trial_month"]:
        st.session_state["trial_count"] = 0
        st.session_state["trial_month"] = current_month
    
    st.session_state["trial_count"] += 1
    return st.session_state["trial_count"]

def create_razorpay_subscription(email, usd_amount):
    """Create a Razorpay subscription for premium access."""
    client = razorpay.Client(auth=(st.secrets["razorpay"]["key_id"], st.secrets["razorpay"]["key_secret"]))
    inr_amount = get_inr_amount(usd_amount) * 100  # Convert to paise
    
    try:
        subscription = client.subscription.create({
            "plan_id": "plan_monthly_premium",  # Create this plan in Razorpay Dashboard
            "customer_notify": 1,
            "quantity": 1,
            "total_count": 12,  # 1-year subscription, adjustable
            "notes": {"email": email},
            "notify_info": {"notify_phone": "", "notify_email": email}
        })
        return subscription
    except Exception as e:
        st.error(f"Razorpay error: {str(e)}")
        return None