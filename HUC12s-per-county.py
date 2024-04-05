import arcpy

# Set the environment workspace to the folder where your shapefiles are located
arcpy.env.workspace = "path/to/your/shapefiles"

# Specify the path to the shapefiles
ohio_counties_shp = "OH_counties.shp"
oh_huc12_shp = "OH_huc12.shp"

# Use the "Intersect" tool to find intersections between counties and HUC12 regions
intersect_output = "OH_counties_HUC12_intersect.shp"
arcpy.Intersect_analysis([ohio_counties_shp, oh_huc12_shp], intersect_output)

# Use a SearchCursor to calculate the number of HUC12s per county
huc12_per_county = {}
with arcpy.da.SearchCursor(intersect_output, ["CountyName", "HUC12"]) as cursor:
    for row in cursor:
        county_name = row[0]
        if county_name in huc12_per_county:
            huc12_per_county[county_name] += 1
        else:
            huc12_per_county[county_name] = 1

# Calculate the average number of HUC12s per county
total_huc12 = sum(huc12_per_county.values())
average_huc12_per_county = total_huc12 / len(huc12_per_county)

print(f"Average number of HUC12s per county: {average_huc12_per_county}")

# Clean up the intermediate intersect output if no longer needed
arcpy.Delete_management(intersect_output)
