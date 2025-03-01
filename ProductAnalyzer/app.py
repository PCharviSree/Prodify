from flask import Flask, render_template, request, jsonify
import sys
import os
import json

# Add the Backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Backend'))

import check_misleading_claims as claims
import recommendation_system as recommendations

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        print("Starting analysis...")
        barcode = request.form.get('barcode')
        claim = request.form.get('claim')
        
        print(f"Analyzing product - Barcode: {barcode}, Claim: {claim}")
        
        # Get product info
        product = claims.fetch_product_by_barcode(barcode)
        
        if not product:
            return jsonify({
                'error': 'Product not found. Please check the barcode and try again.'
            }), 404
        
        # Get ingredients
        ingredients = product.get('ingredients_text', '')
        if not ingredients:
            return jsonify({
                'error': 'No ingredients found for this product.'
            }), 400
            
        print(f"Found ingredients: {ingredients}")
        
        # Analyze claim
        try:
            claim_analysis = claims.analyze_claim(claim, ingredients)
            
            # Format claim analysis for better readability
            if isinstance(claim_analysis, dict):
                formatted_analysis = {}
                for key, value in claim_analysis.items():
                    # Format key to be more readable
                    formatted_key = key.replace('_', ' ').title()
                    
                    # Format value based on its type
                    if isinstance(value, list):
                        formatted_value = ', '.join(value)
                    elif isinstance(value, bool):
                        formatted_value = 'Yes' if value else 'No'
                    else:
                        formatted_value = str(value)
                        
                    formatted_analysis[formatted_key] = formatted_value
                claim_analysis = formatted_analysis
            
            print(f"Claim analysis result: {json.dumps(claim_analysis, indent=2)}")
            
        except Exception as e:
            print(f"Error in claim analysis: {str(e)}")
            claim_analysis = {
                "Analysis Status": "Error",
                "Details": "Failed to analyze claim. Please try again.",
                "Technical Details": str(e)
            }
        
        # Get recommendations
        try:
            healthier_alternatives = recommendations.recommend_healthier_alternatives(barcode)
            if not healthier_alternatives:
                healthier_alternatives = []
                print("No healthier alternatives found")
        except Exception as e:
            print(f"Error getting alternatives: {str(e)}")
            healthier_alternatives = []
        
        # Prepare product information
        product_info = {
            'product_name': product.get('product_name', 'Unknown Product'),
            'ingredients_text': ingredients,
            'nova_group': product.get('nova_group', 'Unknown'),
            'nutrition_grades': product.get('nutrition_grades', 'Unknown'),
            'categories': product.get('categories', 'Unknown Category'),
        }
        
        # Prepare response
        response_data = {
            'product': product_info,
            'claim_analysis': claim_analysis,
            'alternatives': healthier_alternatives
        }
        
        print("Analysis completed successfully")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred while analyzing the product.',
            'details': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure the Backend directory exists
    if not os.path.exists('Backend'):
        print("Warning: Backend directory not found!")
    
    print("Starting Product Analysis Server...")
    print("Access the application at: http://127.0.0.1:5000")
    app.run(debug=True)