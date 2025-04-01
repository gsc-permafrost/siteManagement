######################################################################################################################
# Data Source Management
######################################################################################################################
from dataclasses import dataclass,field
# import helperFunctions as helper
from .siteCoordinates import coordinates as siteCoordinates
import yaml
import os
import re


def safeFmt(string,safeChars='[^0-9a-zA-Z]+',fillChar='_'):
    return(re.sub(safeChars,fillChar, str(string)))

def reprToDict(dc):
    # given a dataclass, dummp itemes where repr=true to a dictionary
    return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__ and dc.__dataclass_fields__[k].repr})


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
                self.measurementID = safeFmt(self.measurementID)
            coordinates = siteCoordinates(self.latitude,self.longitude)
            # self.latitude,self.longitude = coordinates.GCS['y'],coordinates.GCS['x']
            if type(list(self.sourceFiles.values())[0]) is not dict:
                self.sourceFiles = {'':self.sourceFiles}
            if self.dpath:
                pth = os.path.join(self.dpath,self.measurementID)
            else:
                pth = None
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
    # coordinates: dict = field(default_factory=lambda:{})
    Measurements: measurementRecord = field(default_factory=lambda:{k:v for k,v in measurementRecord.__dict__.items() if k[0:2] != '__'})
    dpath: str = field(default=None,repr=False)
    
    def __post_init__(self):
        if self.siteID:
            if self.siteID != '.siteID':
                self.siteID = safeFmt(self.siteID)
            # if 'latitude' in self.coordinates and 'longitude' in self.coordinates:
            #     self.coordinates = siteCoordinates(self.coordinates['latitude'],self.coordinates['longitude'])
            # print(siteCoordinates(**self.coordinates))
            coordinates = map(lambda ID:siteCoordinates(ID = ID,**self.coordinates[ID]), self.coordinates)
            # for ID in self.coordinates:
            #     print(siteCoordinates(**self.coordinates[ID]))
            # print('/')
            # print(coordinates)

            for r in coordinates:
                print(r)
            self.coordinates = {r.ID:reprToDict(r) for r in coordinates}
            print(self.coordinates)
            if type(list(self.Measurements.values())[0]) is not dict:
                self.Measurements = {'':self.Measurements}
            if self.dpath:
                pth = os.path.join(self.dpath,self.siteID)
            else:
                pth = None
            mobj = map(lambda key :measurementRecord(**self.Measurements[key]),self.Measurements)
            self.Measurements = {m.measurementID:reprToDict(m) for m in mobj}
            # self.Measurements = helper.dictToDataclass(measurementRecord,self.Measurements,ID=['measurementID'],constants={'dpath':pth})

@dataclass(kw_only=True)
class siteInventory:
    Sites: dict = None

    def __post_init__(self):
        if type(self.Sites) is str and os.path.isfile(self.Sites):
            with open(self.Sites) as f:
                self.Sites = yaml.safe_load(f)
        robj = map(lambda key: siteRecord(**self.Sites[key]),self.Sites)
        self.Sites = {r.siteID:reprToDict(r) for r in robj}
        

    def makeMap(sef):
        pass
        #     if not siteID.startswith('.'):
        #         siteDF = pd.concat([siteDF,pd.DataFrame(data = self.projectInfo['Sites'][siteID], index=[siteID])])
        # if not siteDF.empty:
        #     Site_WGS = gpd.GeoDataFrame(siteDF, geometry=gpd.points_from_xy(siteDF.longitude, siteDF.latitude), crs="EPSG:4326")
        #     self.mapTemplate = self.mapTemplate.replace('fieldSitesJson',Site_WGS.to_json())
        #     with open(os.path.join(self.projectPath,'fieldSiteMap.html'),'w+') as out:
        #         out.write(self.mapTemplate)