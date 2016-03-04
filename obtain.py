import glob
import time
import netrc
import datetime as dt
# os.system has been replaced by subprocess. 
# It's in the docs: https://docs/python/org/3/library/subprocess
import subprocess 
from os import path
import unittest

class ObtainError(Exception):
    """def __init__(self, message, errors):
        super(ValidationError, self).__init__(message)
        self.errors = errors"""
    pass


class Obtain:
    def __init__(self):
        """
        This __init__ statement contains the paths for where
        files, directories, and programs are located.  
        """
        self.ftppath = "ftp://ftp.ivydb.com/IvyDBIntl/v2.1/" # Case sensitive
        self.savepath = "/if/udata/optionmetrics/raw_zip"

        # programs
        self.curlpath = "/opt/local/bin/curl"

    def download_file(self, name):
        """
        This will get the file of the specified name from 
        the ftp server specified in self.ftppath, and save 
        it in the directory specified in self.savepath.
        
        NOTE
        cURL gets the username and password from the user's .netrc
        (If you do not know what .netrc is, please look it up)
        You will need to add the following three lines to your .netrc:

        machine ftp.ivydb.com
             login USERNAME
             password PASSWORD

        with the USERNAME and PASSWORD you have been given for
        optionmetrics.
        """
        subprocess.call([self.curlpath, '-s', self.ftppath+name,
            '--netrc', '--output', self.savepath+name])
        if path.exists(self.savepath+name):
            print("Sucessfully downloaded {}.".format(name))
        else:
            raise ObtainError("File {} cannot be processed.".format(name) +
                    "  Either it was not found on the FTP server, " +
                    "or it could not be saved.\n")

    def unzip_file(self, date):
        """
        This unzips the file for the specified date.  If the 
        file is already unzipped, it overwrites the previous 
        versions of the files.  The file must be in the 
        directory specified in self.savepath.

        Parameters
        ----------
        date: datetime object
            date to be unziped.
        """
        d = date.strftime('%Y%m%d')
        name = "INTL.IVYDB.{}D.zip".format(d)
        try:
            subprocess.call(['unzip', '-u', self.savepath+name, 
                '-d', self.savepath])
        except subprocess.CalledProcessError:
            print('\n*** File {} was not found.***\n'.format(
                name))
            raise 

    def remove_unzipped(self, date):
        """
        This removes unzipped files for the specified date.  The file 
        must be in the directory specified in self.savepath.

        Parameters
        ----------
        date: datetime object
        """
        date_str = date.strftime('%Y%m%d')
        name = "INTL.IVY*.{}D.text".format(date_str)
        try:
            for f in glob.glob(self.savepath + name):
                print f
                subprocess.call(['rm', f])
        except subprocess.CalledProcessError:
            raise 

    def load_daily_data(self, date):
        """
        This will attempt to load daily data from the zip file.  
        If the zip file does not exist, it downloads the data.

        date: datetime object
            The date for the file.
        """
        # date_str = str(date.year)+str(date.month).zfill(2)+str(date.day).zfill(2)
        date_str = date.strftime('%Y%m%d')
        if path.exists(self.savepath+date_str):
            pass
        else:
            self.download_file("INTL.IVYDB.{}D.zip".format(date_str))


class TestObtain(unittest.TestCase):
    def setUp(self):
        """
        This is a unit test for Obtain.  It is run by adding

        if __name__=='__main__':
            unittest.main()

        to the end of the file and running the program.

        For more information about unit-testing, please see the 
        documenation for the unittest package.
        """
        self.good_day = dt.datetime(2015, 9, 14)
        self.good_day_str = '20150914' 
        self.bad_day = dt.datetime(2015, 9, 13)
        self.bad_day_str = '20150913' 
        self.today = dt.datetime.today()
        self.om = Obtain()

        # backup and remove files for the tests.
        good_day_path = self.om.savepath+"INTL.IVYDB.{}D.zip".format(
                self.good_day_str)
        good_day_unzipped_path = self.om.savepath+"INTL.IVY*.{}D.zip".format(
                self.good_day_str)

        if path.exists(good_day_path):
            subprocess.check_output(['mv', good_day_path, good_day_path+'.bak'])
        if len(glob.glob(good_day_unzipped_path))>0: # files are unzipped.
            for file in glob.glob(good_day_unzipped_path):
                subprocess.check_output(['mv', file, file+'.bak'])

    def tearDown(self):
        """Restore backup files"""
        for file in glob.glob(self.om.savepath+'*.bak'):
            subprocess.check_output(['mv', file, file[:-4]])


    # Tests of .download_file()
    def test01DownloadFileOnServer(self):
        """
        This will attempt to download a file.

        This tests .download_file()
        """
        self.om.download_file("INTL.IVYDB.{}D.zip".format(self.good_day_str))
        self.assertTrue(path.exists(
            self.om.savepath+"INTL.IVYDB.{}D.zip".format(self.good_day_str)))

    def test02DownloadFileNotOnServer(self):
        """
        This will confirm that an error is raised
        when the user requests to downlad a file 
        that is not on the server.

        This tests .download_file()
        """
        with self.assertRaises(ObtainError):
            self.om.download_file("INTL.IVYDB.{}D.zip".format(self.bad_day))

    # Tests for .unzip_file()
    def test10UnzipFile(self):
        """
        This will attempt to unzip a file and confirm that 
        that the files are unzipped.

        This tests .unzip_file()
        """
        self.om.download_file("INTL.IVYDB.{}D.zip".format(self.good_day_str))
        self.om.unzip_file(self.good_day)
        self.assertGreater(len(glob.glob(
            self.om.savepath+"INTL.IVY*.{}D.txt".format(self.good_day_str))),
            0) # Should be a lot of these files.

    # Tests for .remvoe_unzipped()
    def test20RemoveUnzipped(self):
        """
        This will confirm that the self.good_day unzipped
        files are removed.

        This tests .remove_unzipped()
        """
        self.om.download_file("INTL.IVYDB.{}D.zip".format(self.good_day_str))
        self.om.unzip_file(self.good_day)
        self.om.remove_unzipped(self.good_day)
        self.assertEquals(len(glob.glob(
            self.om.savepath+"INTL.IVY*.{}D.txt".format(self.good_day_str))),
            0) # No .txt files for that date.
    # Tests of .load_daily_data()
    def test20LoadDailyDataFileOnServer(self):
        """
        This will attempt to download a file if it is not
        already downloaded. 

        This tests .load_daily_data()
        """
        self.om.load_daily_data(self.good_day)
        self.assertTrue(path.exists(
            self.om.savepath+"INTL.IVYDB.{}D.zip".format(self.good_day_str)))


if __name__=='__main__':
    om = Obtain()
    try:
        # date_str = dt.datetime(2016,2,d).strftime('%Y%m%d')
        date_str = (dt.datetime.today()-dt.timedelta(1)).strftime('%Y%m%d')
        om.download_file("INTL.IVYDB.{}D.zip".format(date_str))
    except:
        pass

