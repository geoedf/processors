#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
#from dotenv import load_dotenv
from wqxweblib import WQXWeb as WQX
from time import sleep


from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError

""" Module for uploading water quality data to WQX through the WQX Web API using WQXWebLib.
"""

class WQXWeb(GeoEDFPlugin):
    
    # WQX Web login credentials will be loaded as environment variables from a .env file
    user_id = 'jackasmith'
    private_key = 'dE/qxZ2jTCc7DjJ951ql/pNfIFgDM4Zb3jTg9VdRE0jXdvg2iWGO0XvL4BH1g+xtBg5iUmZOoSJcNMLCjE4M6w=='

    # in workflow mode, the destination directory will be provided
    target_path = "data"

    # results input file is required
    # import configuration file ID requireed if different than default
    __required_params = ['results_file']
    __optional_params = ['import_config_id','worksheet']
    
    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFPlugin class
    def __init__(self, **kwargs):

        #list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for WQXWeb not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        # set defaults if none provided
        if (self.import_config_id is None):
            self.import_config_id = '7411'
        if (self.worksheet is None):
            self.worksheet = '5'

        # Load environment variables from file
        #load_dotenv(".env")
        # Assign the user id and private key to their own variables
        #self.user_id = os.environ.get("WQXWEB_USERID")
        #self.private_key = os.environ.get("WQXWEB_PRIVATEKEY")

        super().__init__()

    # the process method that uploads the results file to WQX
    # the WQXWebLib library is used to handle all the communications with WQX Web API
    def process(self):
        
        wqxweb = WQX(userID=self.user_id, privateKey=self.private_key)

        try:
            with open(self.results_file, mode='rb') as file:
                file_id = wqxweb.Upload(filename=self.results_file, contents=file.read())

            dataset_id = wqxweb.StartImport(
                importConfigurationId=self.import_config_id,
                fileId=file_id,
                fileType=WQX.XLSX,
                worksheetsToImport=self.worksheet,
                newOrExistingData=WQX.CONTAINS_NEW_OR_EXISTING,
                uponCompletion=WQX.SUBMIT_IMPORT,
                uponCompletionCondition=WQX.EXPORT_IF_NO_WARNING
            )
        except GeoEDFError:
            raise
        except:
            raise

        status = None
        busy_states = ('Waiting to Import','Importing','Waiting to Export','Waiting to Export and Submit','Exporting','Processing at CDX','Waiting to Delete','Deleting','Waiting to Update WQX','Updating WQX')

        try:
            while status is None or status in busy_states:
                status = wqxweb.GetStatus( dataset_id ).get('StatusName')
                if status in busy_states:
                    sleep(10)
        except GeoEDFError:
            raise
        except:
            raise

