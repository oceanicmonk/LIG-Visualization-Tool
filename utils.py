import streamlit as st
import razorpay
import requests
import os
from datetime import datetime

def get_inr_amount(usd_amount):
    """Convert USD to INR using an API or fallback rate."""
    try:
        api_key = st.secrets.get("EXCHANGE_RATE_API_KEY", "2d4bcbdb396723b05d80d831")
        response = requests.get(f"https://api.exchangerate-api.com/v4/latest/USD?apiKey={api_key}")
        rate = response.json()["rates"]["INR"]
        return round(usd_amount * rate)
    except:
        return usd_amount * 85.8  # Fallback rate

def track_trial():
    """Track user trials, limited to 50/month for free users."""
    current_month = datetime.now().strftime("%Y-%m")
    log_file = "usage.log"
    user_id = st.session_state.get("user_email", st.session_state.get("razorpay_payment_id", "anonymous"))
    try:
        if st.session_state.get("razorpay_payment_id"):
            return 0  # Unlimited for premium users
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = f.readlines()
            user_key = f"{current_month}:{user_id}"
            logs = [line for line in logs if current_month in line]
            for i, line in enumerate(logs):
                if user_key in line:
                    count = int(line.split(":")[-1].strip()) + 1
                    logs[i] = f"{user_key}:{count}\n"
                    with open(log_file, "w") as f:
                        f.writelines(logs)
                    return count
            logs.append(f"{user_key}:1\n")
            with open(log_file, "w") as f:
                f.writelines(logs)
            return 1
        else:
            with open(log_file, "w") as f:
                f.write(f"{user_key}:1\n")
            return 1
    except Exception as e:
        st.error(f"Error tracking trials: {e}")
        return 0

def create_razorpay_subscription(email, usd_amount):
    """Create a Razorpay subscription for premium access."""
    try:
        client = razorpay.Client(auth=(st.secrets["razorpay"]["key_id"], st.secrets["razorpay"]["key_secret"]))
        inr_amount = get_inr_amount(usd_amount) * 100  # Convert to paise
        subscription = client.subscription.create({
            "plan_id": "plan_monthly_premium",  # Replace with your Razorpay plan ID
            "customer_notify": 1,
            "quantity": 1,
            "total_count": 12,  # 1-year subscription
            "notes": {"email": email},
            "notify_info": {"notify_phone": "", "notify_email": email}
        })
        return subscription
    except Exception as e:
        st.error(f"Razorpay error: {str(e)}")
        return None