###  `README.md` for `Nato-AirCom` Project:

---

# Nato-AirCom: Air & Sea Rescue Mission Visualization

This project is a prototype for **mission planning and visualization** of search and rescue (SAR) operations, likely designed for air and sea military or civil rescue scenarios.

---

##  Features
- **Interactive Mission Visualization**  
  Display dynamic maps of missions involving aircraft, ships, and rescue teams.
  
- **Streamlit-based Web Application**  
  Visualize real-time or simulated missions through an intuitive Streamlit web interface.

- **Scenario Simulation**  
  Includes notebooks for simulating air pilot rescue scenarios.

- **Data Sources**  
  Uses CSV datasets representing aircraft coordinates, mission schedules, and SAR activities.

---

## 📂 Project Structure

```
Industry/Demos/
├── mainStreamlitThales.py   # Streamlit app main file
├── visualisationMissionsThales.py # Visualization logic
├── AirPilotRescueThales.ipynb # Rescue scenario notebook
├── AirPilotRescueThales2.ipynb # Alternative scenario notebook
├── Images/  # Assets for visualization
├── ICONES/  # Icons used in the maps
├── requirements.txt  # Required Python packages
```

---

##  Installation

1. Clone the repository
   ```bash
   git clone https://github.com/lesliesam96/Nato-AirCom.git
   cd Nato-AirCom/Industry/Demos
   ```

2. Install dependencies  
   *(it's highly recommended to create a virtual environment)*
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Streamlit App
   ```bash
   streamlit run mainStreamlitThales.py
   ```

---

##  Demo Video  
👉 [Click here to watch the demo](https://youtu.be/nL7CUJn0pLM)

---

##  Technologies
- Python
- Streamlit
- Pandas, Matplotlib
- Custom scenario simulation using Jupyter Notebooks
- CSV, image, and geospatial data processing

---
