import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Dosya yükleme
uploaded_file = st.file_uploader("Bir .log dosyası yükleyin", type="log")

if uploaded_file is not None:
    # Dosyayı okuma
    df = pd.read_csv(uploaded_file, delimiter="\t", header=None, skiprows=4, usecols=[0, 2], names=['Tarih', 'Nem'])

    # Veri işleme
    # Tarih sütununu doğru formata çevirme
    df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')

    # Nem sütununu sayısal formata çevirme
    df['Nem'] = pd.to_numeric(df['Nem'].str.replace(',', '.'), errors='coerce')

    st.write("Veri Özetiniz:")
    st.write(df)

    # Tarih aralığı seçimi
    st.subheader("Tarih Aralığı Seçin")
    start_date = st.date_input("Başlangıç Tarihi", df['Tarih'].min().date())
    end_date = st.date_input("Bitiş Tarihi", df['Tarih'].max().date())

    # Tarih aralığına göre filtreleme
    filtered_df = df[(df['Tarih'].dt.date >= start_date) & (df['Tarih'].dt.date <= end_date)]

    # Ortalama nem hesaplama
    avg_moisture = filtered_df['Nem'].mean()
    st.write(f"Seçilen tarih aralığında ortalama nem: {avg_moisture:.2f}")

