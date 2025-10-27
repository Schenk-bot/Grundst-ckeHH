#!/usr/bin/env python3
"""
Interaktive Webplattform für Grundstücksanalyse in Hamburg
Features:
- Dashboard mit Statistiken und Visualisierungen
- Interaktive Karte mit allen Grundstücken
- Preisanalysen und Vergleiche
- Filterfunktionen
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium import plugins
import json
from flask import Flask, render_template, request, jsonify
import os

# Flask App initialisieren
app = Flask(__name__)

# Globale Daten laden
df = pd.read_csv('grundstuecke_hamburg.csv')

# Datenbereinigung
df['purchase_price'] = pd.to_numeric(df['purchase_price'], errors='coerce')
df['plot_area'] = pd.to_numeric(df['plot_area'], errors='coerce')
df['price_per_sqm'] = pd.to_numeric(df['price_per_sqm'], errors='coerce')
df['agent_rating'] = pd.to_numeric(df['agent_rating'], errors='coerce')

# Fehlende price_per_sqm berechnen
df.loc[df['price_per_sqm'].isna() & df['purchase_price'].notna() & df['plot_area'].notna(), 'price_per_sqm'] = \
    df['purchase_price'] / df['plot_area']

def create_price_distribution_chart():
    """Erstellt Preisverteilungsdiagramm"""
    fig = px.histogram(
        df.dropna(subset=['purchase_price']),
        x='purchase_price',
        nbins=30,
        title='Preisverteilung der Grundstücke in Hamburg',
        labels={'purchase_price': 'Kaufpreis (€)', 'count': 'Anzahl'},
        color_discrete_sequence=['#1f77b4']
    )
    fig.update_layout(
        xaxis_tickformat='€,.0f',
        showlegend=False,
        height=400
    )
    return fig.to_html(include_plotlyjs=False, div_id='price_dist')

def create_area_distribution_chart():
    """Erstellt Flächenverteilungsdiagramm"""
    fig = px.histogram(
        df.dropna(subset=['plot_area']),
        x='plot_area',
        nbins=30,
        title='Größenverteilung der Grundstücke',
        labels={'plot_area': 'Grundstücksfläche (m²)', 'count': 'Anzahl'},
        color_discrete_sequence=['#2ca02c']
    )
    fig.update_layout(showlegend=False, height=400)
    return fig.to_html(include_plotlyjs=False, div_id='area_dist')

def create_district_comparison():
    """Vergleich der Stadtteile nach Durchschnittspreis"""
    district_stats = df.groupby('district').agg({
        'purchase_price': ['mean', 'count'],
        'plot_area': 'mean',
        'price_per_sqm': 'mean'
    }).reset_index()
    
    district_stats.columns = ['district', 'avg_price', 'count', 'avg_area', 'avg_price_sqm']
    district_stats = district_stats[district_stats['count'] >= 3].sort_values('avg_price', ascending=False)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=district_stats['district'][:15],
        y=district_stats['avg_price'][:15],
        name='Durchschnittspreis',
        marker_color='#ff7f0e',
        text=[f"€{x:,.0f}" for x in district_stats['avg_price'][:15]],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Top 15 Stadtteile nach Durchschnittspreis',
        xaxis_title='Stadtteil',
        yaxis_title='Durchschnittspreis (€)',
        yaxis_tickformat='€,.0f',
        height=500,
        showlegend=False
    )
    
    return fig.to_html(include_plotlyjs=False, div_id='district_comp')

def create_price_per_sqm_chart():
    """Preis pro m² nach Stadtteil"""
    district_stats = df.groupby('district').agg({
        'price_per_sqm': 'mean',
        'id': 'count'
    }).reset_index()
    
    district_stats.columns = ['district', 'avg_price_sqm', 'count']
    district_stats = district_stats[district_stats['count'] >= 3].sort_values('avg_price_sqm', ascending=False)
    
    fig = px.bar(
        district_stats[:15],
        x='district',
        y='avg_price_sqm',
        title='Durchschnittlicher Preis pro m² nach Stadtteil (Top 15)',
        labels={'district': 'Stadtteil', 'avg_price_sqm': 'Preis/m² (€)'},
        color='avg_price_sqm',
        color_continuous_scale='RdYlGn_r'
    )
    
    fig.update_layout(
        yaxis_tickformat='€,.0f',
        height=500,
        showlegend=False
    )
    
    return fig.to_html(include_plotlyjs=False, div_id='price_sqm')

def create_scatter_plot():
    """Scatter Plot: Preis vs. Fläche"""
    df_clean = df.dropna(subset=['purchase_price', 'plot_area', 'district'])
    
    fig = px.scatter(
        df_clean,
        x='plot_area',
        y='purchase_price',
        color='district',
        size='price_per_sqm',
        hover_data=['title', 'full_address', 'price_per_sqm'],
        title='Kaufpreis vs. Grundstücksgröße nach Stadtteil',
        labels={
            'plot_area': 'Grundstücksfläche (m²)',
            'purchase_price': 'Kaufpreis (€)',
            'district': 'Stadtteil'
        }
    )
    
    fig.update_layout(height=600)
    fig.update_traces(marker=dict(line=dict(width=0.5, color='DarkSlateGrey')))
    
    return fig.to_html(include_plotlyjs=False, div_id='scatter')

def create_map():
    """Erstellt interaktive Karte mit allen Grundstücken"""
    # Filtere Daten mit gültigen Koordinaten
    df_map = df.dropna(subset=['latitude', 'longitude', 'purchase_price'])
    
    # Zentrum von Hamburg
    center_lat = df_map['latitude'].mean()
    center_lng = df_map['longitude'].mean()
    
    # Karte erstellen
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Marker Cluster für bessere Performance
    marker_cluster = plugins.MarkerCluster().add_to(m)
    
    # Farbskala für Preise
    min_price = df_map['price_per_sqm'].min()
    max_price = df_map['price_per_sqm'].max()
    
    def get_color(price_sqm):
        """Bestimmt Farbe basierend auf Preis/m²"""
        if pd.isna(price_sqm):
            return 'gray'
        normalized = (price_sqm - min_price) / (max_price - min_price)
        if normalized < 0.33:
            return 'green'
        elif normalized < 0.66:
            return 'orange'
        else:
            return 'red'
    
    # Marker hinzufügen
    for idx, row in df_map.iterrows():
        popup_html = f"""
        <div style="width:300px">
            <h4>{row['title'][:80] if pd.notna(row['title']) else 'Grundstück'}</h4>
            <hr>
            <b>Adresse:</b> {row['full_address']}<br>
            <b>Preis:</b> €{row['purchase_price']:,.0f}<br>
            <b>Fläche:</b> {row['plot_area']:,.0f} m²<br>
            <b>Preis/m²:</b> €{row['price_per_sqm']:.0f}/m²<br>
            <b>Stadtteil:</b> {row['district']}<br>
        </div>
        """
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=get_color(row['price_per_sqm']), icon='home', prefix='fa')
        ).add_to(marker_cluster)
    
    # Legende hinzufügen
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Preis pro m²</b></p>
    <p><i class="fa fa-circle" style="color:green"></i> Günstig</p>
    <p><i class="fa fa-circle" style="color:orange"></i> Mittel</p>
    <p><i class="fa fa-circle" style="color:red"></i> Teuer</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m._repr_html_()

@app.route('/')
def index():
    """Hauptseite mit Dashboard"""
    # Statistiken berechnen
    stats = {
        'total_count': len(df),
        'avg_price': df['purchase_price'].mean(),
        'median_price': df['purchase_price'].median(),
        'avg_area': df['plot_area'].mean(),
        'avg_price_sqm': df['price_per_sqm'].mean(),
        'districts_count': df['district'].nunique(),
        'min_price': df['purchase_price'].min(),
        'max_price': df['purchase_price'].max()
    }
    
    # Charts erstellen
    charts = {
        'price_dist': create_price_distribution_chart(),
        'area_dist': create_area_distribution_chart(),
        'district_comp': create_district_comparison(),
        'price_sqm': create_price_per_sqm_chart(),
        'scatter': create_scatter_plot()
    }
    
    return render_template('index.html', stats=stats, charts=charts)

@app.route('/map')
def map_view():
    """Karten-Seite"""
    map_html = create_map()
    return render_template('map.html', map_html=map_html)

@app.route('/api/data')
def get_data():
    """API Endpoint für Rohdaten"""
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/districts')
def get_districts():
    """API Endpoint für Stadtteil-Statistiken"""
    district_stats = df.groupby('district').agg({
        'purchase_price': ['mean', 'min', 'max', 'count'],
        'plot_area': 'mean',
        'price_per_sqm': 'mean'
    }).reset_index()
    
    return jsonify(district_stats.to_dict(orient='records'))

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏠 GRUNDSTÜCKS-ANALYSEPLATTFORM FÜR HAMBURG")
    print("="*60)
    print(f"\n📊 Datenübersicht:")
    print(f"   • {len(df)} Grundstücke analysiert")
    print(f"   • {df['district'].nunique()} Stadtteile")
    print(f"   • Durchschnittspreis: €{df['purchase_price'].mean():,.0f}")
    print(f"   • Durchschnittliche Fläche: {df['plot_area'].mean():.0f} m²")
    print(f"\n🌐 Server startet auf: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
