#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import csv
from datetime import datetime
from bs4 import BeautifulSoup

def parse_meal_name_and_calories(meal_text):
    """Yemek adını ve kalorisini ayırır"""
    # Kalori bilgisini çıkar (örn: "- 200 KKAL")
    calorie_match = re.search(r'- (\d+) KKAL', meal_text)
    calories = calorie_match.group(1) + " KKAL" if calorie_match else ""
    
    # Yemek adını temizle (kalori kısmını çıkar)
    meal_name = re.sub(r'\s*- \d+ KKAL.*$', '', meal_text).strip()
    
    # Özel karakterleri düzelt
    meal_name = meal_name.replace('«', 'Ç').replace('–', 'Ğ').replace('˝', 'ı')
    meal_name = meal_name.replace('÷', 'Ö').replace('ı', 'İ').replace('«', 'Ç')
    
    # * işaretlerini süt ikonu ile değiştir
    meal_name = meal_name.replace('*', '🥛')
    
    # + işaretlerini buğday ikonu ile değiştir
    meal_name = meal_name.replace('+', '🌾')
    
    return meal_name, calories

def categorize_meal(meal_name):
    """Yemek tipini belirler"""
    meal_lower = meal_name.lower()
    
    # Çorba kontrolleri
    if 'çorba' in meal_lower or 'aşı' in meal_lower:
        return 'soup'
    
    # İçecek kontrolleri
    if any(drink in meal_lower for drink in ['ayran', 'soda', 'gazoz', 'su']):
        return 'drink'
    
    # Tatlı kontrolleri
    if any(dessert in meal_lower for dessert in ['muhallebi', 'dondurma', 'kek', 'revani', 'tatlı', 'şokola', 'prenses', 'hintpare', 'sitlaç']):
        return 'dessert'
    
    # Meyve kontrolü
    if 'meyve' in meal_lower:
        return 'extra'
    
    # Yoğurt kontrolü
    if 'yoğurt' in meal_lower:
        return 'extra'
    
    # Pilav, makarna gibi yan yemekler
    if any(side in meal_lower for side in ['pilav', 'makarna', 'bulgur', 'pirinç', 'erişte']):
        return 'extra'
    
    # Salata
    if 'salata' in meal_lower:
        return 'extra'
    
    # Geri kalan hepsi ana yemek
    return 'mainDish'

def parse_date(date_str):
    """Tarih string'ini parse eder"""
    # "28 Temmuz 2025 - Pazartesi" formatını parse et
    date_part = date_str.split(' - ')[0].strip()
    
    # Türkçe ay isimlerini rakama çevir
    months = {
        'Ocak': '01', 'Şubat': '02', 'Mart': '03', 'Nisan': '04',
        'Mayıs': '05', 'Haziran': '06', 'Temmuz': '07', 'Ağustos': '08',
        'Eylül': '09', 'Ekim': '10', 'Kasım': '11', 'Aralık': '12',
        'Austos': '08'  # HTML'deki yazım hatası
    }
    
    parts = date_part.split()
    if len(parts) >= 3:
        day = parts[0].zfill(2)
        month_name = parts[1]
        year = parts[2]
        
        month = months.get(month_name, '01')
        return f"{year}-{month}-{day}"
    
    return ""

def main():
    # HTML dosyasını oku
    with open('.venv/lib/<div class="yemek_list">.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # CSV verileri için liste
    csv_data = []
    
    # Her yemek listesi öğesini işle
    for item in soup.find_all('div', class_='yemek_list__item'):
        # Tarihi al
        date_span = item.find('span')
        if not date_span:
            continue
            
        date_text = date_span.get_text().strip()
        date_formatted = parse_date(date_text)
        
        if not date_formatted:
            continue
        
        print(f"İşleniyor: {date_text}")
        
        # Yemekleri al
        meal_items = item.find_all('li')
        current_menu_type = ""
        
        for li in meal_items:
            # h2 etiketi içindeki başlıkları kontrol et
            h2_tag = li.find('h2')
            if h2_tag:
                header_text = h2_tag.get_text().strip()
                current_menu_type = header_text
                
                if 'GÜNÜN MENÜSİ' in header_text:
                    print(f"  📋 GÜNÜN MENÜSİ:")
                elif 'VEJETARYEN MENİ' in header_text:
                    print(f"  🌱 VEJETARYEN MENÜ:")
                elif 'SALATA BÜFESİ' in header_text:
                    print(f"  🥗 SALATA BÜFESİ:")
                continue
            
            text = li.get_text().strip()
            
            # Boş satırları atla
            if not text:
                continue
            
            # Açıklama satırlarını atla
            if text.startswith('*') and 'İÇERDİĞİNİ' in text:
                continue
            if 'YEMEKHANE' in text and 'BANTTA' in text:
                continue
            
            # Normal yemek satırı ise işle
            if text and not text.startswith('<') and 'KKAL' in text:
                meal_name, calories = parse_meal_name_and_calories(text)
                meal_type = categorize_meal(meal_name)
                
                # Verileri CSV listesine ekle
                csv_data.append({
                    'date': date_formatted,
                    'name': meal_name,
                    'type': meal_type,
                    'calories': calories,
                    'menu_type': current_menu_type
                })
                
                # Menü tipine göre farklı simgeler ile yazdır
                if 'VEJETARYEN' in current_menu_type:
                    print(f"    🌱 {meal_name} ({meal_type}) - {calories} KKAL")
                elif 'SALATA' in current_menu_type:
                    print(f"    🥗 {meal_name} ({meal_type}) - {calories} KKAL")
                else:
                    print(f"    🍽️ {meal_name} ({meal_type}) - {calories} KKAL")
    
    # CSV dosyasını oluştur
    csv_filename = 'tusas_meals.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Ad', 'Tarih', 'YemekTür', 'Kalori', 'MenüTür']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in csv_data:
            # Sütun isimlerini yeniden eşleştir
            writer.writerow({
                'Ad': row['name'],
                'Tarih': row['date'],
                'YemekTür': row['type'],
                'Kalori': row['calories'],
                'MenüTür': row['menu_type']
            })
    
    print(f"\n✅ CSV dosyası oluşturuldu: {csv_filename}")
    print(f"Toplam {len(csv_data)} yemek işlendi.")

if __name__ == "__main__":
    main()
