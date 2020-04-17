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

class CovidDashboard:
	def __init__(self):
		self.api = CovId19Data(force=False)
		self._available = self.api.show_available_countries()
	
	def get_world(self):
		self.world_json = self.api.get_all_records_by_country()

	def get_overall_stats(self):
		self.overall_stats = self.api.get_stats()

	def clean_df(self):
		_df = (pd.json_normalize(self.world_json, max_level=0)
			.rename(index={0:'info'})
			.T)
		df_world = pd.json_normalize(_df['info']) #.rename(index={idx:country for idx,country in enumerate(tmp.index)})
		df_world.replace({'label':{
			'US': 'United States of America', 
			'Taiwan*':'Taiwan'}}, inplace=True)
		df_world['confirmed_log10'] = np.log10(df_world['confirmed'])
		return df_world

	def get_world_plot(self, df_world):
		df_plot = (df_world[['label', 'deaths', 'confirmed', 'recovered']]
			.set_index('label')
			.sort_values('confirmed', ascending=False)
			.iloc[:10]
			.rename(columns={'deaths':'succumbed'}))
		return df_plot

	def get_history(self, country):
		hist_json = self.api.get_history_by_country(country)
		_df = (pd.json_normalize(hist_json[country]['history'], max_level=0)
			.rename(index={0:'info'})
			.T
			.reset_index())
		_df.rename(columns={'index':'date'}, inplace=True)

		# df.replace({'label':{'US': 'United States of America', 'Taiwan*':'Taiwan'}}, inplace=True)
		df_history = pd.concat([_df[['date']], pd.json_normalize(_df['info'])], axis=1)
		df_history['date'] = pd.to_datetime(df_history['date'])
		df_history.set_index('date', inplace=True)
		df_history.rename(columns={'deaths':'succumbed', 
			'change_deaths':'change_succumbed'}, inplace=True)

		return df_history

	def show_latest_overall(self):
		self.get_overall_stats()
		st.subheader("The latest total worldwide numbers")
		st.write(f"(Last updated **{self.overall_stats['last_updated']}**)\
			\n* Confirmed cases: **{self.overall_stats['confirmed']:,}**  \
			\n* Recovered cases: **{self.overall_stats['recovered']:,}**  \
			\n* Deaths cases: **{self.overall_stats['deaths']:,}**")

	def show_world_numbers(self):
		st.subheader("Top-20 countries by confirmed cases")
		df_plot = self.get_world_plot(self.clean_df())
		st.bar_chart(df_plot)

	def show_country_trend(self):
		st.subheader("Trends by country")
		country = st.selectbox('Available countries:', self._available).lower()
		alt_names = {'taiwan*':'taiwan'}
		if country in alt_names:
			country = alt_names[country]
		df_history = self.get_history(country)
		st.write('Daily confirmed, succumbed, and deaths')
		st.area_chart(df_history[['confirmed', 'recovered', 'succumbed']])

		# changes
		df_change = df_history[['confirmed', 'succumbed', 'recovered']].diff()
		st.write('Daily changes')
		st.area_chart(df_change[['confirmed', 'recovered', 'succumbed']])

		# total
		# df_total = df_history[['confirmed', 'succumbed', 'recovered']].cumsum()
		# st.write('Total')
		# st.area_chart(df_total[['confirmed', 'recovered', 'succumbed']])

	def make_app(self):
		self.get_world()
		self.get_overall_stats()

		st.title(f"Latest COVID-19 Numbers")
		st.markdown(
		"""
		An app to provide the most up-to-date numbers on the Coronavirus 
		Source: [Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19). Numbers are updated daily.
		""")

		self.show_latest_overall()
		self.show_world_numbers()
		self.show_country_trend()

		"""make streamlit app"""

CovidDashboard().make_app()

# st.subheader('Changes')
# st.area_chart(df_history[['change_confirmed', 'change_recovered', 'change_succumbed']])



# st.subheader("By location")
# st.write('insert bokeh map of world by cases')

# # simple test of bokeh chart
# x = [1, 2, 3, 4, 5]
# y = [6, 7, 2, 4, 5]

# p = figure(
# 	title='simple line example',
# 	x_axis_label='x',
#     y_axis_label='y')

# p.line(x, y, legend='Trend', line_width=2)
# st.bokeh_chart(p)








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

palette = tuple(reversed(palette))

counties = {
    code: county for code, county in counties.items() if county["state"] == "tx"
}

county_xs = [county["lons"] for county in counties.values()]
county_ys = [county["lats"] for county in counties.values()]

county_names = [county['name'] for county in counties.values()]
county_rates = [unemployment[county_id] for county_id in counties]
color_mapper = LogColorMapper(palette=palette)

data=dict(
    x=county_xs,
    y=county_ys,
    name=county_names,
    rate=county_rates,
)

TOOLS = "pan,wheel_zoom,reset,hover,save"
p = figure(
    title="Texas Unemployment, 2009",
    x_axis_location=None, y_axis_location=None,
    tooltips=[
        ("Name", "@name"), ("Unemployment rate", "@rate%"), ("(Long, Lat)", "($x, $y)")
    ])

p = figure(
    title="Texas Unemployment, 2009", tools=TOOLS,
    x_axis_location=None, y_axis_location=None,
    tooltips=[
        ("Name", "@name"), ("Unemployment rate", "@rate%"), ("(Long, Lat)", "($x, $y)")
    ])
p.grid.grid_line_color = None
p.hover.point_policy = "follow_mouse"

p.patches('x', 'y', source=data,
          fill_color={'field': 'rate', 'transform': color_mapper},
          fill_alpha=0.7, line_color="white", line_width=0.5)

st.bokeh_chart(p)

