import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from jupyter_dash import JupyterDash

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

df=pd.read_csv(r"Covid_confirmed.csv")
df=df[df.Lat!=0]
column = df.columns[4:] #= pd.to_datetime(df.columns[4:])#.dt.strftime("%m/%d/%y")
column = pd.to_datetime(column)
column = column.strftime('%Y-%m-%d').tolist()
columnNames = ['Province/State','Country/Region','Lat','Long']
columnNames.extend(column)
df.columns = columnNames


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#app = JupyterDash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("Country"),
                dcc.Dropdown(
                    id='dcountry',
                    value='Afghanistan',
                    clearable=False,
                    multi=False,
                    disabled=False,
                    searchable=True,
                    persistence='string',
                    persistence_type='local',
                    options= [
                        {'label': i, 'value':i}
                        for i in df['Country/Region'].unique()
                    ],
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Scale"),
                dcc.Dropdown(
                    id='dscale',
                    value='N',
                    clearable=False,
                    multi=False,
                    disabled=False,
                    searchable=True,
                    persistence='string',
                    persistence_type='local',
                    options=[
                        {'label': 'Normal', 'value': 'N'},
                        {'label': 'Log', 'value': 'L'}
                    ],
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Type"),
                dcc.Dropdown(
                    id='dtype',
                    value='T',
                    clearable=False,
                    multi=False,
                    disabled=False,
                    searchable=True,
                    persistence='string',
                    persistence_type='local',
                    options=[
                        {'label':'Total', 'value': 'T'},
                        {'label': 'Daily Change', 'value': 'DC'}
                    ],
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Date - For Maps"),
            ]
        ),
        dbc.FormGroup(
            [
                dcc.DatePickerSingle(
                    id='date-single',
                    display_format='Y-M-D',
                    min_date_allowed=datetime.datetime.strptime(df.columns[4], '%Y-%m-%d').date(),
                    max_date_allowed=datetime.datetime.strptime(df.columns[-1], '%Y-%m-%d').date(),
                    initial_visible_month=datetime.datetime.strptime(df.columns[4], '%Y-%m-%d').date(),
                    date=datetime.datetime.strptime(df.columns[4], '%Y-%m-%d').date()
                ),
            ]
        ),
    ],
    body=True,
)

tab_graph = dbc.Card(
    dcc.Graph(id='line-graph')
)

app.layout = dbc.Container(
    [
        html.H1("COVID Test Cases"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                dbc.Col(
                    [
                        dbc.Tabs(
                            [
                                dbc.Tab(label='Graph', tab_id='graph'),
                                dbc.Tab(label='Map', tab_id='map')
                            ],
                            id ='tabs',
                            active_tab='graph'
                        ),
                        html.Div(id='tab-content', className='p-4')
                    ]
                ,md=8),
            ]
        )    
    ],
    fluid=True,
)

@app.callback(
    Output('tab-content', 'children'),
    [
        Input('tabs', 'active_tab'),
        Input('dcountry', 'value'),
        Input('dscale', 'value'),
        Input('dtype', 'value'),
        Input('date-single', 'date'),
    ]
)

def render_tab_content(active_tab, Country, TScale, DType, Date):
    if active_tab is not None:
        if active_tab == 'graph':

            valLog = False
            
            if TScale != 'N':
                valLog = True

            dff=df[(df['Country/Region']==Country)]
            dff=dff.drop(['Province/State','Lat','Long'],axis=1)
            dff = dff.groupby(['Country/Region'], as_index=False).sum()
            dff=dff.transpose()
            dff=dff.drop(dff.index[0])
            dff['processed_data'] = dff[0].diff(1)
            dff['processed_data']=dff['processed_data'].fillna(0)
            
            if DType == 'T':
                figure = px.line(dff, x=dff.index, y=[0], height=600, log_y=valLog)
                figure.update_layout(xaxis={'title':'Date'},yaxis={'title':'Total Sum Cases'}, title={'text':Country, 'font':{'size':28},'x':0.5,'xanchor':'center'})
                return dcc.Graph(figure=figure)
            
            elif DType =='DC':
                figure = px.line(dff, x=dff.index, y='processed_data', height=600, log_y=valLog)
                figure.update_layout(xaxis={'title':'Date'},yaxis={'title':'Daily Cases'}, title={'text':Country, 'font':{'size':28},'x':0.5,'xanchor':'center'})  
                return dcc.Graph(figure=figure)
            
        elif active_tab == 'map':
            agg_dict = { 'Total':sum, 'Lat':np.median, 'Long':np.median }
            dff=df.rename(columns={ 'Country/Region':'Country' }) \
                    .melt(id_vars=['Country', 'Province/State', 'Lat', 'Long'], var_name='date', value_name='Total') \
                    .astype({'date':'datetime64[ns]', 'Total':'int64'}, errors='ignore')
            dff = dff.groupby(['Country', 'date']).agg(agg_dict).reset_index()
            dff = dff[dff['date'] == Date]
            figure = px.scatter_mapbox(dff, lat=dff.Lat, lon=dff.Long, hover_name=dff.Country, size=dff.Total, size_max = 50, zoom=1, mapbox_style="open-street-map")
            return dcc.Graph(figure=figure)
        
        return "No tab selected"

#app.run_server(mode='inline')
if __name__ == '__main__':
    app.run_server(debug=False)