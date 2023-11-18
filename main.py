# %%
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf


# %%

st.set_page_config(layout="wide")

st.header("Modelo de evaluación de instrumento de inversión")

# st.divider()

# tickerSymbol = 'BBVAPYMB.MX'
# inst = yf.Ticker(tickerSymbol)

# tickerData = yf.download(tickerSymbol, start='2022-01-01', end='2022-12-31')
# st.write(tickerData.describe())

st.divider()

with st.container():

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.subheader("Datos del fondo")
        mu1     = st.number_input(label="Retorno medio anualizado", value=0.27) # (Se asume una distribución gausiana...)
        sig1    = st.number_input(label="Desviación estándar", value=13.23)     # (volatididad)
        ogc1    = st.number_input(label="Costo de operar el índice (porcentaje)", min_value=0., max_value=1., value=0.)       # (si no lo conoces, dejar cero)

    with col2:
        st.subheader("Datos de la inversión")
        seedMoney   = st.number_input(label="Monto inicial de la inversión", min_value=1, value=10000)
        contriv_n   = st.number_input(label="Contribuciones periódicas durante el año", min_value=0, value=12)
        contriv_m   = st.number_input(label="Monto de la contribución periódica", min_value=0, value=1000)
        st.divider()
        inflation   = st.number_input(label="Inflación anualizada esperada", min_value=0., value=5.5)
        tax         = st.number_input(label="Tasa impuestos", min_value=0. , value=16.)

    with col3:
        st.subheader("Datos del periodo")
        T   = st.number_input(label="Años totales a invertir", min_value=1, value=25)
        mod_col3 = st.toggle(label="Cambiar", value=False)
        N   = st.number_input(label="Meses en el año", min_value=1, value=12, disabled=not mod_col3)
        n   = st.number_input(label="Días operativos (bursátiles) en el mes", min_value=1, value=21, disabled=not mod_col3)
    
    with col4:
        st.subheader("Datos adicionales")
        pensionRate = st.number_input(label="Safe Withdrawal Rate (SWR)", min_value=1, value=1)
        rebalancing = st.toggle(label="¿Quieres rebalancear anualmente el fondo?", value=False)
        balancing   = st.number_input(label="Ratio anual de rebalanceo del fondo", min_value=1., value=1., disabled=not rebalancing)
        pensionObjetivo = st.number_input(label="Pension objetivo", min_value=0, value=0)

    
    Ns  = st.number_input(label="No. de simulaciones", min_value=1, value=1000, max_value=5000)
    st.caption("método: Geometric Brownian Movement (GBM)")


deltat        = 1/N                  # Time step
contriv       = contriv_n*contriv_m  # Contribuciones periódicas anuales (se incrementarán automáticamente con la inflación)

inflationEnd     = np.empty((0,1), np.float64)     # Inflation over 25 years period
capitalEvolution = np.empty((0,1), np.float64)     # How my capital has evolved? It's yearly
averageInterest  = np.empty((0,1), np.float64)     # Mean interest of the year
capital1Cum      = np.empty((T,Ns), np.float64)    # Growing capital Fund 1
capitalCum       = np.empty((T,Ns), np.float64)    # Growing total capital Fund 1 + Fund 2
capitalEnd       = np.empty((0,1), np.float64)     # Capital after time T

seed             = 5                               # Random seed 
np.random.seed(seed)                               # Initialize random seed for reproducibility


st.divider()

evaluar_btn = st.button("Evaluar")

if evaluar_btn:
    st.divider()
    st.subheader("Resultados")

    for i in range(0,Ns): # Loop over the simulations
        
        capitalTotal    = seedMoney 
        TOTAL_invested  = seedMoney  # Amount of money invested (no inflation) 
        contrivInf      = contriv    # Periodic contributions incremented by inflation
        
        capital1        = capitalTotal*balancing      
        
        for j in range(0,T): # Loop over the years
        
            if rebalancing is True:
                capital1 = capitalTotal*balancing      
                del capitalTotal
            
            capital1Cum[j,i] = capital1
            
            for k in range(0,N): # Monthly loop
                
                # Random interest, sum across the month
                intrestVar1 = np.sum(mu1*deltat/100/n + sig1*(np.sqrt(deltat/n)*np.random.normal(0,1,n))/100) 
                
                # How capital is affected + contrivInf
                capital1 += capital1*intrestVar1
                
                # Let's add the montly payment 
                capital1 += balancing*contrivInf/N
                            
                del intrestVar1
            
            # Update total anount invested
            TOTAL_invested = TOTAL_invested + contrivInf
            
            # Update the contribution for inflation
            contrivInf = contrivInf + (contrivInf*inflation/100)
            
        
            if rebalancing is True:
                # Subtrack ongoing charges OGC
                capitalTotal = capital1 - (capital1*ogc1/100)
                
                # Del capital1 and 2
                del capital1
                
            else:
                capital1 = capital1 - (capital1*ogc1/100)
                capitalTotal = capital1
            
            capitalCum[j,i] = capitalTotal

            
        # Add the final capital for each simulation Ns
        capitalEnd = np.append(capitalEnd, capitalTotal)
        
        del capitalTotal
        del contrivInf
        del i
        del j
        del k
    
    with st.container():

        col1, col2 = st.columns(2)

        with col1:

            capitalEndInf = capitalEnd/(1+T*inflation/100); # Correct final money for inflation
            TOTAL_investedInf = TOTAL_invested/(1+T*inflation/100)

            fig, ax = plt.subplots()
            # ax = sns.distplot(capitalEnd/1000000, kde=False, rug=False, bins=80); 
            ax = sns.distplot(capitalEnd, kde=False, rug=False); 
            ax.set_title(f'Resultado de las simulaciones\n({Ns} corridas)')
            ax.set_xlabel('Millones de $')
            ax.set_ylabel('Número de simulaciones')
            # ax.set_xlim(0,4)
            # ax.plot([TOTAL_invested/1000000, TOTAL_invested/1000000], [0, Ns/15])
            ax.plot([TOTAL_invested, TOTAL_invested], [0, Ns/10])

            st.pyplot(fig)

        with col2:

            pension = (capitalEnd*pensionRate/100/12)*(1-(tax/100))/(1+T*inflation/100)
            # p10 = np.percentile(pension, q=[10])
            p10 = np.median(pension)

            hist, bin_edges = np.histogram(pension, density=False)
            fig, ax = plt.subplots()
            ax = sns.distplot(pension, kde=False, rug=False)
            ax.set_title('Distribución de las posibles pensiones\n(inflación corregida + impuestos)')
            ax.set_xlabel('Monto de la pensión ($)')
            ax.set_ylabel('Cuenta')
            ax.plot([p10, p10], [0, Ns/10])
            ax.plot([pensionObjetivo, pensionObjetivo], [0, Ns/10])
            # ax.set_xlim(0,10000)

            st.pyplot(fig)
            

        # 'Años totales: ' + str(T)
        # 'Número de simulaciones: ' + str(Ns)
        # 'Inversión inicial: ' + str(seedMoney)
        # 'Inversiones periódicas (mensuales): ' + str(contriv/12)
        # 'Impuestos: ' + str(tax)+'%'
        # 'Índice de inflación anual: ' + str(inflation)+'%'
        # 'Safe Withdrawal Rate (SWR): ' + str(pensionRate) + '%'
        # 'Rebalanceo: ' + str(rebalancing)
        # ' '
        # 'Datos del fondo'
        # 'mu (rentabilidad media en un periodo de tiempo): ' + str(mu1)
        # 'sig (desviación estándar / volatilidad): ' + str(sig1)
        # 'ogc (costo anual de mtto del fondo): ' + str(ogc1)
        # 'Balancep: ' + str(balancing)
        # ' '
        st.write(f'Total invertido: ${TOTAL_invested:0,.2f}')
        st.write(f'Probabilidad de vencer la inflación: {(np.size(np.where(capitalEndInf > TOTAL_invested))/Ns)*100:0.2f}%')
        # st.write(f'Savings within (10-90 percentile): $ {np.round(np.percentile(capitalEndInf, q=10)):0,.2f} and $ {np.round(np.percentile(capitalEndInf, q=90)):0,.0f}')
        st.write(f'Mediana del Capital: ${np.median(capitalEndInf):0,.2f}')
        # st.write('Pension between (10-90 percentile): $ {:,.2f} and ${:,.2f}'.format(np.round(np.percentile(pension, q=10)), np.round(np.percentile(pension, q=90))))
        f'Probabilidad de una pensión > ${pensionObjetivo:0,.2f}:  {(np.size(np.where(pension > pensionObjetivo))/Ns)*100:.1f}%'
        f'Mediana de la Pensión: ${np.median(pension):0,.2f}'

