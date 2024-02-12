import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

def generate_graph(df_grouped, chart_type='bar'):
    try:
        if chart_type == 'bar':
            create_bar_chart(df_grouped)
        elif chart_type == 'line':
            create_line_chart(df_grouped)
        elif chart_type == 'scatter':
            create_scatter_chart(df_grouped)
        elif chart_type == 'pie':
            create_pie_chart(df_grouped)
        else:
            print("Tipo di grafico non valido.")
            return

    except KeyboardInterrupt:
        # Gestisci la chiusura della finestra di Matplotlib
        pass

def create_bar_chart(df_grouped):
    plt.bar(df_grouped.index.astype(str), df_grouped.values)
    set_common_properties('Barre')
    plt.show()

def create_line_chart(df_grouped):
    plt.plot(df_grouped.index, df_grouped.values, marker='o')
    set_common_properties('Linee')
    plt.show()

def create_scatter_chart(df_grouped):
    plt.scatter(df_grouped.index, df_grouped.values)
    set_common_properties('Dispersione')
    plt.show()

def create_pie_chart(df_grouped):
    plt.pie(df_grouped.values, labels=df_grouped.index, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    set_common_properties('Torta')
    plt.show()

def set_common_properties(title):
    plt.xlabel('Data')
    plt.ylabel('Numero di messaggi')
    plt.title(f'Grafico dei messaggi per intervallo temporale - {title}')
    plt.xticks(rotation=45)
    plt.tight_layout()

def create_graphs(messages, time_interval, json_file_path, keyword=None, chart_type='bar'):
    # Creazione del DataFrame
    df = pd.DataFrame(messages)
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%dT%H:%M:%S")

    # Raggruppamento dei dati in base all'intervallo temporale scelto
    if time_interval == 'day':
        df_grouped = df.groupby(df['date'].dt.date).size()
    elif time_interval == 'week':
        df_grouped = df.groupby(df['date'].dt.to_period("W")).size()
    elif time_interval == 'month':
        df_grouped = df.groupby(df['date'].dt.to_period("M")).size()
    elif time_interval.isdigit():
        # Campionamento personalizzato in giorni
        days_interval = int(time_interval)
        df_grouped = df.resample(f"{days_interval}D", on='date').size()
    else:
        print("Intervallo temporale non valido.")
        return

    generate_graph(df_grouped, chart_type)

if __name__ == '__main__':
    # Esempio di utilizzo del modulo separatamente
    messages_example = [...]  # Sostituisci con la tua lista di messaggi
    time_interval_example = 'week'
    json_file_path_example = 'path/to/your/json_file.json'
    keyword_example = 'your_keyword'
    chart_type_example = 'bar'  # Sostituisci con il tipo di grafico desiderato ('bar', 'line', 'scatter', 'pie')

    create_graphs(messages_example, time_interval_example, json_file_path_example, keyword_example, chart_type_example)
