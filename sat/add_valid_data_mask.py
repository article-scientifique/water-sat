import base64
import io
import os
import numpy as np
from eolearn.core import EOTask, FeatureType
from skimage.filters import threshold_otsu

from skimage.filters import sobel
from skimage.morphology import closing, disk

import matplotlib.pyplot as plt


class AddValidDataMaskTask(EOTask):
    def execute(self, eopatch):
        is_data_mask = eopatch[FeatureType.MASK, "IS_DATA"].astype(bool)
        cloud_mask = ~eopatch[FeatureType.MASK, "CLM"].astype(bool)
        eopatch[FeatureType.MASK, "VALID_DATA"] = np.logical_and(is_data_mask, cloud_mask)
        return eopatch



def calculate_coverage(array):
    return 1.0 - np.count_nonzero(array) / np.size(array)


class AddValidDataCoverageTask(EOTask):
    def execute(self, eopatch):
        valid_data = eopatch[FeatureType.MASK, "VALID_DATA"]
        time, height, width, channels = valid_data.shape

        coverage = np.apply_along_axis(calculate_coverage, 1, valid_data.reshape((time, height * width * channels)))

        eopatch[FeatureType.SCALAR, "COVERAGE"] = coverage[:, np.newaxis]
        return eopatch


class ValidDataCoveragePredicate:
    def __init__(self, threshold):
        self.threshold = threshold

    def __call__(self, array):
        return calculate_coverage(array) < self.threshold



class WaterDetectionTask(EOTask):
    @staticmethod
    def detect_water(ndwi):
        """Very simple water detector based on Otsu thresholding method of NDWI."""
        otsu_thr = 1.0
        if len(np.unique(ndwi)) > 1:
            ndwi[np.isnan(ndwi)] = -1
            otsu_thr = threshold_otsu(ndwi)

        return ndwi > otsu_thr

    def execute(self, eopatch):
        water_masks = np.asarray([self.detect_water(ndwi[..., 0]) for ndwi in eopatch.data["NDWI"]])

        # we're only interested in the water within the dam borders
        water_masks = water_masks[..., np.newaxis] * eopatch.mask_timeless["NOMINAL_WATER"]

        water_levels = np.asarray(
            [np.count_nonzero(mask) / np.count_nonzero(eopatch.mask_timeless["NOMINAL_WATER"]) for mask in water_masks]
        )

        eopatch[FeatureType.MASK, "WATER_MASK"] = water_masks
        eopatch[FeatureType.SCALAR, "WATER_LEVEL"] = water_levels[..., np.newaxis]

        return eopatch

def plot_rgb_w_water(eopatch, idx):
    ratio = np.abs(eopatch.bbox.max_x - eopatch.bbox.min_x) / np.abs(eopatch.bbox.max_y - eopatch.bbox.min_y)
    fig, ax = plt.subplots(figsize=(ratio * 10, 10))

    ax.imshow(np.clip(2.5 * eopatch.data["BANDS"][..., [2, 1, 0]][idx], 0, 1))

    observed = closing(eopatch.mask["WATER_MASK"][idx, ..., 0], disk(1))
    nominal = sobel(eopatch.mask_timeless["NOMINAL_WATER"][..., 0])
    observed = sobel(observed)
    nominal = np.ma.masked_where(~nominal.astype(int), nominal)
    observed = np.ma.masked_where(~observed.astype(int), observed)

    ax.imshow(nominal, cmap=plt.cm.Reds)
    ax.imshow(observed, cmap=plt.cm.Blues)
    ax.axis("off")
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)        
    figure_plot_rgb_w_water = base64.b64encode(buf.read()).decode('utf-8')


    return ax, figure_plot_rgb_w_water
    


def plot_water_levels(eopatch, max_coverage=1.0):
    fig, ax = plt.subplots(figsize=(20, 7))

    dates = np.asarray(eopatch.timestamp)
    ax.plot(
        dates[eopatch.scalar["COVERAGE"][..., 0] < max_coverage],
        eopatch.scalar["WATER_LEVEL"][eopatch.scalar["COVERAGE"][..., 0] < max_coverage],
        "bo-",
        alpha=0.7,
    )
    ax.plot(
        dates[eopatch.scalar["COVERAGE"][..., 0] < max_coverage],
        eopatch.scalar["COVERAGE"][eopatch.scalar["COVERAGE"][..., 0] < max_coverage],
        "--",
        color="gray",
        alpha=0.7,
    )
    ax.set_ylim(0.0, 1.1)
    ax.set_xlabel("Date")
    ax.set_ylabel("Niveau d'eau")
    ax.set_title("Niveaux d'eau du barrage")
    ax.grid(axis="y")

            # Convertir la figure en un objet BytesIO
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)        
    figure = base64.b64encode(buf.read()).decode('utf-8')


    return ax, figure