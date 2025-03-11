import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.svm import SVR, SVC
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
import random
from datetime import datetime, timedelta

def preprocess_data(data):
    """
    Preprocess the data for machine learning.
    
    Args:
        data: Dictionary containing target and features data
        
    Returns:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
    """
    # Create a dataframe for the target
    target_df = pd.DataFrame({
        'date': data['target']['dates'],
        'target': data['target']['values']
    })
    
    # Create dataframes for each feature
    feature_dfs = []
    feature_names = []
    
    for feature in data['features']:
        if feature['type'] == 'categorical':
            # For categorical features, we'll need to one-hot encode them
            unique_values = list(set([val for sublist in feature['values'] for val in sublist]))
            for i, val in enumerate(unique_values):
                col_name = f"{feature['name']}_{val}"
                feature_names.append(col_name)
                feature_df = pd.DataFrame({
                    'date': feature['dates'],
                    col_name: [values[i] for values in feature['values']]
                })
                feature_dfs.append(feature_df)
        else:
            # For numeric and boolean features
            col_name = feature['name']
            feature_names.append(col_name)
            feature_df = pd.DataFrame({
                'date': feature['dates'],
                col_name: feature['values']
            })
            feature_dfs.append(feature_df)
    
    # Merge all dataframes on date
    merged_df = target_df
    for df in feature_dfs:
        merged_df = pd.merge(merged_df, df, on='date', how='outer')
    
    # Handle missing values
    merged_df = merged_df.fillna(method='ffill').fillna(method='bfill')
    
    # Split into features and target
    X = merged_df.drop(['date', 'target'], axis=1)
    y = merged_df['target']
    
    return X, y, feature_names

def train_model(X, y, model_type, is_classification=False):
    """
    Train a machine learning model.
    
    Args:
        X: Feature matrix
        y: Target vector
        model_type: Type of model to train ('random_forest', 'svm', 'linear_regression')
        is_classification: Whether this is a classification problem
        
    Returns:
        model: Trained model
        X_test: Test features
        y_test: Test targets
        accuracy: Model accuracy or error
    """
    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Select and train model
    if is_classification:
        if model_type == 'random_forest':
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif model_type == 'svm':
            model = SVC(probability=True, random_state=42)
        else:  # linear_regression (actually logistic for classification)
            model = LogisticRegression(random_state=42)
        
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
    else:
        if model_type == 'random_forest':
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == 'svm':
            model = SVR()
        else:  # linear_regression
            model = LinearRegression()
        
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        accuracy = 1 - (mean_squared_error(y_test, y_pred) / np.var(y_test))  # R^2 score
    
    return model, scaler, X_test, y_test, accuracy

def generate_recommendations(data, model, scaler, feature_names, optimization_goal):
    """
    Generate recommendations based on the trained model.
    
    Args:
        data: Dictionary containing target and features data
        model: Trained model
        scaler: Feature scaler
        feature_names: List of feature names
        optimization_goal: 'maximize' or 'minimize'
        
    Returns:
        recommendations: Dictionary with recommendations
    """
    # Create a sample of possible feature combinations
    n_samples = 1000
    n_features = len(feature_names)
    
    # Generate random feature values within the observed ranges
    X, y, _ = preprocess_data(data)
    feature_mins = X.min()
    feature_maxs = X.max()
    
    # Generate random samples
    random_samples = np.random.rand(n_samples, n_features)
    scaled_samples = random_samples * (feature_maxs - feature_mins).values + feature_mins.values
    
    # Scale the samples
    scaled_samples = scaler.transform(scaled_samples)
    
    # Make predictions
    predictions = model.predict(scaled_samples)
    
    # Find the best sample based on the optimization goal
    if optimization_goal == 'maximize':
        best_idx = np.argmax(predictions)
    else:  # minimize
        best_idx = np.argmin(predictions)
    
    best_sample = scaled_samples[best_idx]
    best_sample_original = scaler.inverse_transform([best_sample])[0]
    best_prediction = predictions[best_idx]
    
    # Calculate feature importance if the model supports it
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    else:
        importances = np.ones(n_features) / n_features  # Equal importance if not available
    
    # Create recommendations
    suggested_habits = []
    for i, feature in enumerate(feature_names):
        suggested_habits.append({
            'habit_id': i + 1,  # Placeholder ID
            'name': feature,
            'recommendation': f"{best_sample_original[i]:.2f}" if isinstance(best_sample_original[i], (int, float)) else str(best_sample_original[i]),
            'importance': importances[i]
        })
    
    # Sort habits by importance
    suggested_habits.sort(key=lambda x: x['importance'], reverse=True)
    
    recommendations = {
        'predicted_value': float(best_prediction),
        'confidence': float(np.mean(importances)),  # Simple proxy for confidence
        'suggested_habits': suggested_habits,
        'explanation': f"Based on your historical data, we've identified the optimal habit settings to {optimization_goal} your target variable."
    }
    
    return recommendations

def generate_optimized_schedule(target_habit_id, constraints, habits_data):
    """
    Generate an optimized daily schedule based on target habit and constraints.
    
    Args:
        target_habit_id: ID of the target habit
        constraints: Dictionary of habit constraints
        habits_data: Dictionary of habit data
        
    Returns:
        schedule: Dictionary with the optimized schedule
    """
    # This is a simplified implementation that creates a reasonable schedule
    # In a real implementation, you would use optimization algorithms
    
    # Get the target habit name
    target_habit = next((h for h in habits_data if h['id'] == int(target_habit_id)), None)
    if not target_habit:
        return None
    
    # Create a template schedule with common daily activities
    schedule_template = [
        {'time': '06:00', 'habit': 'Wake up', 'value': 'Yes'},
        {'time': '06:30', 'habit': 'Morning routine', 'value': '30 minutes'},
        {'time': '07:00', 'habit': 'Exercise', 'value': '45 minutes'},
        {'time': '08:00', 'habit': 'Breakfast', 'value': 'Healthy meal'},
        {'time': '09:00', 'habit': 'Deep work', 'value': '3 hours'},
        {'time': '12:00', 'habit': 'Lunch', 'value': '45 minutes'},
        {'time': '13:00', 'habit': 'Meetings/Calls', 'value': '2 hours'},
        {'time': '15:00', 'habit': 'Deep work', 'value': '2 hours'},
        {'time': '17:00', 'habit': 'Exercise', 'value': '30 minutes'},
        {'time': '18:00', 'habit': 'Dinner', 'value': 'Balanced meal'},
        {'time': '19:00', 'habit': 'Family/Social time', 'value': '2 hours'},
        {'time': '21:00', 'habit': 'Wind down routine', 'value': '1 hour'},
        {'time': '22:00', 'habit': 'Sleep', 'value': '8 hours'}
    ]
    
    # Apply constraints to the schedule
    for habit in habits_data:
        habit_id = habit['id']
        if habit_id in constraints:
            constraint = constraints[habit_id]
            habit_name = habit['name']
            
            # Find this habit in the schedule
            schedule_item = next((item for item in schedule_template if item['habit'].lower() == habit_name.lower()), None)
            
            if schedule_item:
                # Apply constraints
                if 'min' in constraint and 'max' in constraint:
                    # For numeric habits, take the average of min and max
                    if habit['variable_type'] == 'numeric':
                        value = (constraint['min'] + constraint['max']) / 2
                        schedule_item['value'] = f"{value} {habit_name.split()[-1] if ' ' in habit_name else ''}"
                    elif habit['variable_type'] == 'boolean':
                        schedule_item['value'] = 'Yes' if constraint['min'] > 0 else 'No'
                elif 'min' in constraint:
                    if habit['variable_type'] == 'numeric':
                        schedule_item['value'] = f"{constraint['min']} {habit_name.split()[-1] if ' ' in habit_name else ''}"
                    elif habit['variable_type'] == 'boolean':
                        schedule_item['value'] = 'Yes' if constraint['min'] > 0 else 'No'
                elif 'max' in constraint:
                    if habit['variable_type'] == 'numeric':
                        schedule_item['value'] = f"{constraint['max']} {habit_name.split()[-1] if ' ' in habit_name else ''}"
                    elif habit['variable_type'] == 'boolean':
                        schedule_item['value'] = 'Yes' if constraint['max'] > 0 else 'No'
    
    # Calculate a predicted value for the target habit
    # This would be based on a real model in a full implementation
    predicted_value = random.uniform(7.5, 9.5)
    
    schedule = {
        'target_habit': target_habit['name'],
        'predicted_value': round(predicted_value, 1),
        'daily_plan': schedule_template
    }
    
    return schedule 