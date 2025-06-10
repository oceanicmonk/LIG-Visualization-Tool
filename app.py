import streamlit as st
import numpy as np
from scipy.optimize import brentq
from mpmath import mp, log, exp, power
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import razorpay
import os
from utils import get_inr_amount, track_trial, create_razorpay_subscription
from datetime import datetime

# High-precision arithmetic
mp.dps = 50

# Page Config
st.set_page_config(page_title="LIG Visualization Tool", layout="wide", initial_sidebar_state="expanded")

# Currency converter
usd_price = 5
inr_price = get_inr_amount(usd_price)
st.session_state['inr_price'] = inr_price

# CSS for styling
st.markdown("""
<style>
    .stButton>button { background-color: #2196F3; color: white; border-radius: 5px; padding: 8px 16px; }
    .stButton>button[kind="primary"] { background-color: #00ff7f; color: black; }
    .stButton>button[kind="primary"]:hover { background-color: #00e66b; }
    .stButton>button[kind="secondary"] { background-color: #1e90ff; color: white; }
    .stButton>button[kind="secondary"]:hover { background-color: #1a7de6; }
    .payment-form { background-color: #f0f8ff; padding: 15px; border-radius: 8px; margin-top: 10px; }
    .stTextInput>div>input { border: 1px solid #2196F3; border-radius: 5px; }
    .stSelectbox>div>div { border: 1px solid #2196F3; border-radius: 5px; }
    .stNumberInput>div>input { border: 1px solid #2196F3; border-radius: 5px; }
    .sidebar .sidebar-content { background-color: #f8f9fa; }
    h1, h2, h3 { color: #2196F3; }
    .footer { font-size: 12px; text-align: center; margin-top: 20px; color: #666; }
    .footer a { color: #1e90ff; text-decoration: none; margin: 0 10px; }
    .footer a:hover { text-decoration: underline; }
</style>
""", unsafe_allow_html=True)

# LIG Functions
def f1(x): return x / log(x) if x > np.e else float('inf')
def f2(x): return log(x) / log(log(x)) if x > mp.exp(mp.e) else float('inf')
def f3(x): return x * log(log(x)) / log(x) if x > mp.exp(mp.e) else float('inf')

def q_log(x, q): return (power(x, 1-q) - 1) / (1 - q) if q != 1 else log(x)

def solve_log_point(c, func=f1, bounds=[np.e + 0.1, np.exp(np.e)]):
    def equation(x): return log(func(x)) - c
    try:
        return float(brentq(equation, bounds[0], bounds[1], xtol=1e-6))
    except:
        return None

def log_distance(x_i, x_j, func=f1, kappa=1e6):
    ln_fi = log(func(x_i))
    ln_fj = log(func(x_j))
    delta = ln_fi - ln_fj
    theta = 1 / (1 + mp.exp(-kappa * delta))
    return float(log(mp.exp(delta) * theta + mp.exp(-delta) * (1 - theta)))

def generate_log_polygon(c_values, func=f1):
    points = [solve_log_point(c, func) for c in c_values]
    if None in points:
        return None, None, None
    max_c = max(abs(c) for c in c_values)
    max_d = log(mp.exp(log(max_c + log(2))))
    edges = [(points[i], points[j]) for i in range(len(points)) for j in range(i+1, len(points))
             if log_distance(points[i], points[j], func) <= max_d]
    distances = [log_distance(p1, p2, func) for p1, p2 in edges]
    return points, edges, distances

def generate_log_cycle(k_start, num_points, delta=log(2), q=None):
    if q:
        func = lambda x: q_log(x, q)
        points = []
        for i in range(num_points):
            k = k_start + i * delta
            try:
                x = float(brentq(lambda x: func(x) - k, np.e + 0.1, np.exp(np.e), xtol=1e-6))
                points.append(x)
            except:
                return None, None, None
    else:
        zeta = lambda x: log((log(x) / log(log(x))) * 
                             (log(log(log(x))) / log(log(log(log(x))))))
        points = []
        for i in range(num_points):
            k = k_start + i * delta
            try:
                x = float(brentq(lambda x: zeta(x) - k, np.e + 0.1, np.exp(np.e), xtol=1e-6))
                points.append(x)
            except:
                return None, None, None
    edges = [(points[i], points[i+1]) for i in range(len(points)-1)] + [(points[-1], points[0])]
    distances = [log_distance(p1, p2, f1) for p1, p2 in edges]
    return points, edges, distances

def generate_log_surface(c1, c2, func1=f1, func2=f2, n_points=100):
    points = []
    for x in np.linspace(np.e + 0.1, np.exp(np.e), n_points):
        if abs(log(func1(x)) - c1) < log(1.2) and abs(log(func2(x)) - c2) < log(1.2):
            points.append([x, float(func1(x)), float(func2(x))])
    return points, None, None

def generate_log_volume(c1, c2, c3, func1=f1, func2=f2, func3=f3, n_points=100):
    points = []
    for x in np.linspace(np.e + 0.1, np.exp(np.e), n_points):
        if all(abs(log(f(x)) - c) < log(1.2) for f, c in [(func1, c1), (func2, c2), (func3, c3)]):
            points.append([x, float(func1(x)), float(func2(x))])
    return points, None, None

def transform_log_point(x, C, weights=[1, 0, 0], funcs=[f1, f2, f3]):
    h_x = mp.prod([f(x)**w for f, w in zip(funcs, weights)])
    return float(exp(log(h_x) * log(C) / log(mp.exp(mp.e))))

# Sidebar
st.sidebar.title("LIG Visualization Tool")
st.sidebar.markdown("""
A novel geometry based on logarithmic operations. Explore log-points, structures, and transformations!
- **Free**: 50 trials/month, 2D visualizations.
- **Premium**: Unlimited trials, 3D visualizations, animations, reports.
""")
st.sidebar.markdown("[Contact](/contact) | [Privacy Policy](/privacy_policy) | [Terms](/terms)")

# Main UI
st.title("LIG Visualization Tool 📐")
st.markdown("""
**Explore Logarithmic Intrinsic Geometry!**
Create non-spatial structures using logarithmic operations, with applications in computational geometry, information theory, and more.
""")

# Inputs
st.subheader("Input Parameters")
structure_type = st.selectbox("Structure Type", ["Log-Polygon", "Log-Cycle", "Log-Surface", "Log-Volume"])
func_choice = st.selectbox("Function", ["f1: x/ln(x)", "f2: ln(x)/ln(ln(x))", "f3: x*ln(ln(x))/ln(x)"])
c_values = st.text_input("Constants (comma-separated, e.g., 1,1.2,1.4)", "1,1.2,1.4")
q_value = st.number_input("Q-Logarithm Parameter (for cycles)", min_value=0.1, max_value=2.0, value=1.0, disabled=structure_type != "Log-Cycle")
C_transform = st.number_input("Transformation Constant C", min_value=np.e, max_value=np.exp(np.e), value=np.e)
weights = st.text_input("Transformation Weights (e.g., 1,0,0)", "1,0,0")
animate_transform = st.checkbox("Animate Transformation (Premium)", disabled=not st.session_state.get("razorpay_payment_id"))

# Trial Tracking
trial_count = track_trial()
st.session_state["trial_count"] = trial_count
st.write(f"Trials this month: {trial_count}/50")

# Razorpay Integration
try:
    key_id = st.secrets["razorpay"]["key_id"]
    key_secret = st.secrets["razorpay"]["key_secret"]
except (KeyError, AttributeError):
    st.warning("Razorpay secrets not found in .streamlit/secrets.toml. Using test keys for local testing.")
    key_id = "test_key_id"
    key_secret = "test_key_secret"

if "razorpay_client" not in st.session_state:
    try:
        st.session_state["razorpay_client"] = razorpay.Client(auth=(key_id, key_secret))
    except Exception as e:
        st.warning(f"Failed to initialize Razorpay: {str(e)}. Running in test mode (no payments).")
        st.session_state["razorpay_client"] = None

# Generate
st.write("DEBUG: Rendering Generate section")
if st.checkbox("Bypass Premium for Testing (Local Only)"):
    st.session_state["razorpay_payment_id"] = "test_premium"
if st.button("Generate", type="primary"):
    if trial_count > 50 and not st.session_state.get("razorpay_payment_id"):
        st.error("Trial limit reached. Upgrade to Premium for unlimited trials and advanced features.")
    else:
        try:
            c_values = [float(c) for c in c_values.split(",")]
            func = {"f1": f1, "f2": f2, "f3": f3}[func_choice.split(":")[0]]
            weights = [float(w) for w in weights.split(",")]

            if structure_type == "Log-Polygon":
                points, edges, distances = generate_log_polygon(c_values, func)
                if points:
                    st.markdown(f"**Points**: {points}")
                    st.markdown(f"**Max Distance**: {max(distances, default=0):.3f}")
                    # 2D Visualization
                    G = nx.Graph()
                    G.add_nodes_from(points)
                    G.add_edges_from(edges)
                    fig, ax = plt.subplots(figsize=(8, 6))
                    pos = nx.spring_layout(G)
                    nx.draw(G, pos, with_labels=True, node_color='#90CAF9', edge_color='gray', ax=ax)
                    nx.draw_networkx_edge_labels(G, pos, {(u, v): f"{log_distance(u, v, func):.3f}" for u, v in edges}, ax=ax)
                    st.pyplot(fig)
                    plt.close(fig)

                    # Premium Features
                    if st.session_state.get("razorpay_payment_id"):
                        # 3D Visualization
                        pos_3d = nx.spring_layout(G, dim=3, seed=42)
                        x = [pos_3d[p][0] for p in points]
                        y = [pos_3d[p][1] for p in points]
                        z = [pos_3d[p][2] for p in points]
                        fig_3d = go.Figure(data=[
                            go.Scatter3d(x=x, y=y, z=z, mode='markers+lines+text', text=[f"{p:.3f}" for p in points],
                                         marker=dict(size=8, color='#2196F3'), line=dict(color='gray'))
                        ])
                        fig_3d.update_layout(title="3D Log-Polygon", scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'))
                        st.plotly_chart(fig_3d)

                        # Transformation
                        transformed_points = [transform_log_point(p, C_transform, weights) for p in points]
                        st.markdown(f"**Transformed Points**: {transformed_points}")

                        # Animation
                        if animate_transform:
                            frames = []
                            for t in np.linspace(0, 1, 10):
                                interp_points = [p + t * (tp - p) for p, tp in zip(points, transformed_points)]
                                frames.append(go.Frame(data=[
                                    go.Scatter3d(x=[pos_3d[p][0] for p in interp_points],
                                                 y=[pos_3d[p][1] for p in interp_points],
                                                 z=[pos_3d[p][2] for p in interp_points],
                                                 mode='markers+lines')
                                ]))
                            fig_3d.update(frames=frames)
                            st.plotly_chart(fig_3d)

                        # Report
                        report = f"""LIG Visualization Report
Structure: {structure_type}
Function: {func_choice}
Points: {points}
Max Distance: {max(distances, default=0):.3f}
Transformed Points: {transformed_points}"""
                        st.download_button("Download Report", report, "lig_report.txt", mime="text/plain")

            elif structure_type == "Log-Cycle":
                q = q_value if q_value != 1.0 else None
                points, edges, distances = generate_log_cycle(c_values[0], len(c_values), q=q)
                if points:
                    st.markdown(f"**Points**: {points}")
                    st.markdown(f"**Max Distance**: {max(distances, default=0):.3f}")
                    # 2D Visualization
                    G = nx.Graph()
                    G.add_nodes_from(points)
                    G.add_edges_from(edges)
                    fig, ax = plt.subplots(figsize=(8, 6))
                    pos = nx.spring_layout(G)
                    nx.draw(G, pos, with_labels=True, node_color='#A5D6A7', edge_color='gray', ax=ax)
                    st.pyplot(fig)
                    plt.close(fig)

                    # Premium 3D
                    if st.session_state.get("razorpay_payment_id"):
                        pos_3d = nx.spring_layout(G, dim=3, seed=42)
                        x = [pos_3d[p][0] for p in points]
                        y = [pos_3d[p][1] for p in points]
                        z = [pos_3d[p][2] for p in points]
                        fig_3d = go.Figure(data=[
                            go.Scatter3d(x=x, y=y, z=z, mode='markers+lines', marker=dict(size=8, color='#A5D6A7'))
                        ])
                        st.plotly_chart(fig_3d)

                        # Report
                        report = f"""LIG Visualization Report
Structure: {structure_type}
Function: {func_choice}
Points: {points}
Max Distance: {max(distances, default=0):.3f}"""
                        st.download_button("Download Report", report, "lig_report.txt", mime="text/plain")

            elif structure_type in ["Log-Surface", "Log-Volume"] and st.session_state.get("razorpay_payment_id"):
                if structure_type == "Log-Surface":
                    points, _, _ = generate_log_surface(c_values[0], c_values[1], func, f2)
                    title = "3D Log-Surface"
                else:
                    points, _, _ = generate_log_volume(c_values[0], c_values[1], c_values[2], func, f2, f3)
                    title = "3D Log-Volume"
                if points:
                    st.markdown(f"**Points**: {points[:10]}... (total {len(points)})")
                    # 3D Visualization
                    x = [p[0] for p in points]
                    y = [p[1] for p in points]
                    z = [p[2] for p in points]
                    fig_3d = go.Figure(data=[
                        go.Scatter3d(x=x, y=y, z=z, mode='markers', marker=dict(size=5, color='#FF9800'))
                    ])
                    fig_3d.update_layout(title=title, scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'))
                    st.plotly_chart(fig_3d)

                    # Report
                    report = f"""LIG Visualization Report
Structure: {structure_type}
Function: {func_choice}
Points: {points[:10]}... (total {len(points)})"""
                    st.download_button("Download Report", report, "lig_report.txt", mime="text/plain")

        except ValueError as ve:
            st.error(f"Invalid input: {str(ve)}. Please check your constants or weights.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}. Contact support if this persists.")

# Payment Form
with st.form(key="payment_form"):
    st.markdown(f'<div class="payment-form">Get Premium for $5/month ≈ ₹{inr_price}/month</div>', unsafe_allow_html=True)
    user_email = st.text_input("Enter Email for Premium Access", value=st.session_state.get("user_email", ""))
    submitted = st.form_submit_button("Upgrade to Premium", type="secondary")
    if submitted and user_email:
        subscription = create_razorpay_subscription(user_email, usd_price)
        if subscription:
            st.session_state["razorpay_payment_id"] = subscription["id"]
            st.session_state["user_email"] = user_email
            st.session_state["trial_count"] = 0
            st.success("Premium subscription activated! Enjoy unlimited trials and advanced features.")

# Handle payment success
if st.query_params.get("payment_id"):
    payment_id = st.query_params["payment_id"][0]
    st.session_state["razorpay_payment_id"] = payment_id
    st.session_state["user_email"] = st.session_state.get("user_email", "anonymous")
    current_month = datetime.now().strftime("%Y-%m")
    log_file = "usage.log"
    user_key = f"{current_month}:{st.session_state.get('user_email', payment_id)}"
    try:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                lines = f.readlines()
            with open(log_file, "w") as f:
                for line in lines:
                    if user_key in line:
                        f.write(f"{user_key}:0\n")
                    else:
                        f.write(line)
        st.session_state["trial_count"] = 0
        st.success(f"Payment successful! Premium access unlocked with Payment ID: {payment_id}")
    except Exception as e:
        st.error(f"Error updating trial count: {e}")

# Footer
st.markdown("""
<div class="footer">
    © 2025 LIG Visualization Tool | 
    <a href="/contact">Contact</a> | 
    <a href="/privacy_policy">Privacy Policy</a> | 
    <a href="/terms">Terms</a>
</div>
""", unsafe_allow_html=True)