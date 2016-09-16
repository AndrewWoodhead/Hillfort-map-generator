# Author: Andrew Woodhead
# Course: GEOG 485 - Final Project
# Date: July 27, 2016
# Purpose: Takes a csv file containing URL's of Scottish hillfort sites from the Canmore database
#          and parses them to create a shapefile containing points for each site.

# import modules
import requests
from bs4 import BeautifulSoup
import pyproj
import BNG
import arcpy
import csv
arcpy.env.overwriteOutput = True

# create a new feature class. These variables can be easily changed.
spatialRef = arcpy.SpatialReference(4326) # WGS 1984 EPSG code
outPath = "C:\\PSUGIS\\GEOG485\\FinalProject"
outName = "Hillforts.shp"
hillfortFC = arcpy.CreateFeatureclass_management(outPath, outName, "POINT", "", "", "", spatialRef)

# add NAME field to new shapefile
arcpy.AddField_management(hillfortFC, "NAME", "TEXT")

hillfortUrls = [] #create an empty list to store the hillfort URL's

# open the csv file and read it using the csv module
csvFile = open("C:/PSUGIS/GEOG485/FinalProject/hillfort_urls.csv", "r") #edit path if using different csv file
csvReader = csv.reader(csvFile)

#create a list of URL's
for row in csvReader:
    hillfortUrls.append(',  '.join(row))
    
i = 1 #create a counter to update the "ID" field

try:
    # parse HTML text, transform coordinate systems, and update shapefile attributes
    for url in hillfortUrls:
        # make a request on the URL and get the HTML as text
        req = requests.get(url)
        page = req.text

        # create a soup object and find all the paragraph tags
        soup = BeautifulSoup(page, 'html.parser')
        pTags = soup.find_all('p')

        # create spatial ref objects for osgb36 and wgs84
        osgb36 = pyproj.Proj("+init=EPSG:27700")
        wgs84 = pyproj.Proj("+init=EPSG:4326")

        sitesList = [] #create an empty list to store the site dictionaries

        # extract the NGR number as a string
        for tag in pTags:
            text = str(tag)
            if text.startswith('<p><strong>NGR'):
                ngr = text[-16:-4].replace(" ","") #isolate the NGR code
                
                # use BNG and pyproj to change ngr into wgs84 lon/lat values
                x,y = BNG.to_osgb36(ngr)
                lon,lat = pyproj.transform(osgb36, wgs84, x, y)

                siteVertex = arcpy.Point(lon, lat) #create a point
                
            if text.startswith('<p><strong>Site Name'):
                siteName = text[31:-4] #isolate the site name

        # create a dictionary for each site
        dict = {
            "Name": siteName,
            "Location": siteVertex,
        }
        sitesList.append(dict) #add each dictionary to the list of sites

        # create an insert cursor to update the shapefile attributes
        cursor = arcpy.da.InsertCursor(hillfortFC, ('NAME','SHAPE@', 'ID'))

        # loop through the list of dictionary keys and update the shapefile attributes for each site
        for site in sitesList:
            cursor.insertRow((site['Name'], siteVertex, i))
            i += 1
        del cursor

except:
    print "Unable to populate feature class."
