from os import path, remove
import sys
import subprocess

class Basetile(object):
    """ArcticNet basemap tile and associated functionalities"""


    
    # Class attributes
    __suffix = {'mask': '_mask', \
                'tile': '_tile', \
                'lcc': '_lcc', \
                'polygon': '_lcc_coord.txt'}
    
    __extension = {'grd': '.grd', \
                   'flt': '.flt', \
                   'cmd': '.cmd', \
                   'ps': '.ps',  \
                   'cpt': '.cpt', \
                   'int': '.int', \
                   'mb-1': '.mb-1', \
                   'aux': '.aux', \
                   'xml': '.xml', \
                   'gif': '.gif'}


    
    def __get_region(self, region, src_proj, dst_proj):
        """Extract all components of the region in geodesic and projected coordinates

        Positional arguments:
        region -- geographic extent of the tile
        src_proj -- inverse projection
        dst_proj -- forward projection

        Returns:
        geoinfo -- dict of corner coordinates in geodesic and projected coordinates
        """
        import pyproj

        # Dictionnary to store tile geo metadata
        geoinfo = dict()
        
        # Source and destination coordinate systems
        p1 = pyproj.Proj(src_proj)
        p2 = pyproj.Proj(dst_proj)

        # Parse the geographic coordinates
        geoinfo['geo'] = region
        geoinfo['xmin'] = float(region.split('/')[0])
        geoinfo['xmax'] = float(region.split('/')[1])
        geoinfo['ymin'] = float(region.split('/')[2])
        geoinfo['ymax'] = float(region.split('/')[3])           
            
        # Get the projected coordinates
        geoinfo['ul'] = pyproj.transform(p1, p2, geoinfo['xmin'], geoinfo['ymax'])
        geoinfo['ur'] = pyproj.transform(p1, p2, geoinfo['xmax'], geoinfo['ymax'])
        geoinfo['lr'] = pyproj.transform(p1, p2, geoinfo['xmax'], geoinfo['ymin'])
        geoinfo['ll'] = pyproj.transform(p1, p2, geoinfo['xmin'], geoinfo['ymin'])

        return geoinfo
    



    def __init__(self, name, region, cellsize, datatype='_Ztopo'):        
        """Creates and initialize a new basetile object

        Positional arguments:
        name -- name of the basemap tile
        region -- geographic extent of the tile
        cellsize -- the spatial resolution of the tile

        Keyword argument:
        datatype -- the type of basetile that will be generated
        """
        PROJ4_LCC = "+proj=lcc +lat_1=70 +lat_2=73 +lat_0=70 +lon_0=-105 +x_0=2000000 +y_0=2000000 +datum=WGS84 +units=m +no_defs" 
        PROJ4_GEO = "+proj=latlong +datum=WGS84"
        GMT_SCALE = "-105/70/70/73/"
        GMT_PROJ = "l"
        PRIM_MERD = -105
        
        # Metadata instance attributes
        self.metadata = {}
        self.metadata['name'] = name
        self.metadata['region'] = self.__get_region(region, PROJ4_GEO, PROJ4_LCC)
        self.metadata['cellsize'] = cellsize
        self.metadata['proj4_proj_lcc'] = PROJ4_LCC
        self.metadata['proj4_proj_geo'] = PROJ4_GEO
        self.metadata['gmt_proj'] = GMT_PROJ
        self.metadata['gmt_scale'] = GMT_SCALE
        self.metadata['prim_merd'] = PRIM_MERD
    
        # netCDF grid instance attributes
        self.nc_grid = {}
        self.nc_grid['no_ext'] = self.metadata['name']+datatype
        self.nc_grid['grid'] = self.nc_grid['no_ext']+self.__extension['grd']
        self.nc_grid['datalist'] = self.nc_grid['no_ext']+self.__extension['mb-1']
        self.nc_grid['mask'] = self.nc_grid['no_ext']+self.__suffix['mask']+self.__extension['grd']
        self.nc_grid['tile'] = self.nc_grid['no_ext']+self.__suffix['tile']+self.__extension['grd']
        self.nc_grid['tile_int'] = self.nc_grid['tile']+self.__extension['int']
        self.nc_grid['cmd_script'] = self.nc_grid['grid']+self.__extension['cmd']

        # ESRI grid instance attibutes
        self.esri_grid = {}
        self.esri_grid['grid'] = self.nc_grid['no_ext']+self.__suffix['tile']+self.__extension['flt']
        self.esri_grid['xml'] = self.esri_grid['grid']+self.__extension['aux']+self.__extension['xml']

        # ps map instance attributes
        self.ps_map = {}
        self.ps_map['no_ext'] = self.metadata['name']+datatype
        self.ps_map['map'] = self.ps_map['no_ext']+self.__extension['ps']
        self.ps_map['shell'] = self.ps_map['no_ext']+self.__extension['cmd']
        self.ps_map['lcc_no_ext'] = self.metadata['name']+datatype+self.__suffix['lcc']
        self.ps_map['lcc_map'] = self.ps_map['lcc_no_ext']+self.__extension['ps']
        self.ps_map['lcc_cpt'] = self.ps_map['lcc_no_ext']+self.__extension['cpt']
        self.ps_map['lcc_shell'] = self.ps_map['lcc_no_ext']+self.__extension['cmd']
        
        # gif map instance attributes
        self.gif_map = {}
        self.gif_map['lcc_map'] = self.ps_map['lcc_no_ext']+self.__extension['gif']



    def __str__(self):
        """print the class attributes"""

        return "ArcticNet basemap tile %s with region %s and spatial resolution %s meters" \
            % (self.name, self.region, self.cellsize)

    

    def __check_dir(self, directory):
        """Check that the directory path terminates with a '/' character. Append it if necessary

        Keyword argument:
        directory -- directory path to check

        Returns:
        directory -- directory path with '/' appended
        """
        if (directory[-1] != '/'):
            directory = directory+'/'

        return directory

        


    def __make_poly_ascii(self, outdir):
        """Generate a ascii file containing coordinates defining the tile's region

        Keyword arguments:
        outdir -- directory path in which to store the ascii file

        Returns:
        filename -- complete path to the ascii file
        """
        import pyproj
       
        # Open a file to store results
        outdir = self.__check_dir(outdir)
        
        filename = outdir+self.metadata['name']+self.__suffix['polygon']           
        out = open(filename, 'w')

        # Print to file
        out.write('''{ulx} {uly}
{urx} {ury}
{lrx} {lry}
{llx} {lly}
{ulx} {uly}'''.format(ulx=self.metadata['region']['ul'][0], \
                      uly=self.metadata['region']['ul'][1], \
                      urx=self.metadata['region']['ur'][0], \
                      ury=self.metadata['region']['ur'][1], \
                      lrx=self.metadata['region']['lr'][0], \
                      lry=self.metadata['region']['lr'][1], \
                      llx=self.metadata['region']['ll'][0], \
                      lly=self.metadata['region']['ll'][1]))

        # Close the file and return
        out.close()
        return filename
        

        
        
    def make_grid(self, datalist, outdir):
        """Make a netCDF bathymetry grid from the specified datalist and basetile metadata

        Positional arguments:
        datalist -- MB-System datalist
        outdir -- directory path in which to store the grid

        Returns: None
        """
        outdir = self.__check_dir(outdir)
        if not(path.isfile(datalist)):
            print "\nError: no such file %s found.\n" % (datalist)
            sys.exit(-1)
            
        # This function must be performed by the inheritated class
        print "Function %s is not implemented in the parent class!\n" % (sys._getframe().f_code.co_name)
        pass

        
            
            

    def cookie_cut(self, outdir):
        """Cookie cut the netCDF grid based on basetile extent

        Positional arguments:
        outdir -- directory path in which to store the grid

        Returns:
        status -- True when the NetCDF grid has valid data. False otherwise.
        """
        status = False
        outdir = self.__check_dir(outdir)

        # Make polygon in projected coordinates
        polyfile = self.__make_poly_ascii(outdir)
        
        # Mask based on projected polygon
        try:
            subprocess.check_call(['which', 'grdmask'])
        except subprocess.CalledProcessError:
            print "\nCould not call grdmask! Please make sure GMT is properly installed\n."
            exit(-1)
        else:            
            subprocess.call(["grdmask", polyfile, "-G"+outdir+self.nc_grid['mask'], "-R"+outdir+self.nc_grid['grid'], "-NNaN/1/1", "-V"])

        # Perform mask
        try:
            subprocess.check_call(['which', 'grdmath'])
        except subprocess.CalledProcessError:
            print "\nCould not call grdmath! Please make sure GMT is properly installed\n."
            exit(-1)
        else:        
            subprocess.call(["grdmath", outdir+self.nc_grid['grid'], outdir+self.nc_grid['mask'], "OR", "=", outdir+self.nc_grid['tile']])

        # Remove unnecessary files
        if path.isfile(polyfile):
            # polygon file
            remove(polyfile)

        if path.isfile(outdir+self.nc_grid['grid']):
            # original NetCDF grid
            remove(outdir+self.nc_grid['grid'])
            
        if path.isfile(outdir+self.nc_grid['mask']):
            # NetCDF grid mask
            remove(outdir+self.nc_grid['mask'])
          
        # Check if the NetCDF grid contains valid data
        try:
            subprocess.check_call(['which', 'grdinfo'])
        except subprocess.CalledProcessError:
            print "\nCould not call grdinfo! Please make sure gmt is properly installed\n."
            exit(-1)
        else:
            zrange = subprocess.check_output("grdinfo %s | grep 'z_min'"  % (outdir+self.nc_grid['tile']), shell=True)
            zmin = float(zrange.split(' ')[2])
            zmax = float(zrange.split(' ')[4])
            if not((zmax == 0) and (zmin == 0)):
                # There is elevation data in the file. Set the return status to True
                status = True
            else:
                # There is no elevation data in the file. Delete the NetCDF grid and mb-1 file
                if path.isfile(outdir+self.nc_grid['tile']):
                    # tiled NetCDF grid
                    remove(outdir+self.nc_grid['tile'])

                if path.isfile(outdir+self.nc_grid['datalist']):
                    # tiled NetCDF grid
                    remove(outdir+self.nc_grid['datalist'])

        return status        





    def make_esri_grid(self, outdir):
        """Make an ESRI grid from the pre-generated NetCDF grid

        Positional arguments:
        outdir -- directory path in which to store the grid
        """
        outdir = self.__check_dir(outdir)
        
        if path.isfile(outdir+self.nc_grid['tile']):
            # Convert NetCDF grid to ESRI Grid
            try:
                subprocess.check_call(['which', 'gdal_translate'])
            except subprocess.CalledProcessError:
                print "\nCould not call gdal_translate! Please make sure GDAL is properly installed\n."
                exit(-1)
            else:                
                subprocess.call(["gdal_translate", "-a_srs", self.metadata['proj4_proj_lcc'], "-of", "EHdr", "-a_nodata", "-99999", outdir+self.nc_grid['tile'], outdir+self.esri_grid['grid']])

                # Remove unnecessary files
                if path.isfile(outdir+self.esri_grid['xml']):
                    remove(outdir+self.esri_grid['xml'])
            
        else:
            print "\nError: NetCDF file %s not found!\n" % (self.nc_grid['tile'])
            print "Generated a NetCDF grid first running either bathy_grid(), amp_grid() or ss_grid().\n" 




    def modify_ps_plot(self, outdir, org_cmd, new_cmd, logo, display=False):
        """Create a new a c-shell script based in the one generated by MB-System's mb_grdplot command to mix a geographic basemap with a projected grid

        Positional arguments:
        outdir -- directory path in which to store the c-shell script
        org_cmd -- name of the original c-shell script
        new_cmd -- name of the modified c-shell script
        logo -- logo to display in the legend

        Kerword argument:
        display -- flag to determine if the resulting ps map should be launched upon execution (default: don't display)
        """
        # This function must be performed by the inheritated class
        print "Function %s is not implemented in the parent class!\n" % (sys._getframe().f_code.co_name)
        pass

            

        

    def make_ps_plot(self, outdir, logo):
        """Make a Postscript map from the pre-generated NetCDF grid

        Keyword arguments:
        outdir -- directory path in which to store the map
        logo -- logo to display in the legend
        """
        # This function must be performed by the inheritated class
        print "Function %s is not implemented in the parent class!\n" % (sys._getframe().f_code.co_name)
        pass




    def make_gif_plot(self, outdir, logo):
        """Make an image (.gif) map from the pre-generated Postscript file. Generate the Postscript if it does not exist.

        Keyword arguments:
        outdir -- directory path in which to store the map
        logo -- logo to display in the legend
        """
        outdir = self.__check_dir(outdir)
        
        if not(path.isfile(outdir+self.ps_map['lcc_map'])):
            self.make_ps_map(outdir, logo)

        # Call ImageMagik
        try:
            subprocess.check_call(['which', 'convert'])
        except subprocess.CalledProcessError:
            print "\nCould not call convert! Please make sure ImageMagick is properly installed\n."
        else:
            subprocess.call(["convert", "-density", "240", "-flatten", outdir+self.ps_map['lcc_map'], outdir+self.gif_map['lcc_map']])
