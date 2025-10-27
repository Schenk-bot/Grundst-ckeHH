from flask import Flask, render_template, send_from_directory
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins
import os

app = Flask(__name__)

# Load and prepare data
try:
    df = pd.read_csv('grundstuecke_hamburg.csv')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
except Exception as e:
    print(f"Error loading data: {e}")
    df = pd.DataFrame()

def check_building_permit_status(row):
    """
    Prüft ob Baugenehmigung oder Bauvorbescheid vorhanden ist.
    Priorität 1: Baugenehmigung
    Priorität 2: Bauvorbescheid
    """
    text_fields = [
        str(row.get('description', '')),
        str(row.get('location_desc', '')),
        str(row.get('further_notes', ''))
    ]
    combined_text = ' '.join(text_fields).lower()
    
    has_permit = 'baugenehmigung' in combined_text
    has_preliminary = 'bauvorbescheid' in combined_text
    
    return has_permit, has_preliminary

def get_construction_priority(row):
    """
    Neue Prioritäten-Klassifizierung:
    
    PRIORITÄT 1 (SOFORT INVESTIERBAR):
    - Mit Baugenehmigung (21 Objekte gefunden)
    - Mit Bauvorbescheid (17 Objekte gefunden)
    
    PRIORITÄT 2 (KURZFRISTIG):
    - Kurzfristig bebaubar ohne explizite Genehmigung
    
    PRIORITÄT 3 (MITTELFRISTIG - GÜNSTIGER):
    - Mit Bebauungsplan + erschlossen
    - §34 BauGB (wie Nachbarbebauung)
    
    PRIORITÄT 4 (LANGFRISTIG):
    - Nur Bebauungsplan
    - Teilerschlossen
    - Nicht erschlossen
    """
    has_permit, has_preliminary = check_building_permit_status(row)
    
    constructible_type = str(row.get('constructible_type', 'Unknown'))
    development = str(row.get('development', 'Unknown'))
    short_term = str(row.get('short_term_constructible', 'Unknown'))
    
    # PRIORITÄT 1: Baugenehmigung (höchste Priorität)
    if has_permit:
        return {
            'priority': 1,
            'status': '🏆 MIT BAUGENEHMIGUNG',
            'icon': 'star',
            'color': 'darkgreen',
            'description': 'Sofort bebaubar - Baugenehmigung liegt vor',
            'investment_note': '⚡ SOFORT INVESTIERBAR - Höchster Wert'
        }
    
    # PRIORITÄT 1: Bauvorbescheid
    if has_preliminary:
        return {
            'priority': 1,
            'status': '⭐ MIT BAUVORBESCHEID',
            'icon': 'star',
            'color': 'green',
            'description': 'Sofort bebaubar - Bauvorbescheid erteilt',
            'investment_note': '⚡ SOFORT INVESTIERBAR'
        }
    
    # PRIORITÄT 2: Kurzfristig bebaubar (ohne explizite Genehmigung)
    if short_term == 'Yes':
        return {
            'priority': 2,
            'status': '✅ KURZFRISTIG BEBAUBAR',
            'icon': 'flag',
            'color': 'lightgreen',
            'description': 'Kurzfristig bebaubar',
            'investment_note': 'Schnelle Realisierung möglich'
        }
    
    # PRIORITÄT 3: Mit Bebauungsplan + erschlossen (GÜNSTIGER!)
    if constructible_type == 'Construction plan' and development == 'Developed':
        return {
            'priority': 3,
            'status': '🏘️ BEBAUUNGSPLAN + ERSCHLOSSEN',
            'icon': 'home',
            'color': 'blue',
            'description': 'Mit Bebauungsplan und vollständiger Erschließung',
            'investment_note': '💰 MITTELFRISTIG - Meist günstiger'
        }
    
    # PRIORITÄT 3: §34 BauGB - wie Nachbarbebauung
    if constructible_type == 'like neighbour construction':
        return {
            'priority': 3,
            'status': '🏘️ §34 BauGB',
            'icon': 'home',
            'color': 'orange',
            'description': 'Bebauung wie Nachbargrundstücke (§34 BauGB)',
            'investment_note': '💰 MITTELFRISTIG'
        }
    
    # PRIORITÄT 3: Nur Bebauungsplan
    if constructible_type == 'Construction plan':
        return {
            'priority': 3,
            'status': '📋 NUR BEBAUUNGSPLAN',
            'icon': 'info-sign',
            'color': 'lightblue',
            'description': 'Bebauungsplan vorhanden',
            'investment_note': '💰 LÄNGERFRISTIG - Günstiger'
        }
    
    # PRIORITÄT 4: Voll erschlossen
    if development == 'Developed':
        return {
            'priority': 4,
            'status': 'ℹ️ VOLL ERSCHLOSSEN',
            'icon': 'info-sign',
            'color': 'cadetblue',
            'description': 'Vollständig erschlossen',
            'investment_note': 'Langfristig'
        }
    
    # PRIORITÄT 4: Teilerschlossen
    if development == 'Developed partially':
        return {
            'priority': 4,
            'status': '⚠️ TEILERSCHLOSSEN',
            'icon': 'exclamation-sign',
            'color': 'lightgray',
            'description': 'Teilweise erschlossen',
            'investment_note': 'Langfristig - Zusatzkosten'
        }
    
    # PRIORITÄT 4: Status unklar
    return {
        'priority': 4,
        'status': '❓ STATUS UNKLAR',
        'icon': 'question-sign',
        'color': 'gray',
        'description': 'Baurechtsstatus nicht eindeutig',
        'investment_note': 'Weitere Prüfung erforderlich'
    }

@app.route('/')
def index():
    if df.empty:
        return "Error: No data available"
    
    # Basic statistics
    total_properties = len(df)
    total_value = df['purchase_price'].sum()
    avg_price = df['purchase_price'].mean()
    avg_price_per_sqm = df['price_per_sqm'].mean()
    
    # District analysis
    district_stats = df.groupby('district').agg({
        'id': 'count',
        'purchase_price': 'mean',
        'plot_area': 'mean'
    }).round(0).reset_index()
    district_stats.columns = ['Stadtteil', 'Anzahl', 'Ø Preis (€)', 'Ø Fläche (m²)']
    
    # Price distribution chart
    fig_price = px.histogram(df, x='purchase_price', nbins=30, 
                             title='Preisverteilung der Grundstücke',
                             labels={'purchase_price': 'Kaufpreis (€)', 'count': 'Anzahl'})
    fig_price.update_layout(template='plotly_white')
    price_chart = fig_price.to_html(full_html=False)
    
    # Top districts chart
    top_districts = df['district'].value_counts().head(10)
    fig_districts = px.bar(x=top_districts.values, y=top_districts.index, 
                          orientation='h',
                          title='Top 10 Stadtteile nach Anzahl der Angebote',
                          labels={'x': 'Anzahl Grundstücke', 'y': 'Stadtteil'})
    fig_districts.update_layout(template='plotly_white')
    districts_chart = fig_districts.to_html(full_html=False)
    
    return render_template('index.html',
                         total_properties=total_properties,
                         total_value=f"{total_value:,.0f}",
                         avg_price=f"{avg_price:,.0f}",
                         avg_price_per_sqm=f"{avg_price_per_sqm:,.0f}",
                         district_stats=district_stats.to_html(classes='table table-striped', index=False),
                         price_chart=price_chart,
                         districts_chart=districts_chart)

@app.route('/map')
def show_map():
    if df.empty:
        return "Error: No data available"
    
    # Create map centered on Hamburg
    m = folium.Map(
        location=[53.5511, 9.9937],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Count properties by priority
    priority_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    
    # Add markers for each property
    for idx, row in df.iterrows():
        priority_info = get_construction_priority(row)
        priority_counts[priority_info['priority']] += 1
        
        # Generate Exposé URL
        expose_url = f"https://www.immobilienscout24.de/expose/{row['id']}"
        
        # Create popup content with construction status prominently displayed
        popup_html = f"""
        <div style="width: 360px; font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{row['title'][:80]}</h4>
            
            <div style="background: linear-gradient(135deg, {priority_info['color']} 0%, {priority_info['color']}dd 100%); 
                        color: white; padding: 12px; border-radius: 8px; margin: 10px 0; font-weight: bold; text-align: center;">
                <div style="font-size: 16px; margin-bottom: 5px;">{priority_info['status']}</div>
                <div style="font-size: 12px; opacity: 0.9;">{priority_info['description']}</div>
                <div style="font-size: 13px; margin-top: 8px; padding: 5px; background: rgba(255,255,255,0.2); border-radius: 4px;">
                    {priority_info['investment_note']}
                </div>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                <tr style="background: #f8f9fa;">
                    <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>Preis:</strong></td>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{row['purchase_price']:,.0f} €</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>Fläche:</strong></td>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{row['plot_area']:,.0f} m²</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>Preis/m²:</strong></td>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{row['price_per_sqm']:,.0f} €</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>Stadtteil:</strong></td>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{row['district']}</td>
                </tr>
            </table>
            
            <a href="{expose_url}" target="_blank" 
               style="display: block; text-align: center; padding: 12px; 
                      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; text-decoration: none; border-radius: 6px; 
                      font-weight: bold; margin-top: 10px; transition: all 0.3s;">
                📋 Exposé öffnen
            </a>
        </div>
        """
        
        # Add marker with custom icon
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=380),
            tooltip=f"{row['title'][:50]}... - {priority_info['status']}",
            icon=folium.Icon(
                color=priority_info['color'],
                icon=priority_info['icon'],
                prefix='glyphicon'
            )
        ).add_to(m)
    
    # Create custom legend with priority ranking
    legend_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; width: 320px; 
                background: white; border: 2px solid #333; z-index: 9999; 
                padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 15px 0; text-align: center; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
            🏗️ Baurechts-Prioritäten
        </h4>
        
        <div style="background: #d4edda; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 4px solid #28a745;">
            <strong style="color: #155724; font-size: 14px;">PRIORITÄT 1 - SOFORT INVESTIERBAR</strong>
        </div>
        <div style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
            <i class="glyphicon glyphicon-star" style="color: darkgreen;"></i>
            <strong>Mit Baugenehmigung ({priority_counts.get(1, 0)} Objekte)</strong><br>
            <span style="font-size: 11px; color: #666;">⚡ Höchster Wert - Sofort bebaubar</span>
        </div>
        <div style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
            <i class="glyphicon glyphicon-star" style="color: green;"></i>
            <strong>Mit Bauvorbescheid</strong><br>
            <span style="font-size: 11px; color: #666;">⚡ Sofortige Realisierung möglich</span>
        </div>
        
        <div style="background: #fff3cd; padding: 10px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #ffc107;">
            <strong style="color: #856404; font-size: 14px;">PRIORITÄT 2 - KURZFRISTIG</strong>
        </div>
        <div style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
            <i class="glyphicon glyphicon-flag" style="color: lightgreen;"></i>
            <strong>Kurzfristig bebaubar ({priority_counts.get(2, 0)} Objekte)</strong><br>
            <span style="font-size: 11px; color: #666;">Schnelle Realisierung</span>
        </div>
        
        <div style="background: #cfe2ff; padding: 10px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #0d6efd;">
            <strong style="color: #084298; font-size: 14px;">PRIORITÄT 3 - MITTELFRISTIG</strong>
        </div>
        <div style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
            <i class="glyphicon glyphicon-home" style="color: blue;"></i>
            <strong>Bebauungsplan + erschlossen ({priority_counts.get(3, 0)} Objekte)</strong><br>
            <span style="font-size: 11px; color: #666;">💰 Meist günstiger - Längere Planung</span>
        </div>
        <div style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
            <i class="glyphicon glyphicon-home" style="color: orange;"></i>
            <strong>§34 BauGB (wie Nachbar)</strong><br>
            <span style="font-size: 11px; color: #666;">💰 Mittelfristig realisierbar</span>
        </div>
        
        <div style="background: #e2e3e5; padding: 10px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #6c757d;">
            <strong style="color: #383d41; font-size: 14px;">PRIORITÄT 4 - LANGFRISTIG</strong>
        </div>
        <div style="margin-bottom: 5px; padding: 6px; background: #f8f9fa; border-radius: 4px;">
            <i class="glyphicon glyphicon-question-sign" style="color: gray;"></i>
            <strong>Sonstige ({priority_counts.get(4, 0)} Objekte)</strong><br>
            <span style="font-size: 11px; color: #666;">Weitere Prüfung erforderlich</span>
        </div>
        
        <div style="margin-top: 15px; padding: 10px; background: #f0f0f0; border-radius: 6px; font-size: 11px; text-align: center;">
            <strong>💡 Investment-Tipp:</strong><br>
            Priorität 1: Höchster Wert, sofort bebaubar<br>
            Priorität 3: Meist günstiger, längere Planung
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    map_html = m._repr_html_()
    
    return render_template('map.html', map_html=map_html)

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
