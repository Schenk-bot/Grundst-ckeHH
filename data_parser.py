#!/usr/bin/env python3
"""
XML-Daten-Parser für ImmobilienScout24 Grundstücksdaten
Extrahiert alle relevanten Informationen und konvertiert sie in strukturierte Daten
"""

import xml.etree.ElementTree as ET
import pandas as pd
import json
import re
from datetime import datetime

class GrundstueckParser:
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.data = []
        
    def parse_price(self, price_str):
        """Extrahiert Preis aus String wie '€598,550' oder '€1,897 / month'"""
        if not price_str:
            return None
        # Entferne €, Leerzeichen und alles nach /
        price_clean = price_str.split('/')[0].replace('€', '').replace(',', '').strip()
        try:
            return float(price_clean)
        except:
            return None
    
    def parse_area(self, area_str):
        """Extrahiert Fläche aus String wie '1,142 m²'"""
        if not area_str:
            return None
        # Extrahiere Zahlen vor m²
        match = re.search(r'([\d,\.]+)\s*m²', area_str)
        if match:
            area_clean = match.group(1).replace(',', '')
            try:
                return float(area_clean)
            except:
                return None
        return None
    
    def extract_coordinates(self, item):
        """Extrahiert GPS-Koordinaten"""
        for section in item.findall('.//sections'):
            if section.find('type') is not None and section.find('type').text == 'MAP':
                location = section.find('location')
                if location is not None:
                    lat = location.find('lat')
                    lng = location.find('lng')
                    if lat is not None and lng is not None:
                        return float(lat.text), float(lng.text)
        return None, None
    
    def extract_address(self, item):
        """Extrahiert vollständige Adresse"""
        for section in item.findall('.//sections'):
            if section.find('type') is not None and section.find('type').text == 'MAP':
                addr1 = section.find('addressLine1')
                addr2 = section.find('addressLine2')
                return {
                    'street': addr1.text if addr1 is not None else None,
                    'full': addr2.text if addr2 is not None else None
                }
        return {'street': None, 'full': None}
    
    def extract_attributes(self, item):
        """Extrahiert alle Attribute aus den verschiedenen Sections"""
        attributes = {}
        
        # Top Attributes (Hauptmerkmale)
        for section in item.findall('.//sections'):
            section_type = section.find('type')
            if section_type is not None and section_type.text == 'TOP_ATTRIBUTES':
                for attr in section.findall('.//attributes'):
                    label = attr.find('label')
                    text = attr.find('text')
                    if label is not None and text is not None:
                        attributes[label.text] = text.text
        
        # Attribute Lists
        for section in item.findall('.//sections'):
            section_type = section.find('type')
            if section_type is not None and section_type.text == 'ATTRIBUTE_LIST':
                for attr in section.findall('.//attributes'):
                    label = attr.find('label')
                    text = attr.find('text')
                    attr_type = attr.find('type')
                    if label is not None:
                        if text is not None:
                            attributes[label.text] = text.text
                        elif attr_type is not None and attr_type.text == 'CHECK':
                            attributes[label.text] = 'Yes'
        
        return attributes
    
    def extract_description(self, item):
        """Extrahiert Beschreibungstexte"""
        descriptions = {}
        
        for section in item.findall('.//sections'):
            section_type = section.find('type')
            if section_type is not None and section_type.text == 'TEXT_AREA':
                title = section.find('title')
                text = section.find('text')
                if title is not None and text is not None:
                    descriptions[title.text] = text.text
        
        return descriptions
    
    def extract_agent_info(self, item):
        """Extrahiert Makler-Informationen"""
        for section in item.findall('.//sections'):
            if section.find('type') is not None and section.find('type').text == 'AGENTS_INFO':
                return {
                    'company': section.find('company').text if section.find('company') is not None else None,
                    'name': section.find('name').text if section.find('name') is not None else None,
                    'rating': section.find('.//rating/value').text if section.find('.//rating/value') is not None else None
                }
        return {'company': None, 'name': None, 'rating': None}
    
    def parse(self):
        """Hauptfunktion zum Parsen der XML-Datei"""
        print(f"Parsing XML-Datei: {self.xml_file}")
        tree = ET.parse(self.xml_file)
        root = tree.getroot()
        
        items = root.findall('.//item')
        print(f"Gefunden: {len(items)} Immobilienangebote")
        
        for idx, item in enumerate(items):
            try:
                # Basic Info
                property_id = item.find('.//header/id').text if item.find('.//header/id') is not None else None
                title_elem = item.find('.//sections[type="TITLE"]/title')
                title = title_elem.text if title_elem is not None else None
                
                # Koordinaten und Adresse
                lat, lng = self.extract_coordinates(item)
                address = self.extract_address(item)
                
                # Attribute extrahieren
                attributes = self.extract_attributes(item)
                
                # Preise und Flächen
                purchase_price = self.parse_price(attributes.get('Purchase:', attributes.get('Purchase price', '')))
                plot_area = self.parse_area(attributes.get('Plot area approx.:', attributes.get('Plot area', '')))
                price_per_sqm = self.parse_price(attributes.get('Price/m²:', ''))
                
                # Beschreibungen
                descriptions = self.extract_description(item)
                
                # Makler-Info
                agent = self.extract_agent_info(item)
                
                # Extrahiere Stadtteil aus Adresse
                district = None
                if address['full']:
                    # Format: "22397 Duvenstedt, Hamburg"
                    parts = address['full'].split(',')
                    if len(parts) > 0:
                        district_part = parts[0].strip()
                        # Entferne PLZ
                        district = re.sub(r'^\d+\s+', '', district_part)
                
                property_data = {
                    'id': property_id,
                    'title': title,
                    'purchase_price': purchase_price,
                    'plot_area': plot_area,
                    'price_per_sqm': price_per_sqm,
                    'street': address['street'],
                    'full_address': address['full'],
                    'district': district,
                    'latitude': lat,
                    'longitude': lng,
                    'commercialisation_type': attributes.get('Commercialisation type:', None),
                    'short_term_constructible': attributes.get('Short-term constructible:', 'No'),
                    'development': attributes.get('Development:', None),
                    'constructible_type': attributes.get('Constructible type:', None),
                    'recommended_use': attributes.get('Recommended use:', None),
                    'demolition': attributes.get('Demolition:', 'No'),
                    'free_from': attributes.get('Free from:', None),
                    'commission': attributes.get('Commission for the purchaser:', None),
                    'description': descriptions.get('Property description', None),
                    'location_desc': descriptions.get('Location', None),
                    'further_notes': descriptions.get('Further notes', None),
                    'agent_company': agent['company'],
                    'agent_name': agent['name'],
                    'agent_rating': agent['rating']
                }
                
                self.data.append(property_data)
                
                if (idx + 1) % 100 == 0:
                    print(f"Verarbeitet: {idx + 1} von {len(items)}")
                    
            except Exception as e:
                print(f"Fehler beim Verarbeiten von Item {idx}: {str(e)}")
                continue
        
        print(f"Erfolgreich geparst: {len(self.data)} Angebote")
        return self.data
    
    def to_dataframe(self):
        """Konvertiert die Daten in einen pandas DataFrame"""
        if not self.data:
            self.parse()
        return pd.DataFrame(self.data)
    
    def to_json(self, output_file):
        """Speichert die Daten als JSON"""
        if not self.data:
            self.parse()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"JSON gespeichert: {output_file}")
    
    def to_csv(self, output_file):
        """Speichert die Daten als CSV"""
        df = self.to_dataframe()
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"CSV gespeichert: {output_file}")

if __name__ == '__main__':
    # Parser initialisieren
    parser = GrundstueckParser('data.xml')
    
    # Daten parsen
    data = parser.parse()
    
    # Statistiken ausgeben
    df = parser.to_dataframe()
    print("\n=== DATEN STATISTIKEN ===")
    print(f"Anzahl Angebote: {len(df)}")
    print(f"Durchschnittspreis: €{df['purchase_price'].mean():,.0f}")
    print(f"Durchschnittliche Grundstücksgröße: {df['plot_area'].mean():.0f} m²")
    print(f"Durchschnittlicher Preis/m²: €{df['price_per_sqm'].mean():.0f}/m²")
    print(f"\nStadtteile mit den meisten Angeboten:")
    print(df['district'].value_counts().head(10))
    
    # Daten speichern
    parser.to_csv('grundstuecke_hamburg.csv')
    parser.to_json('grundstuecke_hamburg.json')
    
    print("\n✅ Daten erfolgreich verarbeitet!")
