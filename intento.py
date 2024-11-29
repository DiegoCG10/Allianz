import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import openai

# Cargar el logo
st.image(r"C:\Users\diego\OneDrive\Documents\UP\8\Ingeniería finan VS\App_Allianz\logo_allianz.png", width=150)

# Título de la aplicación
st.title("Simulador Comparativo de ETFs")
st.markdown("Bienvenido al simulador. Compara el desempeño de ETFs seleccionados contra CETES a 10.20% anual.")

# Entrada de datos del usuario
nombre = st.text_input("Nombre completo")
correo = st.text_input("Correo electrónico")
aceptar = st.checkbox("Acepto los términos y condiciones.")
# Opción para ver el aviso de privacidad
aviso_privacidad = st.checkbox("¿Deseas leer el aviso de privacidad?")

if aviso_privacidad:
    # Texto del aviso de privacidad
    aviso_texto = """
    **Aviso de Privacidad**:  
    Este simulador de ETFs recopila información personal, como tu nombre y correo electrónico, únicamente con fines de proporcionar los resultados de la simulación y mejorar nuestros servicios. Tu información no será compartida con terceros sin tu consentimiento expreso. 
    Si tienes alguna pregunta sobre el manejo de tus datos personales, puedes contactarnos a través del correo proporcionado. 
    Al aceptar los términos y condiciones, consientes el uso de tus datos según lo descrito en este aviso.
    """
    st.markdown(aviso_texto)

if not (nombre and correo and aceptar):
    st.warning("Por favor, completa todos los campos y acepta los términos para continuar.")
    st.stop()

# Parámetros de inversión
st.sidebar.header("Parámetros de Inversión")
inversion_inicial = st.sidebar.number_input("Inversión Inicial (MXN)", value=10000, step=500)
plazo_inversion = st.sidebar.slider("Plazo de Inversión (años)", 1, 10, 5)
rendimiento_cetes = 10.20 / 100  # 10.20% anual

# ETFs disponibles
etf_list = {
  "SPDR S&P 500 (SPY)": "SPY",
    "iShares MSCI Emerging (EEM)": "EEM",
    "Vanguard Total Stock (VTI)": "VTI",
    "Invesco QQQ (QQQ)": "QQQ",
    "iShares Russell (IWM)": "IWM",
    "SPDR DJIA Trust (DIA)": "DIA",
    "Vanguard Emerging Market (VWO)": "VWO",
    "Financial Select Sector SPDR (XLF)": "XLF",
    "Health Care Select Sector (XLV)": "XLV",
    "DJ US Home Construct (ITB)": "ITB",
    "Silver Trust (SLV)": "SLV",
    "MSCI Taiwan Index FD (EWT)": "EWT",
    "MSCI United Kingdom (EWU)": "EWU",
    "MSCI South Korea IND (EWY)": "EWY",
    "MSCI Japan Index FD (EWJ)": "EWJ"
}

selected_etfs = st.sidebar.multiselect("Seleccione los ETFs a comparar", list(etf_list.keys()), default=[])

# Funciones de cálculo
def get_etf_data(ticker, period="5y"):
    """Obtiene datos históricos del ETF."""
    return yf.download(ticker, period=period)["Close"]

def calculate_growth(initial, rate, years):
    """Calcula el crecimiento compuesto."""
    return initial * ((1 + rate) ** years)

def calculate_var(returns, confidence_level=0.95):
    """Calcula el VaR al nivel de confianza especificado."""
    return np.percentile(returns, (1 - confidence_level) * 100)

def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """Calcula el Ratio de Sharpe."""
    excess_returns = returns - risk_free_rate
    return np.mean(excess_returns) / np.std(returns)

# Simulación de resultados
etf_results = {}
st.write(f"### Comparación de Inversión: {plazo_inversion} años")

for etf_name in selected_etfs:
    ticker = etf_list[etf_name]
    data = get_etf_data(ticker, period=f"{plazo_inversion}y")
    
    if data.empty:
        st.warning(f"No se encontraron datos para {etf_name}.")
        continue
    
    data["Return"] = data.pct_change()
    annual_return = data["Return"].mean() * 252
    volatility = data["Return"].std() * np.sqrt(252)
    final_growth = calculate_growth(inversion_inicial, annual_return, plazo_inversion)
    var = calculate_var(data["Return"].dropna())
    sharpe = calculate_sharpe_ratio(data["Return"].dropna())

    etf_results[etf_name] = {
        "Símbolo": ticker,
        "Rendimiento Anual (%)": f"{annual_return * 100:.2f}%",
        "Volatilidad (%)": f"{volatility * 100:.2f}%",
        "Crecimiento Final (MXN)": final_growth,
        "VaR (95%)": f"{var * 100:.2f}%",
        "Ratio de Sharpe": f"{sharpe:.2f}"
    }

# Comparación con CETES
cetes_growth = calculate_growth(inversion_inicial, rendimiento_cetes, plazo_inversion)

# Mostrar tabla de resultados
if etf_results:
    results_df = pd.DataFrame(etf_results).T
    results_df["Crecimiento Final (MXN)"] = results_df["Crecimiento Final (MXN)"].apply(lambda x: f"${x:,.2f}")
    st.write("### Resultados Comparativos")
    st.dataframe(results_df)

    # Gráfico interactivo
    fig = go.Figure()
    for etf_name in selected_etfs:
        fig.add_trace(go.Bar(name=etf_name, x=["ETFs"], y=[etf_results[etf_name]["Crecimiento Final (MXN)"]]))
    fig.add_trace(go.Bar(name="CETES", x=["Inversión Tradicional"], y=[cetes_growth]))
    fig.update_layout(title="Crecimiento Final Comparativo", barmode="group")
    st.plotly_chart(fig)
# Gráfico de crecimiento a lo largo del tiempo (Base 0)
if selected_etfs:
    st.write("### 📈 Crecimiento de Rendimientos a lo Largo de los Años")
    fig_growth = go.Figure()

    # Agregar la curva de crecimiento de CETES
    years = np.arange(1, plazo_inversion + 1)
    cetes_values = [calculate_growth(inversion_inicial, rendimiento_cetes, year) for year in years]
    fig_growth.add_trace(go.Scatter(
        x=years,
        y=cetes_values,
        mode='lines+markers',
        name="CETES",
        line=dict(color="green", width=2),
        marker=dict(size=6)
    ))

    # Agregar la curva de crecimiento de cada ETF seleccionado
    for etf_name in selected_etfs:
        annual_return = float(etf_results[etf_name]["Rendimiento Anual (%)"].strip('%')) / 100
        etf_values = [calculate_growth(inversion_inicial, annual_return, year) for year in years]
        fig_growth.add_trace(go.Scatter(
            x=years,
            y=etf_values,
            mode='lines+markers',
            name=etf_name,
            line=dict(width=2),
            marker=dict(size=6)
        ))

    # Configuración del diseño de la gráfica
    fig_growth.update_layout(
        title="Crecimiento de Rendimientos a lo Largo de los Años",
        xaxis_title="Años",
        yaxis_title="Crecimiento (MXN)",
        yaxis=dict(range=[0, None]),  # Base 0 en el eje Y
        template="plotly_white",
        legend=dict(title="Instrumentos")
    )

    st.plotly_chart(fig_growth)

# Comparación de rendimiento (sin rendimiento ajustado por riesgo)
st.write("### 📊 Comparación de Rendimiento Anualizado")

# Crear un diccionario para almacenar la comparación de rendimiento
comparacion_rendimiento = {}

# Rendimiento de CETES
comparacion_rendimiento["CETES"] = {
    "Rendimiento Anualizado": "10.20%",
    "Crecimiento Final (MXN)": f"${cetes_growth:,.2f}",
}

# Comparar cada ETF con los CETES
for etf_name in selected_etfs:
    rendimiento_anualizado = etf_results[etf_name]["Rendimiento Anual (%)"]
    crecimiento_final = etf_results[etf_name]["Crecimiento Final (MXN)"]
    
    comparacion_rendimiento[etf_name] = {
        "Rendimiento Anualizado": rendimiento_anualizado,
        "Crecimiento Final (MXN)": f"${crecimiento_final:,.2f}",
    }

# Mostrar la tabla comparativa
comparacion_df = pd.DataFrame(comparacion_rendimiento).T

# Ordenar la tabla según el rendimiento anualizado
comparacion_df = comparacion_df.sort_values(by="Rendimiento Anualizado", ascending=False)

# Mostrar la tabla con los datos de comparación

st.dataframe(comparacion_df)


# Recomendaciones basadas en el rendimiento anualizado
st.write("### 📌 Recomendaciones basadas en el rendimiento anualizado:")
for etf_name in selected_etfs:
    # Mostrar la información detallada de cada ETF
    st.markdown(f"#### **{etf_name}:**")
    st.write(f"**Rendimiento Anualizado:** {etf_results[etf_name]['Rendimiento Anual (%)']}")
    st.write(f"**Volatilidad:** {etf_results[etf_name]['Volatilidad (%)']}")
    st.write(f"**Crecimiento Final (MXN):** {etf_results[etf_name]['Crecimiento Final (MXN)']}")
    st.write(f"**VaR (95%):** {etf_results[etf_name]['VaR (95%)']}")
    st.write(f"**Ratio de Sharpe:** {etf_results[etf_name]['Ratio de Sharpe']}")

    # Verificar si el rendimiento anualizado supera el de CETES
    if float(comparacion_rendimiento[etf_name]["Rendimiento Anualizado"].strip('%')) > 10.20:  # Compara con CETES
        st.write(f"✅ **Mejor rendimiento** que los CETES. Es una opción interesante para los inversores dispuestos a asumir el riesgo que representa el mercado.")
    else:
        st.write(f"❌ **No superó el rendimiento** de los CETES. Considera opciones con mayor rendimiento.")



# Opción de contacto por correo
if st.button("Quiero contactar a un asesor"):
    try:
        # Configuración del correo
        EMAIL_EMISOR = "allianzasesor00@gmail.com"  # Cambia por tu correo
        EMAIL_PASSWORD = "llljrzpxhbvbuosf"  # Cambia por tu clave de aplicación

        # Crear mensaje
        msg = MIMEMultipart()
        msg["From"] = EMAIL_EMISOR
        msg["To"] = correo
        msg["Subject"] = "Solicitud de Contacto - Simulador de ETFs"

        body = f"""
        Estimado {nombre},

        Gracias por utilizar el Simulador Comparativo de ETFs. Un asesor se pondrá en contacto contigo a la brevedad.

        Saludos,
        Equipo de Allianz Asesores
        """
        msg.attach(MIMEText(body, "plain"))

        # Enviar correo
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
            server.sendmail(EMAIL_EMISOR, correo, msg.as_string())

        st.success("¡Correo enviado con éxito!")
    except Exception as e:
        st.error(f"Error al enviar el correo: {e}")

