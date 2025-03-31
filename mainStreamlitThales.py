import streamlit as st
import pandas as pd
import folium
from folium import plugins, DivIcon, CustomIcon
from haversine import haversine
from PIL import Image
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import os

@dataclass
class AircraftIcon:
    path: str
    size: Tuple[int, int]
    anchor: Optional[Tuple[int, int]] = None

class PilotRescueApp:
    def __init__(self):
        # Define color and icon configurations within the class
        self.VISUALIZATION_COLORS = {
            'IBM11A': {'marker': 'red', 'trajectory': 'red', 'line': 'red'},
            'IBM11B': {'marker': 'blue', 'trajectory': 'blue', 'line': 'blue'}
        }
        self.ICONS_DIRECTORY = "/Users/leslie/Home/Industry/Demos/ICONES"
        self.ICONS = {
            "F16": AircraftIcon("F16-1.png", (40, 20), (22, 94)),
            "KC135": AircraftIcon("KC135.png", (40, 20), (22, 94)),
            "KC136": AircraftIcon("KC135.png", (40, 20), (22, 94)),  # Uses same as KC135
            "KC137": AircraftIcon("KC137.png", (40, 20), (22, 94)),
            "C130J": AircraftIcon("C130J.png", (40, 20), (22, 94)),
            "E3F": AircraftIcon("E3F.png", (40, 20), (22, 94)),
            "RAFALE": AircraftIcon("RAFALE.png", (40, 20), (22, 94)),
            "TORGEE": AircraftIcon("TORGEE.png", (20, 20)),
            "TORITA": AircraftIcon("TORITA.png", (60, 15)),
            "C27J": AircraftIcon("C27.png", (40, 20)),
            "FREGATE": AircraftIcon("FregateAmie.png", (40, 25)),
            "DESTROYER": AircraftIcon("DestroyerEnnemi.png", (40, 30), (22, 94)),
            "AB212": AircraftIcon("AB212.png", (50, 25)),
            "CH47": AircraftIcon("HELICOFREGATE.png", (50, 25))
        }
        self.setup_page()
        self.setup_sidebar()
        self.initialize_state()
        self.mission_time_df = None  # Will store mission timing info

    def setup_page(self):
        st.set_page_config(
            page_title="Thales Raytheon System - Pilot Rescue Visualization",
            page_icon=":fighter_plane:",  # Military-themed icon
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Add some custom CSS for styling
        st.markdown("""
        <style>
        .main-title {
            font-size: 2.5rem;
            color: #2C3E50;
            text-align: center;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #34495E;
            text-align: center;
            margin-bottom: 20px;
        }
        .mission-overview {
            background-color: #f0f0f0;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="main-title">Thales Raytheon System</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Tactical Mission Visualization Platform</div>', unsafe_allow_html=True)

    def setup_sidebar(self):
        # Load and display logo
        image = Image.open("/Users/leslie/Home/Industry/Demos/ICONES/RAFALE.png")
        st.sidebar.image(image, width=250)

        st.sidebar.header("Mission Visualization Options")

        # Analytics Options with improved layout
        with st.sidebar.expander("Visualization Settings", expanded=True):
            self.visualization_options = {
                'pilot_ejection': st.checkbox('Pilot Ejection Position', value=False, key="pilot_ejection"),
                'airplane_trajectory': st.checkbox('Aircraft Trajectory', value=False, key="airplane_trajectory"),
                'gsar_missions': st.checkbox('Search & Rescue Missions', key="gsar_missions"),
                'air_refueling': st.checkbox('Air Refueling Missions', key="air_refueling"),
                'goca_missions': st.checkbox('GOCA Missions', value=False, key="goca_missions"),
                'airplanes': st.checkbox('Aircraft Positions', key="airplanes")
            }

        with st.sidebar.expander("Geospatial Configuration", expanded=True):
            self.geospatial_options = {
                'show_minimap': st.checkbox('Enable Mini Map', value=True, key="show_minimap_checkbox"),
                'zoom_level': st.slider('Zoom Level', min_value=1, max_value=20, value=6, key="zoom_level_slider"),
                'map_style': st.selectbox('Map Style', options=['Esri/WorldImagery', 'OpenStreetMap'], key="map_style_select")
            }

    def initialize_state(self):
      """Enhanced session state initialization"""
      # Data storage state variables
      if 'aircraft_data' not in st.session_state:
         st.session_state.aircraft_data = None
      if 'ato_data' not in st.session_state:
         st.session_state.ato_data = None
      if 'goca_gsar_data' not in st.session_state:
         st.session_state.goca_gsar_data = None
      
      # Map initialization state
      if 'map_initialized' not in st.session_state:
         st.session_state.map_initialized = False
      
      # Coordinates with more robust default handling
      st.session_state.setdefault("latitude", "38.179722222")
      st.session_state.setdefault("longitude", "13.1030555556")


    def load_data(self, filename, separator=";"):
      """
      Centralized data loading method with error handling
      
      Args:
         filename: Uploaded file object
         separator: CSV file separator (default semicolon)
      
      Returns:
         Loaded DataFrame or None
      """
      if filename is not None:
         try:
               df = pd.read_csv(filename, sep=separator)
               return df
         except Exception as e:
               st.error(f"Error loading file {filename.name}: {e}")
               return None
      return None



    def create_icon(self, aircraft_type: str) -> CustomIcon:
        """Create a custom icon for an aircraft type"""
        if aircraft_type not in self.ICONS:
            aircraft_type = "DEFAULT"  # Fallback to default icon
            
        icon_info = self.ICONS[aircraft_type]
        return CustomIcon(
            icon_image=os.path.join(self.ICONS_DIRECTORY, icon_info.path),
            icon_size=icon_info.size,
            icon_anchor=icon_info.anchor
        )

    def add_pilot_ejection(self, df: pd.DataFrame, map_obj: folium.Map):
        """Add pilot ejection markers to map for multiple callsigns"""
        target_callsigns = ['IBM11A', 'IBM11B']

        for callsign in target_callsigns:
            callsign_df = df[df['Callsign'] == callsign]
            
            if not callsign_df.empty:
                row = callsign_df.iloc[0]
                
                # Use the new color configuration
                color = self.VISUALIZATION_COLORS.get(callsign, {'marker': 'gray'})['marker']
                
                icon = folium.Icon(
                    prefix="fa", 
                    color=color, 
                    icon="arrow-down", 
                    angle=360
                )
                
                coords_ejection = [row['LAT'], row['LON']]
                popup_text = (f"Ejection time {row['TIME']} "
                              f"Callsign {callsign} - "
                              f"Pilote Ejecté LAT {row['LAT']} LON {row['LON']}")
                
                folium.Marker(
                    coords_ejection, 
                    icon=icon, 
                    popup=popup_text, 
                    tooltip=callsign
                ).add_to(map_obj)

    def add_gsar_missions(self, dfg: pd.DataFrame, map_obj: folium.Map):
        """Add GSAR mission visualization"""
        if 'msn_type' not in dfg.columns:
            return  # If msn_type doesn't exist, just return.
        for _, row in dfg[dfg['msn_type'] == "GSAR"].iterrows():
            if row['type'] == "DEPARTURE":
                icon = self.create_icon(row['aircraft_type'])
                coords = [row['latitude'], row['longitude']]
                
                popup_text = (f"Callsign {row['callsign']} Type {row['aircraft_type']} "
                              f"GSAR LAT {row['latitude']} LON {row['longitude']}")
                
                folium.Marker(coords, icon=icon, popup=popup_text).add_to(map_obj)
                
                # Add line to ejection point
                ejection_coords = (37.74805556, 11.9225)
                dist = round(haversine(coords, ejection_coords), 2)
                folium.PolyLine([coords, ejection_coords], 
                                color="purple", 
                                weight=1,
                                tooltip=f"Distance Mission GSAR {dist} kms").add_to(map_obj)

    def add_goca_gsar_missions(self, df: pd.DataFrame, map_obj: folium.Map):
      """
      Enhanced visualization of GOCA and GSAR missions with detailed timing information.
      Combines waypoint data with mission timing info and displays comprehensive flight details.
      """
      if 'msn_type' not in df.columns:
         return

      missions = df.groupby(['air_mission_id', 'msn_type'])
      for (mission_id, mission_type), mission_df in missions:
         mission_coords = []
         
         # Convert mission_id to string for comparison
         str_mission_id = str(mission_id)
         
         # Fetch timing info for this mission
         mission_time_info = self.mission_time_df[self.mission_time_df['mission_nbr'] == str_mission_id]
         if not mission_time_info.empty:
               timing = mission_time_info.iloc[0]
               
               # Parse all timing information
               departure_time = timing['departure_time']
               flight_duration = timing['flight duration to rescue place']
               arrival_rescue = timing['arrivale time on rescue area']
               return_time = timing['arrival time back from rescue']
               
               # Add rescue operation time (15 minutes)
               rescue_duration = "00:15:00"
               
               # Format timings for display
               formatted_timing = {
                  'departure': departure_time,
                  'flight_out': flight_duration,
                  'arrival_zone': arrival_rescue,
                  'rescue_op': rescue_duration,
                  'return': return_time
               }
         else:
               formatted_timing = {
                  'departure': 'N/A',
                  'flight_out': 'N/A',
                  'arrival_zone': 'N/A',
                  'rescue_op': 'N/A',
                  'return': 'N/A'
               }

         # Set visualization properties based on mission type
         mission_props = {
               'GOCA': {'line_color': 'blue', 'marker_color': 'blue', 'highlight': '#4a90e2', 'departure_color': 'red'},
               'GSAR': {'line_color': 'green', 'marker_color': 'green', 'highlight': '#45b17d'}
         }.get(mission_type, {'line_color': 'gray', 'marker_color': 'gray', 'highlight': '#808080', 'departure_color': 'gray'})

         # Sort waypoints by sequence
         mission_df = mission_df.sort_values('sequence')
         
         # Track segments for timing display
         segments = []
         prev_coords = None
         
         for idx, row in mission_df.iterrows():
               coords = [row['latitude'], row['longitude']]
               mission_coords.append(coords)
               
               if prev_coords:
                  segments.append((prev_coords, coords))
               prev_coords = coords

               # Create detailed popup content for each waypoint
               popup_content = f"""
                  <div style='font-family: Arial, sans-serif; font-size: 12px; min-width: 200px;'>
                     <h3 style='margin: 0 0 8px 0; color: {mission_props["line_color"]};'>{mission_type} - {row['type']}</h3>
                     <table style='border-collapse: collapse; width: 100%;'>
                           <tr>
                              <td><b>Mission:</b></td>
                              <td>{row['air_mission_id']}</td>
                           </tr>
                           <tr>
                              <td><b>Callsign:</b></td>
                              <td>{row['callsign']}</td>
                           </tr>
                           <tr>
                              <td><b>Aircraft:</b></td>
                              <td>{row['aircraft_type']}</td>
                           </tr>
                     """
               
               # Add timing information for DEPARTURE points
               if row['type'] == 'DEPARTURE':
                  if mission_type == 'GOCA':
                     popup_content += f"""
                              <tr><td colspan='2'><hr></td></tr>
                              <tr>
                                 <td><b>Départ:</b></td>
                                 <td style="color: {mission_props['departure_color']};">{formatted_timing['departure']}</td>
                              </tr>
                              <tr>
                                 <td><b>Durée vol aller:</b></td>
                                 <td>{formatted_timing['flight_out']}</td>
                              </tr>
                              <tr>
                                 <td><b>Arrivée zone:</b></td>
                                 <td>{formatted_timing['arrival_zone']}</td>
                              </tr>
                              <tr>
                                 <td><b>Durée sauvetage:</b></td>
                                 <td>{formatted_timing['rescue_op']}</td>
                              </tr>
                              <tr>
                                 <td><b>Retour base:</b></td>
                                 <td>{formatted_timing['return']}</td>
                              </tr>
                     """
                  else:
                     popup_content += f"""
                              <tr><td colspan='2'><hr></td></tr>
                              <tr>
                                 <td><b>Départ:</b></td>
                                 <td>{formatted_timing['departure']}</td>
                              </tr>
                              <tr>
                                 <td><b>Durée vol aller:</b></td>
                                 <td>{formatted_timing['flight_out']}</td>
                              </tr>
                              <tr>
                                 <td><b>Arrivée zone:</b></td>
                                 <td>{formatted_timing['arrival_zone']}</td>
                              </tr>
                              <tr>
                                 <td><b>Durée sauvetage:</b></td>
                                 <td>{formatted_timing['rescue_op']}</td>
                              </tr>
                              <tr>
                                 <td><b>Retour base:</b></td>
                                 <td>{formatted_timing['return']}</td>
                              </tr>
                     """
               
               popup_content += """
                     </table>
                  </div>
               """

               # Add waypoint markers with custom styling
               folium.Marker(
                  location=coords,
                  popup=folium.Popup(popup_content, max_width=300),
                  icon=DivIcon(
                     html=f"""
                           <div style="
                              font-size: 12pt;
                              font-family: Arial, sans-serif;
                              color: {mission_props['marker_color']};
                              text-shadow: 1px 1px 1px white;
                              font-weight: bold;
                           ">
                              {row['type']}
                           </div>
                     """
                  )
               ).add_to(map_obj)

               # Add aircraft icon for mission assets
               if pd.notna(row.get('aircraft_type', None)):
                  folium.Marker(
                     location=coords,
                     icon=self.create_icon(row['aircraft_type'])
                  ).add_to(map_obj)

               # Add highlighted circle for key points
               folium.CircleMarker(
                  location=coords,
                  radius=8,
                  color=mission_props['marker_color'],
                  fill=True,
                  fill_opacity=0.6,
                  weight=2,
                  popup=f"{mission_type} Waypoint"
               ).add_to(map_obj)

         # Draw mission paths with timing information
         if len(mission_coords) > 1:
               # Outbound leg
               midpoint = len(mission_coords) // 2
               outbound = mission_coords[:midpoint + 1]
               folium.PolyLine(
                  locations=outbound,
                  color=mission_props['line_color'],
                  weight=3,
                  opacity=0.8,
                  tooltip=f"Vol aller: {formatted_timing['flight_out']}",
                  dash_array='10'
               ).add_to(map_obj)

               # Return leg
               inbound = mission_coords[midpoint:]
               folium.PolyLine(
                  locations=inbound,
                  color=mission_props['line_color'],
                  weight=3,
                  opacity=0.8,
                  tooltip=f"Vol retour: {formatted_timing['return']}",
                  dash_array='5'
               ).add_to(map_obj)

               # Add time markers at key points
               if mission_type == "GSAR":
                  rescue_point = mission_coords[midpoint]
                  folium.Popup(
                     f"""
                     <div style='font-family: Arial, sans-serif;'>
                           <b>Point de sauvetage</b><br>
                           Arrivée: {formatted_timing['arrival_zone']}<br>
                           Durée opération: {formatted_timing['rescue_op']}
                     </div>
                     """,
                     parse_html=True
                  ).add_to(folium.CircleMarker(
                     location=rescue_point,
                     radius=12,
                     color=mission_props['highlight'],
                     fill=True,
                     fill_opacity=0.8
                  ).add_to(map_obj))

    def process_visualization(self, filename1, filename2, filename3, map_obj: folium.Map, lat, long) -> None:
        # Check if at least the first two files are provided
        if filename1 is None or filename2 is None:
            st.write('Please specify at least the first two data files to visualize the main map.')
            return

        try:
            # Read the first two files
            aircraft_df = pd.read_csv(filename1, sep=";")
            ato_df = pd.read_csv(filename2, sep=";")

            # Initialize mission metrics from the first two files
            total_aircraft = len(aircraft_df['Callsign'].unique())
            if 'msn_type' in ato_df.columns:
                total_missions = len(ato_df['msn_type'].unique())
            else:
                total_missions = 0
            critical_alerts = 3  # Placeholder
            fuel_remaining = aircraft_df['FUEL QUANTITY (KGs)'].sum()

            goca_gsar_df = None
            if filename3 is not None:
                goca_gsar_df = pd.read_csv(filename3, sep=",")
                if 'msn_type' in goca_gsar_df.columns:
                    total_missions += len(goca_gsar_df['msn_type'].unique())

            # Read mission time info CSV (final_mission_GSAR_GOCA.csv)
            # Make sure this file and columns match your actual data
            #self.mission_time_df = pd.read_csv("final_mission_GSAR_GOCA.csv", sep=",")
            self.mission_time_df = pd.read_csv("/Users/leslie/Home/Industry/Demos/file/final_mission_GSAR_OCA.csv", sep=";")
            self.mission_time_df['mission_nbr'] = self.mission_time_df['mission_nbr'].astype(str)

            # Display mission overview metrics
            with st.container():
                st.markdown('<div class="mission-overview">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Aircraft", total_aircraft)
                col2.metric("Total Missions", total_missions)
                col3.metric("Critical Alerts", critical_alerts)
                col4.metric("Fuel Remaining", f"{fuel_remaining:.0f} kg")
                st.markdown('</div>', unsafe_allow_html=True)

            st.write('Visualisation - Map is displayed with selected artefacts')

            # Add layers to the first map
            if self.visualization_options['pilot_ejection']:
                self.add_pilot_ejection(aircraft_df, map_obj)

            if self.visualization_options['airplane_trajectory']:
                self.add_trajectory_markers(aircraft_df, ato_df, map_obj)
                self.add_trajectory_line(aircraft_df, ato_df, map_obj)

            if self.visualization_options['gsar_missions']:
                self.add_gsar_missions(ato_df, map_obj)

            if self.visualization_options['air_refueling']:
                self.add_air_refueling(ato_df, map_obj)

            if self.visualization_options['airplanes']:
                self.add_aircraft_positions(aircraft_df, map_obj)

            # Display the PILOT EJECTION map (top)
            st.markdown("<h2 style='text-align: center;'>GEOSPATIAL MAP - PILOT EJECTION TIME - IBM11A - 23h06</h2>", 
                        unsafe_allow_html=True)
            st.components.v1.html(folium.Figure().add_child(map_obj).render(), height=500)

            # If the third file is present, display GOCA and GSAR map (bottom)
            if filename3 is not None and goca_gsar_df is not None:
                center = [float(lat), float(long)]
                map_obj_2 = folium.Map(
                    location=center,
                    tiles=self.geospatial_options['map_style'],
                    zoom_start=self.geospatial_options['zoom_level'],
                    control_scale=True
                )

                if self.geospatial_options['show_minimap']:
                    map_obj_2.add_child(plugins.MiniMap())

                mission_types_to_show = []
                if self.visualization_options['gsar_missions']:
                    mission_types_to_show.append("GSAR")
                if self.visualization_options['goca_missions']:
                    mission_types_to_show.append("GOCA")

                if mission_types_to_show and 'msn_type' in goca_gsar_df.columns:
                    filtered_df = goca_gsar_df[goca_gsar_df['msn_type'].isin(mission_types_to_show)]
                    self.add_goca_gsar_missions(filtered_df, map_obj_2)

                # Display the GOCA and GSAR missions map (bottom)
                st.markdown("<h2 style='text-align: center;'>GEOSPATIAL MAP - GOCA AND GSAR MISSIONS</h2>", 
                            unsafe_allow_html=True)
                st.components.v1.html(folium.Figure().add_child(map_obj_2).render(), height=500)

        except Exception as e:
            st.error(f"Error processing visualization: {str(e)}")
            
            
    def update_visualization_options(self):
      """
      Dynamic visualization update method
      Allows real-time changes to map without full regeneration
      """
      # Check if data is already loaded
      if not st.session_state.map_initialized:
         st.warning("Please generate initial visualization first.")
         return

      # Use stored latitude and longitude from session state
      lat = st.session_state.get("latitude", "38.179722222")
      long = st.session_state.get("longitude", "13.1030555556")

      # Recreate map with current settings
      center = [float(lat), float(long)]
      map_obj = folium.Map(
         location=center,
         tiles=self.geospatial_options['map_style'],
         zoom_start=self.geospatial_options['zoom_level'],
         control_scale=True
      )

      # Add mini-map if enabled
      if self.geospatial_options['show_minimap']:
         map_obj.add_child(plugins.MiniMap())

      # Reprocess visualization with existing data
      # Pass lat and long arguments
      self.process_visualization(
         filename1=st.session_state.aircraft_data, 
         filename2=st.session_state.ato_data, 
         filename3=st.session_state.goca_gsar_data, 
         map_obj=map_obj,
         lat=lat,
         long=long
      )
    

    def get_pilot_coordinates(self, aircraft_df: pd.DataFrame, ato_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Retrieve coordinates for IBM11A and IBM11B from both files
        """
        pilot_coordinates = {}
        if 'Callsign' not in aircraft_df.columns or 'MSN Type' not in aircraft_df.columns:
            return pilot_coordinates
        for callsign in ['IBM11A', 'IBM11B']:
            pilot_info = aircraft_df[aircraft_df['Callsign'] == callsign].iloc[0]
            msn_type = pilot_info['MSN Type']
            if 'msn_type' in ato_df.columns and 'callsign' in ato_df.columns:
                waypoints = ato_df[
                    (ato_df['msn_type'] == msn_type) & 
                    (ato_df['callsign'] == callsign)
                ].sort_values('sequence')
                pilot_coordinates[callsign] = waypoints
        return pilot_coordinates

    def add_trajectory_markers(self, aircraft_df: pd.DataFrame, ato_df: pd.DataFrame, map_obj: folium.Map) -> None:
        """Add trajectory waypoint markers to the map"""
        pilot_coordinates = self.get_pilot_coordinates(aircraft_df, ato_df)
        for callsign, waypoints in pilot_coordinates.items():
            color = self.VISUALIZATION_COLORS.get(callsign, {'trajectory': 'gray'})['trajectory']
            for _, point in waypoints.iterrows():
                coords = [point['latitude'], point['longitude']]
                name = point['type']
                folium.Marker(
                    location=coords,
                    popup=f"Callsign: {callsign}<br>Type: {name}<br>LAT: {point['latitude']}<br>LON: {point['longitude']}",
                    icon=DivIcon(html=f"""<div style="font-size: 14pt;font-family: courier new; color: {color}">{name}</div>""")
                ).add_to(map_obj)

                map_obj.add_child(folium.CircleMarker(
                    location=coords,
                    radius=15,
                    color=color,
                    stroke=False,
                    fill=True,
                    fill_opacity=0.6,
                    weight=1,
                    opacity=1
                ))

    def add_trajectory_line(self, aircraft_df: pd.DataFrame, ato_df: pd.DataFrame, map_obj: folium.Map) -> None:
        """Add trajectory line to the map"""
        pilot_coordinates = self.get_pilot_coordinates(aircraft_df, ato_df)
        for callsign, waypoints in pilot_coordinates.items():
            color = self.VISUALIZATION_COLORS.get(callsign, {'line': 'gray'})['line']
            coordinates = waypoints[['latitude', 'longitude']].values.tolist()

            if coordinates:
                coordinates.append(coordinates[0])

            folium.PolyLine(
                locations=coordinates,
                color=color,
                weight=2,
                tooltip=f"{callsign} Flight Path"
            ).add_to(map_obj)

    def add_air_refueling(self, dfg: pd.DataFrame, map_obj: folium.Map) -> None:
        """Add air refueling mission visualization"""
        if 'msn_type' not in dfg.columns:
            return
        seqNmoinsUn = 0
        indcolor = 3
        points = []
        list_colors = ['black', 'beige', 'lightblue', 'gray', 'blue', 'darkred', 
                       'lightgreen', 'purple', 'red', 'green', 'lightred', 'white', 
                       'darkblue', 'darkpurple', 'cadetblue', 'orange', 'pink', 
                       'lightgray', 'darkgreen']

        for _, row in dfg[dfg['msn_type'] == "AR"].iterrows():
            seqN = row['sequence']
            if seqN >= seqNmoinsUn:
                points.append([row['latitude'], row['longitude']])
                coords = [row['latitude'], row['longitude']]
                
                folium.Marker(
                    location=coords,
                    popup=f"Air Mission ID {row['air_mission_id']} LAT {row['latitude']} LON {row['longitude']}",
                    icon=DivIcon(html=f"""<div style="font-size: 14pt;font-family: courier new; color: black">{seqN}</div>""")
                ).add_to(map_obj)
                
                map_obj.add_child(folium.CircleMarker(location=coords, weight=1, radius=15))
                seqNmoinsUn = seqN

            if row['type'] == "DESTINATION":
                indcolor = (indcolor + 1) % len(list_colors)
                folium.PolyLine(
                    points,
                    color=list_colors[indcolor],
                    weight=2,
                    tooltip="From departure to arrival"
                ).add_to(map_obj)
                seqNmoinsUn = 0
                points = []

    def add_aircraft_positions(self, df: pd.DataFrame, map_obj: folium.Map) -> None:
        """Add aircraft position markers to the map"""
        for _, row in df.iterrows():
            if 'LON' in row and 'LAT' in row and row['LON'] != 0 and row['LAT'] != 0 and row['Callsign'] != "IBM11A":
                coords = [row['LAT'], row['LON']]
                icon = self.create_icon(row['AC TYPE'])
                
                folium.Marker(
                    location=coords,
                    popup=f"Callsign {row['Callsign']} Type {row['AC TYPE']} LAT {row['LAT']} LON {row['LON']}",
                    icon=icon
                ).add_to(map_obj)
                
                if row['AC TYPE'] == "FREGATE":
                    locations2 = coords
                    ejection_point = (37.74805556, 11.9225)
                    dist = round(haversine(locations2, ejection_point), 2)
                    folium.PolyLine(
                        locations=[locations2, ejection_point],
                        color="orange",
                        weight=4,
                        line_opacity=0.5,
                        tooltip=f"Distance Fregate support {dist} kms"
                    ).add_to(map_obj)

    def run(self):
      # Add a professional introduction
      st.markdown("""
      ### Tactical Mission Visualization Platform

      **Upload mission data files to begin visualization**
      """)

      # File upload with drag-and-drop
      col1, col2, col3 = st.columns(3)
      with col1:
         filename1 = st.file_uploader(
               'Upload Aircraft Positions', 
               type=['csv'], 
               help='Upload CSV file with aircraft position data'
         )

      with col2:
         filename2 = st.file_uploader(
               'Upload ATO Missions List', 
               type=['csv'],
               help='Upload CSV file with mission details'
         )

      with col3:
         filename3 = st.file_uploader(
               'Upload GOCA and GSAR Missions', 
               type=['csv'],
               help='Upload CSV file with GOCA and GSAR mission details'
         )

      # Coordinate inputs
      with st.container():
         col1, col2 = st.columns([1, 1])
         with col1:
               lat = st.text_input("Latitude Ejection Pilote", key="Latitude Ejection Pilote")
         with col2:
               long = st.text_input("Longitude Ejection Pilote", key="Longitude Ejection Pilote")

      # Data loading logic
      if filename1 and filename2:
         st.session_state.aircraft_data = filename1
         st.session_state.ato_data = filename2
         st.session_state.goca_gsar_data = filename3

      # Initialize Visualization Button
      if st.button('Initialize/Reset Visualization', type='primary'):
         st.session_state.map_initialized = True
         center = [float(lat), float(long)]
         map_obj = folium.Map(
               location=center,
               tiles=self.geospatial_options['map_style'],
               zoom_start=self.geospatial_options['zoom_level'],
               control_scale=True
         )

         if self.geospatial_options['show_minimap']:
               map_obj.add_child(plugins.MiniMap())

         self.process_visualization(
               filename1=filename1, 
               filename2=filename2, 
               filename3=filename3, 
               map_obj=map_obj, 
               lat=lat, 
               long=long
         )
            
      # Option to update visualization dynamically
      if st.sidebar.button('Update Visualization'):
         self.update_visualization_options()

if __name__ == "__main__":
    app = PilotRescueApp()
    app.run()
