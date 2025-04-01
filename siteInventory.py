######################################################################################################################
# Data Source Management
######################################################################################################################
from dataclasses import dataclass,field
# import helperFunctions as helper
from .siteCoordinates import coordinates as siteCoordinates
from .helperFunctions.updateDict import updateDict
from .helperFunctions.reprToDict import reprToDict
from .helperFunctions.safeFormat import safeFormat
from .helperFunctions.log import log
from pathlib import Path
import geopandas as gpd
import pandas as pd
import json
import yaml
import os
import re



@dataclass(kw_only=True)
class sourceRecord:
    # executes a file search using wildcard pattern matching cross references against a list of exiting files
    sourceID: str = field(default=os.path.join('sourcePath','*wildcard*'),repr=False)
    sourcePath: str = 'sourcePath'
    wildcard: str = '*wildcard*'
    parserKwargs: dict = field(default_factory=lambda:{})

    def __post_init__(self):
        if self.sourcePath != 'sourcePath' and os.path.isdir(self.sourcePath):
            self.sourcePath = os.path.abspath(self.sourcePath)
        self.sourceID = os.path.join(self.sourcePath,self.wildcard)

@dataclass(kw_only=True)
class measurementRecord:
    # Records pertaining to a measurement set
    measurementID: str = '.measurementID'
    description: str = 'This is a template for defining measurement-level metadata'
    fileType: str = None
    sampleFrequency: str = None
    description: str = None
    latitude: float = None
    longitude: float = None
    startDate: str = None
    stopDate: str = None
    sourceFiles: sourceRecord = field(default_factory=lambda:{k:v for k,v in sourceRecord.__dict__.items() if k[0:2] != '__'})
    template: bool = field(default=False,repr=False)
    dpath: str = field(default=None,repr=False)

    def __post_init__(self):
        if self.measurementID:
            if self.measurementID != '.measurementID':
                self.measurementID = safeFormat(self.measurementID)
            self.coordinates = siteCoordinates(ID=self.measurementID,latitude=self.latitude,longitude=self.longitude,attributes={'description':self.description,'pointClass':type(self).__name__})
            self.latitude,self.longitude=self.coordinates.latitude,self.coordinates.longitude
            if type(list(self.sourceFiles.values())[0]) is not dict:
                self.sourceFiles = {'':self.sourceFiles}
            sobj = map(lambda values :sourceRecord(**values),self.sourceFiles.values())
            self.sourceFiles = {s.sourceID:reprToDict(s) for s in sobj}

            if len(self.sourceFiles)>1 and self.__dataclass_fields__['sourceFiles'].default_factory()['sourceID'] in self.sourceFiles:
                self.sourceFiles.pop(self.__dataclass_fields__['sourceFiles'].default_factory()['sourceID'])                

@dataclass(kw_only=True)
class siteRecord:
    # Records pertaining to a field site, including a record of measurements from the site
    siteID: str = '.siteID'
    description: str = 'This is a template for defining site-level metadata'
    Name: str = None
    PI: str = None
    startDate: str = None
    stopDate: str = None
    landCoverType: str = None
    latitude: float = None
    longitude: float = None
    coordinates: dict = field(default_factory=lambda:{},repr=False)
    geojson: dict = field(default_factory=lambda:{},repr=False)
    geodataframe: gpd.GeoDataFrame = field(default_factory=lambda:gpd.GeoDataFrame(),repr=False)
    Measurements: measurementRecord = field(default_factory=lambda:{k:v for k,v in measurementRecord.__dict__.items() if k[0:2] != '__'})
    dpath: str = field(default=None,repr=False)
    
    def __post_init__(self):
        if self.siteID:
            if self.siteID != '.siteID':
                self.siteID = safeFormat(self.siteID)
            if self.latitude and self.longitude:
                self.coordinates = siteCoordinates(ID=self.siteID,latitude=self.latitude,longitude=self.longitude,attributes={'description':self.description,'pointClass':type(self).__name__})
                self.latitude,self.longitude=self.coordinates.latitude,self.coordinates.longitude
                self.geojson = self.coordinates.geojson
                self.geodataframe = self.coordinates.geodataframe
            if type(list(self.Measurements.values())[0]) is not dict:
                self.Measurements = {'':self.Measurements}

            # map the measurements and unpack to dict
            Measurements = map(lambda key :measurementRecord(**self.Measurements[key]),self.Measurements)
            self.Measurements = {measurement.measurementID:measurement for measurement in Measurements}
            for measurementID in self.Measurements:
                if self.Measurements[measurementID].coordinates == {} or measurementID == '.measurementID':
                    pass
                elif self.geojson == {}:
                    self.geojson = self.Measurements[measurementID].coordinates.geojson
                    self.geodataframe = self.Measurements[measurementID].coordinates.geodataframe
                else:
                    self.geojson = updateDict(self.geojson,self.Measurements[measurementID].coordinates.geojson,overwrite='append')
                    self.geodataframe = pd.concat([self.geodataframe,self.Measurements[measurementID].coordinates.geodataframe])
            self.Measurements = {measurementID:reprToDict(self.Measurements[measurementID]) for measurementID in self.Measurements}

@dataclass(kw_only=True)
class siteInventory:
    Sites: dict = None
    verbose: bool = False
    spatialInventory: dict = field(default_factory=lambda:{})
    mapTemplate: str = field(default_factory=lambda:Path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates','MapTemplate.html')).read_text())


    def __post_init__(self):
        if type(self.Sites) is str and os.path.isfile(self.Sites):
            with open(self.Sites) as f:
                self.Sites = yaml.safe_load(f)
        Sites = map(lambda key: siteRecord(**self.Sites[key]),self.Sites)
        self.Sites = {site.siteID:site for site in Sites}
        for siteID in self.Sites:
            if self.Sites[siteID].coordinates == {}:
                pass
            elif self.spatialInventory == {}:
                self.spatialInventory['geojson'] = self.Sites[siteID].geojson
                self.spatialInventory['geodataframes'] = {siteID:self.Sites[siteID].geojson}
            else:
                self.spatialInventory['geojson'] = updateDict(self.spatialInventory['geojson'],self.Sites[siteID].geojson,overwrite='append',verbose=self.verbose)
                self.spatialInventory['geodataframes'][siteID] = self.Sites[siteID].geojson

        self.siteInventory = {siteID:reprToDict(self.Sites[siteID]) for siteID in self.Sites}
        self.mapTemplate = self.mapTemplate.replace('fieldSitesJson',json.dumps(self.spatialInventory))
