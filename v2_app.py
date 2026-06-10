import streamlit as st
import pandas as pd
import joblib
import datetime

st.set_page_config(page_title="Supply Chain AI", layout="wide")

DATA_PATH = '/Users/suyashtatiya/DataCleaning/V2_model/v2_ml_ready_features.csv'
MODEL_PATH = '/Users/suyashtatiya/DataCleaning/V2_model/v2_rf_model.pkl'

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

def main():
    st.title("Predictive Lead Time Engine")
    
    try:
        df = load_data()
        model = load_model()
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return

    vendors = sorted(df['Vendor Name - ID'].dropna().unique())
    programs = sorted(df['Program (MG4)'].dropna().unique())

    st.sidebar.header("Order Parameters")
    selected_vendor = st.sidebar.selectbox("Vendor Name", vendors)
    selected_program = st.sidebar.selectbox("Program (MG4)", programs)
    requested_days = st.sidebar.number_input("Requested Lead Time (Days)", min_value=1, value=30)
    
    po_date = st.sidebar.date_input("PO Creation Date", datetime.date.today())
    order_month = po_date.month

    if st.sidebar.button("Predict Lead Time", type="primary"):
        
        is_valid_supplier = len(df[(df['Vendor Name - ID'] == selected_vendor) & (df['Program (MG4)'] == selected_program)]) > 0

        if not is_valid_supplier:
            st.error(f"STOP: '{selected_vendor}' does not manufacture parts for the '{selected_program}' program.")
            st.info("Prediction aborted. Please review the leaderboard below and select a highlighted vendor.")
        else:
            vendor_history_data = df[df['Vendor Name - ID'] == selected_vendor]['Vendor_Historical_Avg_Days']
            vendor_avg = vendor_history_data.iloc[0] if not vendor_history_data.empty else requested_days

            input_data = pd.DataFrame({
                'Vendor Name - ID': [selected_vendor],
                'Program (MG4)': [selected_program],
                'Requested Lead Time': [requested_days],
                'Order_Month': [order_month],
                'Vendor_Historical_Avg_Days': [vendor_avg]
            })

            prediction = model.predict(input_data)[0]
            predicted_days = int(round(prediction))
            delay = predicted_days - requested_days
            
            expected_delivery_date = po_date + datetime.timedelta(days=predicted_days)

            st.subheader("AI Prediction")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Requested Days", requested_days)
            col2.metric("Predicted Actual Days", predicted_days)
            col3.metric("Est. Delivery Date", expected_delivery_date.strftime("%b %d, %Y"))
            
            if delay > 0:
                col4.metric("Projected Delay", f"{delay} Days Late", delta=-delay, delta_color="inverse")
            elif delay < 0:
                col4.metric("Projected Early", f"{abs(delay)} Days Early", delta=abs(delay), delta_color="normal")
            else:
                col4.metric("Projected Status", "Exactly On Time", delta=0)

        st.markdown("---")
        st.subheader("Global Vendor Leaderboard")
        st.write("Highlighted vendors supply the selected program. Ranked by historical speed.")
        
        leaderboard = df[['Vendor Name - ID', 'Vendor_Historical_Avg_Days']].drop_duplicates()
        
        program_vendors = df[df['Program (MG4)'] == selected_program]['Vendor Name - ID'].unique()
        leaderboard['Supplies Selected Program?'] = leaderboard['Vendor Name - ID'].apply(lambda x: 'Yes' if x in program_vendors else 'No')
        
        leaderboard['Currently Selected?'] = leaderboard['Vendor Name - ID'].apply(lambda x: '<-- Selected' if x == selected_vendor else '')

        leaderboard = leaderboard.sort_values(
            by=['Supplies Selected Program?', 'Vendor_Historical_Avg_Days'], 
            ascending=[False, True]
        ).reset_index(drop=True)
        
        leaderboard.index = leaderboard.index + 1
        leaderboard = leaderboard[['Currently Selected?', 'Vendor Name - ID', 'Vendor_Historical_Avg_Days', 'Supplies Selected Program?']]
        
        def highlight_yes_rows(row):
            if row['Supplies Selected Program?'] == 'Yes':
                return ['background-color: rgba(46, 125, 50, 0.2)'] * len(row)
            return [''] * len(row)

        styled_leaderboard = leaderboard.style.apply(highlight_yes_rows, axis=1)
        st.dataframe(styled_leaderboard, use_container_width=True)

if __name__ == "__main__":
    main()