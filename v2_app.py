import streamlit as st
import pandas as pd
import os
import datetime
import joblib
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Vendor Risk & Performance Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .watermark {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 8rem;
        color: rgba(200, 200, 200, 0.15);
        z-index: 0;
        pointer-events: none;
        white-space: nowrap;
        user-select: none;
    }
    .content-wrapper {
        position: relative;
        z-index: 1;
    }
    </style>
    <div class="watermark">CONFIDENTIAL</div>
    """,
    unsafe_allow_html=True
)

try:
    raw_password = st.secrets["SUPABASE_PASSWORD"]
except Exception:
    raw_password = os.getenv('SUPABASE_PASSWORD', '')

SUPABASE_URI = URL.create(
    drivername="postgresql",
    username="postgres.aapsfndsgoepmlsefosq",
    password=raw_password, 
    host="aws-1-ap-northeast-1.pooler.supabase.com",
    port=5432,
    database="postgres"
)

@st.cache_data(ttl=3600) 
def load_data():
    engine = create_engine(SUPABASE_URI)
    query = 'SELECT * FROM v2_ml_training_data'
    df = pd.read_sql(query, engine)
    df['Delay_Days'] = df['Delivered in Full Days'] - df['Requested Lead Time']
    df['Delivery_Date'] = pd.to_datetime(df['Delivery_Date'], errors='coerce')
    return df

@st.cache_resource
def load_model():
    model_path = os.getenv('MODEL_PATH', 'v2_rf_model.pkl')
    try:
        return joblib.load(model_path)
    except Exception:
        return None

def main():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.title("Vendor Risk & Performance Dashboard")
    st.markdown("Automated historical analysis and AI-driven lead time predictions.")
    
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
        
    model = load_model()

    min_date = df['Delivery_Date'].min().date()
    max_date = df['Delivery_Date'].max().date()

    st.sidebar.header("Timeline Filter (Historical)")
    preset = st.sidebar.radio(
        "Quick Select",
        ["All Time", "Last 30 Days", "Last Quarter (90 Days)", "Last Year", "Custom Range"]
    )

    if preset == "Last 30 Days":
        start_date = max_date - datetime.timedelta(days=30)
        end_date = max_date
    elif preset == "Last Quarter (90 Days)":
        start_date = max_date - datetime.timedelta(days=90)
        end_date = max_date
    elif preset == "Last Year":
        start_date = max_date - datetime.timedelta(days=365)
        end_date = max_date
    elif preset == "All Time":
        start_date = min_date
        end_date = max_date
    else:
        selected_dates = st.sidebar.date_input(
            "Select Custom Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
        else:
            start_date, end_date = min_date, max_date

    filtered_df = df[(df['Delivery_Date'].dt.date >= start_date) & (df['Delivery_Date'].dt.date <= end_date)]

    if filtered_df.empty:
        st.warning("No data found for the selected date range.")
        return

    main_tab1, main_tab2, main_tab3 = st.tabs(["📊 Fleet Analytics", "📈 Vendor Deep Dive", "🔮 Predict Lead Time (AI)"])

    with main_tab1:
        vendor_stats = filtered_df.groupby('Vendor Name - ID').agg(
            Total_Orders=('Vendor Name - ID', 'count'),
            Avg_Requested_Days=('Requested Lead Time', 'mean'),
            Avg_Actual_Days=('Delivered in Full Days', 'mean'),
            Avg_Delay=('Delay_Days', 'mean')
        ).reset_index()
        
        vendor_stats['Avg_Requested_Days'] = vendor_stats['Avg_Requested_Days'].round(0).astype(int)
        vendor_stats['Avg_Actual_Days'] = vendor_stats['Avg_Actual_Days'].round(0).astype(int)
        vendor_stats['Avg_Delay'] = vendor_stats['Avg_Delay'].round(0).astype(int)
        
        def categorize_vendor(delay):
            if delay <= 0:
                return "🟢 Reliable (On Time / Early)"
            elif 1 <= delay <= 10:
                return "🟡 Late (1-10 Days)"
            else:
                return "🔴 Critically Late (11+ Days)"
                
        def categorize_speed(days):
            if days <= 30:
                return "⚡ Fast (≤ 30 Days)"
            elif days <= 90:
                return "⏱️ Standard (31-90 Days)"
            else:
                return "🐢 Slow (91+ Days)"
                
        vendor_stats['Risk Category'] = vendor_stats['Avg_Delay'].apply(categorize_vendor)
        vendor_stats['Speed Category'] = vendor_stats['Avg_Actual_Days'].apply(categorize_speed)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Reliable Vendors", len(vendor_stats[vendor_stats['Avg_Delay'] <= 0]))
        col2.metric("🟡 Late Vendors", len(vendor_stats[(vendor_stats['Avg_Delay'] > 0) & (vendor_stats['Avg_Delay'] <= 10)]))
        col3.metric("🔴 Critical Vendors", len(vendor_stats[vendor_stats['Avg_Delay'] > 10]))
        
        st.markdown("---")
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("**Risk Distribution (Delay)**")
            st.bar_chart(vendor_stats['Risk Category'].value_counts())
        with chart_col2:
            st.markdown("**Delivery Speed Distribution (Head Time)**")
            st.bar_chart(vendor_stats['Speed Category'].value_counts())
        
        display_df = vendor_stats[['Risk Category', 'Vendor Name - ID', 'Total_Orders', 'Avg_Requested_Days', 'Avg_Actual_Days', 'Avg_Delay']]
        display_df.columns = ['Risk Category', 'Vendor Name', 'Total Historical Orders', 'Average Contract Deadline', 'Expected Delivery (Head Time)', 'Average Delay (Days)']
        
        st.subheader("Performance Leaderboards")
        t1, t2, t3 = st.tabs(["🟢 Most Reliable", "⚡ Fastest", "🔴 Critical Risk"])
        with t1:
            rel_df = display_df.sort_values(by='Average Delay (Days)').reset_index(drop=True)
            rel_df.index = rel_df.index + 1
            st.dataframe(rel_df, use_container_width=True, height=300)
        with t2:
            fast_df = display_df.sort_values(by='Expected Delivery (Head Time)').reset_index(drop=True)
            fast_df.index = fast_df.index + 1
            st.dataframe(fast_df, use_container_width=True, height=300)
        with t3:
            crit_df = display_df[display_df['Risk Category'].str.contains("🔴")].sort_values(by='Average Delay (Days)', ascending=False).reset_index(drop=True)
            if not crit_df.empty:
                crit_df.index = crit_df.index + 1
                st.dataframe(crit_df, use_container_width=True, height=300)
            else:
                st.success("No vendors in critical risk category.")

    with main_tab2:
        st.subheader("Comparative Improvement Tracking")
        vendor_list = sorted(df['Vendor Name - ID'].unique())
        selected_vendor = st.selectbox("Select a Supplier to analyze their timeline:", vendor_list)
        
        vendor_history = df[df['Vendor Name - ID'] == selected_vendor].copy()
        vendor_history['YearMonth'] = vendor_history['Delivery_Date'].dt.to_period('M').astype(str)
        
        trend_df = vendor_history.groupby('YearMonth').agg(
            Avg_Delay=('Delay_Days', 'mean'),
            Order_Count=('Vendor Name - ID', 'count')
        ).reset_index()
        
        if not trend_df.empty:
            st.markdown(f"**Month-over-Month Average Delay for {selected_vendor}**")
            st.line_chart(trend_df.set_index('YearMonth')['Avg_Delay'])
            st.dataframe(trend_df.rename(columns={'YearMonth': 'Month', 'Avg_Delay': 'Average Delay (Days)', 'Order_Count': 'Total Orders'}), use_container_width=True)
        else:
            st.info("Not enough historical data to map a trendline for this vendor.")

    with main_tab3:
        st.subheader("AI Lead Time Predictor")
        st.write("Calculate the exact expected delivery date for new orders based on historical data.")
        
        if model is None:
            st.error("Model file (v2_rf_model.pkl) not found. Please ensure it is in the project directory.")
        else:
            with st.form("prediction_form"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    pred_vendor = st.selectbox("Select Vendor:", sorted(df['Vendor Name - ID'].unique()))
                
                with col_b:
                    pred_lead_time = st.number_input("Requested Lead Time (Contract Days):", min_value=0, value=30)
                    pred_order_date = st.date_input("Expected Order Date:", value=datetime.date.today())
                
                submit_prediction = st.form_submit_button("Predict Delivery Time")
                
                if submit_prediction:
                    order_month = pred_order_date.month
                    
                    historical_avg = df[df['Vendor Name - ID'] == pred_vendor]['Delivered in Full Days'].mean()
                    if pd.isna(historical_avg):
                        historical_avg = df['Delivered in Full Days'].mean()
                        
                    vendor_programs = df[df['Vendor Name - ID'] == pred_vendor]['Program (MG4)']
                    if not vendor_programs.empty:
                        auto_program = vendor_programs.mode()[0]
                    else:
                        auto_program = 'Unknown'
                        
                    input_data = pd.DataFrame({
                        'Vendor Name - ID': [pred_vendor],
                        'Program (MG4)': [auto_program],
                        'Requested Lead Time': [pred_lead_time],
                        'Order_Month': [order_month],
                        'Vendor_Historical_Avg_Days': [historical_avg]
                    })
                    
                    try:
                        predicted_days = model.predict(input_data)[0]
                        predicted_days = int(round(predicted_days))
                        predicted_date = pred_order_date + datetime.timedelta(days=predicted_days)
                        
                        st.success(f"### Predicted Delivery Time: {predicted_days} Days")
                        st.info(f"### Expected Arrival Date: {predicted_date.strftime('%B %d, %Y')}")
                        
                        delay_prediction = predicted_days - pred_lead_time
                        if delay_prediction <= 0:
                            st.write("🟢 **Status:** Expected to arrive on time or early.")
                        else:
                            st.write(f"🔴 **Status:** High risk of delay. Expected to be {delay_prediction} days late.")
                            
                    except Exception as e:
                        st.error(f"Prediction failed: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()