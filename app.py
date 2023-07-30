from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Load the data when the application starts
df = pd.read_csv('Data/Bank_Transactions_Data.csv')
df['TRANSACTION_DATE'] = pd.to_datetime(df['TRANSACTION_DATE'])

# Load the rules
df_rules = pd.read_csv('Data/rule.csv')

# Define a function to assign super categories
def assign_super_category(row):
    if row['TRANSACTION_TYPE']=='Debit':
        if row['CATEGORY'] in  ['Bills', 'Home & Garden', 'Transport', 'Health & Beauty', 'Groceries']:
            return 'Needs'
        elif row['CATEGORY'] in ['Eating Out', 'Shopping', 'Entertainment', 'Other', 'Transfers', 'Uncategorised']:
            return 'Wants'
    elif row['TRANSACTION_TYPE']=='Credit':
        return 'Income'
    return 'Other'

# Apply the function to the DataFrame
df['SUPER_CATEGORY'] = df.apply(assign_super_category, axis=1)

# Define a route for getting transactions
@app.route('/transactions', methods=['GET'])
def get_transactions():
    # Get parameters for filtering
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    category = request.args.get('category', None)
    super_category = request.args.get('super_category', None)

    # Start with all transactions
    filtered_df = df

    # Filter by date range if provided
    if start_date is not None and end_date is not None:
        filtered_df = filtered_df[(filtered_df['TRANSACTION_DATE'] >= start_date) & (filtered_df['TRANSACTION_DATE'] <= end_date)]

    # Filter by category if provided
    if category is not None:
        filtered_df = filtered_df[filtered_df['CATEGORY'] == category]

    # Filter by super category if provided
    if super_category is not None:
        filtered_df = filtered_df[filtered_df['SUPER_CATEGORY'] == super_category]

    # Return the filtered data as JSON
    return jsonify(filtered_df.to_dict(orient='records'))

@app.route('/savings', methods=['GET'])
def get_savings():
    # Get parameters for filtering
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)

    # Start with all transactions
    filtered_df = df

    # Filter by date range if provided
    if start_date is not None and end_date is not None:
        filtered_df = filtered_df[(filtered_df['TRANSACTION_DATE'] >= start_date) & (filtered_df['TRANSACTION_DATE'] <= end_date)]

    if start_date is None or end_date is None:
            start_date = max(filtered_df['TRANSACTION_DATE'])
            end_date = min(filtered_df['TRANSACTION_DATE'])

    start_date=datetime.strptime(start_date,'%Y-%m-%d')
    end_date=datetime.strptime(end_date,'%Y-%m-%d')

    no_of_days=(end_date-start_date).days

    # Calculate the total credit, total debit, savings, needs and wants
    total_credit = filtered_df[filtered_df['TRANSACTION_TYPE'] == 'Credit']['AMOUNT'].sum()
    total_debit = filtered_df[filtered_df['TRANSACTION_TYPE'] == 'Debit']['AMOUNT'].sum()
    savings = total_credit - total_debit

    needs = filtered_df[filtered_df['SUPER_CATEGORY'] == 'Needs']['AMOUNT'].sum()
    wants = filtered_df[filtered_df['SUPER_CATEGORY'] == 'Wants']['AMOUNT'].sum()

    # Calculate the savings rate, needs and wants percentage
    if total_credit > 0:
        savings_rate = savings / total_credit
        needs_percentage = needs / total_credit
        wants_percentage = wants / total_credit
    else:
        savings_rate = 0
        needs_percentage = 0
        wants_percentage = 0

    # Compare the percentages with the rules
    savings_rule = df_rules['savings'][0]
    needs_rule = df_rules['needs'][0]
    wants_rule = df_rules['wants'][0]

    savings_status = 'Great! Your Savings are Above Threshold' if savings_rate >= savings_rule else 'Uh-ho! Your Savings Got Below the threshold'
    needs_status = 'Great! Your Expense is Below the Threshold' if needs_percentage <= needs_rule else 'Uh-ho! Your Expense is above the Threshold'
    wants_status = 'Great! Your Expense is Below the Threshold' if wants_percentage <= wants_rule else 'Uh-ho! Your Expense is above the Threshold'

    savings_gap = savings_rule-savings_rate 
    needs_gap = needs_rule-needs_percentage
    wants_gap = wants_rule-wants_percentage

    # Return the savings data as JSON
    return jsonify({
        'total_credit': total_credit,
        'total_debit': total_debit,
        'average credit per month':(total_credit/no_of_days)*30,
        'average debit per month': (total_debit/no_of_days)*30,
        'savings': {
            'amount': savings,
            'threshold': str(savings_rule*100)+'%',
            'percentage': str(savings_rate*100)+'%',
            'gap':str(savings_gap*100)+'%',
            'status': savings_status,
            'average per month': (savings/no_of_days)*30
        },
        'needs': {
            'amount': needs,
            'threshold': str(needs_rule*100)+'%',
            'percentage': str(needs_percentage*100)+'%',
            'gap':str(needs_gap*100)+'%',
            'status': needs_status,
            'average per month': (needs/no_of_days)*30    
        },
        'wants': {
            'amount': wants,
            'threshold': str(wants_rule*100)+'%',
            'percentage': str(wants_percentage*100)+'%',
            'gap':str(wants_gap*100)+'%',
            'status': wants_status,
            'average per month': (wants/no_of_days)*30  
        }
    })


if __name__ == '__main__':
    app.run(debug=True)
