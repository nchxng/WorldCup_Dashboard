import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import requests
from io import StringIO

# Fetch and Prepare Data
url = "https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals"
response = requests.get(url)
response.raise_for_status()
tables = pd.read_html(StringIO(response.text))
df_finals = tables[3]  # Select the table with finals data
df_finals = df_finals[['Year', 'Winners', 'Runners-up']]

# Standardize "West Germany" to "Germany"
df_finals.loc[:, 'Winners'] = df_finals['Winners'].replace("West Germany", "Germany")
df_finals.loc[:, 'Runners-up'] = df_finals['Runners-up'].replace("West Germany", "Germany")

# Define a Mapping of Country Names to ISO-3 Codes
country_iso_map = {
    "Argentina": "ARG", "Brazil": "BRA", "Croatia": "HRV", "Czechoslovakia": "CZE",
    "England": "GBR", "France": "FRA", "Germany": "DEU", "Hungary": "HUN",
    "Italy": "ITA", "Netherlands": "NLD", "Spain": "ESP", "Sweden": "SWE", "Uruguay": "URY"
}

# Function to get ISO-3 codes
def get_iso3(country):
    return country_iso_map.get(country, None)  # Return ISO-3 or None if not in map

# Count Wins per Country
win_counts = df_finals['Winners'].value_counts().reset_index()
win_counts.columns = ['Country', 'Wins']
win_counts['ISO3'] = win_counts['Country'].apply(get_iso3)
win_counts = win_counts.dropna(subset=['ISO3'])

# Create the Choropleth Map
fig = px.choropleth(
    win_counts,
    locations="ISO3",
    locationmode="ISO-3",
    color="Wins",
    hover_name="Country",
    color_continuous_scale="Viridis",
    scope="world",
    title="FIFA World Cup Wins by Country",
    labels={'Wins': 'Number of Wins'}
)

# Get Unique Years for the Dropdown
years = df_finals['Year'].unique().tolist()

# Initialize the Dash App and Server
app = dash.Dash(__name__)
server = app.server

# Dashboard Layout
app.layout = html.Div([
    html.H1("FIFA World Cup Winners Dashboard", style={'textAlign': 'center', 'color': 'black', 'margin-bottom': '30px'}),
    # Map
    dcc.Graph(id='world-map', figure=fig),

    # Dropdown Selection of winning countries
    html.H2("Select a Winning Country to View Its Number of Wins", style={'textAlign': 'center'}),
    html.P("Note: Only countries that have won the World Cup are listed. If a country is not listed, it has not won.", 
           style={'textAlign': 'center', 'fontSize': '14px', 'color': '#7f8c8d'}),
    dcc.Dropdown(
        id='country-dropdown',
        options=[{'label': country, 'value': country} for country in sorted(win_counts['Country'].unique())],
        placeholder="Select a country",
        style={'width': '50%', 'margin': 'auto'},
        clearable=True
    ),
    html.H2("Country Wins", style={'textAlign': 'center'}),
    html.Div(id='selected-country', 
             children="Select a country from the dropdown to see its number of wins", 
             style={'textAlign': 'center'}),
    
    # Dropdown Selection of the year
    html.H2("Select a Year", style={'textAlign': 'center'}),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': year, 'value': year} for year in sorted(years)],
        placeholder="Select a year",
        style={'width': '50%', 'margin': 'auto'}
    ),
    html.H2("Year Information", style={'textAlign': 'center'}),
    html.Div(id='year-info', style={'textAlign': 'center'})
], style={'padding': '20px'})

# Callback for Select Country
@app.callback(
    Output('selected-country', 'children'),
    Input('country-dropdown', 'value')
)
def display_selected_country(selected_country):
    if selected_country is not None:
        wins = win_counts[win_counts['Country'] == selected_country]['Wins'].values[0]
        return f"{selected_country} has won the World Cup {wins} time(s)"
    return "Select a country from the dropdown to see its number of wins"

# Callback for Select Year
@app.callback(
    Output('year-info', 'children'),
    Input('year-dropdown', 'value')
)
def display_year_info(selected_year):
    if selected_year is None:
        return "Select a year to see the winner and runner-up"
    year_data = df_finals[df_finals['Year'] == selected_year]
    if not year_data.empty:
        winner = year_data['Winners'].values[0]
        runner_up = year_data['Runners-up'].values[0]
        return f"In {selected_year}, {winner} won the World Cup against {runner_up}"
    return "No data available for the selected year"

if __name__ == '__main__':
    app.run(debug=True)
