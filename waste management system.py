import folium
import random
import numpy as np
import pandas as pd
from folium.plugins import MarkerCluster

# Define Hyderabad waste bin locations (sample data)
# These coordinates are within Hyderabad boundaries
hyderabad_bins = [
    {"id": 1, "lat": 17.3850, "lon": 78.4867, "fill_level": 85, "waste_type": "Organic", "area": "Banjara Hills"},
    {"id": 2, "lat": 17.4400, "lon": 78.4480, "fill_level": 70, "waste_type": "Recyclable", "area": "Secunderabad"},
    {"id": 3, "lat": 17.3616, "lon": 78.4747, "fill_level": 90, "waste_type": "General", "area": "Mehdipatnam"},
    {"id": 4, "lat": 17.4156, "lon": 78.4347, "fill_level": 65, "waste_type": "Hazardous", "area": "Ameerpet"},
    {"id": 5, "lat": 17.3855, "lon": 78.4570, "fill_level": 78, "waste_type": "Recyclable", "area": "Jubilee Hills"},
    {"id": 6, "lat": 17.4500, "lon": 78.5266, "fill_level": 92, "waste_type": "Organic", "area": "ECIL"},
    {"id": 7, "lat": 17.3840, "lon": 78.4563, "fill_level": 55, "waste_type": "General", "area": "Film Nagar"},
    {"id": 8, "lat": 17.4474, "lon": 78.5068, "fill_level": 83, "waste_type": "Recyclable", "area": "Uppal"},
    {"id": 9, "lat": 17.3687, "lon": 78.5247, "fill_level": 67, "waste_type": "Organic", "area": "LB Nagar"},
    {"id": 10, "lat": 17.5169, "lon": 78.3428, "fill_level": 88, "waste_type": "Hazardous", "area": "Kukatpally"}
]

# Convert the data to a DataFrame
df = pd.DataFrame(hyderabad_bins)

# Define vehicle capacity and other constraints
vehicle_capacity = 500  # kg
max_route_length = 8    # maximum number of bins per route

# Function to calculate distance between two points (Haversine formula)
def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# Create a distance matrix between all bins
n_bins = len(df)
distance_matrix = np.zeros((n_bins, n_bins))

for i in range(n_bins):
    for j in range(n_bins):
        if i != j:
            distance_matrix[i, j] = haversine_distance(
                df.iloc[i]['lat'], df.iloc[i]['lon'],
                df.iloc[j]['lat'], df.iloc[j]['lon']
            )

# Define a simple function to create waste estimates based on fill levels
df['waste_amount'] = df['fill_level'] * 5  # Assume 5kg per 1% fill level

# CSP-inspired optimization with backtracking (simplified for this example)
def optimize_route(start_idx, available_bins, current_load=0, current_route=None):
    if current_route is None:
        current_route = [start_idx]
    
    # Base case: if we've reached capacity or max route length
    if current_load >= vehicle_capacity or len(current_route) >= max_route_length:
        return current_route
    
    # Try each available bin
    best_route = current_route.copy()
    
    for next_bin in available_bins:
        if next_bin in current_route:
            continue
            
        # Calculate the additional load
        additional_load = df.iloc[next_bin]['waste_amount']
        
        # Skip if adding this bin would exceed capacity
        if current_load + additional_load > vehicle_capacity:
            continue
            
        # Try adding this bin to the route
        new_route = current_route + [next_bin]
        new_load = current_load + additional_load
        
        # Recursively optimize the rest of the route
        candidate_route = optimize_route(
            start_idx, 
            available_bins, 
            new_load, 
            new_route
        )
        
        # If this route is better (longer), keep it
        if len(candidate_route) > len(best_route):
            best_route = candidate_route
    
    return best_route

# Generate routes based on fill levels (prioritize bins with higher fill levels)
priority_bins = df.sort_values('fill_level', ascending=False).index.tolist()

# Create multiple routes as needed
routes = []
remaining_bins = set(range(n_bins))

while remaining_bins:
    if not remaining_bins:
        break
        
    # Start with the highest priority remaining bin
    for bin_idx in priority_bins:
        if bin_idx in remaining_bins:
            start_idx = bin_idx
            break
    else:
        break  # No more bins to process
    
    # Optimize route starting from this bin
    route = optimize_route(start_idx, list(remaining_bins))
    
    # Remove the bins in this route from remaining bins
    for bin_idx in route:
        if bin_idx in remaining_bins:
            remaining_bins.remove(bin_idx)
    
    routes.append(route)

# Create a map centered on Hyderabad
m = folium.Map(location=[17.3850, 78.4867], zoom_start=12, tiles="cartodbpositron")

# Add a title to the map
title_html = '''
<h3 align="center" style="font-size:16px"><b>Hyderabad Waste Collection Route Optimization</b></h3>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Color mapping for waste types
color_map = {
    "Organic": "green",
    "Recyclable": "blue",
    "Hazardous": "red",
    "General": "orange"
}

# Create a marker cluster
marker_cluster = MarkerCluster().add_to(m)

# Add bin markers to the map
for i, row in df.iterrows():
    color = color_map.get(row['waste_type'], "gray")
    popup_text = f"""
    <b>Bin #{row['id']}</b><br>
    Area: {row['area']}<br>
    Fill Level: {row['fill_level']}%<br>
    Waste Type: {row['waste_type']}<br>
    Estimated Amount: {row['waste_amount']} kg
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=color, icon="trash", prefix="fa"),
        tooltip=f"Bin #{row['id']} - {row['area']}"
    ).add_to(marker_cluster)

# Add routes to the map with different colors
route_colors = ["red", "blue", "green", "purple", "orange", "darkred", "darkblue", "darkgreen"]

for i, route in enumerate(routes):
    route_color = route_colors[i % len(route_colors)]
    
    # Get the coordinates for each bin in the route
    route_coords = [(df.iloc[idx]['lat'], df.iloc[idx]['lon']) for idx in route]
    
    # Create a route line
    folium.PolyLine(
        route_coords,
        color=route_color,
        weight=4,
        opacity=0.7,
        tooltip=f"Route {i+1}: {len(route)} bins"
    ).add_to(m)
    
    # Highlight the starting bin
    start_idx = route[0]
    folium.CircleMarker(
        location=[df.iloc[start_idx]['lat'], df.iloc[start_idx]['lon']],
        radius=10,
        color=route_color,
        fill=True,
        fill_color=route_color,
        fill_opacity=0.7,
        tooltip=f"Start of Route {i+1}"
    ).add_to(m)
    
    # Add route information
    total_waste = sum(df.iloc[idx]['waste_amount'] for idx in route)
    areas_covered = ", ".join(df.iloc[idx]['area'] for idx in route)
    
    route_html = f'''
    <div style="position: fixed; 
                bottom: {60 + i*80}px; left: 10px; width: 250px; 
                height: 70px; 
                border:2px solid {route_color}; 
                z-index:9999; 
                background-color:white;
                padding: 5px;
                border-radius: 5px;">
        <p><b>Route {i+1}</b><br>
        Bins: {len(route)}<br>
        Total Waste: {total_waste:.1f} kg<br>
        Areas: {areas_covered}</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(route_html))

# Add a legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; right: 10px; 
            border:2px solid grey; z-index:9999; 
            background-color:white;
            padding: 10px;
            border-radius: 5px;">
    <p><b>Waste Types</b><br>
    <i class="fa fa-trash fa-1x" style="color:green"></i> Organic<br>
    <i class="fa fa-trash fa-1x" style="color:blue"></i> Recyclable<br>
    <i class="fa fa-trash fa-1x" style="color:red"></i> Hazardous<br>
    <i class="fa fa-trash fa-1x" style="color:orange"></i> General</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save the map to an HTML file
output_file = "hyderabad_waste_collection_map.html"
m.save(output_file)

# Function to open the HTML file in a web browser
import webbrowser
import os

def open_map():
    filepath = os.path.abspath(output_file)
    webbrowser.open('file://' + filepath)

# Open the map in the default web browser
open_map()

print(f"Map saved as {output_file} and opened in browser")
print("Optimized Routes:")
for i, route in enumerate(routes):
    bin_ids = [df.iloc[idx]['id'] for idx in route]
    areas = [df.iloc[idx]['area'] for idx in route]
    total_waste = sum(df.iloc[idx]['waste_amount'] for idx in route)
    print(f"Route {i+1}: Bin IDs {bin_ids}, Areas: {areas}, Total Waste: {total_waste:.1f} kg")
