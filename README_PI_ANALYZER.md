# PI Analysis Tool

## Panoramica

Il **PI Analysis Tool** è un'applicazione web completa per l'analisi delle metriche di Program Increment (PI) per il progetto ISDOP e i progetti correlati in Jira. L'applicazione scopre automaticamente i progetti collegati attraverso relazioni parent/child e genera report dettagliati sui completamenti durante un periodo PI specificato.

## Caratteristiche Principali

### 🔍 Scoperta Automatica dei Progetti
- Parte dal progetto base inserito nella configurazione
- Identifica automaticamente progetti correlati tramite link parent/child delle sub-feature
- Analizza tutti i progetti collegati in un'unica sessione

### 📊 Analisi Completa delle Metriche PI
- **Conteggio per tipo di issue**: Bug, Story, Sub-task, Sub-Feature, Feature...
- **Analisi delle stime**: Somma delle stime iniziali per ogni tipo
- **Percentuale non stimata**: Calcolo della % di issue senza stime
- **Breakdown per progetto**: Distribuzione del lavoro tra progetti

### 📄 Report PDF Professionale
- Layout professionale con logo aziendale
- Tabelle dettagliate con metriche per tipo e progetto
- Raccomandazioni basate sui dati analizzati
- Numerazione pagine e footer personalizzato
- Metadati PDF con autore e informazioni

### 🌐 Interfaccia Web User-Friendly
- Form di input intuitivo per parametri PI
- Visualizzazione real-time dei risultati
- Cards colorate per diversi tipi di metriche
- Download PDF con un click
- Possibilita' di caricare un CSV con tutte le issue da analizzare (riduce il carico su Jira)
- il file di configurazione poi consente di limitare le ricerche su singolo progetto per ridurre il carico

## Architettura del Sistema

```
pi_analyzer.py          # Core logic per analisi PI
├── PIAnalyzer         # Classe principale per analisi
├── _discover_related_projects()  # Scoperta progetti collegati
├── _fetch_pi_issues()           # Recupero issue completate
├── _analyze_pi_metrics()        # Analisi metriche
└── _create_pi_report()          # Generazione report

pi_web_app.py          # Applicazione Flask
├── /                  # Homepage con form
├── /analyze_pi        # Endpoint per analisi
└── /generate_pi_report # Endpoint per PDF

pi_pdf_generator.py    # Generatore PDF
├── PIPDFReportGenerator # Classe per PDF
├── _create_title_page() # Pagina titolo
├── _create_executive_summary() # Sommario esecutivo
├── _create_detailed_analysis() # Analisi dettagliata
└── _create_recommendations()   # Raccomandazioni

templates/pi_analyzer.html # Interfaccia web
tests/test_pi_analyzer.py  # Suite di test TDD
```

## Installazione e Setup

### Prerequisiti
```bash
pip install flask reportlab python-dateutil requests pandas numpy
```

### Struttura File
```
PerseusLeadTime/
├── pi_analyzer.py
├── pi_web_app.py
├── pi_pdf_generator.py
├── templates/
│   └── pi_analyzer.html
├── static/
│   └── logo.png
|   └── favicon.ico
├── tests/
│   └── test_pi_analyzer.py
└── README_PI_ANALYZER.md
```

## Utilizzo

### 1. Avvio dell'Applicazione Web
```bash
python pi_web_app.py
```
L'applicazione sarà disponibile su `http://localhost:5200`

### 2. Configurazione Parametri
- **Jira Server URL**: URL del server Jira (es. https://company.atlassian.net)
- **Access Token (PAT)**: Personal Access Token per autenticazione
- **PI Start Date**: Data inizio Program Increment (formato YYYY-MM-DD)
- **PI End Date**: Data fine Program Increment (formato YYYY-MM-DD)

### 3. Analisi e Report
1. Inserire i parametri nel form web
2. Cliccare "Analyze PI"
3. Visualizzare i risultati nelle cards colorate
4. Scaricare il report PDF cliccando "Download PDF Report"

## Logica di Scoperta dei Progetti

### Algoritmo di Scoperta
1. **Progetto Base**: Inizia sempre con ISDOP
2. **Query Parent Links**: `project = ISDOP AND issueFunction in hasLinkType("Parent")`
3. **Query Child Links**: `project = ISDOP AND issueFunction in hasLinkType("Child")`
4. **Estrazione Progetti**: Analizza i link delle issue per identificare progetti collegati
5. **Set Finale**: Unisce tutti i progetti trovati per l'analisi

### Tipi di Link Supportati
- **Parent/Child**: Relazioni gerarchiche tra issue
- **Inward/Outward**: Link bidirezionali tra progetti
- **Sub-Feature Links**: Collegamenti specifici per sub-feature

## Metriche Analizzate

### Per Tipo di Issue
- **Count**: Numero totale di issue completate
- **Total Estimates**: Somma delle stime iniziali in ore
- **Estimated Count**: Numero di issue con stime
- **Unestimated Count**: Numero di issue senza stime
- **Unestimated Percentage**: Percentuale di issue non stimate

### Per Progetto
- **Issues Count**: Numero di issue per progetto
- **Total Estimates**: Ore stimate per progetto
- **Distribution**: Distribuzione del lavoro tra progetti

### Metriche Globali
- **Total Issues**: Issue totali completate nel PI
- **Total Projects**: Progetti coinvolti nell'analisi
- **Overall Unestimated %**: Percentuale globale non stimata
- **PI Duration**: Durata del PI in giorni

## Test-Driven Development (TDD)

### Suite di Test Completa
```bash
python -m pytest tests/test_pi_analyzer.py -v
```

### Copertura Test
- **Unit Tests**: Test per ogni metodo della classe PIAnalyzer
- **Integration Tests**: Test del workflow completo
- **Mock Tests**: Test con dati simulati per isolamento
- **Edge Cases**: Test per scenari limite e errori

### Esempi di Test
```python
def test_analyze_pi_success(self):
    """Test successful PI analysis."""
    # Setup mocks and test data
    # Execute analysis
    # Verify results structure and content

def test_discover_related_projects_success(self):
    """Test successful project discovery."""
    # Mock Jira API responses
    # Test project discovery logic
    # Verify related projects found

def test_analyze_pi_metrics(self):
    """Test PI metrics analysis."""
    # Test metrics calculation
    # Verify percentages and totals
    # Check data structure integrity
```

## Configurazione Avanzata

### Personalizzazione Tipi di Issue
```python
# In pi_analyzer.py
self.issue_types = ['Bug', 'Story', 'Sub-task', 'Sub-Feature', 'Feature', 'Epic']
```

### Personalizzazione Status di Completamento
```python
# In pi_analyzer.py
self.completion_statuses = ['Done', 'Closed', 'Resolved', 'Delivered']
```

### Personalizzazione Logo
- Posizionare il logo in `static/logo.png`
- Dimensioni consigliate: 300x300px
- Formato supportato: PNG con trasparenza

## Troubleshooting

### Problemi Comuni

#### 1. Errore di Connessione Jira
```
Error: Failed to connect to Jira. Please check your URL and token.
```
**Soluzione**: Verificare URL Jira e validità del PAT

#### 2. Nessun Progetto Correlato Trovato
```
Warning: Using base project only: ISDOP
```
**Soluzione**: Verificare che esistano link parent/child nelle issue ISDOP

#### 3. Nessuna Issue Completata
```
Error: No issues found for the provided criteria
```
**Soluzione**: Verificare date PI e status di completamento

#### 4. Errore Generazione PDF
```
Error: PDF generation failed
```
**Soluzione**: Verificare installazione reportlab e permessi file

### Debug e Logging

#### Abilitare Debug Logging
```python
# In pi_analyzer.py, cambiare:
logging.basicConfig(level=logging.DEBUG)
```

#### Log Dettagliati
- Scoperta progetti: `🔍 Discovering projects related to ISDOP`
- Fetch issue: `📥 Fetching completed issues from X projects`
- Analisi metriche: `📊 Analyzing metrics for X issues`
- Generazione PDF: `✅ PI PDF report generated successfully`

## Estensioni Future

### Possibili Miglioramenti
1. **Dashboard Interattivo**: Grafici dinamici con Chart.js
2. **Confronto PI**: Analisi comparativa tra diversi PI
3. **Previsioni**: Modelli predittivi basati su dati storici
4. **Export Excel**: Esportazione dati in formato Excel
5. **API REST**: Endpoint per integrazione con altri sistemi
6. **Notifiche**: Alert automatici per anomalie nelle metriche

### Integrazione con Altri Tool
- **Confluence**: Export automatico su pagine Confluence
- **Slack/Teams**: Notifiche automatiche dei report
- **Power BI**: Connettore per dashboard aziendali
- **Jenkins**: Integrazione in pipeline CI/CD

## Supporto e Contributi

### Autore
**Pietro Maffi** - PI Analysis Tool 2025

### Licenza
Copyright Pietro Maffi 2025 - Tutti i diritti riservati

### Contributi
Per contributi e miglioramenti, seguire il processo TDD:
1. Scrivere test per nuove funzionalità
2. Implementare il codice minimo per passare i test
3. Refactoring e ottimizzazione
4. Documentazione aggiornata

---

*Questo tool è stato progettato per supportare Scrum Master e team Agile nell'analisi delle metriche PI e nel miglioramento continuo dei processi di sviluppo.*
