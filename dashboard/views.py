import string
from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Data
import folium
from folium import plugins
import math
import pandas as pd
import matplotlib.cm
import matplotlib as plt
from folium.plugins import HeatMap
from numpy import random
from folium import plugins, raster_layers

# Create your views here.
def register_request(request):
  if request.method == "POST":
    form = NewUserForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      messages.success(request, "Registration successful.")
      return redirect("dashboard-index")
    messages.error(request, "Unsucessful registration. Invalid information.")
  form = NewUserForm()
  return render (request=request, template_name="dashboard/register.html", context={"register_form":form})

def login_request(request):
  if request.method == "POST":
    form =AuthenticationForm(request, data=request.POST)
    if form.is_valid():
      username = form.cleaned_data.get('username')
      password = form.cleaned_data.get('password')
      user = authenticate(username=username, password=password)
      if user is not None:
        login(request, user)
        messages.info(request, f"You are now logged in as {username}.")
        return redirect("dashboard-index")
      else:
        messages.error(request,"Invalid username or password.")
    else:
      messages.error(request,"Invalid username or password.")
  form = AuthenticationForm()
  return render (request=request, template_name="dashboard/login.html", context={"login_form":form})

def logout_request(request):
  logout(request)
  messages.info(request, "You have successfully logged out.")
  return redirect("dashboard-index")

def getDistanceFromLatLonInKm(lat1,lon1,lat2,lon2):
  R = 6371 #Radius of the earth in km
  dLat = deg2rad(lat2-lat1) #deg2rad below
  dLon = deg2rad(lon2-lon1)
  a = (
    math.sin(dLat/2) * math.sin(dLat/2) +
    math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * 
    math.sin(dLon/2) * math.sin(dLon/2)
    )
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  d = R * c #Distance in km
  return d

def deg2rad(deg):
  return deg * (math.pi/180)

def geo_json(lat, lon, step, value):
    cmap = matplotlib.cm.RdBu
    return {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {
            'color': plt.colors.to_hex(cmap(value)),
            'weight': 1,
            'fillColor': plt.colors.to_hex(cmap(value)),
            'fillOpacity': 0.4,
          },
          "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [lon, lat],
                [lon, lat + step],
                [lon + step, lat + step],
                [lon + step, lat],
                [lon, lat],
              ]]}}]}

def get_closest_cities(coordinates, city_data):
  pointLatitude = coordinates[0]
  pointLongitude = coordinates[1]

  closest_cities_distances = {}

  for _, xi in city_data.iterrows():
    distance = getDistanceFromLatLonInKm(pointLatitude, pointLongitude, xi["lat"], xi["lon"])
    closest_cities_distances[xi['name']] = distance
  
  top_3 = sorted(closest_cities_distances, key=closest_cities_distances.get, reverse=False)[:3]
  return top_3, closest_cities_distances

def get_powerline_distance(coordinates, powerline_data):
  pointLatitude = coordinates[0]
  pointLongitude = coordinates[1]

  closest_powerline = {}

  for _, xi in powerline_data.iterrows():
    distance = getDistanceFromLatLonInKm(pointLatitude, pointLongitude, xi["latitude"], xi["longitude"])
    closest_powerline[xi['Legend']] = distance
  
  top_1 = sorted(closest_powerline, key=closest_powerline.get, reverse=False)[:1]
  return top_1, closest_powerline

def get_ssr(coordinates, morocco_data):
  pointLatitude = coordinates[0]
  pointLongitude = coordinates[1]

  closestLat = min(morocco_data["latitude"], key=lambda x:abs(x-pointLatitude))
  closestLong = min(morocco_data["longitude"], key=lambda x:abs(x-pointLongitude))

  filtered_df  = morocco_data.query("longitude == @closestLong and latitude == @closestLat")
  return filtered_df.iloc[0]["ssr"]

def get_location_rating(coordinates, morocco_data):
  label_to_bins = {1:190, 2:170, 3:150, 4:130, 5:110, 6:90, 7:70, 8:50, 9:30, 10:10}

  pointLatitude = coordinates[0]
  pointLongitude = coordinates[1]

  closestLat = min(morocco_data["latitude"], key=lambda x:abs(x-pointLatitude))
  closestLong = min(morocco_data["longitude"], key=lambda x:abs(x-pointLongitude))

  filtered_df  = morocco_data.query("longitude == @closestLong and latitude == @closestLat")

  return list(label_to_bins.keys())[list(label_to_bins.values()).index(filtered_df.iloc[0]["bins"])]

def index(request):
    
    # initialising the map (default location 19, -12)
    map = folium.Map(location=[19, -12], 
                      zoom_start=2,
                      control_scale=True)
    
    '''
    map1 = raster_layers.TileLayer(tiles='CartoDB Dark_Matter').add_to(map)
    #map2 = raster_layers.TileLayer(tiles='CartoDB Positron').add_to(map)
    #map3 = raster_layers.TileLayer(tiles='Stamen Terrain').add_to(map)
    #map4 = raster_layers.TileLayer(tiles='Stamen Watercolor').add_to(map)
    folium.LayerControl().add_to(map)
    '''

    # getting location data for heatmap
    data = Data.objects.all()
    data_list = Data.objects.values_list('latitude', 'longitude', 'solar_radiation')
    # adding heatmap function 
    plugins.HeatMap(data_list).add_to(map)
    
    # adding geocoder plugin (location search function)
    plugins.Geocoder(collapsed=True, add_marker=False, position='topleft').add_to(map)
    
    # adding fullscreen function
    plugins.Fullscreen().add_to(map)

    # df = pd.read_csv("../renanalyst/points.csv")
    pointCoord = [30.52, -5.8]

    #morocco_data = pd.read_csv("../renanalyst/morocco_ssr_july2021.csv")
    morocco_data = pd.read_csv("morocco_df.csv")
    morocco_cities = pd.read_csv("morocco_cities.csv")
    morocco_powerlines = pd.read_csv("existingtransmissionlines.csv")
    heat_df = morocco_data.loc[:,["latitude","longitude","ssr"]]

    top_3, closest_cities_distances = get_closest_cities(pointCoord, morocco_cities)
    top_1, closest_powerline = get_powerline_distance(pointCoord, morocco_powerlines)

    # distance = getDistanceFromLatLonInKm(pointCoord[0], pointCoord[1], df["lat"].iloc[0], df["lon"].iloc[0])
    # distance = str(int(distance))
    # name = "Casablanca"

    # initialising the map
    # map1 = folium.Map(location=[19, -12], 
    #                   zoom_start=2)

    # lat_interval = 1
    # lon_interval = 1
    # grid = []

    # for lat in range(28, 36, lat_interval):
    #     grid.append([[lat, -180],[lat, 180]])

    # for lon in range(-14, -1, lon_interval):
    #     grid.append([[-90, lon],[90, lon]])

    # for g in grid:
    #     folium.PolyLine(g, color="black", weight=0.5, opacity=0.5).add_to(map1)

    morocco_data["bins"] = pd.cut(morocco_data["ssr"], bins=10, labels=[190, 170, 150, 130, 110, 90, 70, 50, 30, 10])

    morocco_data['ssr'] =  morocco_data['ssr'] / 10000000
    
    for _, xi in morocco_data.iterrows():
      folium.GeoJson(geo_json(xi['latitude'], xi['longitude'], 0.25, xi["bins"]), lambda x: x['properties']).add_to(map)
    # folium.GeoJson(geo_json(35.81, 13.16, 0.25)).add_to(map1)
    # folium.GeoJson(geo_json(35.81 + 0.25, 13.16, 0.25)).add_to(map1)

    # heat_data = heat_df.values.tolist()
    # HeatMap(heat_data,radius=13).add_to(map1)

    ssr_point = get_ssr(pointCoord, morocco_data)
    rating = get_location_rating(pointCoord, morocco_data)
    map.choropleth(geo_data="existingtransmissionlines.geojson")
    
    html=f"""
    <html>
    <head>
      <link rel="stylesheet" href="styles.css">
    </head>
    <body>
    <h1 style="font-family: Helvetica">Solar Farm Site</h1>
    <p style="font-family: Helvetica; font-size:14pt">Site Rating = {rating}/10</p>
    <table style="font-family: Arial, Helvetica, sans-serif; border-collapse: collapse; width: 100%;">
        <tr style="border:1px solid #ddd;">
            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #04AA6D; color: white; border:1px solid #ddd; text-align: center;">Solar Irradiance</th>
            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #04AA6D; color: white; border:1px solid #ddd; text-align: center;">Closest Cities</th>
            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #04AA6D; color: white; border:1px solid #ddd; text-align: center;">Powerline Distance</th>
        </tr>
        <tr style="border:1px solid #ddd;">
            <td style="border: 1px solid #ddd; padding: 8px;">{round(ssr_point*10000000, 2)} kW/m<sup>2</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{top_3[0]}: {round(closest_cities_distances[top_3[0]], 2)} km <br>
            {top_3[1]}: {round(closest_cities_distances[top_3[1]], 2)} km <br>
            {top_3[2]}: {round(closest_cities_distances[top_3[2]], 2)} km <br>
            <td style="border: 1px solid #ddd; padding: 8px;">Closest powerline is: {round(closest_powerline[top_1[0]], 2)} km <br>
            Power Rating: {top_1[0]}</td>
            </td>
        </tr>
    </table>
    </body>
    <html>
        """
    iframe = folium.IFrame(html=html, width=600, height=200)
    popup = folium.Popup(iframe, max_width=2650)

    icon = folium.features.CustomIcon('solar-panel.png', icon_size=(30,30))

    folium.Marker(
        location=pointCoord, 
        popup=popup,
        icon=icon
    ).add_to(map)

    plugins.HeatMap(data_list).add_to(map)
    plugins.Fullscreen().add_to(map)
    map = map._repr_html_()
    #plugins.MeasureControl().add_to(map)  (distance measuring function)
    #plugins.Terminator().add_to(map)  (day/night function)

    # map = map._repr_html_()
    context={
        'map' : map,
    }

    return render(request, 'dashboard/index.html', context)