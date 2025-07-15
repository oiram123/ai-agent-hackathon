from flask import Flask, jsonify
from structured_ai_agent import StructuredSparePartsAgent

app = Flask(__name__)
agent = StructuredSparePartsAgent()

@app.route('/api/replacement-predictions', methods=['GET'])
def get_replacement_predictions():
    predictions = agent.predict_part_replacements()
    return jsonify(predictions)

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    metrics = agent.get_dashboard_metrics()
    return jsonify(metrics)

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    alerts = agent.get_maintenance_alerts()
    return jsonify(alerts)

@app.route('/api/costs', methods=['GET'])
def get_costs():
    costs = agent.get_cost_analysis()
    return jsonify(costs)

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    predictions = agent.get_predictions()
    return jsonify(predictions)

@app.route('/api/due-checks', methods=['GET'])
def get_due_checks():
    due_checks = agent.get_due_part_checks()
    return jsonify(due_checks)

if __name__ == '__main__':
    app.run(debug=True) 