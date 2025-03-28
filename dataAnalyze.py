import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO


# Veri yükleme fonksiyonu
@st.cache_data(show_spinner="Veri yükleniyor...")
def load_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sayfa1", engine='openpyxl')
        df.columns = [str(col).strip() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Veri yükleme hatası: {str(e)}")
        return None


def main():
    st.set_page_config(layout="wide", page_title="Finansal Performans Analiz Paneli")

    st.title("🏦 Finansal Performans Analiz Paneli")
    st.markdown("""
    <style>
    .big-font { font-size:18px !important; }
    </style>
    <p class="big-font">Mali İşler Müdürü için stratejik karar destek sistemi</p>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Excel dosyasını yükleyin", type=["xlsx", "xls"])
    if not uploaded_file:
        st.info("Lütfen ZFMR0003 raporunun Excel dosyasını yükleyin")
        return

    df = load_data(uploaded_file)
    if df is None:
        return

    # ORİJİNAL FİLTRELEME SİSTEMİ
    general_columns = [
        'İlgili 1', 'İlgili 2', 'İlgili 3', 'Masraf Yeri', 'Masraf Yeri Adı',
        'Masraf Çeşidi', 'Masraf Çeşidi Adı',
        'Masraf Çeşidi Grubu 1', 'Masraf Çeşidi Grubu 2', 'Masraf Çeşidi Grubu 3'
    ]

    report_base_columns = [
        "Bütçe", "Bütçe ÇKG", "Bütçe Karşılık Masrafı", "Bütçe Bakiye",
        "Fiili", "Fiili ÇKG", "Fiili Karşılık Masrafı", "Fiili Bakiye",
        "Bütçe-Fiili Fark Bakiye", "BE", "BE-Fiili Fark Bakiye"
    ]

    cumulative_columns = [
        "Kümüle Bütçe", "Kümüle Bütçe ÇKG", "Kümüle Bütçe Karşılık Masrafı", "Kümüle Bütçe Bakiye",
        "Kümüle Fiili", "Kümüle Fiili ÇKG", "Kümüle Fiili Karşılık Masrafı", "Kümüle Fiili Bakiye",
        "Kümüle Bütçe-Fiili Fark Bakiye", "Kümüle BE Bakiye", "Kümüle BE-Fiili Fark Bakiye"
    ]

    all_months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

    # SIDEBAR FİLTRELERİ
    with st.sidebar:
        st.header("🔧 Filtre Kontrol Paneli")

        filtered_df = df.copy()
        for col in general_columns:
            if col not in filtered_df.columns:
                continue

            options = sorted(filtered_df[col].dropna().unique().tolist(), key=lambda x: str(x))
            selected = st.multiselect(
                f"🔍 {col} ►",
                options,
                key=f"filter_{col}",
                default=[],
                help=f"{col} için filtre seçin"
            )

            if selected:
                filtered_df = filtered_df[filtered_df[col].isin(selected)]

        # Ay seçimi
        months_options = ["Hiçbiri", "Hepsi"] + all_months
        selected_months = st.multiselect(
            "📅 Görüntülenecek Aylar:",
            months_options,
            default=all_months,
            key="month_filter"
        )
        if "Hiçbiri" in selected_months:
            selected_months = []
        elif "Hepsi" in selected_months:
            selected_months = all_months

        # Rapor sütunları seçimi
        report_base_options = ["Hiçbiri", "Hepsi"] + report_base_columns
        selected_report_bases = st.multiselect(
            "📊 Veri Türleri:",
            report_base_options,
            default=report_base_columns,
            key="report_base_filter"
        )
        if "Hiçbiri" in selected_report_bases:
            selected_report_bases = []
        elif "Hepsi" in selected_report_bases:
            selected_report_bases = report_base_columns

        # Kümülatif sütun seçimi
        cumulative_options = ["Hiçbiri", "Hepsi"] + cumulative_columns
        selected_cumulative_columns = st.multiselect(
            "📈 Kümülatif Veriler:",
            cumulative_options,
            default=cumulative_columns,
            key="cumulative_filter"
        )
        if "Hiçbiri" in selected_cumulative_columns:
            selected_cumulative_columns = []
        elif "Hepsi" in selected_cumulative_columns:
            selected_cumulative_columns = cumulative_columns

        if st.button("🗑️ Tüm Filtreleri Temizle"):
            for key in st.session_state.keys():
                if key.startswith("filter_") or key in ["month_filter", "report_base_filter", "cumulative_filter"]:
                    del st.session_state[key]
            st.cache_data.clear()
            st.rerun()

    # Sütun seçimlerini dinamik olarak oluştur
    selected_columns = general_columns.copy()

    for month in selected_months:
        for base_col in selected_report_bases:
            month_col_name = f"{month} {base_col}"
            if month_col_name in df.columns:
                selected_columns.append(month_col_name)

    for cum_col in selected_cumulative_columns:
        if cum_col in df.columns:
            selected_columns.append(cum_col)

    # Final DataFrame'i oluştur
    final_df = filtered_df[selected_columns]

    # METRİKLER - KÜMÜLE SÜTUNLARINI KONTROL EDEREK
    total_budget = final_df["Kümüle Bütçe"].sum() if "Kümüle Bütçe" in final_df.columns else 0
    total_actual = final_df["Kümüle Fiili"].sum() if "Kümüle Fiili" in final_df.columns else 0
    variance = total_actual - total_budget
    variance_pct = (variance / total_budget) * 100 if total_budget != 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Toplam Bütçe", f"{total_budget:,.0f} ₺")
    with col2:
        st.metric("Toplam Fiili", f"{total_actual:,.0f} ₺")
    with col3:
        st.metric("Fark", f"{variance:,.0f} ₺ ({variance_pct:.1f}%)",
                  delta_color="inverse")

    # TAB SİSTEMİ
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Orijinal Rapor",
        "📈 Trend Analizi",
        "🧮 ROI Dağılımı",
        "📋 Detay Tablosu",
        "🔍 Senaryo Analizi"
    ])

    with tab1:
        st.subheader("Filtrelenmiş Rapor Verisi")
        st.write(f"Toplam kayıt: {len(final_df)}")

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False)

        st.download_button(
            "📥 Excel Olarak İndir",
            data=output.getvalue(),
            file_name="filtrelenmis_rapor.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.dataframe(final_df, use_container_width=True, height=400)

    with tab2:
        st.subheader("Aylık Bütçe-Fiili Performans Trendi")

        if selected_months:
            trend_data = []
            for month in selected_months:
                budget_col = f"{month} Bütçe"
                actual_col = f"{month} Fiili"
                if budget_col in final_df.columns and actual_col in final_df.columns:
                    monthly_budget = final_df[budget_col].sum()
                    monthly_actual = final_df[actual_col].sum()
                    trend_data.append({
                        "Ay": month,
                        "Bütçe": monthly_budget,
                        "Fiili": monthly_actual,
                        "Fark": monthly_actual - monthly_budget
                    })

            if trend_data:
                df_trend = pd.DataFrame(trend_data)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_trend["Ay"],
                    y=df_trend["Bütçe"],
                    name='Bütçe',
                    marker_color='#636EFA',
                    opacity=0.7
                ))
                fig.add_trace(go.Bar(
                    x=df_trend["Ay"],
                    y=df_trend["Fiili"],
                    name='Fiili',
                    marker_color='#EF553B',
                    opacity=0.7
                ))
                fig.add_trace(go.Scatter(
                    x=df_trend["Ay"],
                    y=df_trend["Fark"],
                    name='Fark',
                    line=dict(color='#00CC96', width=3),
                    yaxis='y2'
                ))
                fig.update_layout(
                    barmode='group',
                    yaxis=dict(title='Tutar (₺)'),
                    yaxis2=dict(
                        title='Fark (₺)',
                        overlaying='y',
                        side='right',
                        showgrid=False
                    ),
                    hovermode='x unified',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Seçilen aylara ait veri bulunamadı")
        else:
            st.info("Lütfen en az bir ay seçin")

    with tab3:
        st.subheader("Masraf Türü Bazında Karlılık Analizi")

        if not final_df.empty and "Masraf Çeşidi Adı" in final_df.columns:
            # Kümüle sütunlarını kontrol et
            required_cols = ["Kümüle Bütçe", "Kümüle Fiili"]
            if all(col in final_df.columns for col in required_cols):
                expense_analysis = final_df.groupby("Masraf Çeşidi Adı").agg({
                    "Kümüle Bütçe": "sum",
                    "Kümüle Fiili": "sum"
                }).reset_index()

                expense_analysis["Fark"] = expense_analysis["Kümüle Fiili"] - expense_analysis["Kümüle Bütçe"]
                expense_analysis["Fark Yüzdesi"] = (expense_analysis["Fark"] / expense_analysis["Kümüle Bütçe"]) * 100

                fig = px.treemap(
                    expense_analysis,
                    path=["Masraf Çeşidi Adı"],
                    values="Kümüle Bütçe",
                    color="Fark Yüzdesi",
                    color_continuous_scale='RdYlGn',
                    color_continuous_midpoint=0,
                    hover_data={"Kümüle Bütçe": ":.0f", "Kümüle Fiili": ":.0f", "Fark": ":.0f"},
                    title="Bütçe-Fark Dağılımı (Yeşil: Tasarruf, Kırmızı: Aşım)"
                )
                fig.update_traces(
                    texttemplate="<b>%{label}</b><br>Bütçe: %{customdata[0]:.0f}₺<br>Fark: %{customdata[2]:.0f}₺",
                    hovertemplate="<b>%{label}</b><br>Bütçe: %{customdata[0]:.0f}₺<br>Fiili: %{customdata[1]:.0f}₺<br>Fark: %{color:.1f}%"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Kümüle verileri bulunamadı. Lütfen 'Kümüle Bütçe' ve 'Kümüle Fiili' sütunlarını seçin.")
        else:
            st.warning("Filtrelenmiş veri bulunamadı veya 'Masraf Çeşidi Adı' sütunu eksik")

    with tab4:
        st.subheader("Detaylı Veri İnceleme")

        gb = GridOptionsBuilder.from_dataframe(final_df)
        gb.configure_default_column(
            filterable=True,
            sortable=True,
            editable=False,
            groupable=True
        )
        gb.configure_selection('multiple', use_checkbox=True)
        grid_options = gb.build()

        grid_response = AgGrid(
            final_df,
            gridOptions=grid_options,
            height=400,
            width='100%',
            fit_columns_on_grid_load=True,
            theme='streamlit'
        )

        selected_rows = grid_response['selected_rows']
        if selected_rows:
            st.subheader("Seçilen Kayıtların Detayı")
            st.write(pd.DataFrame(selected_rows))

    with tab5:
        st.subheader("What-If Analiz Paneli")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Bütçe Senaryosu**")
            scenario_budget = st.number_input(
                "Yeni Bütçe Tutarı (₺):",
                min_value=0.0,
                value=total_budget * 0.9,
                step=1000.0,
                key="scenario_budget"
            )

            new_variance = total_actual - scenario_budget
            new_variance_pct = (new_variance / scenario_budget) * 100 if scenario_budget != 0 else 0

            st.metric("Projeksiyon Farkı",
                      f"{new_variance:,.0f} ₺ ({new_variance_pct:.1f}%)",
                      delta_color="inverse")

        with col2:
            st.markdown("**Optimizasyon Simülatörü**")
            reduction_target = st.slider(
                "Tasarruf Hedefi (%):",
                min_value=0,
                max_value=50,
                value=10,
                key="reduction_target"
            )

            potential_saving = total_actual * (reduction_target / 100)
            new_actual = total_actual - potential_saving
            optimized_variance = new_actual - total_budget

            st.metric("Potansiyel Tasarruf",
                      f"{potential_saving:,.0f} ₺",
                      help=f"{reduction_target}% tasarruf ile fiili harcamayı {new_actual:,.0f} ₺'ye düşürür")


if __name__ == "__main__":
    main()
