# -*- coding: utf-8 -*-
"""Delamar githubra.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1qfVIlKV56vWrb08Okq_e0qqhOTyo2rjR
"""

import pandas as pd
import numpy as np
import streamlit as st
from kmodes.kprototypes import KPrototypes
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Function to calculate AIC
def calculate_aic(n, mse, num_params):
    aic = n * np.log(mse) + 2 * num_params
    return aic

# Function to load data
def load_data():
    data = pd.read_excel('data_ready_2.xlsx')  # Ensure this file is in your GitHub repo

    # Drop the first 5 columns
    data = data.drop(data.columns[[0, 1, 2, 3, 4]], axis=1)

    # Set categorical columns
    data['Category'] = data['Category'].astype('category')
    data['Show_status'] = data['Show_status'].astype('category')
    data['Time of the day'] = data['Time of the day'].astype('category')
    data['Capacity level'] = data['Capacity level'].astype('category')

    return data

# Function to preprocess data
def preprocess_data(data):
    # Define features and target variable
    features = ['Number of previous performances', 'Show length (minutes']
    categorical_features = ['Category', 'Show_status', 'Time of the day', 'Capacity level']

    # Define categorical indices for KPrototypes before one-hot encoding
    categorical_indices = [data.columns.get_loc(col) for col in categorical_features]

    # One-hot encode categorical features
    data = pd.get_dummies(data, columns=categorical_features)

    # Extend the features list with one-hot encoded columns
    one_hot_features = [col for col in data.columns if col.startswith(tuple(categorical_features))]
    features.extend(one_hot_features)
    target = 'Total seats sold'

    # Refit the scaler with only necessary columns
    scaler = StandardScaler()
    data[['Number of previous performances', 'Show length (minutes']] = scaler.fit_transform(data[['Number of previous performances', 'Show length (minutes']])

    # Fit KPrototypes
    kproto = KPrototypes(n_clusters=4, init='Cao', verbose=0, random_state=42)
    kproto.fit_predict(data, categorical=categorical_indices)

    # Assign the labels to the DataFrame
    data['Cluster'] = kproto.labels_

    return data, features, target, kproto, scaler, categorical_indices

# Function to train and evaluate a model
def train_and_evaluate_model(X_train, X_test, y_train, y_test, model, model_name):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    r2 = r2_score(y_test, y_pred)
    aic = calculate_aic(len(y_test), mse, X_train.shape[1] + 1)
    print(f"{model_name} - MAE: {mae:.2f}, MSE: {mse:.2f}, RMSE: {rmse:.2f}, AIC: {aic:.2f}")
    return model, aic

# Function to predict ticket sales for a new show
def predict_ticket_sales(new_show, kproto, scaler, data, best_models, features, categorical_indices):
    # Convert the new show to a DataFrame
    new_show_df = pd.DataFrame([new_show])

    # Standardize the numerical variables
    new_show_df[['Number of previous performances', 'Show length (minutes']] = scaler.transform(new_show_df[['Number of previous performances', 'Show length (minutes']])

    # Set categorical columns
    new_show_df['Category'] = new_show_df['Category'].astype('category')
    new_show_df['Show_status'] = new_show_df['Show_status'].astype('category')
    new_show_df['Time of the day'] = new_show_df['Time of the day'].astype('category')
    new_show_df['Capacity level'] = new_show_df['Capacity level'].astype('category')

    # Align the new show DataFrame with the training DataFrame
    new_show_df = new_show_df.reindex(columns=data.columns, fill_value=0)

    # Predict the cluster for the new show
    new_show_df_np = new_show_df.to_numpy()
    cluster = kproto.predict(new_show_df_np[:, :-1], categorical=categorical_indices)[0]

    # Use the best model for the predicted cluster to predict ticket sales
    model = best_models[cluster]
    predicted_tickets = model.predict(new_show_df[features])[0]

    return predicted_tickets

# Load and preprocess data
data = load_data()
data, features, target, kproto, scaler, categorical_indices = preprocess_data(data)

# Initialize model candidates
model_candidates = [
    ("Linear Regression", LinearRegression()),
    ("Decision Tree Regressor", DecisionTreeRegressor(random_state=42)),
    ("Random Forest Regressor", RandomForestRegressor(random_state=42)),
    ("Gradient Boosting Regressor", GradientBoostingRegressor(random_state=42)),
    ("Support Vector Regressor", SVR())
]

# Dictionary to store the best models for each cluster
best_models = {}

# Train models and select the best one for each cluster based on AIC
for cluster in data['Cluster'].unique():
    print(f"Training models for Cluster {cluster}")
    cluster_data = data[data['Cluster'] == cluster]

    # Split the data into training and testing sets
    X = cluster_data[features]
    y = cluster_data[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    best_model = None
    best_aic = np.inf

    for model_name, model in model_candidates:
        model, aic = train_and_evaluate_model(X_train, X_test, y_train, y_test, model, model_name)
        if aic < best_aic:
            best_model = model
            best_aic = aic

    best_models[cluster] = best_model
    print(f"Best model for Cluster {cluster}: {best_model.__class__.__name__} with AIC: {best_aic:.2f}\n")

# Streamlit interface
st.title("Theater Show Ticket Sales Predictor")

# Input form
with st.form(key='show_form'):
    num_prev_performances = st.number_input('Number of previous performances', min_value=0, value=0)
    show_length = st.number_input('Show length (minutes)', min_value=0, value=90)
    category = st.selectbox('Category', ['Musical', 'Cabaret', 'Concert', 'Dans', 'Jeugd', 'Muziektheater', 'Specials', 'Toneel'])
    show_status = st.selectbox('Show status', ['New', 'Returning'])
    time_of_day = st.selectbox('Time of the day', ['Afternoon', 'Evening'])
    capacity_level = st.selectbox('Capacity level', ['S', 'O'])

    submit_button = st.form_submit_button(label='Predict Ticket Sales')

# Prediction
if submit_button:
    new_show = {
        'Number of previous performances': num_prev_performances,
        'Show length (minutes': show_length,
        'Category': category,
        'Show_status': show_status,
        'Time of the day': time_of_day,
        'Capacity level': capacity_level
    }

    predicted_tickets = predict_ticket_sales(new_show, kproto, scaler, data, best_models, features, categorical_indices)
    st.write(f"Predicted tickets sold: {predicted_tickets}")