import streamlit as st
import streamlit.components.v1 as components
import csv
import os, types
import pandas as pd
import folium as folium
from PIL import Image

st.set_page_config(
    page_title="Thales Raytheon System and IBM",
    page_icon="/Users/leslie/Home/Industry/Demos/ICONES/RAFALE.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None,
)

#df = pd.read_csv("C:/Home/Industry/Demos/Images/Coordonnées_AircraftT.csv",sep=";") 
dfall = pd.read_csv("/Users/leslie/Home/Industry/Demos/file/ATO_air_mission_all_ATO_VG.csv",sep=";") 

image = Image.open("/Users/leslie/Home/Industry/Demos/ICONES/RAFALE.png")
st.sidebar.header("Use Case - Pilot Air Rescue")
st.sidebar.image(image) 

# Using object notation
add_selectbox = st.sidebar.selectbox(
    "Type de missions à visualiser",
    ('Ejected Pilot', 'AEW', 'TAL', 'GSUP', 'FLR', 'GOCA', 'AR', 'GSAR', 'MEDEV')
)

selection = add_selectbox

seqNmoinsUn=0
counter=0
indcolor=3
IDENT=""
points=[]
st.header("Missions List")  

for i in range(0,len(dfall)):
       msn = str(dfall.loc[i, "msn_type"])
       sign = str(dfall.loc[i, "callsign"])
       type = str(dfall.loc[i, "type"])
       seqN = dfall.iloc[i]['sequence']
       if msn == selection:
          if seqN >= seqNmoinsUn:
             points.append([dfall.iloc[i]['latitude'], dfall.iloc[i]['longitude']])
             airmission = dfall.iloc[i]['air_mission_id']
             coords = [dfall.iloc[i]['latitude'], dfall.iloc[i]['longitude']]
             #IDENT ="Callsign " + sign + " Mission " + msn + " Air Mission ID " + str(airmission) + " Type " + type + "LAT " + str(dfall.iloc[i]['latitude']) + " LON " + str(dfall.iloc[i]['longitude'])
             #st.write(IDENT)  
             seqNmoinsUn = seqN
             #print(points)
          if type == "DESTINATION":
             seqNmoinsUn = 0
             counter = counter + 1
             points = []
             IDENT="Callsign " + sign + " - Air Mission ID " + str(airmission) + " - Type " + type
             st.write(IDENT) 

if selection=="Ejected Pilot":
   counter=1

st.write("Number of " + str(selection) + " missions : " + str(counter))
#st.write(f"Column name is **{columnName}**")

if selection=='Ejected Pilot':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/Pilot.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read()
    
if selection=='AR':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/AR.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read()
    
if selection=='GSAR':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/GSAR.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read()
      
if selection=='ALL':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/my_map.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read() 

if selection=='AEW':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/AEW.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read() 
   
if selection=='GSUP':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/GSUP.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read() 

if selection=='TAL':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/TAL.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read() 

if selection=='FLR':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/FLR.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read() 

if selection=='AEW':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/AEW.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read() 

if selection=='GOCA':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/GCOA.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read()   

if selection=='MEDEV':
   HtmlFile = open("/Users/leslie/Home/Industry/Demos/image/MEDEV.html", 'r', encoding='utf-8')
   source_code = HtmlFile.read()  
    
st.header("Missions Type " + str(selection), divider=True)
st.components.v1.html(source_code,height = 600)
  