import streamlit as st
import numpy as np
import pandas as pd
import folium
import seaborn as sns
import matplotlib.pyplot as plt
# import folium 
import os
from covid.api import CovId19Data

from bokeh.models import LogColorMapper
from bokeh.palettes import Viridis6 as palette
from bokeh.plotting import figure
from bokeh.sampledata.unemployment import data as unemployment
from bokeh.sampledata.us_counties import data as counties


# To launch this app in your web browser, run "streamlit run app.py"

api = CovId19Data(force=False)
overall_stats = api.get_stats()

st.title(f"Latest COVID-19 Numbers")
st.markdown(
"""
An app to provide the most up-to-date numbers on the Coronavirus 
Source: [Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19). Numbers are updated daily.
""")


# show overall stats
st.subheader("The latest total worldwide numbers")

st.write(f"(Last updated **{overall_stats['last_updated']}**)\
	\n* Confirmed cases: **{overall_stats['confirmed']:,}**  \
	\n* Recovered cases: **{overall_stats['recovered']:,}**  \
	\n* Deaths cases: **{overall_stats['deaths']:,}**")
# show top 20 cases
world_json = api.get_all_records_by_country()
tmp = (pd.json_normalize(world_json, max_level=0)
	.rename(index={0:'info'})
	.T)
df = pd.json_normalize(tmp['info']) #.rename(index={idx:country for idx,country in enumerate(tmp.index)})
df.replace({'label':{'US': 'United States of America', 'Taiwan*':'Taiwan'}}, inplace=True)
df['confirmed_log10'] = np.log10(df['confirmed'])



st.subheader("Top-20 countries by confirmed cases")

df2 = (df[['label', 'deaths', 'confirmed', 'recovered']]
	.set_index('label')
	.sort_values('confirmed', ascending=False)
	.iloc[:10]
	.rename(columns={'deaths':'succumbed'}))
st.bar_chart(df2)



st.subheader("Historical numbers by country")

available = api.show_available_countries()
country = st.selectbox('Available countries:', available).lower()
# time_range = st.slider('Date range', 0, 130, 25)
alt_names = {'taiwan*':'taiwan'}
if country in alt_names:
	country = alt_names[country]

tmp = api.get_history_by_country(country)
tmp_df = (pd.json_normalize(tmp[country]['history'], max_level=0)
	.rename(index={0:'info'})
	.T
	.reset_index())
tmp_df.rename(columns={'index':'date'}, inplace=True)

# df.replace({'label':{'US': 'United States of America', 'Taiwan*':'Taiwan'}}, inplace=True)
df_history = pd.concat([tmp_df[['date']], pd.json_normalize(tmp_df['info'])], axis=1)
df_history['date'] = pd.to_datetime(df_history['date'])
df_history.set_index('date', inplace=True)

df_history.rename(columns={'deaths':'succumbed', 
	'change_deaths':'change_succumbed'}, inplace=True)

st.area_chart(df_history[['confirmed', 'recovered', 'succumbed']])

st.subheader('Changes')
st.area_chart(df_history[['change_confirmed', 'change_recovered', 'change_succumbed']])



st.subheader("By location")
# simple test of bokeh chart
x = [1, 2, 3, 4, 5]
y = [6, 7, 2, 4, 5]

p = figure(
	title='simple line example',
	x_axis_label='x',
    y_axis_label='y')

p.line(x, y, legend='Trend', line_width=2)
st.bokeh_chart(p)

# st.bokeh_chart(p)
# st.write('test')


# world_geo = 'world-countries.json'
# world_map = folium.Map(location=[30,0], zoom_start=1.5)

# folium.Choropleth(
#     geo_data=world_geo, 
#     data=df,
#     name='choropleth',
#     key_on='properties.name',
#     fill_color='BuGn',
#     fill_opacity=0.5,
#     line_opacity=1,
#     columns=['label', 'confirmed_log10'], 
#     legend_name='Confirmed COVID-19 cases (log10)').add_to(world_map)
    
# st.write(world_map)

# palette = tuple(reversed(palette))

# counties = {
#     code: county for code, county in counties.items() if county["state"] == "tx"
# }

# county_xs = [county["lons"] for county in counties.values()]
# county_ys = [county["lats"] for county in counties.values()]

# county_names = [county['name'] for county in counties.values()]
# county_rates = [unemployment[county_id] for county_id in counties]
# color_mapper = LogColorMapper(palette=palette)

# data=dict(
#     x=county_xs,
#     y=county_ys,
#     name=county_names,
#     rate=county_rates,
# )

# TOOLS = "pan,wheel_zoom,reset,hover,save"
# p = figure(
#     title="Texas Unemployment, 2009",
#     x_axis_location=None, y_axis_location=None,
#     tooltips=[
#         ("Name", "@name"), ("Unemployment rate", "@rate%"), ("(Long, Lat)", "($x, $y)")
#     ])

# p = figure(
#     title="Texas Unemployment, 2009", tools=TOOLS,
#     x_axis_location=None, y_axis_location=None,
#     tooltips=[
#         ("Name", "@name"), ("Unemployment rate", "@rate%"), ("(Long, Lat)", "($x, $y)")
#     ])
# p.grid.grid_line_color = None
# p.hover.point_policy = "follow_mouse"

# p.patches('x', 'y', source=data,
#           fill_color={'field': 'rate', 'transform': color_mapper},
#           fill_alpha=0.7, line_color="white", line_width=0.5)

