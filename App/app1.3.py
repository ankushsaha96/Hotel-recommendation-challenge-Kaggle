#!/usr/bin/env python
# coding: utf-8

# In[8]:


import flask
from flask import Flask, request
import pandas as pd
import numpy as np
import math
import random
from geopy.geocoders import Nominatim
from numpy.linalg import norm


related_customers_lookup_table = pd.read_csv('related_customers_lookup_table.csv')
train_customer_cf_existing = pd.read_csv('train_customer_cf_existing.csv')
vendor_categories = pd.read_csv('vendor_categories.csv')

app = Flask(__name__)

@app.route("/")
def startup_page():
    return flask.render_template('index.html')

@app.route('/name',methods=['post'])
def get_name():
    return flask.render_template('name.html')

@app.route('/new_customer',methods=['post'])
def new_customer():
    return request.form.to_dict()

@app.route('/location',methods=['post'])
def get_location_preferences():
    #name = request.form.to_dict()['name'].split(' ')[0]
    max_distance = 17877.08408684324 
    min_distance = 0.06398004160677155
    input_dict = request.form.to_dict()
    def cosine_sim(A,B):
        return np.dot(A,B)/(norm(A)*norm(B))
    def distance(lat,lon):
        R = 6373.0 #radius of the Earth


        #coordinates
        lat1 = lat
        lon1 = lon
        lat2 = 0
        lon2 = 0

        #change in coordinates
        dlon = lon2 - lon1


        dlat = lat2 - lat1

        #Haversine formula
        a = math.sin((dlat / 2)**2) + math.cos(lat1) * math.cos(lat2) * math.sin((dlon / 2)**2)

        c = 2 * math.atan(np.sqrt(a)/np.sqrt(1 - a))
        distance = R * c
        return distance


    new_customer = []
    if 'name' in input_dict.keys():
        if input_dict['name'] == 'Male':
            new_customer.append(1)
        else:
            new_customer.append(0)
    else:
        new_customer.append(0)
        
    if 'location' in input_dict.keys():
        geolocator = Nominatim(user_agent="MyApp")
        location = geolocator.geocode(input_dict['location'])
        if location is not None:
            distance = distance(location.latitude,location.longitude)
            new_customer.append(distance)
        else:
            new_customer.append(0)
    else:
        new_customer.append(0)
    if 'Loc_type' in input_dict.keys():
        Loc_type = input_dict['Loc_type']
        if Loc_type == 'Home':
            new_customer.extend([0,0,0])
        elif Loc_type == 'Work':
            new_customer.extend([0,0,1])
        else:
            new_customer.extend([1,0,0])
    else:
        new_customer.extend([0,1,0])
        
    cuisines = vendor_categories.columns[1:]
    for i in cuisines:
        if i in input_dict.keys():
            new_customer.append(1)
        else:
            new_customer.append(0)
            
    def recommend_vendor_new_customer(customer):
        target_customer = customer
        customers = []
        similerities = []
        for i in range(len(train_customer_cf_existing)):
            ref_customer = train_customer_cf_existing.iloc[i,:].values
            customers.append(ref_customer[0])
            similerities.append(float(cosine_sim(target_customer,ref_customer[1:])))
        related_customers = []
        related_customers_similerities = []
        rank = np.argsort(similerities)[-1:5:-1]
        for i in rank:
            related_customers.append(customers[i])
            related_customers_similerities.append(similerities[i])
        ref_customers = pd.DataFrame({'customer_id':related_customers,'similerities':related_customers_similerities})
        ref_customers = ref_customers.merge(related_customers_lookup_table,on='customer_id')
        ref_customers.ratings = ref_customers.ratings*ref_customers.similerities
        recomended_vendors = pd.DataFrame(ref_customers.groupby('vendor_id')['ratings'].mean()).reset_index()
        recomended_vendors = recomended_vendors[-1:-6:-1]
        recomended_vendors = recomended_vendors.vendor_id.tolist()
  

        return recomended_vendors
            
    return 'recommended vendore are: '+str(recommend_vendor_new_customer(new_customer))
    

@app.route('/name_selector',methods=['post'])
def location_selector_1():
    return flask.render_template('vendor_recomender.html')

@app.route('/vendor_selector',methods=['post'])
def recommend_vendor_existing_customer():
    customer = random.randint(0,len(related_customers_lookup_table))
    customer = related_customers_lookup_table.iloc[customer,0]
    return 'recommended vendore are: '+str(related_customers_lookup_table[related_customers_lookup_table.customer_id == customer].sort_values(by='ratings',ascending=False)['vendor_id'][:5].tolist())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

