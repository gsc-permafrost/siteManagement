# Given lat/lon input, script will:
# 
# 1) Autodetect input format
# 2) convert lat/lon to standardized formats
# 3) get utmCoordinates zone and coordinates

import re
import utm
from pyproj import CRS
from typing import Literal
import geopandas as gpd
from dataclasses import dataclass,field
# from pydantic.dataclasses import dataclass as pydantic_dataclass
# from pydantic import ConfigDict
# import helperFunctions as helper


def reprToDict(dc):
    # given a dataclass, dummp itemes where repr=true to a dictionary
    return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__ and dc.__dataclass_fields__[k].repr})


@dataclass
class utmCoordinates:
    latitude: float = None
    longitude: float = None
    x: float = None
    y: float = None
    datum: str = 'WGS84'
    EPSG: str = None
    name: str = None
    UTM_sig: int = field(default=3)

    def __post_init__(self):
        if self.latitude and self.longitude:
            print(self.latitude,self.longitude)
            UTM_coords = utm.from_latlon(self.latitude,self.longitude)
            crs = CRS.from_dict({'proj': 'utm', 'zone': UTM_coords[2], 'south': UTM_coords[3]<'N', 'datum': self.datum})
            self.EPSG=crs.to_epsg()
            self.namey = crs.coordinate_operation.name
            self.x = round(UTM_coords[0],self.UTM_sig)
            self.y = round(UTM_coords[1],self.UTM_sig)


@dataclass
class geographicCoordinates:
    degreeString: str = field(default='°',repr=False)
    DD_sig: float = field(default=7,repr=False)
    DDM_sig: float = field(default=5,repr=False)
    DMS_sig: float = field(default=1,repr=False)
    latitude: float = None
    latitudeDDM: str = None
    latitudeDMS: str = None
    longitude: float = None
    longitudeDDM: str = None
    longitudeDMS: str = None
    datum: str = 'WGS84'
    EPSG: str = None

    def __post_init__(self):
        codes = {'WGS84':'4326','NAD83':'4269'}
        self.EPSG = codes[self.datum]
        self.latitude,self.latitudeDDM,self.latitudeDMS = self.getDD(str(self.latitude),'NS')
        self.longitude,self.longitudeDDM,self.longitudeDMS = self.getDD(str(self.longitude),'EW')

    def getDD(self,value,hemisphere):
        value = re.sub(r'\b(\d+)S\b|\bS\b|\bS(\d+)\b', r'-\1\2', value)
        value = re.sub(r'\b(\d+)W\b|\bW\b|\bW(\d+)\b', r'-\1\2', value)
        value = re.sub(r'[^0-9,.-]+',',',value)
        value = value.replace(',,',',')
        if '-' in value: 
            self.sign = -1
            hemisphere = hemisphere[1]
        else: 
            self.sign = 1
            hemisphere = hemisphere[0]
        value = value.replace('-','')
        value = [self.sign*float(v) for v in value.split(',') if len(v)>0]
        DD = round(sum([l*m for l,m in zip(value,[1,1/60,1/3600])]),self.DD_sig)
        DDM = hemisphere+str(int(abs(DD)))+self.degreeString+' '+str(round((DD%1)*60,self.DDM_sig))+"`"
        DMS = hemisphere+str(int(abs(DD)))+self.degreeString+' '+str(int((DD%1)*60))+"' "+str(round((DD%1*60)%1*60,self.DMS_sig))+'"'
        return(DD,DDM,DMS)

@dataclass
class coordinates:
    ID:list = None
    latitude: list = None
    longitude: list = None
    kwargs: dict = field(default_factory=lambda:{},repr=False)
    datum: str = field(default='WGS84',repr=False)
    # geojson_template: dict = None
    # GCS: geographicCoordinates = field(default_factory=lambda:{k:v for k,v in geographicCoordinates.__dict__.items() if k[0:2] != '__'})
    # UTM: utmCoordinates = field(default_factory=lambda:{k:v for k,v in utmCoordinates.__dict__.items() if k[0:2] != '__'})
    
    def __post_init__(self):
        self.geographicCoordinates = reprToDict(
            geographicCoordinates(latitude=self.latitude,longitude=self.longitude,datum=self.datum)
        )
        self.latitude,self.longitude=self.geographicCoordinates['latitude'],self.geographicCoordinates['longitude']
        self.UTM = reprToDict(
            utmCoordinates(latitude=self.latitude,longitude=self.longitude,datum=self.datum)
        )
        self.geodataframe = gpd.GeoDataFrame(index=[self.ID],
                                             data=self.kwargs,
                                             geometry=gpd.points_from_xy([self.UTM['x']],[self.UTM['y']]),
                                             crs=self.UTM['EPSG'])
        
    
        self.geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "siteID": self.ID
                    }|self.kwargs,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [self.longitude, self.latitude] 
                    }
                }
            ]
        }


# @dataclass
# class coordinates:
#     latitude: str = field(default=None,repr=False)
#     longitude: str = field(default=None,repr=False)
#     datum: Literal['WGS84','NAD83'] = 'WGS84'
#     formatted: dict = field(default_factory=lambda:{'DMS':None,'DDM':None})
#     # geographicCoordinates: dict = field(default_factory=lambda:{'EPSG':None,'latitude':None,'longitude':None})

        # self.latitude,latDDM,latDMS = self.getDD(str(self.latitude),'NS')
        # self.longitude,lonDDM,lonDMS = self.getDD(str(self.longitude),'EW')
        # self.formatted['DDM'] = [latDDM,lonDDM]
        # self.formatted['DMS'] = [latDMS,lonDMS]
        # self.getUTM()
        # self.geographicCoordinates = geographicCoordinates(datum=self.datum,x=self.longitude,y=self.latitude).__dict__

