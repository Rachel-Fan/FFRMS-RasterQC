#-------------------------------------------------------------------------------
# Name:        FFRMS_Raster_QC_Riverine.py
# Purpose:     This tool is developed to automate raster QC checklist on FFRMS FVA rasters. 
#              All STARR II PTS Zone3 partners are authorized to use this tool for raster QC checks. 
# Author:      Rachel Fan, GISP
#              rachel.fan@stantec.com
# Version:     1.3
# Updated:     10/11/2023
# Created:     09/23/2023
# Copyright:   (c) rfan2023

#-------------------------------------------------------------------------------

import arcpy
import arcpy.sa as sa
import os
from datetime import datetime, timedelta
import sys
import traceback
import shutil
import re
import csv
import glob
   
import numpy
import math
import time
import jinja2
import pandas as pd
from arcpy.sa import *

scriptPath = os.path.dirname(__file__)
configFile = os.path.join(scriptPath, 'FFRMS_RasterQC_Configuration.xlsx')

def check_extention():
    try:
        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
            print ("Checked out \"Spatial\" Extension")
        else:
            raise LicenseError
    except LicenseError:
        print ("Spatial Analyst license is unavailable")
    except:
        print ("Exiting")

def printError():  # Function to print out error messages
    """Prints out error messages using ArcPy."""
    tb = sys.exc_info()[1]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(1) + "\n"
    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)

def retrieveConfig(sheet):  # Function to retrieve configuration data from config excel file
    """Retrieves configuration data from NPDES Key excel file."""
    # Use pandas to read excel file
    df = pd.read_excel(configFile, sheet)
    df = df[['Desc', 'Value']]
    configDict = df.set_index('Desc').to_dict(orient='index')
    return configDict

def compareExtent(raster0, raster1, raster2, raster3,tempFolder, outputFolder): #Function to compare the extent of 00FVA, 01FVA, 02 FVA and 03FVA 
    """compare raster extent between each adjecent freeboard value set: 00FVA vs 01FVA, 02FVA vs 03FVA, 02FVA vs 03FVA"""
    arcpy.env.workspace = tempFolder
     
    #convert raster to polygon
    polyFva0 = os.path.join(tempFolder, "FVA0.shp")
    raster0_int = arcpy.sa.Int(arcpy.Raster(raster0))
    arcpy.conversion.RasterToPolygon(raster0_int, polyFva0, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART") #direct output shp to temp folder
          
    polyFva1 = os.path.join(tempFolder, "FVA1.shp")
    raster1_int = arcpy.sa.Int(arcpy.Raster(raster1))
    arcpy.conversion.RasterToPolygon(raster1_int, polyFva1, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART")
    
    polyFva2 = os.path.join(tempFolder, "FVA2.shp")
    raster2_int = arcpy.sa.Int(arcpy.Raster(raster2))
    arcpy.conversion.RasterToPolygon(raster2_int, polyFva2, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART")
    
    polyFva3 = os.path.join(tempFolder, "FVA3.shp")
    raster3_int = arcpy.sa.Int(arcpy.Raster(raster3))
    arcpy.conversion.RasterToPolygon(raster3_int, polyFva3, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART")    
    
    #create extent difference shapefile by erasing the lower values from higher values
    clipFva1_0 = os.path.join(tempFolder, "clipFva1_0.shp")
    arcpy.analysis.Erase(polyFva1, polyFva0, clipFva1_0)
    diffFva1_0 = os.path.join(tempFolder, "diffFva1_0.shp")
    arcpy.management.MultipartToSinglepart(clipFva1_0, diffFva1_0)
    arcpy.management.AddField(diffFva1_0, "Area", "DOUBLE")
    #calculate area of each record and add it back to the Area field
    with arcpy.da.UpdateCursor(diffFva1_0, ["SHAPE@", "Area"]) as cursor:
        for row in cursor:
            area = row[0].area
            row[1] = area
            cursor.updateRow(row)

    #detect if lower freeboard values have larger extent by reversely erasing. Warning message is added if it occurs.
    clipFva0_1 = os.path.join(tempFolder, "clipFva0_1.shp")
    arcpy.analysis.Erase(polyFva0, polyFva1, clipFva0_1)
    diffFva0_1 = os.path.join(outputFolder, "diffFva0_1.shp")
    arcpy.management.MultipartToSinglepart(clipFva0_1, diffFva0_1)
    arcpy.management.AddField(diffFva0_1, "Area", "DOUBLE")
    #calculate area of each record and add it back to the Area field
    with arcpy.da.UpdateCursor(diffFva0_1, ["SHAPE@", "Area"]) as cursor:
        for row in cursor:
            area = row[0].area
            row[1] = area
            cursor.updateRow(row)

    # Get the count of features in the shapefile
    feature_count = int(arcpy.GetCount_management(diffFva0_1).getOutput(0))

    # Check if there are any records
    if feature_count > 0:
        diff0_1_sts = "Fail! See " + diffFva0_1 + " in Output folder for details. "
        #Define a parameter to pass this "Pass or Fail" value out of the function, and use it in Function createReport
        print("Warning! FFRMS FVA 1 raster extent is less than WSE raster extent. See diffFva0_1.shp in Output folder for details. ")
    else:
        diff0_1_sts = "Pass"
        print("FFRMS FVA01 and FVA00 extent comparison Pass!")

    clipFva2_1 = os.path.join(tempFolder, "clipFva2_1.shp")
    arcpy.analysis.Erase(polyFva2, polyFva1, clipFva2_1)
    diffFva2_1 = os.path.join(tempFolder, "diffFva2_1.shp")
    arcpy.management.MultipartToSinglepart(clipFva2_1, diffFva2_1)
    arcpy.management.AddField(diffFva2_1, "Area", "DOUBLE")
    #calculate area of each record and add it back to the Area field
    with arcpy.da.UpdateCursor(diffFva2_1, ["SHAPE@", "Area"]) as cursor:
        for row in cursor:
            area = row[0].area
            row[1] = area
            cursor.updateRow(row)

    #detect if lower freeboard values have larger extent by reversely erasing. Warning message is added if it occurs.
    clipFva1_2 = os.path.join(tempFolder, "clipFva1_2.shp")
    arcpy.analysis.Erase(polyFva1, polyFva2, clipFva1_2)
    diffFva1_2 = os.path.join(outputFolder, "diffFva1_2.shp")
    arcpy.management.MultipartToSinglepart(clipFva1_2, diffFva1_2)
    arcpy.management.AddField(diffFva1_2, "Area", "DOUBLE")
    #calculate area of each record and add it back to the Area field
    with arcpy.da.UpdateCursor(diffFva1_2, ["SHAPE@", "Area"]) as cursor:
        for row in cursor:
            area = row[0].area
            row[1] = area
            cursor.updateRow(row)

    # Get the count of features in the shapefile
    feature_count1 = int(arcpy.GetCount_management(diffFva1_2).getOutput(0))

    # Check if there are any records
    if feature_count1 > 0:
        #Define a parameter to pass this "Pass or Fail" value out of the function, and use it in Function createReport
        diff1_2_sts = "Fail! See " + diffFva1_2 + " in Output folder for details. "
        print("Warning! FFRMS FVA 2 raster extent is less than FFRMS FVA 1 raster extent. See diffFva1_2.shp in Output folder for details. ")#Please refine the wording as needed. 
    else:
        diff1_2_sts = "Pass"
        print("FFRMS FVA02 and FVA01 extent comparison Pass!")

    clipFva3_2 = os.path.join(tempFolder, "clipFva3_2.shp")
    arcpy.analysis.Erase(polyFva3, polyFva2, clipFva3_2)
    diffFva3_2 = os.path.join(tempFolder, "diffFva3_2.shp")
    arcpy.management.MultipartToSinglepart(clipFva3_2, diffFva3_2)
    arcpy.management.AddField(diffFva3_2, "Area", "DOUBLE")
    #calculate area of each record and add it back to the Area field
    with arcpy.da.UpdateCursor(diffFva3_2, ["SHAPE@", "Area"]) as cursor:
        for row in cursor:
            area = row[0].area
            row[1] = area
            cursor.updateRow(row)

    #detect if lower freeboard values have larger extent by reversely erasing. Warning message is added if it occurs.
    clipFva2_3 = os.path.join(tempFolder, "clipFva2_3.shp")
    arcpy.analysis.Erase(polyFva2, polyFva3, clipFva2_3)
    diffFva2_3 = os.path.join(outputFolder, "diffFva2_3.shp")
    arcpy.management.MultipartToSinglepart(clipFva2_3, diffFva2_3)
    arcpy.management.AddField(diffFva2_3, "Area", "DOUBLE")
    #calculate area of each record and add it back to the Area field
    with arcpy.da.UpdateCursor(diffFva2_3, ["SHAPE@", "Area"]) as cursor:
        for row in cursor:
            area = row[0].area
            row[1] = area
            cursor.updateRow(row)

    # Get the count of features in the shapefile
    feature_count2 = int(arcpy.GetCount_management(diffFva2_3).getOutput(0))

    # Check if there are any records
    if feature_count2 > 0:
        #Define a parameter to pass this "Pass or Fail" value out of the function, and use it in Function createReport
        diff2_3_sts = "Fail! See " + diffFva2_3 + " in Output folder for details. "
        print("Warning! FFRMS FVA 3 raster extent is less than FFRMS FVA 2 raster extent. See diffFva2_3.shp in Output folder for details. ")#Please refine the wording as needed. 
    else:
        diff2_3_sts = "Pass"
        print("FFRMS FVA03 and FVA02 extent comparison Pass!")   
        
    return diff0_1_sts, diff1_2_sts, diff2_3_sts

def compareExtent02(raster0, raster02, tempFolder, outputFolder):
    arcpy.env.workspace = tempFolder
    #convert raster to polygon
    polyFva0 = os.path.join(tempFolder, "FVA0.shp")
    raster0_int = arcpy.sa.Int(arcpy.Raster(raster0))
    arcpy.conversion.RasterToPolygon(raster0_int, polyFva0, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART") #direct output shp to temp folder
    
    polyFva02 = os.path.join(tempFolder, "FVA02.shp")
    raster02_int = arcpy.sa.Int(arcpy.Raster(raster02))
    arcpy.conversion.RasterToPolygon(raster02_int, polyFva02, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART") #direct output shp to temp folder
    #print("Raster 0.2% to Polygon done at " + polyFva02)
    
    clipFva0_02 = os.path.join(tempFolder, "clipFva0_02.shp")
    arcpy.analysis.Erase(polyFva0, polyFva02, clipFva0_02)
    diffFva0_02 = os.path.join(outputFolder, "diffFva0_02.shp")
    arcpy.management.MultipartToSinglepart(clipFva0_02, diffFva0_02)
    arcpy.management.AddField(diffFva0_02, "Area", "DOUBLE")
    #calculate area of each record and add it back to the Area field
    with arcpy.da.UpdateCursor(diffFva0_02, ["SHAPE@", "Area"]) as cursor:
        for row in cursor:
            area = row[0].area
            row[1] = area
            cursor.updateRow(row)

    clipFva02_0 = os.path.join(tempFolder, "clipFva02_0.shp")
    arcpy.analysis.Erase(polyFva02, polyFva0, clipFva02_0)
    diffFva02_0 = os.path.join(tempFolder, "diffFva02_0.shp")
    arcpy.management.MultipartToSinglepart(clipFva02_0, diffFva02_0)
    arcpy.management.AddField(diffFva02_0, "Area", "DOUBLE")
    #calculate area of each record and add it back to the Area field
    with arcpy.da.UpdateCursor(diffFva02_0, ["SHAPE@", "Area"]) as cursor:
        for row in cursor:
            area = row[0].area
            row[1] = area
            cursor.updateRow(row)

    # Get the count of features in the shapefile
    feature_count_02 = int(arcpy.GetCount_management(diffFva0_02).getOutput(0))

    # Check if there are any records
    if feature_count_02 > 0:
        diff02_0_sts = "Fail! See " + diffFva0_02 + " in Output folder for details. "
        #Define a parameter to pass this "Pass or Fail" value out of the function, and use it in Function createReport
        print("Warning! FFRMS FVA00 raster extent is less than 0.2 PCT raster extent. See diffFva0_02.shp in Output folder for details. ")
    else:
        diff02_0_sts = "Pass"
        print("FFRMS FVA00 and 0.2 PCT raster extent comparison Pass!")
        
    return diff02_0_sts

def compareCellvalue(raster0, raster1, raster2, raster3, tempFolder, outputFolder):
    """run cell size compare on each raster"""
    try:
        
        minus1 = RasterCalculator([raster0, raster1], ["x","y"], "y-x", "UnionOf","FirstOf")
        minus1.save(os.path.join(tempFolder, "minus1"))

        minus2 = RasterCalculator([raster1, raster2], ["x","y"], "y-x", "UnionOf","FirstOf")
        minus2.save(os.path.join(tempFolder, "minus2"))
        
        minus3 = RasterCalculator([raster2, raster3], ["x","y"], "y-x", "UnionOf","FirstOf")
        minus3.save(os.path.join(tempFolder, "minus3.tif"))
        print("3 math calculation on rasters are complete.")

        reclas1 = arcpy.sa.Reclassify(minus1, "Value", RemapRange([[-1,0.95,1],[0.95,1.05,0],[1.05,10,1]]))
        reclas1.save(os.path.join(tempFolder, "reclassify1"))
        reclas2 = arcpy.sa.Reclassify(minus2, "Value", RemapRange([[-1,0.95,1],[0.95,1.05,0],[1.05,10,1]]))
        reclas2.save(os.path.join(tempFolder, "reclassify2"))
        reclas3 = arcpy.sa.Reclassify(minus3, "Value", RemapRange([[-1,0.95,1],[0.95,1.05,0],[1.05,10,1]]))
        reclas3.save(os.path.join(tempFolder, "reclassify3"))
        
        print("3 reclassify complete.") 
    except:
        print("Could not compare the cell values.")
    return reclas1, reclas2, reclas3

    
def compareCellvalue02(raster0, raster02, tempFolder, outputFolder):
    """run cell size compare on each raster"""
    try:
        
        minus1 = RasterCalculator([raster02, raster0], ["x","y"], "y-x", "UnionOf","FirstOf")
        minus1.save(os.path.join(tempFolder, "minus02"))

        reclas02 = arcpy.sa.Reclassify(minus1, "Value", RemapRange([[-1,0.95,1],[0.95,1.05,0],[1.05,10,1]]))
        reclas02.save(os.path.join(tempFolder, "reclassify02"))
        
        #print("reclassify02 is generated.") 
    except:
        print("Could not compare the cell values.")
    return reclas02  

def convertToshp(reclas1, reclas2, reclas3, tempFolder, outputFolder):
    '''convert raster minus result to shapefile using reclassify'''
    try:
        cellDiff1_0 = os.path.join(tempFolder, "cellDiff1_0.shp")
        reclas1_poly = os.path.join(tempFolder, "reclas1_poly.shp")
        arcpy.conversion.RasterToPolygon(reclas1, cellDiff1_0, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART")
        #arcpy.management.Dissolve(reclas1_poly, cellDiff1_0, "gridcode", None, "MULTI_PART","DISSOLVE_LINES","")
        print("cellDiff1_0 created! ")
        
        cellDiff2_1 = os.path.join(tempFolder, "cellDiff2_1.shp")
        reclas2_poly = os.path.join(tempFolder, "reclas2_poly.shp")
        arcpy.conversion.RasterToPolygon(reclas2, reclas2_poly, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART")
        arcpy.management.Dissolve(reclas2_poly, cellDiff2_1, "gridcode", None, "MULTI_PART","DISSOLVE_LINES","")
        print("cellDiff2_1 created! ")
        
        cellDiff3_2 = os.path.join(tempFolder, "cellDiff3_2.shp")
        reclas3_poly = os.path.join(tempFolder, "reclas3_poly.shp")
        arcpy.conversion.RasterToPolygon(reclas3, reclas3_poly, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART")
        arcpy.management.Dissolve(reclas3_poly, cellDiff3_2, "gridcode", None, "MULTI_PART","DISSOLVE_LINES","")
        print("cellDiff3_2 created! ")
    except:
        print("Could not convert to shapefiles!")
        printError()
    return cellDiff1_0, cellDiff2_1, cellDiff3_2
    
def convertToshp02(reclas02, tempFolder, outputFolder):
    '''convert raster minus result to shapefile using reclassify'''
    try:
        cellDiff0_02 = os.path.join(tempFolder, "cellDiff0_02.shp")
        reclas1_poly = os.path.join(tempFolder, "reclas02_poly.shp")
        arcpy.conversion.RasterToPolygon(reclas02, cellDiff0_02, "NO_SIMPLIFY","","MULTIPLE_OUTER_PART")
        print("cellDiff0_02 created! ")
        
    except:
        print("Could not convert to shapefiles!")
        printError()
    return cellDiff0_02

def extractCellValue(cellDiff1_0, in_raster0, in_raster1, tempFolder, outputFolder):
    '''convert raster minus result to shapefile using reclassify'''
    try:
        templayer = os.path.join(tempFolder, "templayer.lyr")
        arcpy.management.MakeFeatureLayer(cellDiff1_0, templayer)        # Run SelectLayerByAttribute to determine which features to delete
        arcpy.management.SelectLayerByAttribute(templayer, "NEW_SELECTION", '"gridcode" = 1')
        cellDiff1_0_cp = os.path.join(tempFolder, "cellDiff1_0_cp.shp")
        arcpy.CopyFeatures_management(templayer, cellDiff1_0_cp)
        cellDiff1_0_cp_multi = os.path.join(tempFolder, "cellDiff1_0_cp_multi.shp")
        arcpy.management.MultipartToSinglepart(cellDiff1_0_cp, cellDiff1_0_cp_multi)
        
        points_records_no = int(arcpy.GetCount_management(cellDiff1_0_cp_multi).getOutput(0))
        if points_records_no == 0:
            cellDiff1_0_pts = os.path.join(outputFolder, f'cellDiff{str (cellDiff1_0)[-7:-4]}_pts.shp')
            arcpy.CreateFeatureclass_management(outputFolder, f'cellDiff{str (cellDiff1_0)[-7:-4]}_pts.shp', "POINT")
            
        else:       
            cellDiff1_0_pts = os.path.join(outputFolder, f'cellDiff{str (cellDiff1_0)[-7:-4]}_pts.shp')
            arcpy.management.FeatureToPoint(cellDiff1_0_cp_multi, cellDiff1_0_pts, "INSIDE")
            FieldName_lower = re.search(r"\d+FVA", str(in_raster0)).group()
            FieldName_higher = re.search(r"\d+FVA", str(in_raster1)).group()
            #print(str(FieldName_lower),str(FieldName_higher))

            arcpy.sa.ExtractMultiValuesToPoints(cellDiff1_0_pts, [[in_raster0,FieldName_lower], [in_raster1,FieldName_higher]], "NONE")
            #print('ExtractMultiValuesToPoints is done')
            arcpy.management.AddField(cellDiff1_0_pts, "ValueDiff", "FLOAT")
            #print("Add field is done")
            field1 = str(FieldName_lower)
            field2 = str(FieldName_higher)
            arcpy.management.CalculateField(cellDiff1_0_pts, "ValueDiff", f"!{field2}! - !{field1}!") 
            #print('calculate field done')
    except:
        print("Could not convert to points!")
        printError()
    return cellDiff1_0_pts

def extractCellValue02(cellDiff1_0, in_raster0, in_raster1, tempFolder, outputFolder):
    '''convert raster minus result to shapefile using reclassify'''
    try:
        templayer = os.path.join(tempFolder, "templayer.lyr")
        arcpy.management.MakeFeatureLayer(cellDiff1_0, templayer)        # Run SelectLayerByAttribute to determine which features to delete
        arcpy.management.SelectLayerByAttribute(templayer, "NEW_SELECTION", '"gridcode" = 1')
        cellDiff1_0_cp = os.path.join(tempFolder, "cellDiff1_0_cp.shp")
        arcpy.CopyFeatures_management(templayer, cellDiff1_0_cp)
        cellDiff1_0_cp_multi = os.path.join(tempFolder, "cellDiff1_0_cp_multi.shp")
        arcpy.management.MultipartToSinglepart(cellDiff1_0_cp, cellDiff1_0_cp_multi)

        points_records_no = int(arcpy.GetCount_management(cellDiff1_0_cp_multi).getOutput(0))
        if points_records_no == 0:
            cellDiff1_0_pts = os.path.join(outputFolder, f'cellDiff{str (cellDiff1_0)[-7:-4]}_pts.shp')
            arcpy.CreateFeatureclass_management(outputFolder, f'cellDiff{str (cellDiff1_0)[-7:-4]}_pts.shp', "POINT")
            
        else:       
            cellDiff1_0_pts = os.path.join(outputFolder, f'cellDiff{str (cellDiff1_0)[-7:-4]}_pts.shp')
            arcpy.management.FeatureToPoint(cellDiff1_0_cp_multi, cellDiff1_0_pts, "INSIDE")
            
            FieldName_lower = "0_" + re.search(r"\d+PCT", str(in_raster0)).group()
            FieldName_higher = re.search(r"\d+FVA", str(in_raster1)).group()
            #print(str(FieldName_lower),str(FieldName_higher))

            arcpy.sa.ExtractMultiValuesToPoints(cellDiff1_0_pts, [[in_raster0,FieldName_lower], [in_raster1,FieldName_higher]], "NONE")
            arcpy.management.AddField(cellDiff1_0_pts, "ValueDiff", "FLOAT")
            field1 = str(FieldName_lower)
            field2 = str(FieldName_higher)
            arcpy.management.CalculateField(cellDiff1_0_pts, "ValueDiff", f"!{field2}! - !{field1}!") 
            #print('calculate field done')
        
    except:
        print("Could not convert to points!")
        printError()
    return cellDiff1_0_pts
        
def reportCellComp(cellDiffPts):
    '''convert raster minus result to shapefile using reclassify'''
    try:
        # Get the count of features in the shapefile
        feature_count = int(arcpy.GetCount_management(cellDiffPts).getOutput(0))

        # Check if there are any records
        if feature_count > 0:
            celldiff1_0_sts = "Fail! See " + cellDiffPts + " in Output folder for details. "
            #Define a parameter to pass this "Pass or Fail" value out of the function, and use it in Function createReport
            print("Warning! There are cells of higher freeboard value that are less than lower freeboard value. See " + cellDiffPts + " in Output folder for details. ")
        else:
            celldiff1_0_sts = "Pass"
            print("Pass.")
    except:
        print("Could not convert to points!")
    return celldiff1_0_sts

def getRasterProperties(in_Raster):
    
    r = sa.Raster(in_Raster)
    # check spatial references are defined
    if r.spatialReference:
        sr_name = r.spatialReference.name
    else:
        sr_name = 'Not Defined'
	
    if r.spatialReference.VCS:
        vcs_name = r.spatialReference.VCS.name
    else:
        vcs_name = 'Not Defined'

    raster_properties = [
        r.name, #QC R3
        r.pixelType,#QC R4
        round(r.meanCellHeight,5),  #QC R6
        sr_name,    #QC R7
        vcs_name #QC R8
    ]
    return raster_properties
     
    

def generate_csv(in_raster0, in_raster1, in_raster2,in_raster3, in_raster02, output_csv):
    # Output CSV file

    # Write the data to the CSV file
    try:
        
        csvheader = ['Name',
            'Pixel_Type',
            'Cell_Size',
            'Spatial_Reference',
            'Vertical_Datum',
            '',
            '',
            '3 FVA rasters extents compare',
            '3 FVA rasters cells value compare',
            'pbl(still developing)'       
            ]

        qclist = ['R3',
            'R4',
            'R6',
            'R7',
            'R8',
            '',
            '',
            'R11',
            'R14',
            'R17'
            ]          
    except:
        print("Could not create CSV")
    
    with open(output_csv, 'w', newline='') as csv_file:
        # Write header
        try:
            csv_file.write('AttributeName,QC checklist item,FVA0 Raster properties, FVA1 Raster properties, FVA2 Raster properties, FVA3 Raster properties, 0.2PCT Raster properties\n')

            # Write data rows for column 1 and column 2
            csv_writer = csv.writer(csv_file)
            #
            for item1, item2, item3, item4, item5, item6, item7 in zip(csvheader,qclist, in_raster0,in_raster1,in_raster2,in_raster3, in_raster02):
                #row_str = f'{column1_data[i][0], {column1_data[1][i]}}\n'
                csv_writer.writerow([item1, item2,item3, item4, item5,item6, item7])
            print("Data written to CSV:", output_csv)
        except:
            print("Could not write to CSV")

def generate_csv_wo02(in_raster0, in_raster1, in_raster2,in_raster3, output_csv):
    # Output CSV file

    # Write the data to the CSV file
    try:
        
        csvheader = ['Name',
            'Pixel_Type',
            'Cell_Size',
            'Spatial_Reference',
            'Vertical_Datum',
            '',
            '',
            '3 FVA rasters extents compare',
            '3 FVA rasters cells value compare',
            'pbl(still developing)'       
            ]

        qclist = ['R3',
            'R4',
            'R6',
            'R7',
            'R8',
            '',
            '',
            'R11',
            'R14',
            'R17'
            ]          
    except:
        print("Could not create CSV")



    
    with open(output_csv, 'w', newline='') as csv_file:
        # Write header
        try:
            csv_file.write('AttributeName,QC checklist item,FVA0 Raster properties, FVA1 Raster properties, FVA2 Raster properties, FVA3 Raster properties\n')

            # Write data rows for column 1 and column 2
            csv_writer = csv.writer(csv_file)
            for item1, item2, item3, item4, item5, item6 in zip(csvheader,qclist, in_raster0,in_raster1,in_raster2,in_raster3):
                #row_str = f'{column1_data[i][0], {column1_data[1][i]}}\n'
                csv_writer.writerow([item1, item2,item3, item4, item5,item6])
            print("Data written to CSV:", output_csv)
        except:
            print("Could not write to CSV")

#-------------------------------------------------------------------------------
#Main functions start from here
#-------------------------------------------------------------------------------


#Record start time using current time
start_time = time.time()
now = datetime.now()
current_time = time.strftime("%m-%d %X",time.localtime())
print("Start processing at ",current_time)
   
try:
    
    # Check Spatial Analyst extention
    check_extention()

    #Define input and output parameters
    arcpy.env.overwriteOutput = True
    config = retrieveConfig("RasterCompare")
    
    raster0 = arcpy.Raster(config['FVA0 input raster']['Value'])
    raster1 = config['FVA1 input raster']['Value']
    raster2 = config['FVA2 input raster']['Value']
    raster3 = config['FVA3 input raster']['Value']
    raster02 = config['FFRMS 0.2% ACF raster']['Value']
    print(raster02)
    if pd.notna(raster02):
        print("All 5 rasters have been read by the tool!")
    else:
        print("No valid 0.2 % raster was found. Tool will only QC 4 existing rasters.")
    
    tempFolder = os.path.join(scriptPath, 'Temp')
    outputFolder = os.path.join(scriptPath, 'Output')
    #outputFolder = config['OutputDirectory']['Value']
    outputCSVName = config['OutputSpreadSheet']['Value']
    outputCSV = os.path.join(scriptPath, outputCSVName + ".csv")
    
    print('')
    print('********************************')
    print('Import config file successfully')
    print('********************************')
        
    
    try:
        
        print('')
        print('********************************')
        print('Initializing compare extent')
        diff0_1_sts, diff1_2_sts, diff2_3_sts = compareExtent(raster0, raster1, raster2, raster3, tempFolder, outputFolder)
        if pd.notna(raster02):
            diff02_0_sts = compareExtent02(raster0, raster02, tempFolder, outputFolder)
        
        print('Compare raster extent successfully completed.')
        print('********************************')

    except:

        print('')
        print('********************************')
        print('Error in compare extent...')
        print('********************************')
        
    try:
    
        print('')
        print('********************************')
        print('Initializing comparing cell values')
        reclas1, reclas2, reclas3 = compareCellvalue(raster0, raster1, raster2, raster3, tempFolder, outputFolder)
        if pd.notna(raster02):
            reclas02 = compareCellvalue02(raster0, raster02, tempFolder, outputFolder)
        
        print('Comparing cell values successfully completed.')
        print('********************************')

    except:

        print('')
        print('********************************')
        print('Error in comparing cell values...')
        print('********************************')
    
    
    try:
    
        print('')
        print('********************************')
        print('Initializing exporting cell value difference shapefiles')
        #run convertToShp to convert reclassified rasters to shapefiles
        cellDiff1_0, cellDiff2_1, cellDiff3_2 = convertToshp(reclas1, reclas2, reclas3, tempFolder, outputFolder)
        if pd.notna(raster02):
            cellDiff0_02 = convertToshp02(reclas02, tempFolder, outputFolder)
        #print('Function convertToShp is complete')
        
        #extract cell values from both lower and higher FVA rasters to result shapefiles
        cellDiff1_0_pts = extractCellValue(cellDiff1_0, raster0, raster1, tempFolder, outputFolder) #test only FVA1 vs FVA0, will add other occurances later
        cellDiff2_1_pts = extractCellValue(cellDiff2_1, raster1, raster2, tempFolder, outputFolder)
        cellDiff3_2_pts = extractCellValue(cellDiff3_2, raster2, raster3, tempFolder, outputFolder)
        if pd.notna(raster02):
            cellDiff0_02_pts = extractCellValue02(cellDiff0_02, raster02, raster0, tempFolder, outputFolder)
        #print('Function extractCellValue  is complete')
        
        #get the PASS/FAIL status of cell value comparison result 
        celldiff1_0_sts = reportCellComp(cellDiff1_0_pts) 
        celldiff2_1_sts = reportCellComp(cellDiff2_1_pts)
        celldiff3_2_sts = reportCellComp(cellDiff3_2_pts)
        if pd.notna(raster02):
            celldiff0_02_sts = reportCellComp(cellDiff0_02_pts)
        #print('Function reportCellComp is complete')
         
        print('Cell value difference result successfully exported.')
        print('********************************')
   
    except:

        print('')
        print('********************************')
        print('Error in exporting cell value difference shapefiles...')
        print('********************************')


    try:
    
        print('')
        print('********************************')
        print('Initializing extracting properties of FVA rasters based on QC checklist')
        raster0_properties = getRasterProperties(raster0)
        raster1_properties = getRasterProperties(raster1)
        raster2_properties = getRasterProperties(raster2)
        raster3_properties = getRasterProperties(raster3)

        if pd.notna(raster02):
            raster02_properties = getRasterProperties(raster02)
        
        print('Raster properties of FVA rasters successfully extracted.')
        print('********************************')

    except:

        print('')
        print('********************************')
        print('Error in extracting of FVA rasters properties...')
        print('********************************')

    try:
        print('')
        print('********************************')
        print('Initializing creating QC result csv')
        raster0_properties.extend(("","01FVA vs 00FVA", diff0_1_sts, celldiff1_0_sts, "TBD"))
        raster1_properties.extend(("","02FVA vs 01FVA", diff1_2_sts, celldiff2_1_sts,  "TBD"))
        raster2_properties.extend(("","03FVA vs 02FVA",diff2_3_sts, celldiff3_2_sts,  "TBD"))
        if pd.notna(raster02):
            raster3_properties.extend(("","","", "", ""))
            raster02_properties.extend(("","02PCT vs 00FVA", diff02_0_sts, celldiff0_02_sts, ""))
        else:
            raster3_properties.extend(("","","", "", ""))

        if pd.notna(raster02):
            generate_csv(raster0_properties,raster1_properties,raster2_properties,raster3_properties, raster02_properties, outputCSV)
        else:
            generate_csv_wo02(raster0_properties,raster1_properties,raster2_properties,raster3_properties, outputCSV)
        
        print('QC result csv successfully created.')
        print('********************************')

    except:

        print('')
        print('********************************')
        print('Error in creating QC result csv...')
        print('********************************')
  
except:

    print('')
    print('********************************')
    print('Error in reading config file...')
    print('********************************')

finally:
    print('')
    print('********************************')
    arcpy.CheckInExtension("Spatial")
    print("Spatial Extension checked in")   
    finish_time = time.time()
    time_period = str(timedelta(seconds=(finish_time - start_time)))
    print("Finish processing at ", current_time)
    print("The tool has been running for ", time_period)
