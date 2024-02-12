import json
import pandas as pd
import os
from tqdm import tqdm
import xlsxwriter
import random
import sys
from graph import generate_graph  # Importa la funzione generate_graph dal modulo separato
from fourier_analysis import fourier_analysis

# Dichiarazione della lista per i messaggi partizionati
partitioned_messages_list = []

def get_default_json_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_folder = os.path.join(script_dir, 'data')
    json_path = os.path.join(json_folder, 'result.json')
    return json_path

def filter_messages(messages, keyword):
    filtered_messages = [message for message in messages if 'text' in message and isinstance(message['text'], list) and len(message['text']) > 0 and keyword.lower() in ' '.join(map(str, message['text'])).lower()]
    return filtered_messages

def convert_json_to_excel(messages, excel_file, time_interval, json_file_path, keyword=None, perform_fourier_analysis=False):
    # Aggiunta del filtro dei messaggi se una parola chiave è specificata
    if keyword:
        messages = filter_messages(messages, keyword)

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
    elif time_interval == 'hour':  # Aggiunta per gestire il campionamento orario
        df_grouped = df.groupby(df['date'].dt.floor('H')).size()
    elif time_interval.isdigit():
        # Campionamento personalizzato in giorni
        days_interval = int(time_interval)
        df_grouped = df.resample(f"{days_interval}D", on='date').size()
    else:
        print("Intervallo temporale non valido.")
        return
    
    if time_interval.isdigit():
        days_interval = int(time_interval)
        df_grouped = df.resample(f"{days_interval}D", on='date').size()

        # Chiamata alla funzione per l'analisi di Fourier con il nuovo set di dati e campionamento personalizzato
        if perform_fourier_analysis:
            fourier_analysis(df_grouped, time_interval, df, days_interval)
    elif time_interval == 'hour':  # Aggiunta per gestire il campionamento orario
        df_grouped = df.resample('H', on='date').size()
    
        # Chiamata alla funzione per l'analisi di Fourier con il nuovo set di dati e campionamento personalizzato
        if perform_fourier_analysis:
            fourier_analysis(df_grouped, time_interval, df, 1)
    else:
        df_grouped = df.groupby(df['date'].dt.date).size()


    # Imposta il percorso del file Excel
    if not excel_file:
        default_excel_file = os.path.splitext(json_file_path)[0] + "_output.xlsx"
        excel_file = input(f"Inserisci il percorso per la creazione del file Excel (invio per default '{default_excel_file}'): ")
        if not excel_file:
            excel_file = default_excel_file

    # Esporta i dati in un file Excel
    export_to_excel(df_grouped, excel_file)

    return df_grouped

def export_to_excel(data, excel_file, json_file_path=None):
    try:
        workbook = xlsxwriter.Workbook(excel_file)
        worksheet = workbook.add_worksheet()

        if json_file_path:
            worksheet.write(0, 0, 'JSON File Path')
            worksheet.write(0, 1, json_file_path)

        if isinstance(data, pd.Series):
            # Caso DataFrame completo
            for idx, (date, count) in enumerate(tqdm(data.items(), desc="Creazione file Excel"), 1):
                worksheet.write(idx, 0, str(date))  # Data
                worksheet.write(idx, 1, count)
        elif isinstance(data, list):
            # Caso messaggi partizionati
            for idx, message in enumerate(tqdm(data, desc="Creazione file Excel"), 1):
                worksheet.write(idx, 0, message.get('nome_opera', ''))
                worksheet.write(idx, 1, message.get('link_href', ''))
                worksheet.write(idx, 2, message.get('nome_cognome', ''))
                worksheet.write(idx, 3, message.get('micronazione', ''))
                worksheet.write(idx, 4, message.get('data_pubblicazione', ''))
                worksheet.write(idx, 5, message.get('luogo', ''))

        # Salva il file Excel
        workbook.close()

        # Conferma la creazione del file Excel solo se il file è stato creato correttamente
        if os.path.exists(excel_file):
            print(f"Conversione completata. Dati salvati in {excel_file}")
        else:
            print("Errore durante la conversione. Il file Excel non è stato creato correttamente.")

    except Exception as e:
        print(f"Errore durante la creazione del file Excel: {e}")

def is_bsl_format(messages, sample_size=10):
    sample_messages = random.sample(messages, min(len(messages), sample_size))

    for message in sample_messages:
        if 'text' in message and isinstance(message['text'], list) and len(message['text']) > 0:
            text_parts = message['text']
            if len(text_parts) >= 3 and text_parts[0] and text_parts[1] and text_parts[2]:
                return True
    return False

def partition_messages(messages):
    global partitioned_messages_list

    # Verifica se almeno un messaggio segue il formato BSL
    if not is_bsl_format(messages):
        print("Avviso: La funzione di partizionamento è disponibile solo per il formato BSL.")
        return []

    partitioned_messages = []

    for message in messages:
        if 'text' in message and isinstance(message['text'], list) and len(message['text']) > 0:
            text_parts = message['text']
            
            nome_opera = text_parts[0]
            link_text = text_parts[1] if len(text_parts) > 1 and isinstance(text_parts[1], dict) and text_parts[1].get('type') == 'text_link' else None
            resto = text_parts[2]

            if nome_opera and link_text and resto:
                link_href = link_text.get('href') if 'href' in link_text else None
                
                if resto:
                    parts = resto.split(',')
                    
                    if len(parts) == 2:
                        nome_cognome, data_pubblicazione_micronazione_luogo = [part.strip() for part in parts]
                        data_pubblicazione, micronazione_luogo_part = map(str.strip, data_pubblicazione_micronazione_luogo.split('-'))
                        
                        micronazione_luogo_parts = micronazione_luogo_part.split('[')
                        
                        if len(micronazione_luogo_parts) == 2:
                            micronazione = micronazione_luogo_parts[0].strip()
                            luogo = micronazione_luogo_parts[1].strip(']')
                        else:
                            micronazione = micronazione_luogo_parts[0].strip()
                            luogo = None
                        
                        message['nome_opera'] = nome_opera
                        message['link_href'] = link_href
                        message['nome_cognome'] = nome_cognome
                        message['micronazione'] = micronazione
                        message['data_pubblicazione'] = data_pubblicazione
                        message['luogo'] = luogo
                        
                        partitioned_messages.append(message)
                        partitioned_messages_list.append(message)
    
    return partitioned_messages

def get_unique_titles(messages):
    titles = set(message.get('nome_opera', '') for message in messages)
    return titles

def get_authors_count(messages):
    authors_count = {}
    for message in messages:
        author = message.get('nome_cognome', '')
        if author:
            authors_count[author] = authors_count.get(author, 0) + 1

    # Ordina autori in ordine decrescente
    authors_count = dict(sorted(authors_count.items(), key=lambda item: item[1], reverse=True))
    return authors_count

def get_unique_micronations(messages):
    micronations = set(message.get('micronazione', '') for message in messages)
    return micronations

def get_unique_locations(messages):
    locations = set(message.get('luogo_pubblicazione', '') for message in messages)
    return locations

def display_titles(messages):
    titles = get_unique_titles(messages)
    print("Titoli unici delle opere:")
    for title in titles:
        print(title)

def display_authors_count(messages):
    authors_count = get_authors_count(messages)
    print("Conteggio degli autori:")
    for author, count in authors_count.items():
        print(f"{author}: {count}")

def display_micronations(messages):
    micronations = get_unique_micronations(messages)
    print("Micronazioni uniche:")
    for micronation in micronations:
        print(micronation)

def display_locations(messages):
    locations = get_unique_locations(messages)
    print("Luoghi di pubblicazione unici:")
    for location in locations:
        print(location)

def main():
    while True:
        # Utilizziamo la nuova funzione per ottenere il percorso del file JSON
        json_file_path = get_default_json_path()
        if not os.path.exists(json_file_path):
            print(f"Errore: il file JSON '{json_file_path}' non esiste. Riprova.")
            continue

        with open(json_file_path, 'r', encoding='utf-8') as file:
            chat_data = json.load(file)

        messages = chat_data.get('messages', [])

        # Dichiarazione della lista per i messaggi partizionati
        partitioned_messages_list = []

        # Impostazioni iniziali
        time_interval = 'day'
        start_date = messages[0]['date']
        end_date = messages[-1]['date']

        # Barra di avanzamento durante la lettura del file JSON
        with tqdm(total=len(messages), desc="Lettura file JSON") as pbar:
            for message in messages:
                pbar.update(1)

        while True:
            # Menu principale
            print("\nMenu:")
            print("1. Campionamento")
            print("2. Grafico")
            print("3. Esporta")
            print("4. Filtra")
            print("5. Partizionamento")
            print("6. Analisi di Fourier")
            print("7. Quit")

            choice = input("Seleziona un'opzione: ").lower()

            if choice == '1':
                # Sottomenu per il campionamento
                print("\nCampionamento:")
                print("a. Giorno")
                print("b. Settimana")
                print("c. Mese")
                print("d. Personalizzato")
                print("e. Orario")
                print("f. Indietro")

                campionamento_choice = input("Seleziona un'opzione: ").lower()

                if campionamento_choice == 'a':
                    time_interval = 'day'
                elif campionamento_choice == 'b':
                    time_interval = 'week'
                elif campionamento_choice == 'c':
                    time_interval = 'month'
                elif campionamento_choice == 'd':
                    time_interval = input("Inserisci il numero di giorni per il campionamento personalizzato: ")
                elif campionamento_choice == 'e':
                    time_interval = 'hour'
                elif campionamento_choice == 'f':
                    # Torna al menu principale
                    break
                else:
                    print("Opzione non valida. Riprova.")

            elif choice == '2':
                # Visualizza il grafico
                df_grouped = convert_json_to_excel(messages, None, time_interval, json_file_path)
                generate_graph(df_grouped)  # Richiama la funzione per creare i grafici


            elif choice == '3':
                # Esporta i dati in un file Excel
                default_output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
                excel_file_path = os.path.join(default_output_folder, os.path.splitext(os.path.basename(json_file_path))[0] + "_output.xlsx")
                convert_json_to_excel(messages, excel_file_path, time_interval, json_file_path)

            elif choice == '4':
                # Filtra i messaggi
                keyword = input("Inserisci la parola chiave per il filtro: ")
                messages = filter_messages(messages, keyword)

            elif choice == '5':
                # Visualizza i messaggi partizionati
                partitioned_messages_list = partition_messages(messages)
                while True:
                    print("\nMenu Partizionamento:")
                    print("a. Opera")
                    print("b. Autori")
                    # print("c. Micronazione")
                    # print("d. Luogo")
                    print("c. Esporta in Excel")
                    print("d. Indietro")

                    partition_choice = input("Seleziona un'opzione: ").lower()

                    if partition_choice == 'a':
                        # Restituisce i titoli delle opere
                        display_titles(partitioned_messages_list)
                    elif partition_choice == 'b':
                        # Restituisce gli autori e il conteggio
                        display_authors_count(partitioned_messages_list)
                    elif partition_choice == 'c':
                        # Esporta i dati partizionati in Excel
                        default_output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
                        output_excel_path = os.path.join(default_output_folder, os.path.splitext(os.path.basename(json_file_path))[0] + "_partizionato.xlsx")
                        export_to_excel(partitioned_messages_list, output_excel_path, json_file_path)
                        print(f"Dati partizionati esportati in Excel: {output_excel_path}")
                    elif partition_choice == 'd':
                        # Torna al menu principale del partizionamento
                        break
                    else:
                        print("Opzione non valida. Riprova.")

            elif choice == '6':
                # Esegui l'analisi di Fourier
                df_grouped = convert_json_to_excel(messages, None, time_interval, json_file_path)
                fourier_analysis(df_grouped, time_interval)

            elif choice == '7':
                print("Uscita dal programma.")
                sys.exit(0)

            else:
                print("Opzione non valida. Riprova.")

if __name__ == '__main__':
    main()