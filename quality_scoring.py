#!/usr/bin/env python3
"""
Qualitäts-Scoring-System für Grundstücke in Hamburg
Bewertet Grundstücke basierend auf Baugenehmigungsstatus und anderen Kriterien
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class QualityScorer:
    """
    Bewertet Grundstücke nach Bauqualität und berechnet qualitätsadjustierte Preise
    """
    
    # Scoring-Gewichte (0-100 Punkte pro Kategorie)
    WEIGHTS = {
        'building_permission': 0.40,  # 40% - Wichtigster Faktor
        'development': 0.25,          # 25% - Erschließung
        'construction_readiness': 0.20, # 20% - Kurzfristige Bebaubarkeit
        'demolition': 0.15            # 15% - Abriss nötig
    }
    
    def __init__(self, csv_file='grundstuecke_hamburg.csv'):
        self.df = pd.read_csv(csv_file)
        self._prepare_data()
    
    def _prepare_data(self):
        """Bereitet Daten für Scoring vor"""
        # Konvertiere zu numerischen Werten
        numeric_cols = ['purchase_price', 'plot_area', 'price_per_sqm']
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
    
    def score_building_permission(self, row):
        """
        Bewertet Baugenehmigungsstatus (0-100 Punkte)
        
        Kategorien:
        - Baugenehmigung vorhanden: 100 Punkte (sofort baubar)
        - Bauvorbescheid: 70 Punkte (hohe Sicherheit)
        - Bebauungsplan: 50 Punkte (mittlere Sicherheit)
        - Ohne Genehmigung: 20 Punkte (unsicher)
        """
        constructible_type = str(row['constructible_type']).lower()
        
        # Hier erweitern wir basierend auf den Daten
        if 'construction plan' in constructible_type or 'bebauungsplan' in constructible_type:
            return 50  # Bebauungsplan vorhanden
        elif 'like neighbour' in constructible_type:
            return 40  # Nach Nachbarbebauung
        elif pd.isna(row['constructible_type']):
            return 20  # Keine Information = niedrig bewerten
        else:
            return 30  # Sonstige
    
    def score_development(self, row):
        """
        Bewertet Erschließungsstatus (0-100 Punkte)
        
        - Voll erschlossen: 100 Punkte
        - Teilweise erschlossen: 60 Punkte  
        - Nicht erschlossen: 20 Punkte
        """
        development = str(row['development']).lower()
        
        if 'developed' == development or development == 'developed':
            return 100  # Voll erschlossen
        elif 'partially' in development:
            return 60   # Teilweise erschlossen
        elif 'not developed' in development:
            return 20   # Nicht erschlossen
        else:
            return 50   # Unbekannt = mittlere Bewertung
    
    def score_construction_readiness(self, row):
        """
        Bewertet kurzfristige Bebaubarkeit (0-100 Punkte)
        
        - Kurzfristig bebaubar: 100 Punkte
        - Nicht kurzfristig: 40 Punkte
        """
        short_term = str(row['short_term_constructible']).lower()
        
        if short_term == 'yes':
            return 100
        else:
            return 40
    
    def score_demolition(self, row):
        """
        Bewertet Abriss-Notwendigkeit (0-100 Punkte)
        
        - Kein Abriss nötig: 100 Punkte (besser)
        - Abriss nötig: 30 Punkte (zusätzliche Kosten)
        """
        demolition = str(row['demolition']).lower()
        
        if demolition == 'no':
            return 100  # Kein Abriss = gut
        elif demolition == 'yes':
            return 30   # Abriss nötig = Abzug
        else:
            return 70   # Unbekannt
    
    def calculate_quality_score(self):
        """Berechnet Gesamtqualitätsscore für alle Grundstücke"""
        
        # Einzelscores berechnen
        self.df['score_building_permission'] = self.df.apply(self.score_building_permission, axis=1)
        self.df['score_development'] = self.df.apply(self.score_development, axis=1)
        self.df['score_construction_readiness'] = self.df.apply(self.score_construction_readiness, axis=1)
        self.df['score_demolition'] = self.df.apply(self.score_demolition, axis=1)
        
        # Gewichteter Gesamtscore (0-100)
        self.df['quality_score'] = (
            self.df['score_building_permission'] * self.WEIGHTS['building_permission'] +
            self.df['score_development'] * self.WEIGHTS['development'] +
            self.df['score_construction_readiness'] * self.WEIGHTS['construction_readiness'] +
            self.df['score_demolition'] * self.WEIGHTS['demolition']
        )
        
        # Qualitätskategorie zuweisen
        self.df['quality_category'] = pd.cut(
            self.df['quality_score'],
            bins=[0, 40, 60, 80, 100],
            labels=['Niedrig', 'Mittel', 'Gut', 'Sehr Gut']
        )
        
        return self.df
    
    def calculate_quality_adjusted_price(self):
        """
        Berechnet qualitätsadjustierte Preise
        
        Logik:
        - Sehr Gut (80-100): Preis bleibt oder steigt um 10%
        - Gut (60-80): Preis = Basispreis
        - Mittel (40-60): Preis sollte 10-20% niedriger sein
        - Niedrig (0-40): Preis sollte 20-40% niedriger sein
        """
        
        # Berechne erwarteten Preis basierend auf Qualität
        # Referenz: Score 70 = fairer Preis
        self.df['quality_factor'] = self.df['quality_score'] / 70.0
        
        # Erwarteter Preis basierend auf Qualität
        self.df['expected_price_per_sqm'] = self.df['price_per_sqm'] / self.df['quality_factor']
        
        # Berechne Über-/Unterbewertung
        self.df['price_quality_ratio'] = (
            self.df['price_per_sqm'] / self.df['expected_price_per_sqm']
        )
        
        # Rating: Ist der Preis fair für die Qualität?
        def get_value_rating(ratio):
            if pd.isna(ratio):
                return 'Keine Daten'
            elif ratio < 0.85:
                return 'Sehr günstig'
            elif ratio < 0.95:
                return 'Günstig'
            elif ratio <= 1.05:
                return 'Fair'
            elif ratio <= 1.15:
                return 'Teuer'
            else:
                return 'Sehr teuer'
        
        self.df['value_rating'] = self.df['price_quality_ratio'].apply(get_value_rating)
        
        return self.df
    
    def get_quality_statistics(self):
        """Erstellt Statistiken nach Qualitätskategorie"""
        
        stats = self.df.groupby('quality_category').agg({
            'id': 'count',
            'purchase_price': ['mean', 'median'],
            'plot_area': 'mean',
            'price_per_sqm': 'mean',
            'quality_score': 'mean'
        }).round(0)
        
        stats.columns = ['Anzahl', 'Ø Preis', 'Median Preis', 'Ø Fläche', 'Ø Preis/m²', 'Ø Score']
        
        return stats
    
    def find_best_quality_deals(self, top_n=20):
        """
        Findet die besten Angebote basierend auf Qualität-Preis-Verhältnis
        
        Kombiniert:
        - Hohe Qualität
        - Günstiger Preis relativ zur Qualität
        """
        
        # Filtere gültige Daten
        valid_df = self.df.dropna(subset=['quality_score', 'price_quality_ratio', 'purchase_price'])
        
        # Sortiere nach: Hohe Qualität UND günstiger Preis
        valid_df['deal_score'] = (
            valid_df['quality_score'] * 0.6 +  # 60% Qualität
            (100 - valid_df['price_quality_ratio'] * 50) * 0.4  # 40% Preis-Attraktivität
        )
        
        best_deals = valid_df.nlargest(top_n, 'deal_score')[
            ['title', 'district', 'purchase_price', 'plot_area', 'price_per_sqm',
             'quality_score', 'quality_category', 'value_rating', 'deal_score',
             'short_term_constructible', 'development', 'constructible_type']
        ].copy()
        
        return best_deals
    
    def create_quality_visualizations(self, output_dir='charts'):
        """Erstellt Visualisierungen zur Qualitätsanalyse"""
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Qualitätsverteilung
        plt.figure(figsize=(12, 6))
        quality_counts = self.df['quality_category'].value_counts()
        colors = ['#e74c3c', '#f39c12', '#3498db', '#27ae60']
        quality_counts.plot(kind='bar', color=colors[:len(quality_counts)])
        plt.title('Verteilung der Grundstücks-Qualitätskategorien', fontsize=14, fontweight='bold')
        plt.xlabel('Qualitätskategorie', fontsize=12)
        plt.ylabel('Anzahl Grundstücke', fontsize=12)
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/quality_distribution.png', dpi=300, bbox_inches='tight')
        print(f"✅ Chart gespeichert: {output_dir}/quality_distribution.png")
        
        # 2. Qualität vs. Preis/m²
        plt.figure(figsize=(12, 8))
        valid_data = self.df.dropna(subset=['quality_score', 'price_per_sqm'])
        
        scatter = plt.scatter(
            valid_data['quality_score'],
            valid_data['price_per_sqm'],
            c=valid_data['quality_score'],
            s=valid_data['plot_area'] / 20,
            alpha=0.6,
            cmap='RdYlGn'
        )
        plt.colorbar(scatter, label='Qualitäts-Score')
        plt.xlabel('Qualitäts-Score (0-100)', fontsize=12)
        plt.ylabel('Preis pro m² (€)', fontsize=12)
        plt.title('Qualitäts-Score vs. Preis pro m²', fontsize=14, fontweight='bold')
        plt.axvline(x=70, color='red', linestyle='--', alpha=0.5, label='Referenz-Score (70)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'{output_dir}/quality_vs_price.png', dpi=300, bbox_inches='tight')
        print(f"✅ Chart gespeichert: {output_dir}/quality_vs_price.png")
        
        # 3. Preis-Qualitäts-Rating
        plt.figure(figsize=(14, 6))
        rating_counts = self.df['value_rating'].value_counts()
        rating_order = ['Sehr günstig', 'Günstig', 'Fair', 'Teuer', 'Sehr teuer']
        rating_counts = rating_counts.reindex([r for r in rating_order if r in rating_counts.index])
        
        colors_rating = ['#27ae60', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
        rating_counts.plot(kind='bar', color=colors_rating[:len(rating_counts)])
        plt.title('Preis-Qualitäts-Bewertung der Grundstücke', fontsize=14, fontweight='bold')
        plt.xlabel('Bewertung', fontsize=12)
        plt.ylabel('Anzahl Grundstücke', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/value_rating_distribution.png', dpi=300, bbox_inches='tight')
        print(f"✅ Chart gespeichert: {output_dir}/value_rating_distribution.png")
        
        # 4. Qualitätsfaktoren-Heatmap
        plt.figure(figsize=(10, 8))
        quality_cols = ['score_building_permission', 'score_development', 
                       'score_construction_readiness', 'score_demolition']
        
        # Durchschnittliche Scores nach Qualitätskategorie
        heatmap_data = self.df.groupby('quality_category')[quality_cols].mean()
        heatmap_data.columns = ['Baugenehmigung', 'Erschließung', 'Kurzfristig bebaubar', 'Kein Abriss']
        
        sns.heatmap(heatmap_data.T, annot=True, fmt='.0f', cmap='RdYlGn', 
                   cbar_kws={'label': 'Durchschnitts-Score'})
        plt.title('Qualitätsfaktoren nach Kategorie', fontsize=14, fontweight='bold')
        plt.xlabel('Qualitätskategorie', fontsize=12)
        plt.ylabel('Qualitätsfaktor', fontsize=12)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/quality_factors_heatmap.png', dpi=300, bbox_inches='tight')
        print(f"✅ Chart gespeichert: {output_dir}/quality_factors_heatmap.png")
        
        plt.close('all')
    
    def export_quality_analysis(self, filename='grundstuecke_mit_qualitaet.xlsx'):
        """Exportiert erweiterte Analyse mit Qualitätsscores"""
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Sheet 1: Alle Daten mit Qualitätsscores
            export_cols = [
                'id', 'title', 'district', 'purchase_price', 'plot_area', 'price_per_sqm',
                'quality_score', 'quality_category', 'value_rating',
                'score_building_permission', 'score_development', 
                'score_construction_readiness', 'score_demolition',
                'short_term_constructible', 'development', 'constructible_type', 'demolition',
                'full_address'
            ]
            
            self.df[export_cols].to_excel(writer, sheet_name='Alle Daten mit Qualität', index=False)
            
            # Sheet 2: Qualitätsstatistiken
            quality_stats = self.get_quality_statistics()
            quality_stats.to_excel(writer, sheet_name='Qualitätsstatistiken')
            
            # Sheet 3: Top Qualitäts-Angebote
            best_deals = self.find_best_quality_deals(30)
            best_deals.to_excel(writer, sheet_name='Top Qualitäts-Angebote', index=False)
            
            # Sheet 4: Nach Qualitätskategorie
            for category in ['Sehr Gut', 'Gut', 'Mittel', 'Niedrig']:
                category_df = self.df[self.df['quality_category'] == category][export_cols]
                if len(category_df) > 0:
                    sheet_name = f'Qualität: {category}'
                    category_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✅ Excel-Datei erstellt: {filename}")
        return filename
    
    def save_enhanced_csv(self, filename='grundstuecke_hamburg_mit_qualitaet.csv'):
        """Speichert erweiterte CSV mit Qualitätsscores"""
        self.df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Erweiterte CSV gespeichert: {filename}")
        return filename

def main():
    print("\n" + "="*80)
    print("🎯 QUALITÄTS-SCORING-SYSTEM FÜR GRUNDSTÜCKE")
    print("="*80 + "\n")
    
    # Scorer initialisieren
    scorer = QualityScorer()
    
    print("📊 Berechne Qualitäts-Scores...")
    scorer.calculate_quality_score()
    scorer.calculate_quality_adjusted_price()
    
    # Statistiken
    print("\n" + "="*80)
    print("📈 QUALITÄTS-STATISTIKEN")
    print("="*80)
    stats = scorer.get_quality_statistics()
    print(stats.to_string())
    
    # Verteilung
    print("\n" + "="*80)
    print("📊 QUALITÄTS-VERTEILUNG")
    print("="*80)
    print(scorer.df['quality_category'].value_counts().to_string())
    
    # Best Deals
    print("\n" + "="*80)
    print("💎 TOP 10 QUALITÄTS-ANGEBOTE (Beste Preis-Qualitäts-Verhältnis)")
    print("="*80)
    best_deals = scorer.find_best_quality_deals(10)
    print(best_deals[['district', 'purchase_price', 'quality_score', 
                     'quality_category', 'value_rating']].to_string())
    
    # Preis-Rating Verteilung
    print("\n" + "="*80)
    print("💰 PREIS-QUALITÄTS-BEWERTUNG")
    print("="*80)
    print(scorer.df['value_rating'].value_counts().to_string())
    
    # Visualisierungen
    print("\n📈 Erstelle Visualisierungen...")
    scorer.create_quality_visualizations()
    
    # Export
    print("\n📊 Exportiere Daten...")
    scorer.export_quality_analysis()
    scorer.save_enhanced_csv()
    
    print("\n" + "="*80)
    print("✅ QUALITÄTS-ANALYSE ABGESCHLOSSEN!")
    print("="*80)
    print("\n📁 Erstellte Dateien:")
    print("   • grundstuecke_mit_qualitaet.xlsx - Excel mit Qualitätsscores")
    print("   • grundstuecke_hamburg_mit_qualitaet.csv - Erweiterte CSV")
    print("   • charts/quality_distribution.png - Qualitätsverteilung")
    print("   • charts/quality_vs_price.png - Qualität vs. Preis")
    print("   • charts/value_rating_distribution.png - Preis-Bewertungen")
    print("   • charts/quality_factors_heatmap.png - Qualitätsfaktoren")
    print()

if __name__ == '__main__':
    main()
