# FFRMS-RasterQC
The Raster Quality Control Tool is a Python script that helps you compare and analyze raster datasets in a geographic information system (GIS) environment using ArcGIS's Spatial Analyst extension. This manual provides an overview of the tool and comprehensive instructions on its effective utilization.

**Introduction**
The Raster Quality Control Tool is a Python script that helps you compare and analyze raster datasets in a geographic information system (GIS) environment using ArcGIS's Spatial Analyst extension. This manual provides an overview of the tool and instructions on how to use it effectively.

1.	Getting Started
- Prerequisites
  Before using the Raster Quality Control Tool, ensure you have the following prerequisites in place:
  •	ArcGIS with Spatial Analyst Extension: Ensure that ArcGIS software with the Spatial Analyst extension is installed and licensed on your system.
  •	Python: The tool is written in Python; ensure Python 3.x is installed on your system.
  
- Installation
      No specific installation is required. Please follow the instructions in Section 3 to run the script.

2.	Tool Overview
- Purpose
  The Raster Quality Control Tool is designed to compare raster datasets, particularly Flood Fractionation Raster (FFR) datasets, to ensure their quality and accuracy. It performs the following key functions:
    o	Compares the extent of different raster datasets.
    o	Compares cell values between raster datasets.
    o	Generates reports and exports results to CSV files.
_Note_: This tool is primarily developed for riverine raster datasets. While it is generally compatible with coastal datasets, complexities might arise. Most coastal comparisons yield consistent results, but some scenarios may need individual attention due to inherent coastal methodology differences.
  
- Key Features
  o	Automated Comparison: The tool automatically compares raster extents and cell values, reducing the need for manual analysis.
  o	Extensive Reporting: It generates detailed reports and outputs CSV files summarizing the results.
  o	User-Friendly: The script is designed to be easy to use and understand, even for users with minimal programming experience.
  
- Supported Formats
  The tool is designed to work with raster datasets in the ArcGIS environment. It supports various raster formats, including TIFF, GRID, and others supported by ArcGIS.
  
3.	Using the Tool
- Setting up folder structure 
  Follow these steps to set up the script running environment:
    1.	Copy the unzipped FFRMS_Raster_QC_Tool folder to your designated path (with > 20GB free disk space). You will see 2 files (script: FFRMS_RasterQC_1.3.py; configure: FFRMS_RasterQC_Configuration.xlsx) and 2 empty folders (Output/Temp) in this folder.
       ![image](https://github.com/Rachel-Fan/FFRMS-RasterQC/assets/9139057/cb20545e-6304-4572-971b-9614ec706fcf)

    2.	Open FFRMS_RasterQC_Configuration.xlsx and set up input data (including path, name and extension) and output CSV file name.
       a.	Input full folder path of the rasters, including extension in the “Value” field
       b.	If 0.2% ACF raster is not appliable in your study, leave it blank. You may use “Backspace” on your keyboard to ensure nothing (including space) is in this cell.
       c.	For OutputSpreadSheet, type name only. The CSV file will be created under the script folder.
    Note that the input raster needs to be in the folder. Geodatabase is not working for current version of the tool. 
       ![image](https://github.com/Rachel-Fan/FFRMS-RasterQC/assets/9139057/8061b798-9352-40bc-94db-82d8dea05519)

- Running the Script
  1.	Right click on _FFRMS_RasterQC_V1.3.py_ and click “Edit with IDLE (ArcGIS Pro). Once the script is open,  there are 2 options to start the script:
      a.	press F5 on the keyboard 
      b.	click ”Run” dropdown from the Menu bar and choose “Run Module” option. 
  2. A new IDLE Shell window should pop up, which means the tool is successfully started. It takes about 20 minutes for my pilot study area to process.
          ![image](https://github.com/Rachel-Fan/FFRMS-RasterQC-Riverine/assets/9139057/1132aa4f-1a00-4336-ad85-13044b619c79)
  3.	After completion, a new CSV file will be created in the same folder as the script, named according to the configuration file.
  4.	The Output folder contains shapefiles displaying differences in raster extents and cell values. These shapefiles can be used to visualize areas of discrepancies.
  5.	The Temp folder contains intermediate files of the geoprocessing procedures, useful for checking specific steps of the script.

- Output Files
  The tool generates several output files:
  •	Shapefiles: Shapefiles containing differences in raster extents and cell values. Specifically if one QC check is failed, user can use the result shapefile to visualize the fail spots.
  •	A CSV Report: Detailed reports summarizing the raster properties and comparison results.
    ![image](https://github.com/Rachel-Fan/FFRMS-RasterQC-Riverine/assets/9139057/df2ea2e6-221e-4354-9c2f-315332a02c02)

- Understanding the Results
The tool provides pass/fail status for various comparisons, such as extent comparisons (e.g., 00FVA vs. 01FVA) and cell value comparisons. Here's how to interpret the results:
•	Extent Comparisons: 
o	A "Pass" indicates the extent of the higher FVA raster is greater than the lower FVA raster. 
o	A "Fail" suggests the extent of the lower FVA raster is greater.
	If a fail occurs, a polygon shapfile “diff[lowerFVA]_[higherFVA].shp” is created in the output folder. The shapefile contains the areas that fail the check. An Area field is added to represent the area of each polygon. It can be used to sort and identify the large failing areas. 
	e.g. if FVA2 has some extent which FVA3 doesn’t cover, a diff2_3.shp is created containing these failing areas. 
•	Cell Value Comparisons:
o	A "Pass" indicates that all cell values in the higher FVA raster are 1 foot greater than those in the lower FVA raster. To account for calculation system errors, the algorithm uses a range of 0.95-1.05 to represent a 1-foot difference.
o	A "Fail" indicates that there are cells where the difference in cell values between the higher FVA raster and the lower FVA raster is greater or less than 1 foot. In the algorithm, values >1.05 and <0.95 are used to represent a 1-foot difference, eliminating calculation system errors.
	If a fail occurs, a points shapfile “celldiff[higherFVA]_[lowerFVA])pts.shp” is created in the Output folder. The shapefile contains the points that fail the check. The attribute table of the shapefiles contains the following fields: lowerFVA cell value, higherFVA cell value, and cell value difference. 
	e.g. if some cells of FVA1 has lower elevation compared with FVA0, a celldiff1_0_pts.shp is created containing these failing points.

4.  What to self-check when the tool fails?
   •	Check your free space of disk the tool locates. The total size of 5 rasters of my pilot study is less than  1G, however the intermediate files created by the tool takes over 20GB. 
  •  	Close ArcGIS Pro if you opened the raster data or the results data in it. Sometimes removing the data from ArcGIS Pro may not release the lock/
  •	If the tool is running a second time, ensure the IDLE window (showing your tool results) from your 1st time run is closed. 

5.	Contact Information

    For support, feedback, or inquiries about this Raster Quality Control Tool, please contact:
  	Rachel Fan (rachel.fan@stantec.com)
