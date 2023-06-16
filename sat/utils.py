




# Liste des formats de fichiers Sentinel

from datetime import datetime
import os
from eodag import EODataAccessGateway
from eodag.utils import ProgressCallback

from pyproj import CRS, Transformer

from water_sat.settings import EODAG__CREODIAS__AUTH__CREDENTIALS__PASSWORD, EODAG__CREODIAS__AUTH__CREDENTIALS__USERNAME, EODAG__PEPS__AUTH__CREDENTIALS__PASSWORD, EODAG__PEPS__AUTH__CREDENTIALS__USERNAME


dag = EODataAccessGateway()
dag.set_preferred_provider("creodias")

#creation de l'espace de stockage des images telechargées
workspace = 'C:\dev\web\python\eodag_download'

if not os.path.isdir(workspace):
    os.mkdir(workspace)
os.environ["EODAG__PEPS__AUTH__CREDENTIALS__USERNAME"] = EODAG__PEPS__AUTH__CREDENTIALS__USERNAME
os.environ["EODAG__PEPS__AUTH__CREDENTIALS__PASSWORD"] = EODAG__PEPS__AUTH__CREDENTIALS__PASSWORD
os.environ["EODAG__PEPS__DOWNLOAD__OUTPUTS_PREFIX"] = os.path.abspath(workspace)

os.environ["EODAG__CREODIAS__AUTH__CREDENTIALS__USERNAME"] = EODAG__CREODIAS__AUTH__CREDENTIALS__USERNAME
os.environ["EODAG__CREODIAS__AUTH__CREDENTIALS__PASSWORD"] = EODAG__CREODIAS__AUTH__CREDENTIALS__PASSWORD
os.environ["EODAG__CREODIAS__DOWNLOAD__OUTPUTS_PREFIX"] = os.path.abspath(workspace)


crs_4326 = CRS.from_epsg(4326)
crs1 = CRS("epsg:4326")
resolution = 0.0001
transformer = Transformer.from_crs(crs_4326, crs_4326, always_xy=True)


sentinel_formats = [
    'safe',
    'zip',
    'nc',
    'tif',
    'jp2',
    'xml'
]

def list_sentinel_files(directory):
    sentinel_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_format = file.split('.')[-1].lower()
            if file_format in sentinel_formats:
                sentinel_files.append(os.path.join(root, file))
    return sentinel_files




# une fonction qui formate une date en utilisant le format "YYYY-MM-DD" par défaut, mais qui permet également de fournir un format spécifique en tant que paramètre

def format_date_to_specific_format(date, date_format="%Y-%m-%d"):
    if isinstance(date, str):
        date = datetime.strptime(date, date_format)
    formatted_date = date.strftime(date_format)
    return formatted_date


# fonction qui transforme les donnees en chaine de caractère
def transform_data_to_str(data):
    try:
        # Essayer de parser les données en utilisant le module ast
        parsed_data = str(data)
        return parsed_data
    except (ValueError, SyntaxError):
        # Si une erreur se produit, retourner une erreur
        #raise ValueError("Les données ne peuvent pas être parsées en utilisant ast.literal_eval.")
        return data


def search_satellite_products(productType, sensorOperationalMode, startTime, endTime, polygon=0, geometry=0):

    # search_results = eo.search(
    #         geom=geom,
    #         productType='S2',
    #         start_date="2023-01-01", end_date="2023-02-07"
    #     )
    #search_results = dag.search_all(productType, sensorOperationalMode, startTime, endTime, polygon)

    #dag.set_preferred_provider("creodias")
    #print(dag.get_preferred_provider())
    #print(dag.available_providers())
    

    search_criteria = {
    "productType": productType,
    "start": startTime,
    "end": endTime,
    "geom": polygon if (geometry==0) else geometry
}
    search_results, estimated_total_number= dag.search(**search_criteria)
    return search_results, estimated_total_number

def search_product_from_id(product_id):
    product_found = dag.search(id=product_id)
    if product_found:
        return product_found
    else:
        return None


def download_image_and_create_session(product_to_download):
    #print(dag)
    print("demarrage du téléchargement ")
    download_task = dag.download(product_to_download,
        progress_callback=ProgressCallback(),
    )
    print("\n\n Vous serez notifié e la fin")
    return download_task
