import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
import math

# Black-Scholes formula for reference prices
def bs(S0, K, T, r, sigma):
    d1 = (np.log(S0 / K) + (r + 0.5 * (sigma**2)) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    c = S0 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    p = c + K * np.exp(-r * T) - S0
    return c, p


# Generate binomial stock price tree
def getSmatrix1(S0, sigma, T, M):
    dt = T / M  # length of time interval
    u = np.exp(sigma * np.sqrt(dt))  # up-factor
    d = 1 / u  # down-factor
    S = np.zeros((M + 1, M + 1))
    S[0, :] = S0
    for t in range(M + 1):
        for j in range(t + 1):
            S[j, t] = S0 * (u**(t - j)) * (d**j)
    return S


# CRR Option Valuation
def CRR_option_value(S0, K, T, r, sigma, option_type, M=10):
    dt = T / M
    df = math.exp(-r * dt)
    u = math.exp(sigma * math.sqrt(dt))
    d = 1 / u
    q = (math.exp(r * dt) - d) / (u - d)

    # Stock price tree
    S = getSmatrix1(S0, sigma, T, M)

    # Initialize option payoff
    if option_type == 'C':
        V = np.maximum(S - K, 0)
    else:
        V = np.maximum(K - S, 0)

    # Backward induction
    for t in range(M - 1, -1, -1):
        for j in range(t + 1):
            V[j, t] = (q * V[j, t + 1] + (1 - q) * V[j + 1, t + 1]) * df

    return V[0, 0], V


# Streamlit UI
st.title("Binomial Tree and European Option Pricing")
st.markdown(
    "This app generates a binomial tree for stock prices and calculates European option values using the Cox-Ross-Rubinstein model."
)

# User Inputs
st.sidebar.header("Model Parameters")
S0 = st.sidebar.number_input("Initial Stock Price (S0)", value=36.0, step=1.0)
K = st.sidebar.number_input("Strike Price (K)", value=40.0, step=1.0)
T = st.sidebar.number_input("Time to Maturity (T in years)", value=1.0, step=0.1)
r = st.sidebar.number_input("Risk-Free Rate (r, as a decimal)", value=0.06, step=0.01)
sigma = st.sidebar.number_input("Volatility (σ, as a decimal)", value=0.2, step=0.01)
M = st.sidebar.number_input("Number of Steps (M)", value=10, step=1, min_value=1)

option_type = st.sidebar.radio("Option Type", ["Call", "Put"], index=1)
option_type = "C" if option_type == "Call" else "P"

# Compute Binomial Tree and Option Value
if st.button("Generate Binomial Tree and Value Option"):
    with st.spinner("Calculating..."):
        binomial_tree = getSmatrix1(S0, sigma, T, M)
        option_value, option_tree = CRR_option_value(S0, K, T, r, sigma, option_type, M)

    # Display results
    st.subheader("Binomial Tree for Stock Prices")
    st.write(pd.DataFrame(binomial_tree).fillna(""))

    st.subheader(f"European Option Value ({'Call' if option_type == 'C' else 'Put'})")
    st.write(f"The calculated European option value is: **{option_value:.4f}**")

    # Display the European option value tree
    st.subheader("Option Value Tree")
    st.write(pd.DataFrame(option_tree).fillna(""))

    # Plotting the convergence of the option value
    st.subheader("Convergence of Option Value with Increasing Steps")
    
    # Dynamically generate steps based on the input M
    max_steps = max(10, M)  # Ensure at least 10 steps
    steps = range(10, max_steps + 10, 10)  # Generate steps in increments of 10
    
    # Exact value for reference
    exact_value = bs(S0, K, T, r, sigma)[0 if option_type == "C" else 1]
    
    # Compute option values for each step
    CRR_values = [CRR_option_value(S0, K, T, r, sigma, option_type, m)[0] for m in steps]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(steps, CRR_values, label="CRR Values", marker="o", markersize=5)
    ax.axhline(exact_value, color="red", linestyle="--", linewidth=1.5, label="Exact Value (BS Model)")
    ax.set_xlabel("Number of Steps (M)")
    ax.set_ylabel("Option Value")
    ax.legend()
    ax.grid(True)
    
    # Dynamically set x-axis limits based on steps
    ax.set_xlim(min(steps), max(steps) + 10)
    ax.set_ylim(min(CRR_values) * 0.95, max(CRR_values) * 1.05)  # Padding for better visualization
    st.pyplot(fig)

