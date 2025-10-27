#!/usr/bin/env python3
"""
Erweiterte Web-Plattform mit Qualitäts-Scoring
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium import plugins
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Lade Daten mit Qualitätsscores
df = pd.read_csv('grundstuecke_hamburg_mit_qualitaet.csv')

# Datenbereinigung
numeric_cols = ['purchase_price', 'plot_area', 'price_per_sqm', 'quality_score']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

def create_quality_distribution():
    """Qualitätsverteilung"""
    quality_counts = df['quality_category'].value_counts()
    colors = {'Sehr Gut': '#27ae60', 'Gut': '#3498db', 'Mittel': '#f39c12', 'Niedrig': '#e74c3c'}
    
    fig = go.Figure(data=[
        go.Bar(
            x=quality_counts.index,
            y=quality_counts.values,
            marker_color=[colors.get(cat, '#95a5a6') for cat in quality_counts.index],
            text=quality_counts.values,
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Qualitätsverteilung der Grundstücke',
        xaxis_title='Qualitätskategorie',
        yaxis_title='Anzahl',
        height=400,
        showlegend=False
    )
    
    return fig.to_html(include_plotlyjs=False, div_id='quality_dist')

def create_quality_vs_price():
    """Qualität vs. Preis Scatter"""
    fig = px.scatter(
        df.dropna(subset=['quality_score', 'price_per_sqm']),
        x='quality_score',
        y='price_per_sqm',
        color='quality_category',
        size='plot_area',
        hover_data=['title', 'district', 'purchase_price'],
        title='Qualitäts-Score vs. Preis pro m²',
        labels={
            'quality_score': 'Qualitäts-Score (0-100)',
            'price_per_sqm': 'Preis/m² (€)',
            'quality_category': 'Qualität'
        },
        color_discrete_map={'Sehr Gut': '#27ae60', 'Gut': '#3498db', 'Mittel': '#f39c12', 'Niedrig': '#e74c3c'}
    )
    
    fig.update_layout(height=500)
    return fig.to_html(include_plotlyjs=False, div_id='quality_price')

def create_value_rating():
    """Preis-Qualitäts-Rating"""
    rating_counts = df['value_rating'].value_counts()
    rating_order = ['Sehr günstig', 'Günstig', 'Fair', 'Teuer', 'Sehr teuer']
    rating_counts = rating_counts.reindex([r for r in rating_order if r in rating_counts.index])
    
    colors = ['#27ae60', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
    
    fig = go.Figure(data=[
        go.Bar(
            x=rating_counts.index,
            y=rating_counts.values,
            marker_color=colors[:len(rating_counts)],
            text=rating_counts.values,
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Preis-Qualitäts-Bewertung',
        xaxis_title='Bewertung',
        yaxis_title='Anzahl',
        height=400,
        showlegend=False
    )
    
    return fig.to_html(include_plotlyjs=False, div_id='value_rating')

def create_district_quality():
    """Durchschnittliche Qualität nach Stadtteil"""
    district_quality = df.groupby('district').agg({
        'quality_score': 'mean',
        'id': 'count'
    }).reset_index()
    
    district_quality = district_quality[district_quality['id'] >= 3].sort_values('quality_score', ascending=False)[:15]
    
    fig = px.bar(
        district_quality,
        x='district',
        y='quality_score',
        title='Top 15 Stadtteile nach Durchschnittsqualität',
        labels={'district': 'Stadtteil', 'quality_score': 'Ø Qualitäts-Score'},
        color='quality_score',
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(height=500, showlegend=False)
    return fig.to_html(include_plotlyjs=False, div_id='district_quality')

def create_enhanced_map():
    """Karte mit Qualitäts-Farbcodierung"""
    df_map = df.dropna(subset=['latitude', 'longitude', 'quality_score'])
    
    center_lat = df_map['latitude'].mean()
    center_lng = df_map['longitude'].mean()
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    marker_cluster = plugins.MarkerCluster().add_to(m)
    
    def get_quality_color(score):
        """Farbe basierend auf Qualitätsscore"""
        if pd.isna(score):
            return 'gray'
        elif score >= 70:
            return 'green'
        elif score >= 50:
            return 'blue'
        elif score >= 40:
            return 'orange'
        else:
            return 'red'
    
    for idx, row in df_map.iterrows():
        popup_html = f"""
        <div style="width:320px">
            <h4>{row['title'][:80] if pd.notna(row['title']) else 'Grundstück'}</h4>
            <hr>
            <b>📍 Adresse:</b> {row['full_address']}<br>
            <b>💰 Preis:</b> €{row['purchase_price']:,.0f}<br>
            <b>📏 Fläche:</b> {row['plot_area']:,.0f} m²<br>
            <b>💶 Preis/m²:</b> €{row['price_per_sqm']:.0f}/m²<br>
            <hr>
            <b>⭐ Qualitäts-Score:</b> {row['quality_score']:.0f}/100<br>
            <b>🏆 Kategorie:</b> {row['quality_category']}<br>
            <b>💎 Bewertung:</b> {row['value_rating']}<br>
            <hr>
            <small>
            <b>Bebaubarkeit:</b> {row['short_term_constructible']}<br>
            <b>Erschließung:</b> {row['development']}<br>
            </small>
        </div>
        """
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.Icon(
                color=get_quality_color(row['quality_score']),
                icon='star' if row['quality_score'] >= 70 else 'home',
                prefix='fa'
            )
        ).add_to(marker_cluster)
    
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 220px; height: 160px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:13px; padding: 12px; border-radius: 5px;">
    <p style="margin:0; font-weight:bold; font-size:14px;">Qualitäts-Score</p>
    <hr style="margin:5px 0;">
    <p style="margin:3px 0;"><i class="fa fa-star" style="color:green"></i> <b>Sehr Gut/Gut</b> (70-100)</p>
    <p style="margin:3px 0;"><i class="fa fa-home" style="color:blue"></i> <b>Mittel</b> (50-69)</p>
    <p style="margin:3px 0;"><i class="fa fa-home" style="color:orange"></i> <b>Mittel-</b> (40-49)</p>
    <p style="margin:3px 0;"><i class="fa fa-home" style="color:red"></i> <b>Niedrig</b> (&lt;40)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m._repr_html_()

@app.route('/')
def index():
    """Dashboard mit Qualitätsanalyse"""
    stats = {
        'total_count': len(df),
        'avg_price': df['purchase_price'].mean(),
        'avg_quality': df['quality_score'].mean(),
        'high_quality': len(df[df['quality_category'] == 'Gut']) + len(df[df['quality_category'] == 'Sehr Gut']),
        'best_value': len(df[df['value_rating'].isin(['Sehr günstig', 'Günstig'])])
    }
    
    charts = {
        'quality_dist': create_quality_distribution(),
        'quality_price': create_quality_vs_price(),
        'value_rating': create_value_rating(),
        'district_quality': create_district_quality()
    }
    
    return render_template('index_enhanced.html', stats=stats, charts=charts)

@app.route('/map')
def map_view():
    """Karte mit Qualitätsscores"""
    map_html = create_enhanced_map()
    return render_template('map_enhanced.html', map_html=map_html)

@app.route('/api/quality-data')
def quality_data():
    """API für Qualitätsdaten"""
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/quality-stats')
def quality_stats():
    """API für Qualitätsstatistiken"""
    stats = df.groupby('quality_category').agg({
        'purchase_price': ['mean', 'count'],
        'quality_score': 'mean',
        'price_per_sqm': 'mean'
    }).reset_index()
    
    return jsonify(stats.to_dict(orient='records'))

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🏠 ERWEITERTE GRUNDSTÜCKS-ANALYSEPLATTFORM MIT QUALITÄTS-SCORING")
    print("="*80)
    print(f"\n📊 Datenübersicht:")
    print(f"   • {len(df)} Grundstücke mit Qualitätsscores")
    print(f"   • Ø Qualitäts-Score: {df['quality_score'].mean():.1f}/100")
    print(f"   • Hohe Qualität (Gut+): {len(df[df['quality_category'].isin(['Gut', 'Sehr Gut'])])} Angebote")
    print(f"   • Beste Preis-Qualität: {len(df[df['value_rating'].isin(['Sehr günstig', 'Günstig'])])} Angebote")
    print(f"\n🌐 Server startet auf: http://localhost:5001")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
