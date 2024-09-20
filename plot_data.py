import geopandas as gpd
from pathlib import Path
from dash import Dash,jupyter_dash
import dash
from dash import html
from dash import dcc
from dash import Output,Input,State
import dash_leaflet as dl
from dash_extensions.javascript import arrow_function, assign
import json
raw_data_path = './data/census/geojson'
raw_data_path = Path(raw_data_path)
raw_data_list = list(raw_data_path.rglob('*.geojson'))
crs = 'EPSG:4326' # WGS84
result_gdf = gpd.read_file('data/branch_list_geo_dta_without_duplicate.geojson')
result_gdf.to_crs(crs=crs)
states = result_gdf[result_gdf['STATE_NAME'].notnull()]['STATE_NAME'].unique().tolist()
states.sort()
geo_dcit = {}
for i,raw_data_path in enumerate(raw_data_list):
    gdf = gpd.read_file(raw_data_path)
    state = gdf['STATE_NAME'].iloc[0]
    gdf.set_index('FIPSWITHTRACT', inplace=True)
    gdf.to_crs(crs=crs)
    geo_dcit[state] = gdf
default_zoom = 4
default_center = (37.0902, -95.7129)
default_bounds = [[16.88865978738161, -136.40625000000003], [53.067626642387374, -55.01953125000001]]

url_template = "http://{{s}}.tile.stamen.com/{}/{{z}}/{{x}}/{{y}}.png"
# Some tile urls.
keys = ["toner", "terrain"]
attribution = 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, ' \
              '<a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data ' \
              '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
app = Dash(__name__)
style_handle = assign("""function(feature, context){
    const {colorscale, style,counties,is_highly} = context.hideout;  // get props from hideout
    style.fillColor = colorscale[2];
    if(is_highly){
        if(counties && counties.includes(feature.properties.COUNTY_NAME)){
            // style.fillColor = colorscale[6];
            style.fillOpacity = 0.8;
            style.color = 'black';
            // style.dashArray = '1';
            // style.weight = 1;
        }
        else{
            style.fillOpacity = 0.2;
            style.color = 'white';
            // style.dashArray = '1';
            // style.weight = 0.1;
        }    
    }
    return style;
}""")
style = dict(weight=0.5, opacity=1, color='white', dashArray='3', fillOpacity=0.7)
colorscale = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026']
default_hightout =dict(colorscale=colorscale, 
                                             style=style,
                                             )
on_geodf_each_feature = assign("""function(feature, layer, context){
    layer.bindTooltip(`<div class="content">
    <div><strong>FIPSWITHTRACT:</strong>${feature.id}</div>
    <div><strong>STATE:</strong>${feature.properties.STATE_NAME}</div>
    <div><strong>is_highly:</strong>${feature.properties.is_highly}</div>
    <div><strong>TRACT:</strong>${feature.properties.TRACTCE10}</div>
    <div><strong>COUNTY:</strong>${feature.properties.COUNTY_NAME}</div>
</div>`)
}""")
on_marker_each_feature = assign("""function (feature, layer, context) {
    // if it is a cluster, don't bind popup
    // layer.bindTooltip(`<div class="marker-content">
    if (feature.properties.TRACTCE10) {
        layer.bindPopup(`<div class="marker-content">
        <div><strong>Tract:</strong>${feature.properties.TRACTCE10}</div>
        <div><strong>State:</strong>${feature.properties.STATE_NAME}</div>
        <div><strong>Country:</strong>${feature.properties.COUNTY_NAME}</div>
        <div><strong>Name:</strong>${feature.properties.namefull}</div>
        <div><strong>Addresbr:</strong>${feature.properties.addresbr}</div>
</div>`);
    }
}""")
geo_list = []
markers_list = []
button = html.Button("回到默认视角", id="reset-view-btn",n_clicks=0)
app.layout = html.Div([
    html.H1("Banking Deserts in the United States"),
    dcc.Dropdown(
        id='state-dropdown',
        options=
        [{
            'label': 'United States',
            'value': 'United States'
            },]+
        [{'label': state, 'value': state} for state in states],
        value='United States',
        placeholder="Select a State",
        clearable=False
    ),
    # Dropdown to highlight a county (dependent on selected state)
    dcc.Dropdown(
        id='county-dropdown',
        placeholder="Highlight a County",
        clearable=True,
        multi=True
    ),
    dcc.Loading(
        id="map-loading",
        type="circle",  # 可选样式有 "circle", "dot", "cube", etc.
        children=[
        dl.Map([
            dl.TileLayer(),
            dl.LayersControl(
                # [dl.BaseLayer(dl.TileLayer(url=url_template.format(key), attribution=attribution),
                #               name=key, checked=key == "toner") for key in keys] +
                [
                dl.Overlay(dl.LayerGroup(children=geo_list,id='tractLayer'),name="geojson",checked=True),
                dl.Overlay(dl.LayerGroup(children=markers_list,id="markerLayer")
                            , name="markers", checked=True),
                ], id="lc"
            ),
            dl.GeoJSON(children={},id='storeData',hideout={}),
            dl.ScaleControl(position="bottomleft", imperial=False),
            dl.MeasureControl(position="topleft", primaryLengthUnit="kilometers", primaryAreaUnit="hectares",
                        activeColor="#214097", completedColor="#972158"),
            dl.FullScreenControl(),
            # dl.Colorbar(colorscale=colorscale, width=20, height=200, min=0, max=50, position="topright"),
    ], zoom=default_zoom, center=default_center, style={'height': '80vh'}, id="map",),
        ]
        )
])
# 回调函数来监听按钮点击并重置地图视角
@app.callback(
    [
    Output("map", "center"),
    Output("map", "zoom"),
    ],
    
    [    Input('state-dropdown', 'value'),],
)
def reset_map_view(selected_state):
    # 当按钮被点击时，重置地图中心和缩放级别
    if selected_state == 'United States':
        return default_center, default_zoom
    # 初始状态不做修改
    return dash.no_update, dash.no_update

# Callback to update the county dropdown based on the selected state
@app.callback(
    Output('county-dropdown', 'options'),
    Input('state-dropdown', 'value')
)
def update_county_dropdown(selected_state):
    # Filter the GeoDataFrame for the selected state
    if selected_state:
        if selected_state != 'United States':
            gdf = geo_dcit[selected_state]
            counties = gdf[gdf['STATE_NAME'] == selected_state]['COUNTY_NAME'].unique()
        # if selected_state == 'United States':
        #     counties = result_gdf['COUNTY_NAME'].unique()
            return [{'label': county, 'value': county} for county in counties]
    return []
@app.callback(
    Output('geojson', 'hideout'),
    Input('state-dropdown', 'value'),
     Input('county-dropdown', 'value'),
     State('geojson', 'hideout')
)
def update_hideout(selected_state, selected_counties:list, hideout):
    if selected_state and selected_state != 'United States' \
        and selected_counties and len(selected_counties) != 0:
        hideout['counties'] = selected_counties
        hideout['is_highly'] = True
    else:
        hideout = default_hightout
    return hideout
point_to_layer = assign("""function(feature, latlng, context){
    const scatterIcon = L.DivIcon.extend({
        createIcon: function(oldIcon) {
               let icon = L.DivIcon.prototype.createIcon.call(this, oldIcon);
               icon.style.backgroundColor = this.options.color;
               return icon;
        }
    })
    const icon = new scatterIcon({
        className: "marker-cluster",
        iconSize: L.point(20, 20),
        color: 'red',
    });
    const marker = L.marker(latlng, {icon: icon});  // render a simple circle marker
    return marker;  // render a simple circle marker
}""")


# # 使用 pointToLayer 自定义点的渲染方式
# def point_to_layer(feature, latlng,context):
#     return dl.CircleMarker(latlng, radius=10, fillOpacity=1, zIndexOffset=1000,fillColor='red')  # zIndexOffset 确保自定义点在最上方
# 创建 hover 样式的 JavaScript 函数
@app.callback(
    [Output('tractLayer', 'children'),
     Output('markerLayer', 'children'),
     Output('map', 'bounds'),
     Output('storeData','hideout'),
     ],
    [Input('state-dropdown', 'value'),
     State('storeData', 'hideout'),
     ]
    # prevent_initial_call=True
)
def update_tract_layer(selected_state,store_hideout:dict):
    geo_list = []
    markers_list = []
    bounds = None
    context = dash.callback_context
    if not context.triggered:
        return geo_list,markers_list,bounds,store_hideout
    trigger = context.triggered[0]
    if selected_state == 'United States':  
        return geo_list,markers_list,dash.no_update
    if selected_state and selected_state != 'United States':
        # if trigger['prop_id'] == 'state-dropdown.value':
        gdf = geo_dcit.get(selected_state)
        if gdf is not None:
            sample_gdf = result_gdf.query(f'STATE_NAME == "{selected_state}"')
            hideout = default_hightout.copy()
            bounds = gdf.total_bounds
            hideout['bounds'] = bounds
            geojson = dl.GeoJSON(data=gdf.to_geo_dict(),  # geopandas to geojson
                                style=style_handle,  # how to style each polygon
                                zoomToBounds=True,  # when true, zooms to bounds when data changes (e.g. on load)
                                onEachFeature=on_geodf_each_feature,  # how to bind data to each feature
                                zoomToBoundsOnClick=False,  # when true, zooms to bounds of feature (e.g. polygon) on click
                                hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
                                hideout=hideout,
                                # id=f"geojson_{gdf['STATE_NAME'].iloc[0]}")
                                id=f"geojson")
            geo_list.append(geojson)
            markers = dl.GeoJSON(data=sample_gdf.to_geo_dict(),  # geopandas to geojson
                    id="markers",
                    onEachFeature=on_marker_each_feature,  # how to bind data to each feature
                    # style=arrow_function(dict(zIndex=1000)),
                    cluster=True, 
                    zoomToBoundsOnClick=True,
                    superClusterOptions={"radius": 100},
                    pointToLayer=point_to_layer,
                    )
            markers_list.append(markers)
            
    return geo_list,markers_list,bounds,store_hideout

if __name__ == '__main__':
    app.run_server(port=18851)