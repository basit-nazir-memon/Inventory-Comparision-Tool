from flask import Flask, request, jsonify, send_file
import pandas as pd
import io
import os

app = Flask(__name__)

@app.route('/compare', methods=['POST'])
def compare_inventory():
    if 'fbaFile' not in request.files or 'shopifyFile' not in request.files:
        return jsonify({'error': 'Both FBA and Shopify files are required'}), 400

    try:
        # Read uploaded CSV files into Pandas DataFrames
        fba_file = request.files['fbaFile']
        shopify_file = request.files['shopifyFile']
        
        fba_df = pd.read_csv(fba_file)
        shopify_df = pd.read_csv(shopify_file)

        # Normalize columns
        fba_df['SKU'] = fba_df['SKU'].str.strip().str.upper()
        shopify_df['SKU'] = shopify_df['SKU'].str.strip().str.upper()

        # Merge datasets on SKU
        merged_df = pd.merge(shopify_df, fba_df, on='SKU', how='outer', suffixes=('_shopify', '_fba'))

        # Flag issues
        merged_df['Status'] = 'Match'
        merged_df.loc[merged_df['Shopify_Quantity'] != merged_df['FBA_Quantity'], 'Status'] = 'Mismatch'
        merged_df.loc[merged_df['FBA_Quantity'].isna(), 'Status'] = 'Missing in FBA'
        merged_df.loc[merged_df['Shopify_Quantity'].isna(), 'Status'] = 'Missing in Shopify'

        # Convert DataFrame to CSV in-memory
        output = io.StringIO()
        merged_df.to_csv(output, index=False)
        output.seek(0)

        return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, attachment_filename='audit_report.csv')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Get PORT from Render, default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)