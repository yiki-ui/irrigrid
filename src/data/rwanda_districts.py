#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rwanda Administrative Divisions - Districts Level
Complete geographic data for all 30 districts
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class District:
    """District geographic data"""
    name: str
    province: str
    latitude: float
    longitude: float
    altitude: float  # meters above sea level
    area_km2: float
    population: int
    sectors: List[str]
    climate_zone: str
    avg_rainfall_mm: float
    avg_temp_c: float
    soil_types: List[str]


# Rwanda's 30 Districts with complete geographic data
RWANDA_DISTRICTS = {
    # KIGALI CITY (3 Districts)
    "Gasabo": District(
        name="Gasabo",
        province="Kigali City",
        latitude=-1.9536,
        longitude=30.0606,
        altitude=1567,
        area_km2=430.3,
        population=530907,
        sectors=["Bumbogo", "Gatsata", "Jali", "Gikomero", "Gisozi", "Jabana", "Kacyiru", 
                "Kimihurura", "Kimironko", "Kinyinya", "Ndera", "Nduba", "Remera", "Rusororo", "Rutunga"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1100,
        avg_temp_c=19.5,
        soil_types=["Clay", "Loam", "Sandy Loam"]
    ),
    
    "Kicukiro": District(
        name="Kicukiro",
        province="Kigali City",
        latitude=-1.9667,
        longitude=30.1000,
        altitude=1450,
        area_km2=166.7,
        population=318061,
        sectors=["Gahanga", "Gatenga", "Gikondo", "Kagarama", "Kanombe", "Kicukiro", 
                "Kigarama", "Masaka", "Niboye", "Nyarugunga"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1050,
        avg_temp_c=20.0,
        soil_types=["Clay", "Loam"]
    ),
    
    "Nyarugenge": District(
        name="Nyarugenge",
        province="Kigali City",
        latitude=-1.9500,
        longitude=30.0588,
        altitude=1497,
        area_km2=134.0,
        population=284561,
        sectors=["Gitega", "Kanyinya", "Kigali", "Kimisagara", "Mageragere", "Muhima", 
                "Nyakabanda", "Nyamirambo", "Nyarugenge", "Rwezamenyo"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1000,
        avg_temp_c=20.5,
        soil_types=["Clay", "Loam"]
    ),
    
    # SOUTHERN PROVINCE (8 Districts)
    "Gisagara": District(
        name="Gisagara",
        province="Southern Province",
        latitude=-2.5833,
        longitude=29.8333,
        altitude=1650,
        area_km2=671.6,
        population=289532,
        sectors=["Gikonko", "Gishubi", "Kansi", "Kibilizi", "Kigembe", "Mamba", 
                "Muganza", "Mugombwa", "Mukindo", "Musha", "Ndora", "Nyanza", "Save"],
        climate_zone="Tropical Highland",
        avg_rainfall_mm=1200,
        avg_temp_c=18.5,
        soil_types=["Clay", "Sandy Clay", "Loam"]
    ),
    
    "Huye": District(
        name="Huye",
        province="Southern Province",
        latitude=-2.5969,
        longitude=29.7389,
        altitude=1768,
        area_km2=581.6,
        population=381900,
        sectors=["Gishamvu", "Karama", "Kigoma", "Kinazi", "Maraba", "Mbazi", 
                "Mukura", "Ngoma", "Ruhashya", "Rusatira", "Rwaniro", "Simbi", "Tumba", "Huye"],
        climate_zone="Tropical Highland",
        avg_rainfall_mm=1300,
        avg_temp_c=17.5,
        soil_types=["Clay", "Loam", "Sandy Loam"]
    ),
    
    "Kamonyi": District(
        name="Kamonyi",
        province="Southern Province",
        latitude=-2.0167,
        longitude=29.8833,
        altitude=1700,
        area_km2=655.5,
        population=340501,
        sectors=["Gacurabwenge", "Karama", "Kayenzi", "Kayumbu", "Mugina", "Musambira", 
                "Ngamba", "Nyamiyaga", "Nyarubaka", "Rukoma", "Rugarika", "Runda"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1150,
        avg_temp_c=19.0,
        soil_types=["Clay", "Loam"]
    ),
    
    "Muhanga": District(
        name="Muhanga",
        province="Southern Province",
        latitude=-2.0833,
        longitude=29.7500,
        altitude=1817,
        area_km2=637.7,
        population=323683,
        sectors=["Cyeza", "Kabacuzi", "Kibangu", "Kiyumba", "Muhanga", "Mushishiro", 
                "Nyabinoni", "Nyamabuye", "Nyarusange", "Rongi", "Rugendabari", "Shyogwe"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1250,
        avg_temp_c=18.0,
        soil_types=["Clay", "Sandy Clay", "Loam"]
    ),
    
    "Nyamagabe": District(
        name="Nyamagabe",
        province="Southern Province",
        latitude=-2.4833,
        longitude=29.4167,
        altitude=2100,
        area_km2=1181.0,
        population=335771,
        sectors=["Buruhukiro", "Cyanika", "Gasaka", "Gatare", "Kaduha", "Kamegeri", 
                "Kibirizi", "Kibumbwe", "Kitabi", "Mbazi", "Mugano", "Musange", 
                "Musebeya", "Mushubi", "Nkomane", "Tare", "Uwinkingi"],
        climate_zone="Afro-Alpine",
        avg_rainfall_mm=1400,
        avg_temp_c=15.5,
        soil_types=["Volcanic", "Clay", "Loam"]
    ),
    
    "Nyanza": District(
        name="Nyanza",
        province="Southern Province",
        latitude=-2.3500,
        longitude=29.7500,
        altitude=1707,
        area_km2=672.4,
        population=323719,
        sectors=["Busasamana", "Busoro", "Cyabakamyi", "Kibirizi", "Mukingo", "Muyira", 
                "Ntyazo", "Nyagisozi", "Rwabicuma", "Mukingo"],
        climate_zone="Tropical Highland",
        avg_rainfall_mm=1200,
        avg_temp_c=18.5,
        soil_types=["Clay", "Loam"]
    ),
    
    "Nyaruguru": District(
        name="Nyaruguru",
        province="Southern Province",
        latitude=-2.6167,
        longitude=29.3667,
        altitude=2200,
        area_km2=1041.0,
        population=317895,
        sectors=["Cyahinda", "Kibeho", "Kivu", "Mata", "Muganza", "Munini", 
                "Ngera", "Ngoma", "Nyabimata", "Nyagisozi", "Ruheru", "Ruramba", 
                "Rusenge", "Rwabicuma"],
        climate_zone="Afro-Alpine",
        avg_rainfall_mm=1500,
        avg_temp_c=14.5,
        soil_types=["Volcanic", "Clay", "Peat"]
    ),
    
    "Ruhango": District(
        name="Ruhango",
        province="Southern Province",
        latitude=-2.2333,
        longitude=29.7833,
        altitude=1650,
        area_km2=629.3,
        population=277425,
        sectors=["Bweramana", "Byimana", "Kabagari", "Kinazi", "Kinihira", "Mbuye", 
                "Mwendo", "Ntongwe", "Ruhango"],
        climate_zone="Tropical Highland",
        avg_rainfall_mm=1150,
        avg_temp_c=19.0,
        soil_types=["Clay", "Loam", "Sandy Loam"]
    ),
    
    # WESTERN PROVINCE (7 Districts)
    "Karongi": District(
        name="Karongi",
        province="Western Province",
        latitude=-2.0000,
        longitude=29.3833,
        altitude=1650,
        area_km2=1012.0,
        population=333808,
        sectors=["Bwishyura", "Gashari", "Gishyita", "Gisovu", "Gitesi", "Mubuga", 
                "Murambi", "Murundi", "Mutuntu", "Rubengera", "Rugabano", "Ruganda", "Rwankuba"],
        climate_zone="Tropical",
        avg_rainfall_mm=1300,
        avg_temp_c=20.0,
        soil_types=["Clay", "Loam", "Sandy"]
    ),
    
    "Ngororero": District(
        name="Ngororero",
        province="Western Province",
        latitude=-1.8167,
        longitude=29.5500,
        altitude=1900,
        area_km2=674.0,
        population=317395,
        sectors=["Bwira", "Gatumba", "Hindiro", "Kabaya", "Kageyo", "Kavumu", 
                "Matyazo", "Muhanda", "Muhororo", "Ndaro", "Ngororero", "Nyange", "Sovu"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1400,
        avg_temp_c=17.5,
        soil_types=["Clay", "Volcanic", "Loam"]
    ),
    
    "Nyabihu": District(
        name="Nyabihu",
        province="Western Province",
        latitude=-1.6500,
        longitude=29.5167,
        altitude=2100,
        area_km2=534.0,
        population=288359,
        sectors=["Bigogwe", "Jenda", "Jomba", "Kabatwa", "Karago", "Kintobo", 
                "Mukamira", "Muringa", "Rambura", "Rugera", "Rurembo", "Shyira"],
        climate_zone="Afro-Alpine",
        avg_rainfall_mm=1600,
        avg_temp_c=15.0,
        soil_types=["Volcanic", "Clay", "Peat"]
    ),
    
    "Nyamasheke": District(
        name="Nyamasheke",
        province="Western Province",
        latitude=-2.3167,
        longitude=29.1000,
        altitude=1800,
        area_km2=1412.0,
        population=334893,
        sectors=["Bushekeri", "Bushenge", "Cyato", "Gihombo", "Kagano", "Kanjongo", 
                "Karambi", "Karengera", "Kirimbi", "Macuba", "Mahembe", "Nyabitekeri", 
                "Nkanka", "Rangiro", "Ruharambuga", "Shangi", "Tétéro"],
        climate_zone="Tropical Highland",
        avg_rainfall_mm=1500,
        avg_temp_c=17.0,
        soil_types=["Volcanic", "Clay", "Loam"]
    ),
    
    "Rubavu": District(
        name="Rubavu",
        province="Western Province",
        latitude=-1.6833,
        longitude=29.2667,
        altitude=1550,
        area_km2=388.0,
        population=407923,
        sectors=["Bugeshi", "Busasamana", "Cyanzarwe", "Gisenyi", "Kanama", "Kanzenze", 
                "Mudende", "Nyakiriba", "Nyamyumba", "Nyundo", "Rubavu", "Rugerero"],
        climate_zone="Tropical",
        avg_rainfall_mm=1200,
        avg_temp_c=19.5,
        soil_types=["Volcanic", "Sandy", "Loam"]
    ),
    
    "Rusizi": District(
        name="Rusizi",
        province="Western Province",
        latitude=-2.4833,
        longitude=28.9000,
        altitude=950,
        area_km2=1125.0,
        population=317895,
        sectors=["Bugarama", "Butare", "Bweyeye", "Gashonga", "Giheke", "Gihundwe", 
                "Gitambi", "Kamembe", "Muganza", "Mururu", "Nkanka", "Nkombo", 
                "Nkungu", "Nyakabuye", "Nyakarenzo", "Nzahaha", "Rwimbogo"],
        climate_zone="Tropical Lowland",
        avg_rainfall_mm=1100,
        avg_temp_c=23.0,
        soil_types=["Alluvial", "Clay", "Sandy"]
    ),
    
    "Rutsiro": District(
        name="Rutsiro",
        province="Western Province",
        latitude=-1.9833,
        longitude=29.3500,
        altitude=1850,
        area_km2=1149.0,
        population=317895,
        sectors=["Boneza", "Gihango", "Kigeyo", "Kivumu", "Manihira", "Mukura", 
                "Murunda", "Musasa", "Mushonyi", "Mushubati", "Nyabirasi", "Ruhango", "Rusebeya"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1350,
        avg_temp_c=18.0,
        soil_types=["Clay", "Loam", "Volcanic"]
    ),
    
    # NORTHERN PROVINCE (5 Districts)
    "Burera": District(
        name="Burera",
        province="Northern Province",
        latitude=-1.4833,
        longitude=29.8833,
        altitude=2000,
        area_km2=1043.0,
        population=338659,
        sectors=["Bungwe", "Butaro", "Cyanika", "Cyeru", "Gahunga", "Gatebe", 
                "Gitovu", "Kagogo", "Kinoni", "Kinyababa", "Kivuye", "Nemba", 
                "Rugarama", "Rugendabari", "Ruhunde", "Rusarabuye", "Rwerere"],
        climate_zone="Afro-Alpine",
        avg_rainfall_mm=1400,
        avg_temp_c=15.5,
        soil_types=["Volcanic", "Clay", "Peat"]
    ),
    
    "Gakenke": District(
        name="Gakenke",
        province="Northern Province",
        latitude=-1.6833,
        longitude=29.7833,
        altitude=2100,
        area_km2=704.0,
        population=338586,
        sectors=["Busengo", "Coko", "Cyabingo", "Gakenke", "Gashenyi", "Mugunga", 
                "Janja", "Kamubuga", "Karambo", "Kivuruga", "Mataba", "Minazi", 
                "Muhondo", "Muyongwe", "Muzo", "Nemba", "Ruli", "Rushashi", "Rusasa"],
        climate_zone="Afro-Alpine",
        avg_rainfall_mm=1500,
        avg_temp_c=14.5,
        soil_types=["Volcanic", "Clay", "Loam"]
    ),
    
    "Gicumbi": District(
        name="Gicumbi",
        province="Northern Province",
        latitude=-1.5833,
        longitude=30.0667,
        altitude=1850,
        area_km2=846.0,
        population=476853,
        sectors=["Bukure", "Bwisige", "Byumba", "Cyumba", "Giti", "Kageyo", 
                "Kaniga", "Manyagiro", "Miyove", "Mukarange", "Muko", "Mutete", 
                "Nyamiyaga", "Nyankenke", "Rubaya", "Rukomo", "Rushaki", "Rutare", 
                "Ruvune", "Rwamiko", "Shangasha"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1300,
        avg_temp_c=17.0,
        soil_types=["Clay", "Loam", "Volcanic"]
    ),
    
    "Musanze": District(
        name="Musanze",
        province="Northern Province",
        latitude=-1.5000,
        longitude=29.6333,
        altitude=1850,
        area_km2=530.0,
        population=368267,
        sectors=["Busogo", "Cyuve", "Gacaca", "Gashaki", "Gataraga", "Kimonyi", 
                "Kinigi", "Muhoza", "Muko", "Musanze", "Nkotsi", "Nyange", 
                "Remera", "Rwaza", "Shingiro"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1450,
        avg_temp_c=16.0,
        soil_types=["Volcanic", "Clay", "Loam"]
    ),
    
    "Rulindo": District(
        name="Rulindo",
        province="Northern Province",
        latitude=-1.7667,
        longitude=30.0667,
        altitude=1800,
        area_km2=567.0,
        population=287681,
        sectors=["Base", "Burega", "Bushoki", "Buyoga", "Cyinzuzi", "Cyungo", 
                "Kinihira", "Kisaro", "Masoro", "Mbogo", "Murambi", "Ngoma", 
                "Ntarabana", "Rukozo", "Rusiga", "Shyorongi", "Tumba"],
        climate_zone="Temperate Highland",
        avg_rainfall_mm=1350,
        avg_temp_c=17.5,
        soil_types=["Clay", "Loam", "Volcanic"]
    ),
    
    # EASTERN PROVINCE (7 Districts)
    "Bugesera": District(
        name="Bugesera",
        province="Eastern Province",
        latitude=-2.2167,
        longitude=30.1667,
        altitude=1350,
        area_km2=1314.0,
        population=363339,
        sectors=["Gashora", "Juru", "Kamabuye", "Mareba", "Mayange", "Musenyi", 
                "Mwogo", "Ngeruka", "Ntarama", "Nyamata", "Nyarugenge", "Rilima", 
                "Ruhuha", "Rweru", "Shyara"],
        climate_zone="Tropical Savanna",
        avg_rainfall_mm=900,
        avg_temp_c=21.5,
        soil_types=["Sandy", "Clay", "Loam"]
    ),
    
    "Gatsibo": District(
        name="Gatsibo",
        province="Eastern Province",
        latitude=-1.6167,
        longitude=30.4167,
        altitude=1450,
        area_km2=1582.0,
        population=433020,
        sectors=["Gasange", "Gatsibo", "Gitoki", "Kabarore", "Kageyo", "Kiramuruzi", 
                "Kiziguro", "Muhura", "Murambi", "Ngarama", "Nyagihanga", "Remera", "Rugarama", "Rwimbogo"],
        climate_zone="Tropical Savanna",
        avg_rainfall_mm=1000,
        avg_temp_c=20.5,
        soil_types=["Sandy Loam", "Clay", "Laterite"]
    ),
    
    "Kayonza": District(
        name="Kayonza",
        province="Eastern Province",
        latitude=-1.8833,
        longitude=30.4167,
        altitude=1450,
        area_km2=1703.0,
        population=344157,
        sectors=["Gahini", "Kabare", "Kabarondo", "Mukarange", "Murama", "Murundi", 
                "Mwiri", "Ndego", "Nyamirama", "Rukara", "Ruramira", "Rwinkwavu"],
        climate_zone="Tropical Savanna",
        avg_rainfall_mm=1050,
        avg_temp_c=20.0,
        soil_types=["Sandy Loam", "Clay", "Laterite"]
    ),
    
    "Kirehe": District(
        name="Kirehe",
        province="Eastern Province",
        latitude=-2.2167,
        longitude=30.7167,
        altitude=1350,
        area_km2=1206.0,
        population=339467,
        sectors=["Gahara", "Gatore", "Kigarama", "Kigina", "Kirehe", "Mahama", 
                "Mpanga", "Musaza", "Mushikiri", "Nasho", "Nyamugari", "Nyarubuye"],
        climate_zone="Tropical Savanna",
        avg_rainfall_mm=850,
        avg_temp_c=22.0,
        soil_types=["Sandy", "Clay", "Laterite"]
    ),
    
    "Ngoma": District(
        name="Ngoma",
        province="Eastern Province",
        latitude=-2.1833,
        longitude=30.5000,
        altitude=1400,
        area_km2=850.0,
        population=334001,
        sectors=["Gashanda", "Jarama", "Karembo", "Kazo", "Kibungo", "Mugesera", 
                "Murama", "Mutenderi", "Remera", "Rukira", "Rukumberi", "Rurenge", "Sake", "Zaza"],
        climate_zone="Tropical Savanna",
        avg_rainfall_mm=950,
        avg_temp_c=21.0,
        soil_types=["Sandy Loam", "Clay", "Laterite"]
    ),
    
    "Nyagatare": District(
        name="Nyagatare",
        province="Eastern Province",
        latitude=-1.3000,
        longitude=30.3333,
        altitude=1450,
        area_km2=1741.0,
        population=466944,
        sectors=["Gatunda", "Karama", "Karangazi", "Katabagemu", "Kiyombe", "Matimba", 
                "Mimuri", "Mukama", "Musheli", "Nyagatare", "Rukomo", "Rwempasha", 
                "Rwimiyaga", "Tabagwe"],
        climate_zone="Tropical Savanna",
        avg_rainfall_mm=950,
        avg_temp_c=21.5,
        soil_types=["Sandy", "Clay", "Laterite"]
    ),
    
    "Rwamagana": District(
        name="Rwamagana",
        province="Eastern Province",
        latitude=-1.9500,
        longitude=30.4333,
        altitude=1500,
        area_km2=714.0,
        population=313888,
        sectors=["Fumbwe", "Gahengeri", "Gishari", "Karenge", "Kigabiro", "Muhazi", 
                "Munyaga", "Munyiginya", "Musha", "Muyumbu", "Mwulire", "Nyakaliro", 
                "Nzige", "Rubona"],
        climate_zone="Tropical Savanna",
        avg_rainfall_mm=1000,
        avg_temp_c=20.5,
        soil_types=["Sandy Loam", "Clay", "Laterite"]
    ),
}


def get_district(name: str) -> Optional[District]:
    """Get district by name"""
    return RWANDA_DISTRICTS.get(name)


def get_districts_by_province(province: str) -> List[District]:
    """Get all districts in a province"""
    return [d for d in RWANDA_DISTRICTS.values() if d.province == province]


def get_all_provinces() -> List[str]:
    """Get list of all provinces"""
    return list(set(d.province for d in RWANDA_DISTRICTS.values()))


def get_all_district_names() -> List[str]:
    """Get list of all district names"""
    return list(RWANDA_DISTRICTS.keys())
