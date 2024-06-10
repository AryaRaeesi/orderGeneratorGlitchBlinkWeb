#%%
import requests as req
import pandas as pd
import csv

def getCompany(organizationNumber):
    url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{organizationNumber}"
    responce = req.get(url)
    data = responce.json()
    print(data)

#getCompany("929741994")

with open("orderid.csv","w", newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["orderID","company","adress","serviceOrdered","customerContactName","seller"])
    
    for i in range(100428,199999):
        writer.writerow([i,"","","","",""])
# %%
