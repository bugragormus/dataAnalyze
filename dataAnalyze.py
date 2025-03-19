import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

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


    # Nem seviyelerini kategorilere ayırma
    def categorize_moisture(value):
        if value < 5:
            return 'Düşük Akış'
        elif 5 <= value < 10:
            return 'Normal Akış'
        else:
            return 'Yüksek Akış'


    filtered_df['Akış Durumu'] = filtered_df['Nem'].apply(categorize_moisture)

    # Kategorilere göre sayılar
    st.subheader("Nem Kategorilerine Göre Dağılım")
    st.write(filtered_df['Akış Durumu'].value_counts())

    # Zaman serisi grafiği (nem değeri değişimi)
    st.subheader("Nem Değeri Zaman Serisi")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(filtered_df['Tarih'], filtered_df['Nem'], label="Nem", color='b')
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Nem Değeri")
    ax.set_title("Nem Değerinin Zaman İçindeki Değişimi")
    ax.grid(True)
    st.pyplot(fig)

    # Nem seviyelerinin histogramı
    st.subheader("Nem Seviyeleri Dağılımı (Histogram)")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(filtered_df['Nem'], bins=20, color='skyblue', edgecolor='black')
    ax.set_xlabel("Nem Değeri")
    ax.set_ylabel("Frekans")
    ax.set_title("Nem Seviyeleri Dağılımı")
    st.pyplot(fig)

    # Verimlilik hesaplama (nem 5 ve üzeri normal akış, altı düşük akış)
    st.subheader("Verimlilik Hesaplama")
    low_flow = filtered_df[filtered_df['Nem'] < 5]
    normal_flow = filtered_df[filtered_df['Nem'] >= 5]

    low_flow_percentage = (len(low_flow) / len(filtered_df)) * 100
    normal_flow_percentage = (len(normal_flow) / len(filtered_df)) * 100

    st.write(f"Düşük akış yüzdesi: {low_flow_percentage:.2f}%")
    st.write(f"Normal akış yüzdesi: {normal_flow_percentage:.2f}%")

    # Akış durumu ile grafik
    st.subheader("Akış Durumuna Göre Zaman Serisi")
    fig, ax = plt.subplots(figsize=(10, 5))
    for status in ['Düşük Akış', 'Normal Akış', 'Yüksek Akış']:
        status_data = filtered_df[filtered_df['Akış Durumu'] == status]
        ax.plot(status_data['Tarih'], status_data['Nem'], label=status)
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Nem Değeri")
    ax.set_title("Akış Durumuna Göre Nem Değeri Zaman Serisi")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Veri istatistikleri
    st.subheader("Veri İstatistikleri")
    st.write(f"Minimum Nem: {filtered_df['Nem'].min():.2f}")
    st.write(f"Maksimum Nem: {filtered_df['Nem'].max():.2f}")
    st.write(f"Ortalama Nem: {filtered_df['Nem'].mean():.2f}")
    st.write(f"Standart Sapma: {filtered_df['Nem'].std():.2f}")

    # Veriyi indirilebilir hale getirme
    st.subheader("Veriyi İndir")
    csv = filtered_df.to_csv(index=False, encoding='utf-8-sig', sep=';')
    st.download_button(label="CSV Olarak İndir", data=csv, file_name="nem_verisi.csv", mime="text/csv")

