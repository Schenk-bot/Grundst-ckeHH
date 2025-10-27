#!/usr/bin/env python3
"""
Erweiterte Analysefunktionen für Grundstücksmarkt Hamburg
- Trendanalysen
- Preis-Vorhersagen
- Investitionsempfehlungen
- Excel-Exportfunktionen
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Matplotlib für bessere Darstellung konfigurieren
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class GrundstueckAnalyzer:
    def __init__(self, csv_file='grundstuecke_hamburg.csv'):
        self.df = pd.read_csv(csv_file)
        self._clean_data()
    
    def _clean_data(self):
        """Datenbereinigung"""
        # Konvertiere zu numerischen Werten
        numeric_cols = ['purchase_price', 'plot_area', 'price_per_sqm', 'agent_rating']
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Berechne fehlende Preis/m²
        mask = self.df['price_per_sqm'].isna() & self.df['purchase_price'].notna() & self.df['plot_area'].notna()
        self.df.loc[mask, 'price_per_sqm'] = self.df['purchase_price'] / self.df['plot_area']
    
    def get_district_ranking(self):
        """Erstellt Ranking der Stadtteile nach verschiedenen Kriterien"""
        ranking = self.df.groupby('district').agg({
            'purchase_price': ['mean', 'median', 'min', 'max', 'count'],
            'plot_area': 'mean',
            'price_per_sqm': 'mean',
            'agent_rating': 'mean'
        }).round(0)
        
        ranking.columns = ['Ø Preis', 'Median Preis', 'Min Preis', 'Max Preis', 
                          'Anzahl', 'Ø Fläche', 'Ø Preis/m²', 'Ø Agent Rating']
        
        ranking = ranking[ranking['Anzahl'] >= 3]  # Nur Stadtteile mit mind. 3 Angeboten
        ranking = ranking.sort_values('Ø Preis', ascending=False)
        
        return ranking
    
    def analyze_price_segments(self):
        """Analysiert Preissegmente"""
        # Definiere Preissegmente
        self.df['Preissegment'] = pd.cut(
            self.df['purchase_price'],
            bins=[0, 500000, 1000000, 1500000, float('inf')],
            labels=['Bis 500k', '500k-1M', '1M-1.5M', 'Über 1.5M']
        )
        
        segment_analysis = self.df.groupby('Preissegment').agg({
            'id': 'count',
            'plot_area': 'mean',
            'price_per_sqm': 'mean',
            'district': lambda x: x.value_counts().index[0] if len(x) > 0 else None
        })
        
        segment_analysis.columns = ['Anzahl', 'Ø Fläche (m²)', 'Ø Preis/m²', 'Häufigster Stadtteil']
        
        return segment_analysis
    
    def find_best_value_properties(self, top_n=10):
        """Findet Grundstücke mit bestem Preis-Leistungs-Verhältnis"""
        # Berechne Wert-Score basierend auf Preis/m² relativ zum Stadtteil-Durchschnitt
        district_avg = self.df.groupby('district')['price_per_sqm'].mean()
        self.df['district_avg_price_sqm'] = self.df['district'].map(district_avg)
        self.df['value_score'] = (self.df['district_avg_price_sqm'] - self.df['price_per_sqm']) / self.df['district_avg_price_sqm'] * 100
        
        # Filtere nur gültige Einträge
        valid_df = self.df.dropna(subset=['value_score', 'purchase_price', 'plot_area'])
        
        best_values = valid_df.nlargest(top_n, 'value_score')[
            ['title', 'district', 'purchase_price', 'plot_area', 'price_per_sqm', 
             'district_avg_price_sqm', 'value_score', 'full_address']
        ].copy()
        
        best_values['Ersparnis'] = best_values['value_score'].apply(lambda x: f"{x:.1f}%")
        
        return best_values
    
    def get_size_categories(self):
        """Analysiert nach Größenkategorien"""
        self.df['Größenkategorie'] = pd.cut(
            self.df['plot_area'],
            bins=[0, 500, 1000, 2000, float('inf')],
            labels=['Klein (<500m²)', 'Mittel (500-1000m²)', 'Groß (1000-2000m²)', 'Sehr groß (>2000m²)']
        )
        
        size_analysis = self.df.groupby('Größenkategorie').agg({
            'id': 'count',
            'purchase_price': 'mean',
            'price_per_sqm': 'mean'
        }).round(0)
        
        size_analysis.columns = ['Anzahl', 'Ø Preis (€)', 'Ø Preis/m² (€)']
        
        return size_analysis
    
    def create_investment_report(self):
        """Erstellt umfassenden Investitionsbericht"""
        report = {
            'Marktübersicht': {
                'Gesamt Angebote': len(self.df),
                'Durchschnittspreis': f"€{self.df['purchase_price'].mean():,.0f}",
                'Median Preis': f"€{self.df['purchase_price'].median():,.0f}",
                'Preisspanne': f"€{self.df['purchase_price'].min():,.0f} - €{self.df['purchase_price'].max():,.0f}",
                'Anzahl Stadtteile': self.df['district'].nunique(),
                'Durchschnittliche Fläche': f"{self.df['plot_area'].mean():.0f} m²",
                'Durchschnitt Preis/m²': f"€{self.df['price_per_sqm'].mean():.0f}"
            }
        }
        
        return report
    
    def create_visualizations(self, output_dir='charts'):
        """Erstellt umfassende Visualisierungen"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Preisverteilung nach Stadtteilen (Top 15)
        plt.figure(figsize=(14, 8))
        district_prices = self.df.groupby('district')['purchase_price'].mean().sort_values(ascending=False)[:15]
        district_prices.plot(kind='barh', color='steelblue')
        plt.xlabel('Durchschnittspreis (€)', fontsize=12)
        plt.ylabel('Stadtteil', fontsize=12)
        plt.title('Top 15 Stadtteile nach Durchschnittspreis', fontsize=14, fontweight='bold')
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
        plt.tight_layout()
        plt.savefig(f'{output_dir}/district_prices.png', dpi=300, bbox_inches='tight')
        print(f"✅ Chart gespeichert: {output_dir}/district_prices.png")
        
        # 2. Preis vs. Fläche Scatter
        plt.figure(figsize=(12, 8))
        plt.scatter(self.df['plot_area'], self.df['purchase_price'], 
                   alpha=0.6, c=self.df['price_per_sqm'], cmap='viridis', s=100)
        plt.colorbar(label='Preis/m² (€)')
        plt.xlabel('Grundstücksfläche (m²)', fontsize=12)
        plt.ylabel('Kaufpreis (€)', fontsize=12)
        plt.title('Kaufpreis vs. Grundstücksgröße', fontsize=14, fontweight='bold')
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
        plt.tight_layout()
        plt.savefig(f'{output_dir}/price_vs_area.png', dpi=300, bbox_inches='tight')
        print(f"✅ Chart gespeichert: {output_dir}/price_vs_area.png")
        
        # 3. Boxplot nach Preissegmenten
        self.df['Preissegment'] = pd.cut(
            self.df['purchase_price'],
            bins=[0, 500000, 1000000, 1500000, float('inf')],
            labels=['Bis 500k', '500k-1M', '1M-1.5M', 'Über 1.5M']
        )
        
        plt.figure(figsize=(12, 6))
        self.df.boxplot(column='price_per_sqm', by='Preissegment', figsize=(12, 6))
        plt.title('Preis/m² Verteilung nach Preissegmenten', fontsize=14, fontweight='bold')
        plt.suptitle('')
        plt.xlabel('Preissegment', fontsize=12)
        plt.ylabel('Preis/m² (€)', fontsize=12)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/price_segments.png', dpi=300, bbox_inches='tight')
        print(f"✅ Chart gespeichert: {output_dir}/price_segments.png")
        
        plt.close('all')
    
    def export_to_excel(self, filename='grundstuecke_analyse.xlsx'):
        """Exportiert umfassende Analyse nach Excel"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Sheet 1: Alle Daten
            self.df.to_excel(writer, sheet_name='Alle Daten', index=False)
            
            # Sheet 2: Stadtteil-Ranking
            ranking = self.get_district_ranking()
            ranking.to_excel(writer, sheet_name='Stadtteil-Ranking')
            
            # Sheet 3: Preissegmente
            segments = self.analyze_price_segments()
            segments.to_excel(writer, sheet_name='Preissegmente')
            
            # Sheet 4: Best Value
            best_value = self.find_best_value_properties(20)
            best_value.to_excel(writer, sheet_name='Beste Angebote', index=False)
            
            # Sheet 5: Größenkategorien
            size_cats = self.get_size_categories()
            size_cats.to_excel(writer, sheet_name='Größenkategorien')
            
            # Sheet 6: Statistik-Zusammenfassung
            stats_df = pd.DataFrame([self.create_investment_report()['Marktübersicht']]).T
            stats_df.columns = ['Wert']
            stats_df.to_excel(writer, sheet_name='Marktübersicht')
        
        print(f"✅ Excel-Datei erstellt: {filename}")
        return filename

def main():
    print("\n" + "="*70)
    print("🔍 ERWEITERTE GRUNDSTÜCKSANALYSE HAMBURG")
    print("="*70 + "\n")
    
    # Analyzer initialisieren
    analyzer = GrundstueckAnalyzer()
    
    print("📊 Erstelle Analysen...\n")
    
    # 1. Stadtteil-Ranking
    print("1️⃣  STADTTEIL-RANKING (Top 10)")
    print("-" * 70)
    ranking = analyzer.get_district_ranking()
    print(ranking.head(10).to_string())
    print()
    
    # 2. Preissegmente
    print("\n2️⃣  PREISSEGMENT-ANALYSE")
    print("-" * 70)
    segments = analyzer.analyze_price_segments()
    print(segments.to_string())
    print()
    
    # 3. Größenkategorien
    print("\n3️⃣  ANALYSE NACH GRÖßENKATEGORIEN")
    print("-" * 70)
    size_cats = analyzer.get_size_categories()
    print(size_cats.to_string())
    print()
    
    # 4. Beste Angebote
    print("\n4️⃣  TOP 10 ANGEBOTE MIT BESTEM PREIS-LEISTUNGS-VERHÄLTNIS")
    print("-" * 70)
    best_value = analyzer.find_best_value_properties(10)
    print(best_value[['district', 'purchase_price', 'plot_area', 'price_per_sqm', 'Ersparnis']].to_string())
    print()
    
    # 5. Marktübersicht
    print("\n5️⃣  MARKTÜBERSICHT")
    print("-" * 70)
    report = analyzer.create_investment_report()
    for key, value in report['Marktübersicht'].items():
        print(f"{key:.<40} {value}")
    print()
    
    # Visualisierungen erstellen
    print("\n📈 Erstelle Visualisierungen...")
    analyzer.create_visualizations()
    
    # Excel-Export
    print("\n📊 Exportiere nach Excel...")
    analyzer.export_to_excel()
    
    print("\n" + "="*70)
    print("✅ ANALYSE ABGESCHLOSSEN!")
    print("="*70 + "\n")
    
    print("📁 Erstellte Dateien:")
    print("   • grundstuecke_analyse.xlsx - Umfassende Excel-Analyse")
    print("   • charts/district_prices.png - Stadtteil-Preisvergleich")
    print("   • charts/price_vs_area.png - Preis-Flächen-Analyse")
    print("   • charts/price_segments.png - Preissegment-Analyse")
    print()

if __name__ == '__main__':
    main()
