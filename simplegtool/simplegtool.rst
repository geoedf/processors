SimplegTool
====================

.. py:class:: GeoEDF.processor.SimplegTool()

   Module for running 02_data_proc binary file that generates
   two database files ( LANDDATA.har, DATACHKS.har).
   SimplegTool requires two parameters:
   1) har_input_dir : directory where INC, POP, QCROP, VCROP, QLAND data exist
   2) target_year : base year
   An economic model (02_data_proc.tab) is compiled into a Fortran code by GEMPACK
   program(copsmodels.com), and then transforms into an executable named 02_data_proc.
   The resulting executable/binary takes a command file (CMF) that instructs
   model to load inputs(INC, POP, QCROP, and so on). 
   User needs to edit the cmf file in order to select the base year(which is 
   same as target_year,one of the required parameters). User specified target_year
   will be automatically set in the command file through edit_CMF_target_path().
   Remember that base year or target_year must fall within start_year and 
   end_year of the SimpleDataClean processor.
   Input Data files  (see input folder)!    
   --------------------------------------     
   FILE INC_DAT   # real GDP (in USD 2005) #;
   FILE POP_DAT   # population (in numbers) #;
   FILE QCROP_DAT # aggregate crop output (in corn. eq. MTs) #;
   FILE VCROP_DAT # Value of aggregate crop output (in USD) #;
   FILE QLAND_DAT # cropland (in ha) #;
   ------------------------------------------
   Note that SimplegTool processor modifies CSV2HAR processor's output directory.
   It copies YYYY_variable.har files to YYYY/variable.har because the command file
   reads inputs from the baHar files left in target_path will be returned to the users as final output.
        Turns out that copying files using subprocess with wildcard causes 
        either failure or shell execution concern.
        This function copies all har files in subdirectory of the target path 
        to the destination directory.se_year/variable.har.
   Please refer to move_har_to_YYYY() for details.

   .. py:attribute:: har_input_dir (str,required)

   Directory where INC, POP, QCROP, VCROP, QLAND data exist

   .. py:attribute:: target_year (int,required)

   Base year.

