# -*- coding: utf-8 -*-
"""Delamar githubra.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1qfVIlKV56vWrb08Okq_e0qqhOTyo2rjR
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from kmodes.kprototypes import KPrototypes
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import streamlit as st

# Function to load and preprocess data
def load_data():
    data = pd.read_excel('data_ready_2.xlsx')  # Ensure this file is in your GitHub repo
    data = data.drop(data.columns[[0, 1, 2, 3, 4]], axis=1)
    data['Category'] = data['Category'].astype('category')
    data['Show_status'] = data['Show_status'].astype('category')
    data['Time of the day'] = data['Time of the day'].astype('category')
    data['Capacity level'] = data['Capacity level'].astype('category')
    return data

# Function to train and evaluate models
def train_models(data):
    features = ['Number of previous performances', 'Show length (minutes']
    categorical_features = ['Category', 'Show_status', 'Time of the day', 'Capacity level']
    categorical_indices = [data.columns.get_loc(col) for col in categorical_features]
    data = pd.get_dummies(data, columns=categorical_features)
    one_hot_features = [col for col in data.columns if col.startswith(tuple(categorical_features))]
    features.extend(one_hot_features)
    target = 'Total seats sold'
    scaler = StandardScaler()
    data[['Number of previous performances', 'Show length (minutes']] = scaler.fit_transform(data[['Number of previous performances', 'Show length (minutes']])
    kproto = KPrototypes(n_clusters=4, init='Cao', verbose=0)
    kproto.fit_predict(data, categorical=categorical_indices)
    data['Cluster'] = kproto.labels_
    best_models = {}
    model_candidates = [
        ("Linear Regression", LinearRegression()),
        ("Decision Tree Regressor", DecisionTreeRegressor(random_state=42)),
        ("Random Forest Regressor", RandomForestRegressor(random_state=42)),
        ("Gradient Boosting Regressor", GradientBoostingRegressor(random_state=42)),
        ("Support Vector Regressor", SVR())
    ]
    for cluster in data['Cluster'].unique():
        cluster_data = data[data['Cluster'] == cluster]
        X = cluster_data[features]
        y = cluster_data[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        best_model = None
        best_aic = np.inf
        for model_name, model in model_candidates:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            aic = calculate_aic(len(y_test), mse, X_train.shape[1] + 1)
            if aic < best_aic:
                best_model = model
                best_aic = aic
        best_models[cluster] = best_model
    return kproto, scaler, best_models, features, categorical_indices

# Function to predict ticket sales
def predict_ticket_sales(new_show, kproto, scaler, data, best_models, features, categorical_indices):
    new_show_df = pd.DataFrame([new_show])
    new_show_df[['Number of previous performances', 'Show length (minutes']] = scaler.transform(new_show_df[['Number of previous performances', 'Show length (minutes']])
    new_show_df = pd.get_dummies(new_show_df)
    new_show_df = new_show_df.reindex(columns=data.columns, fill_value=0)
    cluster = kproto.predict(new_show_df.to_numpy()[:, :-1], categorical=categorical_indices)[0]
    model = best_models[cluster]
    predicted_tickets = model.predict(new_show_df[features])[0]
    return predicted_tickets

# Streamlit app
st.title('Theater Ticket Sales Prediction')
st.write("Enter the show details to predict the number of tickets sold")

new_show = {
    'Number of previous performances': st.number_input('Number of previous performances', min_value=0, value=0),
    'Show length (minutes': st.number_input('Show length (minutes', min_value=0, value=90),
    'Category': st.selectbox('Category', ['Musical', 'Cabaret', 'Concert', 'Dans', 'Jeugd', 'Muziektheater', 'Specials', 'Toneel']),
    'Show_status': st.selectbox('Show status', ['New', 'Returning']),
    'Time of the day': st.selectbox('Time of the day', ['Afternoon', 'Evening']),
    'Capacity level': st.selectbox('Capacity level', ['S', 'O'])
}

data = load_data()
kproto, scaler, best_models, features, categorical_indices = train_models(data)

if st.button('Predict Tickets Sold'):
    predicted_tickets = predict_ticket_sales(new_show, kproto, scaler, data, best_models, features, categorical_indices)
    st.write(f"Predicted tickets sold: {predicted_tickets}")