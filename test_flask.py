from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Flask is working!'

if __name__ == '__main__':
    print("✅ Flask is installed correctly!")
    print("🚀 Starting test server...")
    app.run(port=5000)