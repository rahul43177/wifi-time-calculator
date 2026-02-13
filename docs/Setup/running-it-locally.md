To check the UI, follow these steps:

1. Start the application server:
Run the following command in your terminal from the project root:
    
```
./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8787 --reload
```

2. Access the Dashboard:
Open your web browser and go to: http://localhost:8787