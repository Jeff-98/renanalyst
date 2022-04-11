import folium

coordinate = (37.8199286, -122.4782551)
m = folium.Map(
    name="choropleth",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
)
m.save('index.html')
