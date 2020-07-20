""" Simple web page scrapper

Convert curl queries to Python requests: https://curl.trillworks.com/

Notes:
- Supported export file formats: XML, XLS, CSV

"""

# pylint: disable=logging-fstring-interpolation, broad-except

import argparse
import logging
import os
import time
import sys
import requests
from bs4 import BeautifulSoup

LOG_FORMAT = "%(asctime)-11s [%(levelname)s] [%(name)s] %(message)s"
LOGGER = logging.getLogger("scraper")
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

SUPPORTED_FILE_TYPES = ("csv", "xml", "xls")


class UnsupportedExportType(Exception):
    """ Class to throw exception in case unkown file extension is used """


class WebScrapper:
    """ Simple Web scrapper """

    url = "https://echa.europa.eu/pact"

    params = (
        ("p_p_id", "disspact_WAR_disspactportlet"),
        ("p_p_lifecycle", "2"),
        ("p_p_state", "normal"),
        ("p_p_mode", "view"),
        ("p_p_resource_id", "exportResults"),
        ("p_p_cacheability", "cacheLevelPage"),
        ("p_p_col_id", "column-1"),
        ("p_p_col_pos", "1"),
        ("p_p_col_count", "2"),
    )

    # pylint: disable=line-too-long
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    }

    EXPORT_FILE = "data.{}"

    def __init__(self, cached=False, export_type="csv"):
        self.cached = cached
        self.export_type = export_type
        self.page = None

        self._validate_file_extension()

    def download(self):
        """ Download local copy of scrapped page """

        filename = "main.html"
        if os.path.exists(filename):
            LOGGER.info(
                f"Filename {filename} exists skipping download. Use locally cached web page.."
            )
            with open(filename, "rb") as file:
                self.page = file.read().strip()
        else:
            try:
                LOGGER.info(f"Saving data into filename: {filename}")
                with open(filename, "wb") as file:
                    self.get_page()
                    LOGGER.info(f"Length of HTML page: {len(self.page)}")
                    file.write(self.page)
            except IOError as ex:
                LOGGER.error(ex)
            except Exception as ex:
                LOGGER.error(f"Unknown error: {ex}")

    def get_page(self):
        """ Get HTML page content """
        try:
            with requests.Session() as session:
                response = session.get(WebScrapper.url, timeout=10)
                status = response.status_code
                if status == 200:
                    self.page = response.content
                else:
                    LOGGER.error(
                        f"Some error occured while fetching data! Status code: {status}"
                    )
        except requests.HTTPError as ex:
            LOGGER.error(f"Some error occured while fetching data: {ex}")
        except Exception as ex:
            LOGGER.error(f"Unknown error: {ex}")

    def _scrape_form_input_data(self):
        """ Helper method to re-build form input data from HTML form """
        # download locally if cached attr is True
        if self.cached:
            self.download()

        # Grab page if not in memory yet
        if not self.page:
            self.get_page()

        soup = BeautifulSoup(self.page, "html.parser")

        form_id = "_disspact_WAR_disspactportlet_exportForm"
        export_form = soup.find(name="form", attrs={"id": form_id})

        inputs = export_form.find_all("input")
        data = {}
        for item in inputs:
            if item.get("name") == "_disspact_WAR_disspactportlet_exportType":
                data.update({item.get("name"): self.export_type})
            else:
                data.update({item.get("name"): item.get("value")})

        LOGGER.debug(f"Total number of input attributes: {len(inputs)}")

        return data

    def _validate_file_extension(self):
        if self.export_type.lower() not in SUPPORTED_FILE_TYPES:
            msg = f"Unknown file type. Supported file types: {SUPPORTED_FILE_TYPES}"
            LOGGER.error(msg)
            raise UnsupportedExportType

    def export_data_to_file(self, export_type=None):
        """ Export scraped data into file type

        Raises:
            UnsupportedExportType: [description]
        """
        if export_type:
            self.export_type = export_type

        self._validate_file_extension()

        datafile = self.EXPORT_FILE.format(self.export_type)
        LOGGER.info(f"Exporting content to {datafile}.")

        data = self._scrape_form_input_data()

        LOGGER.debug(
            f"url={self.url}, headers={self.headers}, params={self.params}, data={data}"
        )

        try:
            with requests.Session() as session:
                response = session.post(
                    self.url, headers=self.headers, params=self.params, data=data
                )
                if response.status_code == 200:
                    if self.export_type in ("csv", "xml"):
                        filemode = "w"
                    elif self.export_type == "xls":
                        filemode = "wb"

                    try:
                        with open(datafile, filemode) as file:
                            if filemode == "w":
                                file.write(response.text)
                            else:
                                file.write(response.content)
                    except IOError as ex:
                        LOGGER.error(ex)
                    except Exception as ex:
                        LOGGER.error(f"Unknown error: {ex}")
                else:
                    LOGGER.error(
                        f"Something went wrong. Status code: {response.status_code}"
                    )
        except requests.HTTPError as ex:
            LOGGER.error(f"Something went wrong while exporting data: Error: {ex}")
        except Exception as ex:
            LOGGER.error(f"Unknown error: {ex}")


def parse_args():
    """ Parse arguments from CLI """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--filetype",
        help="file type to export",
        choices=SUPPORTED_FILE_TYPES,
        required=True,
    )
    args = parser.parse_args()

    if args.filetype not in SUPPORTED_FILE_TYPES:
        # logging.error('Invalid file type provided. Aborting..')
        parser.print_help()
        sys.exit(1)

    return args.filetype


def test_all_export():
    """ Test whether exporting all supported file types work as expected """
    for file_type in SUPPORTED_FILE_TYPES:
        start = time.time()
        scraper.export_data_to_file(export_type=file_type)
        LOGGER.info("Export total time: {:0.2f} seconds".format(time.time() - start))


if __name__ == "__main__":
    filetype = parse_args()
    scraper = WebScrapper(cached=False, export_type=filetype)

    start = time.time()
    scraper.export_data_to_file()
    LOGGER.info("Export total time: {:0.2f} seconds".format(time.time() - start))
