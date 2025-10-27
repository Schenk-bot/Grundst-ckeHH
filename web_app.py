#!/usr/bin/env python3
"""
Interaktive Webplattform für Grundstücksanalyse in Hamburg - FIXED VERSION
Mit verbesserter Fehlerbehandlung für die Karte
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins
import json
from flask import Flask, render_template, request, jsonify
import os
import traceback

# Flask App initialisieren
app = Flask(__name__)

# Globale Daten laden
try:
    df = pd.read_csv('grundstuecke_hamburg.csv')
    print(f"✅ CSV geladen: {len(df)} Einträge")
except Exception as e:
    print(f"❌ FEHLER beim Laden der CSV: {e}")
    df = pd.DataFrame()

# Datenbereinigung
df['purchase_price'] = pd.to_numeric(df['purchase_price'], errors='coerce')
df['plot_area'] = pd.to_numeric(df['plot_area'], errors='coerce')
df['price_per_sqm'] = pd.to_numeric(df['price_per_sqm'], errors='coerce')
df['agent_rating'] = pd.to_numeric(df['agent_rating'], errors='coerce')
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

# Fehlende price_per_sqm berechnen
df.loc[df['price_per_sqm'].isna() & df['purchase_price'].notna() & df['plot_area'].notna(), 'price_per_sqm'] = \
    df['purchase_price'] / df['plot_area']

def create_price_distribution_chart():
    """Erstellt Preisverteilungsdiagramm"""
    try:
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
    except Exception as e:
        print(f"Fehler bei price_distribution: {e}")
        return "<p>Diagramm konnte nicht geladen werden</p>"

def create_area_distribution_chart():
    """Erstellt Flächenverteilungsdiagramm"""
    try:
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
    except Exception as e:
        print(f"Fehler bei area_distribution: {e}")
        return "<p>Diagramm konnte nicht geladen werden</p>"

def create_district_comparison():
    """Vergleich der Stadtteile nach Durchschnittspreis"""
    try:
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
    except Exception as e:
        print(f"Fehler bei district_comparison: {e}")
        return "<p>Diagramm konnte nicht geladen werden</p>"

def create_price_per_sqm_chart():
    """Preis pro m² nach Stadtteil"""
    try:
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
    except Exception as e:
        print(f"Fehler bei price_per_sqm_chart: {e}")
        return "<p>Diagramm konnte nicht geladen werden</p>"

def create_scatter_plot():
    """Scatter Plot: Preis vs. Fläche"""
    try:
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
    except Exception as e:
        print(f"Fehler bei scatter_plot: {e}")
        return "<p>Diagramm konnte nicht geladen werden</p>"

def create_map():
    """Erstellt interaktive Karte mit allen Grundstücken - VERBESSERTE VERSION"""
    try:
        # Filtern und Datenbereinigung
        df_map = df.dropna(subset=['latitude', 'longitude', 'purchase_price']).copy()
        
        if len(df_map) == 0:
            return "<h3>Keine Grundstücke mit GPS-Koordinaten gefunden</h3>"
        
        print(f"🗺️  Erstelle Karte mit {len(df_map)} Grundstücken...")
        
        # Zentrum berechnen
        center_lat = df_map['latitude'].mean()
        center_lng = df_map['longitude'].mean()
        
        # Karte erstellen
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Marker Cluster hinzufügen
        marker_cluster = plugins.MarkerCluster().add_to(m)
        
        # Preisspanne für Farbcodierung
        price_data = df_map[df_map['price_per_sqm'].notna()]['price_per_sqm']
        if len(price_data) > 0:
            min_price = price_data.min()
            max_price = price_data.max()
        else:
            min_price = 0
            max_price = 1000
        
        def get_color(price_sqm):
            """Bestimmt Farbe basierend auf Preis/m²"""
            try:
                if pd.isna(price_sqm):
                    return 'gray'
                if max_price == min_price:
                    return 'blue'
                normalized = (price_sqm - min_price) / (max_price - min_price)
                if normalized < 0.33:
                    return 'green'
                elif normalized < 0.66:
                    return 'orange'
                else:
                    return 'red'
            except:
                return 'gray'
        
        # Marker für jedes Grundstück hinzufügen
        success_count = 0
        error_count = 0
        
        for idx, row in df_map.iterrows():
            try:
                # Sichere Werte extrahieren
                title = str(row.get('title', 'Grundstück'))[:80]
                address = str(row.get('full_address', 'Keine Adresse'))
                price = float(row.get('purchase_price', 0))
                area = float(row.get('plot_area', 0))
                price_sqm = float(row.get('price_per_sqm', 0)) if pd.notna(row.get('price_per_sqm')) else 0
                district = str(row.get('district', 'Unbekannt'))
                lat = float(row['latitude'])
                lng = float(row['longitude'])
                
                # Popup HTML erstellen mit Exposé-Link
                expose_id = row.get('id', '')
                expose_url = f"https://www.immobilienscout24.de/expose/{expose_id}" if expose_id else ""
                
                popup_html = f"""
                <div style="width:320px">
                    <h4 style="margin-bottom: 10px;">{title}</h4>
                    <hr style="margin: 10px 0;">
                    <b>📍 Adresse:</b> {address}<br>
                    <b>💰 Preis:</b> €{price:,.0f}<br>
                    <b>📏 Fläche:</b> {area:,.0f} m²<br>
                    <b>💵 Preis/m²:</b> €{price_sqm:.0f}/m²<br>
                    <b>🏘️ Stadtteil:</b> {district}<br>
                    {'<br><a href="' + expose_url + '" target="_blank" style="display: inline-block; margin-top: 10px; padding: 8px 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">📄 Zum Exposé →</a>' if expose_url else ''}
                </div>
                """
                
                # Marker hinzufügen
                folium.Marker(
                    location=[lat, lng],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color=get_color(price_sqm), icon='home', prefix='fa')
                ).add_to(marker_cluster)
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"  ⚠️  Fehler bei Marker {idx}: {e}")
                continue
        
        print(f"  ✅ {success_count} Marker erfolgreich hinzugefügt")
        if error_count > 0:
            print(f"  ⚠️  {error_count} Marker übersprungen")
        
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
        
    except Exception as e:
        error_msg = f"Fehler beim Erstellen der Karte: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return f"<h3>Fehler beim Laden der Karte</h3><p>{error_msg}</p>"

@app.route('/')
def index():
    """Hauptseite mit Dashboard"""
    try:
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
        
        charts = {
            'price_dist': create_price_distribution_chart(),
            'area_dist': create_area_distribution_chart(),
            'district_comp': create_district_comparison(),
            'price_sqm': create_price_per_sqm_chart(),
            'scatter': create_scatter_plot()
        }
        
        return render_template('index.html', stats=stats, charts=charts)
    except Exception as e:
        print(f"Fehler in index route: {e}")
        return f"<h1>Fehler beim Laden der Seite</h1><p>{str(e)}</p>", 500

@app.route('/map')
def map_view():
    """Karten-Seite - VERBESSERTE VERSION"""
    try:
        print("\n" + "="*60)
        print("🗺️  MAP ROUTE AUFGERUFEN")
        print("="*60)
        
        map_html = create_map()
        
        return render_template('map.html', map_html=map_html)
    except Exception as e:
        error_msg = f"Fehler in map route: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return f"<h1>Fehler beim Laden der Karte</h1><p>{error_msg}</p><pre>{traceback.format_exc()}</pre>", 500

@app.route('/api/data')
def get_data():
    """API Endpoint für Rohdaten"""
    try:
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/districts')
def get_districts():
    """API Endpoint für Stadtteil-Statistiken"""
    try:
        district_stats = df.groupby('district').agg({
            'purchase_price': ['mean', 'min', 'max', 'count'],
            'plot_area': 'mean',
            'price_per_sqm': 'mean'
        }).reset_index()
        
        return jsonify(district_stats.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏠 GRUNDSTÜCKS-ANALYSEPLATTFORM FÜR HAMBURG (FIXED)")
    print("="*60)
    print(f"\n📊 Datenübersicht:")
    print(f"   • {len(df)} Grundstücke analysiert")
    print(f"   • {df['district'].nunique()} Stadtteile")
    print(f"   • {(df['latitude'].notna() & df['longitude'].notna()).sum()} Grundstücke mit GPS-Koordinaten")
    print(f"   • Durchschnittspreis: €{df['purchase_price'].mean():,.0f}")
    print(f"   • Durchschnittliche Fläche: {df['plot_area'].mean():.0f} m²")
    print(f"\n🌐 Server startet...")
    print("="*60 + "\n")
    
    # WICHTIG: Port von Umgebungsvariable lesen (für Render.com)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
