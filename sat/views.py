from datetime import datetime
import os
from threading import Thread
from django.contrib import messages

# Create your views here.
from django.shortcuts import render

# Loading polygon of nominal water extent
import shapely.wkt
from shapely.geometry import box
import geopandas as gpd
import numpy as np


# sentinelhub-py package
from sentinelhub import CRS, BBox, DataCollection

from eodag import EODataAccessGateway
from eolearn.core import EOTask, EOWorkflow, FeatureType, OutputTask, linearly_connect_tasks
# filtering of scenes
from eolearn.features import NormalizedDifferenceIndexTask, SimpleFilterTask

# burning the vectorised polygon to raster
from eolearn.geometry import VectorToRasterTask
from eolearn.io import SentinelHubInputTask



from sat.add_valid_data_mask import AddValidDataCoverageTask, AddValidDataMaskTask, ValidDataCoveragePredicate, WaterDetectionTask, plot_rgb_w_water, plot_water_levels

from sat.utils import download_image_and_create_session, format_date_to_specific_format, list_sentinel_files, search_product_from_id, search_satellite_products, transform_data_to_str
from water_sat.settings import BASE_DIR




def index(request):
    # Initialiser eodag
    eodag = EODataAccessGateway()

    # Déclarer les variables globales
    product_types = []
    search_results= []
    estimated_total_number=0
    images_list=[]
    images_downloaded= []
    product_types =eodag.list_product_types(fetch_providers=False)
  

    # try:
    #     product_types = product_type_list()
    # except Exception as e :
    #     print(e)
    #     raise Exception(
    #     "nous avons recontrer un problème lors du traitement, verifier vos reglages et réessayer 1"
    # )
    context = {'product_types': product_types}

    if request.method == "POST":
        

        # Charger les données géographiques à partir du fichier Shapefile
        #interest_area_file = request.FILES.get('shapefile')
        if 'shapefile' in request.FILES:
            interest_area_file = request.FILES['shapefile']
        else:
            print('122')
            interest_area_file = "shapefile.shp"

        #interest_area_file="shapefile.shp"
        print(interest_area_file)
        shapefile = gpd.read_file(transform_data_to_str(interest_area_file), driver='ESRI Shapefile')

        # Récupérer la géométrie de la zone géographique d'intérêt
        geometry = shapefile.unary_union

        #recupérer les types de produit ou catalogue des plateformes
        product_type = transform_data_to_str(request.POST['product_type'])

        # date de depart
        start_date = format_date_to_specific_format(request.POST['start'])

        #date de fin de l'intervalle
        end_date = format_date_to_specific_format(request.POST['end'])

        # Changer le chemin de stockage
        dossier = int(request.POST['inlineRadioOptions'])

        # Recherche les images satellitaires selon les critères
        try:
            search_results, estimated_total_number = search_satellite_products(productType=product_type, sensorOperationalMode=0, startTime=start_date, endTime=end_date, polygon=0, geometry=geometry)
        except Exception as e :
            print(e)
            raise Exception(
            "nous avons recontrer un problème lors du traitement, verifier vos reglages et réessayer 2"
        )
        
        #search_results[0].download()
        # products_id = [p["ID"] for p in search_results]
        # print(products_id)

        for image in search_results:
            
            # data = image.download()
            # images_downloaded.append(data)
            #print(image.properties.get('thumbnail'))
            #print(image.geometry)
            #print(image.provider)
            #print(image.product_type)
            #print(image.search_kwargs)
            #print(image.remote_location)
            #print(image.location)
            


            #images_list += SatelliteData(image)
            images_list.append({
                "abstract":image.properties.get("abstract", ""),
                "instrument":image.properties.get("instrument", ""),
                "platform":image.properties.get("platform", ""),
                "platformSerialIdentifier":image.properties.get("platformSerialIdentifier", ""),
                "processingLevel":image.properties.get("processingLevel", ""),
                "keywords":image.properties.get("keywords", ""),
                "sensorType":image.properties.get("sensorType", ""),
                "license":image.properties.get("license", ""),
                "title":image.properties.get("title", ""),
                "missionStartDate":image.properties.get("missionStartDate", ""),
                "productType":image.properties.get("productType", ""),
                "startTimeFromAscendingNode":image.properties.get("startTimeFromAscendingNode", ""),
                "completionTimeFromAscendingNode":image.properties.get("completionTimeFromAscendingNode", ""),
                "id":image.properties.get("id", ""),
                "storageStatus":image.properties.get("storageStatus", ""),
                "class_field":image.properties.get("class", ""),
                "dataset":image.properties.get("dataset", ""),
                "expver":image.properties.get("expver", ""),
                "format":image.properties.get('format'),
                "model_level":image.properties.get('model_level'),
                "step":image.properties.get('step'),
                "stream":image.properties.get('stream'),
                "time":image.properties.get('time'),
                "variable":image.properties.get('variable'),
                "downloadLink":image.properties.get('downloadLink'),
                "cloud_cover":image.properties.get('cloud_cover'),
                "thumbnail": image.properties.get('thumbnail')
                })

        # Envoyer le contexte à la page        
        context = {'product_types': product_types, 'search_results':search_results, 'estimated_total_number':estimated_total_number, 'images_list':images_list, 'images_downloaded': images_downloaded}
    
    return render(request, "index.html", context)









def previsualisation_download(request):

    # Dossier courant
    current_dir = os.getcwd()
    product_downloaded = ""

    if request.method == 'POST':
        # Récupération des données du formulaire
        product_ids = request.POST.getlist('product_ids')
        download_path = request.POST.get('download_path')

        download_path = download_path if download_path else current_dir

        # Téléchargement des données
        for product_id in product_ids:
            
            products = search_product_from_id(product_id=product_id)
            # for product in products[0]: #Todo ameliorer
            #     print(product.properties.get('id'))
            #     product_downloaded = product.download()


        #    # Code pour télécharger la donnée satellitaire
        #     data_size = 100 # Taille de la donnée en MB
        #     downloaded = 0 # Quantité téléchargée initialement
        #     with open('data.sat', 'wb') as f:
        #         for chunk in tqdm(response.iter_content(chunk_size=1024), total=data_size / 1024, unit='KB', unit_scale=True):
        #             if chunk: # filter out keep-alive new chunks
        #                 f.write(chunk)
        #                 downloaded += len(chunk)

        
            if len(products[0])!=0 and products[0][0]:
                product_to_download = products[0][0]
                print(product_to_download)
                #product_downloaded =download_image_and_create_session(product_to_download=product_to_download)
                # request.session['task_id'] = transform_data_to_str(product_downloaded.properties.get('id')) #download_task.id
                # print(request.session['task_id'], "request session")
                #print(product_downloaded)
                t = Thread(target=download_image_and_create_session, args=(product_to_download,))
                t.start()
                # inform the user that the download has started
                messages.info(request, 'Le téléchargement a été lancé en arrière-plan, vous serez notifié une fois terminé')
                #return render(request, 'download_confirmation.html', {'product_ids': product_ids, "product_downloaded": t})
            else:
                messages.error(request, 'Aucun produit ne correspond à l\'identifiant spécifié.')
                print("Aucun produit trouvé")
                product_downloaded=[]

            
        # Affichage de la page de confirmation
        return render(request, 'download_confirmation.html', {'product_ids': product_ids, "product_downloaded": t})



    # Téléchargement des données satellites
    #download_path = eo.download(query[0], current_dir)

    # Affichage du résultat du téléchargement
    #context = {'download_path': query, 'metadatas': query }
    return render(request, "previsualisation-download.html")


def liste_images(request):
    # productype = request.GET.get('product_type')    
    date = request.GET.get('date')
    # if productype and date:
    #     images = SatelliteImage.objects.filter(productype = productype, date=date)
    # elif productype:
    #     images = SatelliteImage.objects.filter(productype = productype)
    # elif date :
    #     images = SatelliteImage.objects.filter(date = date)
    # else:
    #     images  = SatelliteImage.objects.all()
    # context = {
    #     "images":images
    # }
    current_dir = os.getcwd()
    print(current_dir)
    new_dir = r"C:\dev\web\python\eodag_download"

    # On change le répertoire de travail courant
    os.chdir(new_dir)
    
    download_path = os.getcwd() # Remplacer avec le chemin vers votre répertoire de téléchargement
    #downloaded_files = [f for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f)) and match_file(f)]
    print(download_path)
    #print(downloaded_files)
    
    # for file in downloaded_files:

    #     # Obtenir les informations sur le fichier
    #     file_info = os.stat(file)

    #     # Afficher toutes les informations disponibles sur le fichier
    #     print("Informations sur le fichier:")
    #     print("  Nom du fichier:", os.path.basename(file))
    #     print("  Taille du fichier:", file_info.st_size, "octets")
    #     print("  Mode:", oct(file_info.st_mode))
    #     print("  Nombre de liens:", file_info.st_nlink)
    #     print("  Propriétaire:", file_info.st_uid, "Groupe:", file_info.st_gid)
    #     print("  Dernier accès:", file_info.st_atime)
    #     print("  Dernière modification:", file_info.st_mtime)
    #     print("  Dernière modification du status:", file_info.st_ctime)
    #     #print("  Blocs alloués:", file_info.st_blocks)
    #     #print("  Blocs alloués (taille):", file_info.st_blksize)
    #     print("  ID du device:", file_info.st_dev)
    #     print("  ID du fichier:", file_info.st_ino)
    

    directory = download_path
    sentinel_files = list_sentinel_files(directory)

   
    context = {
        "downloaded_files": sentinel_files,
    }
    
    return render(request, "liste.html",context)



def waterlevel(request):

    if request.method == "POST":
        # Récupérer le fichier shapefile
        #interest_area_file = request.FILES.get('shapefile')
        interest_area_file=""
        if 'shapefile' in request.FILES:
            interest_area_file = request.FILES['shapefile']
        else:
        
            interest_area_file = "map.wkt"
        start_date =format_date_to_specific_format(request.POST.get('start_date'))
        end_date = format_date_to_specific_format(request.POST.get('end_date'))

        # # Récupérer le fichier transformée
        # shapefile = gpd.read_file(transform_data_to_str(interest_area_file), driver='ESRI Shapefile')

        # # Extraire la géométrie de la zone d'intérêt en utilisant la méthode unary_union() de geopandas
        # geometry = shapefile.unary_union


        dam_nominal = 0.0
        

        # The polygon of the dam is written in wkt format and WGS84 coordinate reference system
        with open(transform_data_to_str(interest_area_file), "r") as f:
            dam_wkt = f.read()

        dam_nominal = shapely.wkt.loads(dam_wkt)

        # inflate the BBOX
        inflate_bbox = 0.1
        minx, miny, maxx, maxy = dam_nominal.bounds

        print(dam_nominal.bounds)
        delx = maxx - minx
        dely = maxy - miny
        minx = minx - delx * inflate_bbox
        maxx = maxx + delx * inflate_bbox
        miny = miny - dely * inflate_bbox
        maxy = maxy + dely * inflate_bbox

        dam_bbox = BBox([minx, miny, maxx, maxy], crs=CRS.WGS84)
        

        download_task = SentinelHubInputTask(
            data_collection=DataCollection.SENTINEL2_L1C,
            bands_feature=(FeatureType.DATA, "BANDS"),
            resolution=20,
            time_difference=datetime.timedelta(days=20),
            maxcc=0.5,
            bands=["B02", "B03", "B04", "B08"],
            additional_data=[(FeatureType.MASK, "dataMask", "IS_DATA"), (FeatureType.MASK, "CLM")],
            cache_folder="cached_data",
        )

        calculate_ndwi = NormalizedDifferenceIndexTask((FeatureType.DATA, "BANDS"), (FeatureType.DATA, "NDWI"), (1, 3))

        dam_gdf = gpd.GeoDataFrame(crs=CRS.WGS84.pyproj_crs(), geometry=[dam_nominal])

        add_nominal_water = VectorToRasterTask(
            dam_gdf,
            (FeatureType.MASK_TIMELESS, "NOMINAL_WATER"),
            values=1,
            raster_shape=(FeatureType.MASK, "IS_DATA"),
            raster_dtype=np.uint8,
        )
        

        # Créer la tâche pour ajouter un masque de données valides à l'EOPatch
        add_valid_mask = AddValidDataMaskTask()
            
            # # Ajouter le masque de données valides à l'EOPatch
            # eopatch = add_valid_mask(eopatch)

        add_coverage = AddValidDataCoverageTask()



        cloud_coverage_threshold = 0.05
        remove_cloudy_scenes = SimpleFilterTask(
            (FeatureType.MASK, "VALID_DATA"), ValidDataCoveragePredicate(cloud_coverage_threshold))
        
    
        water_detection = WaterDetectionTask()

            # To access the final data we use the OutputTask (alternatively we could save the eopatch)
        output_task = OutputTask("final_eopatch")


        workflow_nodes = linearly_connect_tasks(
            download_task,
            calculate_ndwi,
            add_nominal_water,
            add_valid_mask,
            add_coverage,
            remove_cloudy_scenes,
            water_detection,
            output_task,
        )
        
        workflow = EOWorkflow(workflow_nodes)
        

        time_interval = [start_date, end_date]

        # The download task requires additional arguments at execution. These are linked to the node the task is in.
        download_node = workflow_nodes[0]

        result = workflow.execute(
            {
                download_node: {"bbox": dam_bbox, "time_interval": time_interval},
            }
        )
        
      
        patch = result.outputs["final_eopatch"]

        ax, figure_plot_rgb_w_water = plot_rgb_w_water(patch, 0)

        figure_plot_rgb_w_water_0 = figure_plot_rgb_w_water

        ax, figure_plot_rgb_w_water_0 = plot_rgb_w_water(patch, -1)

        figure_plot_rgb_w_water_1 = figure_plot_rgb_w_water

        ax, figure = plot_water_levels(patch, 1.0)


        # Passer l'image en tant que contexte dans la vue
        context = {'image_data': figure, 'figure_plot_rgb_w_water_0':figure_plot_rgb_w_water_0,
                   'figure_plot_rgb_w_water_1':figure_plot_rgb_w_water_1
                   }
        
        return render(request, "niveau-eau.html", context )
    return render(request, "niveau-eau.html" )


def pretraitement(request):
    return render(request, "pre-traitement.html")

def posttraitement(request):
    return render(request, "post-traitement.html")

def classification(request):
    return render(request, "classification.html")

def visualisation(request):
    return render(request, "visualisation.html")


def analyse(request):

    current_dir = os.getcwd()
    # file_dir = current_dir + "/eodag_download1/S1A_EW_GRDM_1SDH_20230302T071553_20230302T071653_047462_05B2BB_BC52"
    # print(file_dir)
    print(BASE_DIR)
    print("="*20)
    download_path = BASE_DIR / "eodag_download1"
         # Récupération du nom du fichier de données
    file_name = f"{download_path}\S1A_EW_GRDM_1SDH_20230302T071553_20230302T071653_047462_05B2BB_BC52"
    file_name = "C:\dev\web\python\eodag_download\C:\dev\web\python\eodag_download\S1A_IW_GRDH_1SDV_20230228T183535_20230228T183600_047440_05B209_BCDE\S1A_IW_GRDH_1SDV_20230228T183535_20230228T183600_047440_05B209_BCDE.SAFE"
    #test = os.path.join(file_name)
    # print(test)
    
    print(file_name)
    # Open the file using rasterio
    # with rio.open(file_name) as src:
    #     # Read the data as a numpy array
    #     data = src.read()
    #     print(data)
    #     # Define the water detection threshold (for NDWI and NDSI)
    #     threshold = 0.2
        
    #     # Get the polarimetric data for the VV polarization
    #     pol_data = data[1]
        
    #     # Compute the NDWI and NDSI
    #     ndwi = (data[0] - pol_data) / (data[0] + pol_data)
    #     ndsi = (pol_data - data[2]) / (pol_data + data[2])
        
    #     # Compute the water mask using the NDWI and NDSI thresholds
    #     water_mask = np.logical_and(ndwi > threshold, ndsi > threshold)
        
    #     # Compute the water level using the water mask and the polarimetric data
    #     water_level = np.median(np.extract(water_mask, pol_data))
    
    # # Return the water level as a JSON response
    # data = {
    #     'water_level': water_level
    # }
    # print(data)

   
    # # Lecture des données avec xarray
    # ds = xr.open_dataset(file_name, engine="netcdf4")
    # print(ds)
    # # Extraction des dimensions et variables pertinentes
    # time = ds['time'].values
    # lat = ds['latitude'].values
    # lon = ds['longitude'].values
    # vv = ds['vv'].values
    # vh = ds['vh'].values

    # # Calcul de statistiques descriptives
    # vv_mean = np.mean(vv)
    # vh_mean = np.mean(vh)
    # vv_std = np.std(vv)
    # vh_std = np.std(vh)
    # vv_min = np.min(vv)
    # vh_min = np.min(vh)
    # vv_max = np.max(vv)
    # vh_max = np.max(vh)

    # # Génération de graphiques pour les données
    # fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
    # ax[0].imshow(vv, cmap='gray')
    # ax[0].set_title('Amplitude de la polarisation VV')
    # ax[0].axis('off')
    # ax[1].imshow(vh, cmap='gray')
    # ax[1].set_title('Amplitude de la polarisation VH')
    # ax[1].axis('off')
    # fig.tight_layout()

    # # Encodage du graphique en base64
    # import io
    # from django.core.files.base import ContentFile
    # buffer = io.BytesIO()
    # plt.savefig(buffer, format='png')
    # image_png = buffer.getvalue()
    # buffer.close()
    # graphic = ContentFile(image_png, 'sentinel1.png')

    # # Création du contexte pour le template
    # context = {
    #     'file_name': file_name,
    #     'vv_mean': vv_mean,
    #     'vv_std': vv_std,
    #     'vv_min': vv_min,
    #     'vv_max': vv_max,
    #     'vh_mean': vh_mean,
    #     'vh_std': vh_std,
    #     'vh_min': vh_min,
    #     'vh_max': vh_max,
    #     'graphic': graphic
    # }

    # Renvoi du template avec le contexte
    return render(request, 'analyse.html')


def contact(request):
    return render(request, "contact.html")


def download_satellite_image_from_id(request, image_id):

    

    product_id =transform_data_to_str(image_id)

    print(product_id)

    # # verifier l'existence de l'image avec son id
    # products = eodag.search(product_id=product_id)

    # print("++++")
    # for product in products:

    #     print(product)
    # #products[0].download()
    # # for product in products:
    # #     print(product)
    # #     #print(product.remote_location)
    # #     # tetee= EOProduct.get_quicklook(product)
    # #     # print(tetee)

    # #     product.download()
    # #     # eodag.download(product[0])# spécifier le chemin
    
            
    products = search_product_from_id(product_id=product_id)



    # if len(products[0])!=0 and products[0][0]:
    #     product_to_download = products[0][0]
    #     print(product_to_download)
    #     # product_downloaded = download_image_and_create_session(product_to_download=product_to_download)
    #     # print(product_downloaded)
    #     # scheduler = BlockingScheduler()
    #     # scheduler.add_job(download_image_and_create_session(product_to_download=product_to_download))
    #     # scheduler.start()
    #     # print('fin tache')

    #     download_image_and_create_session(product_to_download=product_to_download).delay()
    #     # messages.info(request, 'Le téléchargement des données a été lancé en arrière-plan.')

    #     return render(request, 'download_confirmation.html', {'product_ids': image_id})

    if len(products[0]) != 0 and products[0][0]:
        product_to_download = products[0][0]
        # create a thread to download the product
        t = Thread(target=download_image_and_create_session, args=(product_to_download,))
        t.start()
        # inform the user that the download has started
        messages.info(request, 'Le téléchargement a été lancé en arrière-plan, vous serez notifié une fois terminé')
    else:
        messages.error(request, 'Aucun produit ne correspond à l\'identifiant spécifié.')
    
    return render(request, 'download_confirmation.html', {'product_ids': image_id})

