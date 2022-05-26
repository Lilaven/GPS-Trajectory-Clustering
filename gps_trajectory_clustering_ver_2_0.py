# -*- coding: utf-8 -*-
"""GPS Trajectory Clustering - Ver 2.0.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Dhgrpv8zMoJIwfXwcI1GcBf8-acYJ9bd

Upload data
"""

from google.colab import files
uploaded = files.upload()

"""# Preprocessing data"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
# %matplotlib inline
import matplotlib.pyplot as plt
!pip install nibabel
!pip install dipy
import dipy, nibabel
import dipy.segment.clustering
from dipy.tracking.streamline import Streamlines
from dipy.segment.clustering import QuickBundles
import geopy.distance
from dipy.segment.metric import Metric
from dipy.segment.metric import ResampleFeature

# Read json file
df = pd.read_json('data.json', encoding='utf-8', lines=True, orient='column')
df.head()

# get gps of tripcodes 
from pandas.io.json import json_normalize

di = pd.DataFrame([md for md in df.departure])
den = pd.DataFrame([md for md in df.destination])
trip = pd.DataFrame([md for md in df.trips[0]])
gps = pd.DataFrame([md for md in trip.gps[0]],)
dta = pd.json_normalize(data=df.trips[0], record_path='gps', meta=['tripCode'])

# visualize raw data
dta.plot(kind="scatter", x="lng", y="lat",
    cmap=plt.get_cmap("jet"),
    colorbar=True, alpha=0.2, figsize=(10,6))
plt.legend()
plt.show()

# Create data streamline structure
streams = []

for i in range(0,len(dta.tripCode.unique())):
    gps = pd.DataFrame([md for md in trip.gps[i]]).drop(columns=['time']).to_numpy()
    streams.append(gps);   

streams

"""# Find number of mainpoint"""

# Design metric

class GPSDistance(Metric):
  def __init__(self):
    super(GPSDistance, self).__init__(feature=ResampleFeature(nb_points=256))

  def are_compatible(self, shape1, shape2):
    return len(shape1) == len(shape2)

  def dist(self, v1, v2):
    x = [geopy.distance.vincenty([p[0][0],p[0][1]], [p[1][0],p[1][1]]).km for p in list(zip(v1,v2))]
    currD = np.mean(x)
    return currD

#Clustering sample data

metric = GPSDistance()
qb = QuickBundles(threshold=1, metric=metric)
clusters = qb.cluster(streams)

print("Nb. clusters:", len(clusters))
print("Small clusters:", clusters < 10)

# Define function to concatenate points of cluster centroid with departure and destination
def rpoint(i):
  dep = np.array(di)[:,2:].astype(float)
  des = np.array(den)[:,2:].astype(float)
  route = clusters[i].centroid.astype(float)
  rp_point = np.concatenate((dep, route, des))
  return rp_point;


# Calculate distance among point of one cluster
def lnglat(dt,i):
  return dt[i:].tolist()[0];

def distance(data):
  from geopy.distance import distance
  i = 0
  d = 0
  while i < (len(data) - 1):
    dn = distance(lnglat(data,i), lnglat(data,(i +1))).km
    d = d + dn
    i = i +1
  return d;

# Find the the number of mainpoint

dist_between_two_point = 0.25
def number_point(all_clusters):
    return float(sum(all_clusters)) / max(len(all_clusters), 1) * (1/dist_between_two_point)

def totaldist(clusters):  
  total_dis = []
  for i in range(len(clusters)):
    total_dis.append(distance(rpoint(i)))
  return total_dis

nb_p = int(round(number_point(totaldist(clusters)),0))

"""# Find popular route"""

class GPSDistance(Metric):

  def __init__(self,nb_p):
    self.nb_p = nb_p
    super(GPSDistance, self).__init__(feature=ResampleFeature(nb_points=nb_p))

  def are_compatible(self, shape1, shape2):
    return len(shape1) == len(shape2)

  def dist(self, v1, v2):
    x = [geopy.distance.vincenty([p[0][0],p[0][1]], [p[1][0],p[1][1]]).km for p in list(zip(v1,v2))]
    currD = np.mean(x)
    return currD

#Clustering by QuickBundles

metric = GPSDistance(nb_p=nb_p)
qb = QuickBundles(threshold=1.7, metric=metric)
clusters = qb.cluster(streams)

print("Nb. clusters:", len(clusters))

# Genenate the cluster corresponding to the popular route from departure to destination
for i in range(len(clusters)-1):
  if len(clusters[i].indices) > len(clusters[i + 1].indices):
    cluster_po = i
    break
  elif len(clusters[i].indices) == len(clusters[i + 1].indices):
    if distance(rpoint(i)) <= distance(rpoint(i + 1)):
      cluster_po = i
    else: cluster_po = i + 1
    break
  else: cluster_po = i + 1;

# Convert to dataframe to visualize
rp_points = pd.DataFrame(rpoint(cluster_po), columns=["lat", "lng"])


# Return the popular route from departure to destination
popular_route = rpoint(cluster_po)

print("The coordinates of popular_route:", popular_route)

# Convert the popular route to dataframe to visualize
rp_points = pd.DataFrame(rpoint(cluster_po), columns=["lat", "lng"])

# Visualize the shortest route
fig, ax = plt.subplots(figsize=[15, 10])
dta_scatter = ax.scatter(dta['lng'], dta['lat'], c='#99cc99', edgecolor='None', alpha=0.7, s=3)
rp_scatter = ax.scatter(rp_points['lng'], rp_points['lat'], c='k', alpha=0.9, s=5)

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.legend([dta_scatter, rp_scatter], ['Full set', 'Reduced set'], loc='upper right')
plt.show()

"""# Find shortest route"""

#Design metric

metric = GPSDistance(nb_p=nb_p)
qb = QuickBundles(threshold=1, metric=metric)
clusters = qb.cluster(streams)

print("Nb. clusters:", len(clusters))
print("Small clusters:", clusters < 10)

# Find the cluster number corresponding to the shortest route from departure to destination
min = distance(rpoint(0))
cluster_op = 0
for i in range(len(clusters)):
  if distance(rpoint(i)) < min:
    cluster_op = i
    min = distance(rpoint(i))
  else:
    continue

# Return the shortest route from departure to destination
shortest_route = rpoint(cluster_op)

# Estimate distance of shortest route
esdist = distance(rpoint(cluster_op))

print("The coordinates of shortest route:", shortest_route)
print("The distance of shortest route:", esdist)

# Convert the popular route to dataframe to visualize
rp_points = pd.DataFrame(rpoint(cluster_op), columns=["lat", "lng"])

# Visualize the shortest route
fig, ax = plt.subplots(figsize=[15, 10])
dta_scatter = ax.scatter(dta['lng'], dta['lat'], c='#99cc99', edgecolor='None', alpha=0.7, s=2)
rp_scatter = ax.scatter(rp_points['lng'], rp_points['lat'], c='k', alpha=0.9, s=5)

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.legend([dta_scatter, rp_scatter], ['Full set', 'Reduced set'], loc='upper right')
plt.show()