from flask import Flask, request
app = Flask(__name__)

@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        print(request.json)  # Assuming the request data is in JSON format
        return "Request received and printed", 200
    else:
        print(request.json)
        return "This endpoint only accepts POST requests", 405

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
