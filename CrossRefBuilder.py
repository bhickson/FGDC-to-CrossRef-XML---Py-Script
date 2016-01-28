#!/usr/local/bin/python2.7

import sys, argparse, os, time
import xml.etree.ElementTree as ET
from xml.dom import minidom as md
from datetime import datetime

parser=argparse.ArgumentParser()
parser.add_argument("inputDir", help="Input Directory to search XML files for.", action="store")
parser.add_argument("outputFile", help="Output XML file in CrossRef Schema", action="store")
args = parser.parse_args()

inFolder = str(args.inputDir)
outFile = str(args.outputFile)

if not os.path.exists(inFolder):
    print "Input Directory specified does not exist.  Exiting"
    sys.exit

if not outFile.split("/")[-1].endswith(".xml"):
    print "Output File specified should have xml extension.  Renaming to " + outFile.split("/")[-1] + ".xml"
    outFile += ".xml"

if os.path.exists(outFile):
    if outFile.split("/")[-1].split(".") > 2:
        print "Output file name contains multiple '.'. Please re-run with new file name."
        sys.exit
    else:
        outFileName = outFile.split("/")[-1].split(".")[0] + "-new.xml"
        print "Specified output xml file already exists.  Renaming to " + outFileName
        outFile = "./" + outFileName

print "Input Directory: " + inFolder
print "Output XML File: " + outFile

pretty_print = lambda f: '\n'.join([line for line in md.parseString(f).toprettyxml().split('\n') if line.strip()])

def writeToFile(x):
    roughString = ET.tostring(x)
    xmlFromString = ET.fromstring(pretty_print(roughString))
    tRoot = xmlFromString.find(".")
    def getChildren(elem):
        elems = elem.findall('*')
        if len(elems) > 0:  #if any children
            for x in elems:
                getChildren(x)
        else:  #if no children
            if elem.text > 0:
                try:
                    while elem.text[0] == "\t" or elem.text[0] == " " or elem.text[0] == "\n":
                        elem.text = elem.text[1:]
                    while elem.text[-1] == "\t" or elem.text[-1] == " " or elem.text[-1] == "\n":
                        elem.text = elem.text[:-1]
                except:
		    pass
                    #print "Failed for", elem.tag  #Fails on empty tags. E.g. <ftname />
    
    getChildren(tRoot)
    ET.register_namespace("","http://www.crossref.org/schema/4.3.0")
    newTree = ET.ElementTree(xmlFromString)
    newTree.write(outFile,encoding="UTF-8")

doi_batch_Elem = ET.Element("doi_batch", {
					"version":"4.3.0",
					"xmlns":"http://www.crossref.org/schema/4.3.0",
					"xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance",
					"xsi:schemaLocation":"http://www.crossref.org/schema/4.3.0  http://www.crossref.org/schema/deposit/crossref4.3.0.xsd"})

#ALL DEFAULT HEAD INFO.  NOT DERIVED, BUT SET
head_Elem = ET.SubElement(doi_batch_Elem, "head")
doiBatchId_Elem = ET.SubElement(head_Elem, "doi_batch_id")
doiBatchId_Elem.text = "Geo Submission - " + str(datetime.now())
timestamp_Elem = ET.SubElement(head_Elem, "timestamp")
timestamp_Elem.text = time.strftime("%Y%m%d%H%M%S")
depositor_Elem = ET.SubElement(head_Elem, "depositor")
name_Elem = ET.SubElement(depositor_Elem,"name")
name_Elem.text = "Ben Hickson"
email_Elem = ET.SubElement(depositor_Elem,"email_address")
email_Elem.text = "bhickson@email.arizona.edu"
registrant_Elem = ET.SubElement(head_Elem, "registrant")
registrant_Elem.text = "University of Arizona Library, Office of Digital Innovation and Stewardship"

body_Elem = ET.SubElement(doi_batch_Elem, "body")
database_Elem = ET.SubElement(body_Elem,"database")
databaseMetadata_Elem = ET.SubElement(database_Elem,"database_metadata")
titles_Elem = ET.SubElement(databaseMetadata_Elem, "titles")
title_Elem = ET.SubElement(titles_Elem, "title")
title_Elem.text = "Spatial Data Explorer Repository"
description_Elem = ET.SubElement(databaseMetadata_Elem,"description",{"language":"en"})
description_Elem.text = "The repository collection of geospatial data hosted and maintained by the University of Arizona Library.  Vector datasets are held in a PostGIS enabled PostgreSQL database wh ile raster datasets are kept as flat files (tif)."
institution_Elem = ET.SubElement(databaseMetadata_Elem, "institution")
institutionName_Elem = ET.SubElement(institution_Elem,"institution_name")
institutionName_Elem.text = "University of Arizona Library"

fileCount = 0
for root, dirs, files in os.walk(inFolder):
    for file in files:
        if file.endswith(".xml"):
            fileCount +=1
	    print fileCount, file
            fpath = os.path.join(root,file)
            tree = ET.parse(fpath)  #Parse xml file for dataset
            treeRoot = tree.getroot()

            idinfo_Elem = treeRoot.find("idinfo")
	    timeinfo_Elem = idinfo_Elem.find("timeperd").find("timeinfo")
	    sngdate = timeinfo_Elem.find("sngdate")
	    if sngdate is not None:
		contentDate = sngdate.find("caldate").text
	    else:
		rngdates = timeinfo_Elem.find("rngdates")
		contentDate = rngdates.find("enddate").text

            citeinfo_Elem = idinfo_Elem.find("citation").find("citeinfo")
            title = citeinfo_Elem.find("title").text
            publisher = citeinfo_Elem.find("pubinfo").find("publish").text
            pubDate = citeinfo_Elem.find("pubdate").text
            originators_Elems = citeinfo_Elem.findall("origin")
            #IN FGDC SCHEMA THERE CAN BE MULTIPLE originator ELEMENTS.  HERE WE BUILD A STRING OF THEM.
            for originator in originators_Elems:
                try:
                    originators
                    originators += ", "+ originator.text
                except:
                    originators = originator.text

            descript_Elem = idinfo_Elem.find("descript")
            abstract = descript_Elem.find("abstract").text

            #IN FGDC SCHEMA THERE CAN BE MULTIPLE distinfo ELEMENTS.
            #WE NEED TO FIND THE ONE WITH resdesc element for the University of Arizona
            distinfo_Elems = treeRoot.findall("distinfo")
            for distinfo in distinfo_Elems:
                resdesc_Elem = distinfo.find("resdesc")
                if resdesc_Elem.get("PUID") == "University of Arizona Registered DOI":
                    resdesc = resdesc_Elem.text
                else:
                    """Change print to print to command line"""
                    print "FAIL Could not find resdesc element for file"
                    sys.exit()

            ftname_Elems = [elem for elem in treeRoot.getiterator() if elem.tag == "ftname" ]
            ftname = ftname_Elems[0].text
            #GET NECESSARY METADATA INFO FOR CROSSREF


            dataset_Elem = ET.Element("dataset", {"dataset_type":"other"})  #Create dataset Element External to database tag, append later

            contributors_Elem = ET.SubElement(dataset_Elem,"contributors")
            organization_Elem = ET.SubElement(contributors_Elem,"organization", {"sequence":"additional", "contributor_role":"editor"})
            organization_Elem.text = originators                     #FROM <metadata><idinfo><citation><citeinfo><origin>

            dtitles_Elem = ET.SubElement(dataset_Elem,"titles")
            dtitle_Elem = ET.SubElement(dtitles_Elem,"title")
            dtitle_Elem.text = title                                #FROM <metadata><idinfo><citation><citeinfo><title>

            databaseDate_Elem = ET.SubElement(dataset_Elem,"database_date")

	    dates = {"creation_date":contentDate, "publication_date":pubDate, "update_date":pubDate}

	    def getDate(date):
		if date == "Unknown" or date == "01" or date == None:
			return False
		if "-" in date:
			year = date.split("-")[0]
			month = date.split("-")[1]
			day = date.split("-")[2]
            	else:
                	year = date[0:4]
                	month = date[4:6]
                	day = date[6:8]

		return {"day":day,"month":month,"year":year}


	    def datesElements(dateElement):
		for key, value in sorted(dateElement.iteritems()):
			date_Elem = ET.SubElement(databaseDate_Elem, key, {"media_type":"online"})
			if not getDate(value):  #  WE MUST CREATE ALL OF THE DATE ELEMENTS (CREATION,PUBLICATION,UPDATE), OR CROSSREF INGEST WILL FAIL.  FAIL IF NO DATE FOR ANY.
				errorText = "No " + str(key) + " found for " + str(file) + " .  Publication date mandatory. Exiting..."
				sys.exit(errorText)

			if getDate(value)["month"]:
				month_Elem = ET.SubElement(date_Elem,"month")
				month = getDate(value)["month"]
				if int(month) >= 1 and int(month) <= 12:
				    	month_Elem.text = month
				else:
					errorText = "Invalid month value for " + str(key) + ".  Month must be between 1 and 31. Exiting..."
					sys.exit(errorText)			

			if getDate(value)["day"]:
			    	day_Elem = ET.SubElement(date_Elem,"day")
				day = getDate(value)["day"]
				if int(day) >= 1 and int(day) <= 31:
					print day
				    	day_Elem.text = day
				else:
					errorText = "Invalid day value for " + str(key) + ".  Day must be between 1 and 31. Exiting..."
					sys.exit(errorText)

			if getDate(value)["year"]:
			    	year_Elem = ET.SubElement(date_Elem,"year")
			    	year_Elem.text = getDate(value)["year"]

	    datesElements(dates)

            datasetDescription_Elem = ET.SubElement(dataset_Elem,"description",{"language":"en"})
            datasetDescription_Elem.text = abstract                 #FROM <metadata><idinfo><descript><abstract>

            doiData_Elem = ET.SubElement(dataset_Elem,"doi_data")
            doi_Elem = ET.SubElement(doiData_Elem,"doi")
            doi_Elem.text = resdesc                                 #FROM <metadtata><distinfo><resdesc> element
            dTimestamp_Elem = ET.SubElement(doiData_Elem,"timestamp")
            dTimestamp_Elem.text = time.strftime("%Y%m%d%H%M%S")    #GENERATED AT TIME OF WRITING
            resource_Elem = ET.SubElement(doiData_Elem, "resource")
            """THIS IS CRITICALLY CORRESPONDENT TO THE POPULATED layer_id in the Solr schema.
            Where ogp ingest would populate the LayerId value for the Solr record from the ftname
            tag, we have it set prefix the ftname value with "10.2458/azu_geo_".  So our LayerId's
            look like 10.2458/azu_geo_<ftname>.  The result of this is that OGP will build the
            direct-to-layer link from the LayerId, but translated into URI encoding
            (10.2458%2Fazu_geo_<LayerId>), so we have to build the resource value for CrossRef to
            reflect that link.  Make sense?"""

            resource_Elem.text = "https://geo.library.arizona.edu/?ogpids=10.2458%2Fazu_geo_" + ftname.lower()

            database_Elem.append(dataset_Elem)
            del originators  # Deleting originators variable because of try statement (above) will not reset originators for next file

#BEAUTIFY THE NEW XML CONTENT BEFORE WRITING TO FILE


writeToFile(doi_batch_Elem)
print "Finished"
