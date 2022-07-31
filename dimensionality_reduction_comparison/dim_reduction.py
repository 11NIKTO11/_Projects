import numpy as np
from sklearn.decomposition import PCA, KernelPCA
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.preprocessing import normalize
from sklearn.manifold import TSNE
import umap
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.feature_selection import VarianceThreshold
from sklearn.neighbors import KNeighborsClassifier
from nxcurve import quality_curve

import fruits_dataset as od

KERNELS = ["linear", "rbf", "poly"]
FLOWER_FEATURES = "dev_flower_feature_vectors.npy"
FLOWER_CLASSES = "dev_flower_classes.npy"
FLOWER_CLASS_NAMES = ["daisy","dandelion", "rose", "sunflower", "tulip"]

ALZHEIMER_FEATURES = "dev_alzheimer_feature_vectorsB0-ut.npy"
ALZHEIMER_CLASSES = "dev_alzheimer_classesB0-ut.npy"
ALZHEIMER_CLASS_NAMES = [ "Mild_Demented", "Moderate_Demented", "Non_Demented", "Very_Mild_Demented"  ]

FRUITS_FEATURES = "dev_fruit_feature_vectorsB0-10K.npy"
FRUITS_CLASSES = "dev_fruit_classesB0-10K.npy"
FRUITS_CLASS_NAMES = od.FRUITS.LABELS

MARK_SIZE = 7

FEATURES =      ALZHEIMER_FEATURES
CLASSES =       ALZHEIMER_CLASSES
CLASS_NAMES =   ALZHEIMER_CLASS_NAMES

PREDICTIONS=False

PLOT_CMAP=plt.get_cmap('jet')

#todo comparation based on separability (via kNN)
#todo comparation on crowding problem - distance
#todo ISOMAP

def pca_view(features, labels):
    pca = PCA(n_components=2)
    transformed = pca.fit_transform(normalize(features))
    plt.title(f"PCA")
    scatter = plt.scatter(transformed[:,0], transformed[:,1], c = labels, s = MARK_SIZE,cmap=PLOT_CMAP)
    #plt.legend(scatter.legend_elements()[0],CLASS_NAMES)
    plt.legend(
        scatter.legend_elements()[0],
        np.array(CLASS_NAMES)[
            [int(''.join(i for i in x if i.isdigit())) for x in scatter.legend_elements()[1]]
        ]
    )
    plt.show()
    
    eval_reduction(features, transformed, labels)

def kernel_pca_view(features, labels):
    for kernel in KERNELS:
        pca = KernelPCA(n_components=2)
        transformed = pca.fit_transform(normalize(features))
        plt.title(f"PCA with {kernel} kernel")
        scatter =plt.scatter(transformed[:,0], transformed[:,1], c = labels, s = MARK_SIZE,cmap=PLOT_CMAP)
        plt.legend(
            scatter.legend_elements()[0],
            np.array(CLASS_NAMES)[
                [int(''.join(i for i in x if i.isdigit())) for x in scatter.legend_elements()[1]]
            ]
        )
        plt.show()


def t_sne_view(features, labels):
    #todo modify perplexity, default 30
    t_sne = TSNE(n_components=2, init = "pca")
    transformed = t_sne.fit_transform(normalize(features))
    plt.title(f"t-SNE")
    scatter =plt.scatter(transformed[:,0], transformed[:,1], c = labels, s = MARK_SIZE,cmap=PLOT_CMAP)
    plt.legend(
        scatter.legend_elements()[0],
        np.array(CLASS_NAMES)[
            [int(''.join(i for i in x if i.isdigit())) for x in scatter.legend_elements()[1]]
        ]
    )
    plt.show()
    
    eval_reduction(features, transformed, labels)

def umap_view(features, labels):
    #todo modify perplexity, default 30
    um = umap.UMAP(n_components=2)
    transformed = um.fit_transform(normalize(features))
    plt.title(f"Umap")
    scatter =plt.scatter(transformed[:,0], transformed[:,1], c = labels, s = MARK_SIZE,cmap=PLOT_CMAP)
    plt.legend(
        scatter.legend_elements()[0],
        np.array(CLASS_NAMES)[
            [int(''.join(i for i in x if i.isdigit())) for x in scatter.legend_elements()[1]]
        ]
    )
    plt.show()
    eval_reduction(features, transformed, labels)

def lda_view(features, labels):
    #uses classes - kind of cheating? 
    lda = LinearDiscriminantAnalysis(n_components=2)
    transformed = lda.fit_transform(normalize(features), labels)
    plt.title(f"lda (svd)")
    scatter =plt.scatter(transformed[:,0], transformed[:,1], c = labels, s = MARK_SIZE,cmap=PLOT_CMAP)
    plt.legend(
        scatter.legend_elements()[0],
        np.array(CLASS_NAMES)[
            [int(''.join(i for i in x if i.isdigit())) for x in scatter.legend_elements()[1]]
        ]
    )
    plt.show()
    eval_reduction(features, transformed, labels)


def variance_threshold_view(features, labels):
    vt = VarianceThreshold()
    transformed = vt.fit_transform(features, labels)
    plt.title(f"variance thresholding")
    scatter = plt.scatter(transformed[:,0], transformed[:,1], c = labels, s = MARK_SIZE,cmap=PLOT_CMAP)
    plt.legend(
        scatter.legend_elements()[0],
        np.array(CLASS_NAMES)[
            [int(''.join(i for i in x if i.isdigit())) for x in scatter.legend_elements()[1]]
        ]
    )
    plt.show()
    eval_reduction(features, transformed, labels)


def eval_reduction(data, data2D, labels):
    
    if PREDICTIONS:
        prediction = np.argmax(np.load("dev_alzheimer_predictionsB0-ut.npy"),axis=1)
        select =(labels==prediction)
        plt.scatter(data2D[select,0], data2D[select,1], c = labels[select], s = MARK_SIZE,cmap=PLOT_CMAP)
        select =np.invert(select)
        plt.scatter(data2D[select,0], data2D[select,1], c = "grey", s = MARK_SIZE,cmap=PLOT_CMAP)
        plt.show()
    
    
    kNN = KNeighborsClassifier(n_neighbors = 5)
    kNN.fit(data2D, labels)
    predictions = kNN.predict(data2D)
    err_cout = np.sum(predictions != labels)
    
    print(f"k-NN Error rate of the method = {err_cout/len(labels)}")
    view_embedding_quality_curves(data, data2D)

# Copied from https://timsainburg.com/coranking-matrix-python-numba.html
#region Copied code

from sklearn.metrics import pairwise_distances, pairwise_distances_chunked
from joblib import Parallel, delayed
import numba
from tqdm.autonotebook import tqdm

def compute_ranking_matrix_parallel(D):
    """ Compute ranking matrix in parallel. Input (D) is distance matrix
    """
    # if data is small, no need for parallel
    if len(D) > 1000:
        n_jobs = -1
    else:
        n_jobs = 1
    r1 = Parallel(n_jobs, prefer="threads")(
            delayed(np.argsort)(i)
            for i in tqdm(D.T, desc = "computing rank matrix", leave=False)
        )
    r2 = Parallel(n_jobs, prefer="threads")(
            delayed(np.argsort)(i)
            for i in tqdm(r1, desc = "computing rank matrix", leave=False)
        )
    # write as a single array
    r2_array = np.zeros((len(r2), len(r2[0])), dtype='int32')
    for i, r2row in enumerate(tqdm(r2, desc="concatenating rank matrix", leave=False)):
        r2_array[i] = r2row
    return r2_array


@numba.njit(fastmath=True)
def populate_Q(Q, i, m, R1, R2):
    """ populate coranking matrix using numba for speed
    """
    for j in range(m):
        k = R1[i, j]
        l = R2[i, j]
        Q[k, l] += 1
    return Q

def iterate_compute_distances(data):
    """ Compute pairwise distance matrix iteratively, so we can see progress
    """
    n = len(data)
    D = np.zeros((n, n), dtype='float32')
    col = 0
    with tqdm(desc="computing pairwise distances", leave=False) as pbar:
        for i, distances in enumerate(
                pairwise_distances_chunked(data, n_jobs=-1),
            ):
            D[col : col + len(distances)] = distances
            col += len(distances)
            if i ==0:
                pbar.total = int(len(data) / len(distances))
            pbar.update(1)
    return D

def compute_coranking_matrix(data_ld, data_hd = None, D_hd = None):
    """ Compute the full coranking matrix
    """
   
    # compute pairwise probabilities
    if D_hd is None:
        D_hd = iterate_compute_distances(data_hd)
    
    D_ld =iterate_compute_distances(data_ld)
    n = len(D_ld)
    # compute the ranking matrix for high and low D
    rm_hd = compute_ranking_matrix_parallel(D_hd)
    rm_ld = compute_ranking_matrix_parallel(D_ld)
    
    # compute coranking matrix from_ranking matrix
    m = len(rm_hd)
    Q = np.zeros(rm_hd.shape, dtype='int16')
    for i in tqdm(range(m), desc="computing coranking matrix"):
        Q = populate_Q(Q,i, m, rm_hd, rm_ld)
        
    Q = Q[1:,1:]
    return Q
#endregion

def view_embedding_quality_curves(data, embedding, n_neighbors = 20):
    # quality_curve(data,embedding, n_neighbors,'r',True)
    # quality_curve(data,embedding, n_neighbors,'q',True)
    # quality_curve(data,embedding, n_neighbors,'b',True)
    
    Q_ = compute_coranking_matrix(data_ld=embedding, data_hd = data)
    plt.matshow(np.log(Q_+1e-2),cmap=plt.get_cmap('hot'))
    plt.show()

feature_vectors = np.load(file = FEATURES)
classes = np.load(CLASSES)


# pca_view(feature_vectors, classes)
t_sne_view(feature_vectors, classes)
umap_view(feature_vectors, classes)
# lda_view(feature_vectors, classes)
# variance_threshold_view(feature_vectors, classes)