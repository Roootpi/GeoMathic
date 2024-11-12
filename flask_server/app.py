# app.py
from flask import Flask, request, jsonify, render_template
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Store expressions and x-range globally (in-memory for simplicity)
expressions = []
x_range = (-10, 10)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_expression', methods=['POST'])
def add_expression():
    """Add a mathematical expression entered by the user"""
    data = request.json
    expression = data.get("expression", "").strip()
    
    if not expression:
        return jsonify({"error": "Expression cannot be empty"}), 400
    
    try:
        # Ensure expression is of the form 'y = ...'
        if '=' not in expression:
            raise ValueError("Function must be in the form 'y = ...'")
        
        lhs, rhs = expression.split('=')
        lhs, rhs = lhs.strip(), rhs.strip()
        
        if lhs != 'y':
            raise ValueError("Function must start with 'y ='")
        
        # Validate the expression using sympy
        parsed_expr = sp.sympify(rhs)
        expressions.append(parsed_expr)  # Add the parsed function
        
        return jsonify({"message": f"Function '{expression}' added."})
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except sp.SympifyError:
        return jsonify({"error": "Invalid function. Please enter a valid mathematical function."}), 400

@app.route('/set_range', methods=['POST'])
def set_range():
    """Set the x-coordinate range for plotting"""
    data = request.json
    range_text = data.get("range", "")
    try:
        x_min, x_max = map(int, range_text.split(','))
        if x_min >= x_max:
            raise ValueError("Minimum x should be less than maximum x.")
        
        global x_range
        x_range = (x_min, x_max)
        return jsonify({"message": "Range updated successfully"})
    
    except ValueError:
        return jsonify({"error": "Invalid range format. Use two integers, e.g., '-10,10'"}), 400

@app.route('/plot_graphs', methods=['GET'])
def plot_graphs():
    """Plot all the stored functions and return the graph as an image"""
    if not expressions:
        return jsonify({"error": "No functions to plot."}), 400
    
    x_vals = np.linspace(x_range[0], x_range[1], 400)
    x = sp.symbols('x')
    
    plt.figure()
    plt.axhline(0, color='black', linewidth=1)
    plt.axvline(0, color='black', linewidth=1)
    
    for expr in expressions:
        try:
            # Convert to a lambda function for numpy compatibility
            func = sp.lambdify(x, expr, modules=['numpy'])
            y_vals = func(x_vals)
            plt.plot(x_vals, y_vals, label=f"y = {sp.pretty(expr)}")
        
        except Exception as e:
            continue  # Skip functions that can't be plotted
    
    plt.xlabel("x")
    plt.ylabel("y")
    plt.legend()
    plt.grid(True)
    
    # Save plot to a BytesIO object as PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.read()).decode('utf-8')
    plt.close()
    
    return jsonify({"image": img_base64})

if __name__ == "__main__":
    app.run(debug=True)