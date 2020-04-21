import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import os
from covid.api import CovId19Data
import json

from bokeh.models import LogColorMapper
from bokeh.palettes import Viridis6 as palette
from bokeh.plotting import figure
from shapely import affinity
from shapely.geometry import mapping, shape

# To launch this app in your web browser, run "streamlit run app.py"

class CovidDashboard:
	def __init__(self):
		self.api = CovId19Data(force=False)
		self._available = self.api.show_available_countries()
	
	# @st.cache
	def get_world(self):
		self.world_json = self.api.get_all_records_by_country()

	# @st.cache
	def get_us(self):
		states_df = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
		self.latest_states = states_df[states_df.date == states_df.date.iloc[-1]]

	def get_state(self):
		# county_df = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv')
		# self.latest_states = states_df[states_df.date == states_df.date.iloc[-1]]
		pass

	def get_overall_stats(self):
		self.overall_stats = self.api.get_stats()

	def get_coordinates(self, json_data):
	    depth = lambda L: isinstance(L, list) and max(map(depth, L))+1
	    country_id = []
	    longitudes = []
	    latitudes = []	

	    for feature in json_data['features']:
	        coordinates = feature['geometry']['coordinates']
	        number_dimensions = depth(coordinates)
	        # one border
	        if number_dimensions == 3:
	            country_id.append(feature['properties']['name'])
	            points = np.array(coordinates[0], 'f')
	            longitudes.append(points[:, 0])
	            latitudes.append(points[:, 1])
	        # several borders
	        else:
	            for shape in coordinates:
	                country_id.append(feature['properties']['name'])
	                points = np.array(shape[0], 'f')
	                longitudes.append(points[:, 0])
	                latitudes.append(points[:, 1])
	    return country_id, longitudes, latitudes

    

	def get_geojson(self):
	    '''
	    Returns
	    -------
	    str - geojson with Alaska and Hawaii translated to fit in extent of Continental US.
	    states geojson available at: 
	    http://s3.amazonaws.com/bokeh_data/us_states_simplified_albers.geojson
	    '''
	    with open('geojson/us_states.geojson') as us_states_file:
	        geojson = json.loads(us_states_file.read())
	        for f in geojson['features']:
	            f['properties']['name'] = f['properties']['NAME']
	            if f['properties']['NAME'] == 'Alaska':
	                geom = affinity.translate(shape(f['geometry']), xoff=1.2e6, yoff=-4.8e6)
	                geom = affinity.scale(geom, .4, .4)
	                geom = affinity.rotate(geom, 30)
	                f['geometry'] = mapping(geom)
	            elif f['properties']['NAME'] == 'Hawaii':
	                geom = affinity.translate(shape(f['geometry']), xoff=4.6e6, yoff=-1.1e6)
	                geom = affinity.rotate(geom, 30)
	                f['geometry'] = mapping(geom)
	    return geojson

	def clean_world_data(self):
		_df = (pd.json_normalize(self.world_json, max_level=0)
			.rename(index={0:'info'})
			.T)
		self.df_world = pd.json_normalize(_df['info']) #.rename(index={idx:country for idx,country in enumerate(tmp.index)})
		self.df_world.rename(columns={'label':'country'}, inplace=True)
		self.df_world.replace({'country':{
			'US': 'United States of America', 
			'Taiwan*':'Taiwan', 
			'Congo (Kinshasa)':'Democratic Republic of the Congo', 
			'Congo (Brazzaville)':'Republic of the Congo', 
			'Tanzania':'United Republic of Tanzania'}},
			inplace=True)
		self.df_world['confirmed_log10'] = np.log10(self.df_world['confirmed'])

	def get_world_plot(self):
		df_plot = (self.df_world[['country', 'deaths', 'confirmed', 'recovered']]
			.set_index('country')
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

		df_history = pd.concat([_df[['date']], pd.json_normalize(_df['info'])], axis=1)
		df_history['date'] = pd.to_datetime(df_history['date'])
		df_history.set_index('date', inplace=True)
		df_history.rename(columns={'deaths':'succumbed', 
			'change_deaths':'change_succumbed'}, inplace=True)

		return df_history

	def show_latest_overall(self):
		self.get_overall_stats()
		st.header("Summary across the globe")
		st.write(f"**Last updated** {self.overall_stats['last_updated']}\
			\n* Confirmed cases: **{self.overall_stats['confirmed']:,}**  \
			\n* Recovered: **{self.overall_stats['recovered']:,}**  \
			\n* Deaths: **{self.overall_stats['deaths']:,}**")

	# @st.cache
	def show_world_numbers(self):
		st.subheader("Top-10 countries by confirmed cases")
		df_plot = self.get_world_plot()
		st.bar_chart(df_plot)

	# @st.cache
	def show_country_trend(self):
		st.subheader("Trends by country")
		country = st.selectbox('Available countries:', self._available).lower()
		alt_names = {'taiwan*':'taiwan'}
		if country in alt_names:
			country = alt_names[country]
		df_history = self.get_history(country)
		st.write('Total confirmed, recovered, and succumbed by date')
		st.area_chart(df_history[['confirmed', 'recovered', 'succumbed']])

		# changes
		df_change = df_history[['confirmed', 'succumbed', 'recovered']].diff()
		st.write('Daily change')
		st.area_chart(df_change[['confirmed', 'recovered', 'succumbed']])

		# total
		# df_total = df_history[['confirmed', 'succumbed', 'recovered']].cumsum()
		# st.write('Total')
		# st.area_chart(df_total[['confirmed', 'recovered', 'succumbed']])
	
	# @st.cache
	def show_world_map(self):
		palette_ = tuple(reversed(palette))
		with open('geojson/world-geo.json') as f:
			json_data = json.load(f)
		color_mapper = LogColorMapper(palette=palette_)
		
		country, lon, lat = self.get_coordinates(json_data)
		df_countries = pd.DataFrame({"country":country, "lon":lon, "lat":lat}, columns=['country', 'lon', 'lat'])
		df_tmp = self.df_world[['country', 'confirmed', 'deaths', 'recovered']]
		df4 = pd.merge(df_countries, df_tmp, how='left', left_on='country', right_on='country')

		confirmed = df4['confirmed'].values
		deaths = df4['deaths'].values
		recovered = df4['recovered'].values
		countries = df4['country'].values
		lon = df4['lon'].values
		lat = df4['lat'].values

		data=dict(
			x=lon,
		    y=lat,
		    name=countries,
		    confirmed=confirmed,
		    recovered=recovered,
		    deaths=deaths
			)

		TOOLS = "pan,wheel_zoom,reset,hover,save"
		p = figure(
		    title="Total worldwide COVID-19 cases",
		    x_axis_location=None, y_axis_location=None,
		    tooltips=[
		    ("Name", "@name"), ("Confirmed", "@confirmed"), ("Deaths", "@deaths"), ("Recovered", "@recovered")
		    ],
		    active_scroll='wheel_zoom',
		    match_aspect=True)

		p.grid.grid_line_color = None
		p.hover.point_policy = "follow_mouse"

		p.patches('x', 'y', source=data,
		          fill_color={'field': 'confirmed', 'transform': color_mapper},
		          fill_alpha=0.7, line_color="white", line_width=0.5)

		st.bokeh_chart(p)

	# @st.cache
	def show_us_map(self):
		palette_ = tuple(reversed(palette))
		with open('geojson/world-geo.json') as f:
			json_data = json.load(f)
		color_mapper = LogColorMapper(palette=palette_)

		states_geo = self.get_geojson()
		states, lons, lats = self.get_coordinates(states_geo)

		states_geo = pd.DataFrame({'state':states, 'lons':lons, 'lats':lats})

		states_df = pd.merge(states_geo, self.latest_states, left_on='state', right_on='state')
		states_df.set_index('state', inplace=True)

		cases = states_df['cases'].values
		deaths = states_df['deaths'].values
		death_pct = [x/y*100 for x,y in zip(deaths, cases)]

		data=dict(
		    x=lons,
		    y=lats,
		    name=states,
		    cases=cases,
		    deaths=deaths,
		    pct=death_pct
			)

		TOOLS = "pan,wheel_zoom,reset,hover,save"
		p = figure(
		    title="Total US COVID-19 cases",
		    x_axis_location=None, y_axis_location=None,
		    tooltips=[
		    ("Name", "@name"), ("Cases", "@cases"), 
		    ("Deaths", "@deaths"), ("Percentage", "@pct%")
		    ],
		    active_scroll='wheel_zoom',
		    match_aspect=True)

		p.grid.grid_line_color = None
		p.hover.point_policy = "follow_mouse"

		p.patches('x', 'y', source=data,
		          fill_color={'field': 'cases', 'transform': color_mapper},
		          fill_alpha=0.7, line_color="white", line_width=0.5)		
		st.bokeh_chart(p)

	def show_state(self):
		pass

	def make_app(self):
		self.get_world()
		self.get_us()
		self.get_state()
		self.get_overall_stats()
		self.clean_world_data()

		st.title(f"COVID-19 Info Tracker")
		st.write('A dashboard to provide the most up-to-date numbers on the Coronavirus pandemic')

		self.show_latest_overall()
		self.show_world_numbers()
		self.show_country_trend()
		self.show_world_map()
		self.show_us_map()

		st.markdown(
		"""
		---
		**Source:** Worldwide data is from 
		[Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19) and
		US data is from [NY Times](https://github.com/nytimes/covid-19-data).
		The numbers are updated daily. Small business venture data is from [GoDaddy]
		(https://www.godaddy.com/ventureforward/research).
		""")

		

CovidDashboard().make_app()
