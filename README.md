# Habit Tracker & ML Optimization

A comprehensive habit tracking application with machine learning capabilities to optimize your daily routines and help you achieve your goals.

<img width="1347" alt="Screenshot 2025-03-11 at 5 19 51 PM" src="https://github.com/user-attachments/assets/ae66e18c-5368-4d15-9374-ffd48a2c18aa" />

## Features

### 1. Habit Tracking
- Create and manage multiple habit boards for different areas of your life
- Support for various data types:
  - Boolean (yes/no)
  - Numeric (quantities, durations)
  - Categorical (predefined options)
- Flexible tracking frequencies (daily, weekly, monthly)
- Intuitive logging interface for quick data entry


### 2. Data Visualization
- Interactive charts powered by Plotly.js
- Visualize habit trends over time
- Compare multiple habits to identify correlations
- Customizable date ranges for analysis

<img width="1350" alt="Screenshot 2025-03-11 at 5 21 15 PM" src="https://github.com/user-attachments/assets/ffcaca69-2676-4176-94b5-c2a9e9cec509" />


### 3. Machine Learning Optimization
- Predict how habits influence each other using advanced ML models
- Supported algorithms:
  - Random Forest
  - Support Vector Machines
  - Linear/Logistic Regression
- Identify which habits have the most impact on your goals
- Generate personalized recommendations based on your historical data

<img width="1228" alt="Screenshot 2025-03-11 at 5 25 15 PM" src="https://github.com/user-attachments/assets/9eb52208-5bd9-4fef-896f-bb241030b403" />


## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **ML Libraries**: scikit-learn, pandas, numpy
- **Visualization**: Plotly.js
- **Frontend**: HTML, CSS, JavaScript, Bootstrap

## Getting Started

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/habit-tracker.git
cd habit-tracker
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Initialize the database
```bash
python init_db.py
```

5. Run the application
```bash
python app.py
```

6. Open your browser and navigate to http://localhost:5000
