# ----------------------------------------------------------------------------
# Preparing FAOSTAT data for creating SIMPLE database
# Coded by UBaldos 07-05-2017
# ----------------------------------------------------------------------------
# This code creates country level data which will be aggregated later
# via a GEMPACK program
#
# =============================== #
# General processing for all data #
# =============================== #
#

# ----- clear R memorylist
rm(list=ls())

# fetch command line arguments specifying:
# 1. Start year
# 2. End year
# 3. input directory containing FAOSTAT CSVs
# 4. output directory
# 5. region map csv
# 6. region sets csv
# 7. crop sets csv
# 8. livestock sets csv
args <-  commandArgs(trailingOnly=TRUE)

start_year_str = args[1]
end_year_str = args[2]
input_dir = toString(args[3])
output_dir = toString(args[4])
reg_map_csv = toString(args[5])
reg_csv = toString(args[6])
crop_csv = toString(args[7])
livestock_csv = toString(args[8])

# create a temp dir to hold intermediate outputs
temp_dir = paste(output_dir,"temp",sep="/")
dir.create(temp_dir)

# determine years of processing
start_year <- as.numeric(start_year_str)
end_year <- as.numeric(end_year_str)
years     <- seq(start_year,end_year,1) # start year and end year

# read in static input files
country   <- read.csv(reg_csv) #reg_sets.csv
country   <- country[,1]
crop      <- read.csv(crop_csv) #crop_sets.csv
crop      <- crop[,1]
livestock <- read.csv(livestock_csv) #livestock_sets.csv
livestock <- livestock[,1]

# ======================== #
# Data specific processing #
# ======================== #
# These codes do the following:
#   Read data, get subset data depending on year and variable of interest as well as
#   SIMPLE country and crop coverage. Then drop observations with NA values for each
#   and finally write filtered data

# 	Arable land and Permanent crops
# ----- Filter data to get GDP (Item.Code) in 2005 USD (Element.Code) and re-write file

# first setup file paths
input_file = paste(input_dir,"Inputs_LandUse_E_All_Data_(Normalized).csv",sep="/")
temp_file = paste(temp_dir, "00_cropland.csv",sep="/")
qland_out = paste(temp_dir, "QLAND.csv",sep="/")

datatable  <- read.csv(input_file)
datatable2 <- subset(datatable, select=c("Area.Code", "Item.Code", "Element.Code", "Year.Code", "Value"))
datatable2 <- subset(datatable2,  Item.Code==6620)
datatable2 <- subset(datatable2,  Element.Code==5110)
datatable2 <- datatable2[datatable2$ Area.Code %in% country,]
datatable2 <- datatable2[datatable2$Year %in% years,]
datatable2 <- subset(datatable2, select=c("Area.Code", "Year.Code", "Value"))
datatable2 <- datatable2[complete.cases(datatable2),]
write.csv(datatable2,temp_file, row.names=FALSE )
names(datatable2) <- c("CNTRY","YEAR","QLAND")
write.csv(datatable2, qland_out, row.names=FALSE )


# GDP in 2015 USD
# ----- Filter data to get GDP (Item.Code) in 2005 USD (Element.Code) and re-write file

input_file = paste(input_dir,"Macro-Statistics_Key_Indicators_E_All_Data_(Normalized).csv",sep="/")
temp_file = paste(temp_dir, "00_realgdp.csv",sep="/")
inc_out = paste(temp_dir, "INC.csv",sep="/")

datatable  <- read.csv(input_file)
datatable2 <- subset(datatable, select=c("Area.Code", "Item.Code", "Element.Code", "Year.Code", "Value"))
datatable2 <- subset(datatable2,  Item.Code==22008)
datatable2 <- subset(datatable2,  Element.Code==6184)
datatable2 <- datatable2[datatable2$ Area.Code %in% country,]
datatable2 <- datatable2[datatable2$Year %in% years,]
datatable2 <- subset(datatable2, select=c("Area.Code", "Year.Code", "Value"))
datatable2 <- datatable2[complete.cases(datatable2),]
write.csv(datatable2,temp_file, row.names=FALSE )
names(datatable2) <- c("CNTRY","YEAR","INC")
write.csv(datatable2, inc_out, row.names=FALSE )

# Population
# ----- Filter data to get Total Population (Element.Code) & Rename Country.Code to Area.Code

input_file = paste(input_dir,"Population_E_All_Data_(Normalized).csv",sep="/")
temp_file = paste(temp_dir, "00_population.csv",sep="/")
pop_out = paste(temp_dir, "POP.csv",sep="/")

datatable  <- read.csv(input_file)
datatable2 <- subset(datatable, select=c("Area.Code", "Item.Code", "Element.Code", "Year.Code", "Value"))
datatable2 <- subset(datatable2,  Item.Code==3010)
datatable2 <- subset(datatable2,  Element.Code==511)
datatable2 <- datatable2[datatable2$ Area.Code %in% country,]
datatable2 <- datatable2[datatable2$Year %in% years,]
datatable2 <- subset(datatable2, select=c("Area.Code", "Year.Code", "Value"))
datatable2 <- datatable2[complete.cases(datatable2),]
colnames(datatable2) <- c("Area.Code", "Year.Code", "Value")
write.csv(datatable2,temp_file, row.names=FALSE )
names(datatable2) <- c("CNTRY","YEAR","POP")
write.csv(datatable2, pop_out, row.names=FALSE )

# Crop Prices (USD currency only)

input_file = paste(input_dir,"Prices_E_All_Data_(Normalized).csv",sep="/")
temp_file = paste(temp_dir, "00_cropprices.csv",sep="/")

datatable  <- read.csv(input_file)
datatable2 <- subset(datatable, select=c("Area.Code", "Item.Code", "Element.Code", "Year.Code", "Value"))
datatable2 <- subset(datatable2,  Element.Code==5532)
datatable2 <- datatable2[datatable2$ Area.Code %in% country,]
datatable2 <- datatable2[datatable2$ Item.Code %in% crop,]
datatable2 <- datatable2[datatable2$Year %in% years,]
datatable2 <- subset(datatable2, select=c("Area.Code", "Item.Code", "Year.Code", "Value"))
datatable2 <- datatable2[complete.cases(datatable2),]
write.csv(datatable2, temp_file, row.names=FALSE )

# Livestock Prices (USD currency only)

input_file = paste(input_dir,"Prices_E_All_Data_(Normalized).csv",sep="/")
temp_file = paste(temp_dir, "00_liveprices.csv",sep="/")

datatable  <- read.csv(input_file)
datatable2 <- subset(datatable, select=c("Area.Code", "Item.Code", "Element.Code", "Year.Code", "Value"))
datatable2 <- subset(datatable2,  Element.Code==5532)
datatable2 <- datatable2[datatable2$ Area.Code %in% country,]
datatable2 <- datatable2[datatable2$ Item.Code %in% livestock,]
datatable2 <- datatable2[datatable2$Year %in% years,]
datatable2 <- datatable2[complete.cases(datatable2),]
datatable2 <- subset(datatable2, select=c("Area.Code", "Item.Code", "Year.Code", "Value"))
write.csv(datatable2, temp_file, row.names=FALSE )

# Crop Production

input_file = paste(input_dir,"Production_Crops_Livestock_E_All_Data_(Normalized).csv",sep="/")
temp_file = paste(temp_dir, "00_cropprod.csv",sep="/")

datatable  <- read.csv(input_file)
datatable2 <- subset(datatable, select=c("Area.Code", "Item.Code", "Element.Code", "Year.Code", "Value"))
datatable2 <- subset(datatable2,  Element.Code==5510)
datatable2 <- datatable2[datatable2$ Area.Code %in% country,]
datatable2 <- datatable2[datatable2$ Item.Code %in% crop,]
datatable2 <- datatable2[datatable2$Year %in% years,]
datatable2 <- datatable2[complete.cases(datatable2),]
datatable2 <- subset(datatable2, select=c("Area.Code", "Item.Code", "Year.Code", "Value"))
write.csv(datatable2, temp_file, row.names=FALSE )

# Crop Harvested Area
input_file = paste(input_dir,"Production_Crops_Livestock_E_All_Data_(Normalized).csv",sep="/")
temp_file = paste(temp_dir, "00_cropharea.csv",sep="/")

datatable  <- read.csv(input_file)
datatable2 <- subset(datatable, select=c("Area.Code", "Item.Code", "Element.Code", "Year.Code", "Value"))
datatable2 <- subset(datatable2,  Element.Code==5312)
datatable2 <- datatable2[datatable2$ Area.Code %in% country,]
datatable2 <- datatable2[datatable2$ Item.Code %in% crop,]
datatable2 <- datatable2[datatable2$Year %in% years,]
datatable2 <- datatable2[complete.cases(datatable2),]
datatable2 <- subset(datatable2, select=c("Area.Code", "Item.Code", "Year.Code", "Value"))
write.csv(datatable2, temp_file, row.names=FALSE )

# Livestock Production

input_file = paste(input_dir,"Production_Crops_Livestock_E_All_Data_(Normalized).csv",sep="/")
temp_file = paste(temp_dir, "00_liveprod.csv",sep="/")

datatable  <- read.csv(input_file)
datatable2 <- subset(datatable, select=c("Area.Code", "Item.Code", "Element.Code", "Year.Code", "Value"))
datatable2 <- subset(datatable2,  Element.Code==5510)
datatable2 <- datatable2[datatable2$ Area.Code %in% country,]
datatable2 <- datatable2[datatable2$ Item.Code %in% livestock,]
datatable2 <- datatable2[datatable2$Year %in% years,]
datatable2 <- datatable2[complete.cases(datatable2),]
datatable2 <- subset(datatable2, select=c("Area.Code", "Item.Code", "Year.Code", "Value"))
write.csv(datatable2, temp_file, row.names=FALSE )

# =========================================== #
# Corn-equivalent weights for crop production #
# =========================================== #
# ----- Read in crop production and prices
cropprice  <- read.csv(paste(temp_dir,"00_cropprices.csv",sep="/"))
cropprod   <- read.csv(paste(temp_dir,"00_cropprod.csv",sep="/"))

# ----- Merge production and price data then calculate value
cropvalue <- merge(cropprice, cropprod, by=c("Area.Code","Item.Code","Year.Code"), all = FALSE)
names(cropvalue) <- c("Area.Code","Item.Code","Year.Code","Price","Prod")
cropvalue$Value <- cropvalue$Price*cropvalue$Prod
cropvalue <- subset(cropvalue, select=c("Area.Code","Item.Code","Year.Code","Prod","Value"))

# ----- Remove obs with zero value and prod values then aggregate prod and value by item and year
cropvalue[cropvalue == 0] <- NA
cropvalue <- cropvalue[complete.cases(cropvalue),]
write.csv(cropvalue,paste(temp_dir,"00_cropvalue.csv",sep="/"), row.names=FALSE )
wldcrop <- aggregate(cropvalue, list(cropvalue$Item.Code, cropvalue$Year.Code), sum)
wldcrop <- subset(wldcrop, select=c( "Group.1","Group.2","Prod","Value"))
names(wldcrop) <- c("Item.Code","Year.Code","Prod","Value")

# ----- Calculate global prices, corn equivalent price for each crop and write data
wldcrop$PriceW <- wldcrop$Value / wldcrop$Prod
wldcropprice_csv = paste(temp_dir,"00_wldcropprice.csv",sep="/")
write.csv(subset(wldcrop, select=c("Item.Code","Year.Code","PriceW")), wldcropprice_csv, row.names=FALSE )

wldcornprice_csv = paste(temp_dir,"00_wldcornprice.csv",sep="/")
wldcornprice <- subset(wldcrop, Item.Code==56, select=c("Year.Code","PriceW"))
write.csv(wldcornprice, wldcornprice_csv, row.names=FALSE )

names(wldcornprice) <- c("Year.Code","CornPriceW")
wldcrop <- merge(wldcrop, wldcornprice, by=c("Year.Code"))
wldcrop$CornEqPriceW <- wldcrop$PriceW / wldcrop$CornPriceW
WldCornEqPrice <- subset(wldcrop, select=c("Year.Code","Item.Code","CornEqPriceW"))

wldcorneqprice_csv = paste(temp_dir,"00_WldCornEqPrice.csv",sep="/")
write.csv(WldCornEqPrice, wldcorneqprice_csv, row.names=FALSE )

# ----- Recalculate new value data and corn equivalent data
cropprod_csv = paste(temp_dir,"00_cropprod.csv",sep="/")
wldcorneqprice  <- read.csv(wldcorneqprice_csv)
wldcropprices   <- read.csv(wldcropprice_csv)
cropprod        <- read.csv(cropprod_csv)
wldcornprice    <- read.csv(wldcornprice_csv)

fincropprod  <- merge(cropprod, wldcorneqprice, by=c("Item.Code","Year.Code"), all = FALSE)
fincropprod$QCROP <- fincropprod$Value * fincropprod$CornEqPriceW
fincropprod  <- subset(fincropprod, select=c("Item.Code","Year.Code","Area.Code","QCROP"))
fincropprod  <- merge(fincropprod, wldcornprice, by=c("Year.Code"), all = FALSE)
fincropprod$VCROP <- fincropprod$QCROP * fincropprod$PriceW
fincropprod  <- subset(fincropprod, select=c("Area.Code","Year.Code","QCROP","VCROP"))
fincropprod  <- aggregate(fincropprod, list(fincropprod$Area.Code, fincropprod$Year.Code), sum)
names(fincropprod) <- c("CNTRY","YEAR"," Area.Code"," Year.Code","QCROP","VCROP")

qcrop_out = paste(temp_dir,"QCROP.csv",sep="/")
vcrop_out = paste(temp_dir,"VCROP.csv",sep="/")

write.csv(subset(fincropprod, select= c("CNTRY","YEAR","QCROP")), qcrop_out, row.names=FALSE)
write.csv(subset(fincropprod, select= c("CNTRY","YEAR","VCROP")), vcrop_out, row.names=FALSE)

# =================================================== #
# Chicked-equivalent weights for livestock production #
# =================================================== #
# ----- Skip this one for now ------#


# ===================================================== #
# Merge all data together and create har file from data #
# ===================================================== #
REG    <- read.csv(reg_map_csv)
INC    <- read.csv(inc_out)
POP    <- read.csv(pop_out)
QCROP  <- read.csv(qcrop_out)
VCROP  <- read.csv(vcrop_out)
QLAND  <- read.csv(qland_out)

data_names <- c("INC","POP","QCROP","VCROP","QLAND")

# write out separate files for each year
for(i in data_names){
for(j in years){
data_table     <- merge(get(i), REG, by="CNTRY", all=FALSE)
data_table     <- data_table[data_table$YEAR == j,]
data_table2    <- aggregate(data_table[,3], list(data_table$REG), sum)
names(data_table2) <- c("REG",i)
write.csv(data_table2, paste(output_dir,"/",j,"_",i,".csv", sep=""), row.names=FALSE)}}

# ======== #
# Clean-up #
# ======== #

# Delete 'temp' folder
unlink(temp_dir, recursive = TRUE)
