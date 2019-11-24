# -*- coding: utf-8 -*-

from numpy import *
from scipy.stats import norm
import math
from sklearn.feature_extraction import image
import time
import heapq

def dissimilarity_weights(m):
    w = int((m-1)/2)
    v = range(-w, w+1)
    [x, y] = meshgrid(v, v)
    g=norm.pdf(x)*norm.pdf(y)
    return g

def patches_dissimilarity(p1, p2, alpha, g):
    d2 = (p1-p2)**2
    weighted_d2 = g*d2
    dissim = -alpha*weighted_d2.sum()
    return dissim

def idx1d_to_idx2d(idx, M, N):
    j = int(floor(idx/M))
    i = idx - j*M
    return [i, j]

def idx2d_to_idx1d(i, j, M, N):
    idx = int(M*j + i)
    return idx


def try_improve_a_from_b(idx_a, idx_b, heap_a, heap_b,
                         patches_t, patches, M, N, alpha, g):
    k = len(heap_a)
    p0 = patches_t[idx_a, :, :]# patch around pixel idx_a
    for nn in range(0,k):
        # compute the 2D offset corresponding idx_b's nn-est nearest neighbour
        offs_b = heap_b[nn][1]
        idx_d = int(idx_a + offs_b)
        idx_d = max(idx_d, 0)
        idx_d = min(idx_d, patches.shape[0]-1)
        offs_b = idx_d - idx_a
        p2 = patches[idx_d, :, :]# patch around the new pixel to compare to idx_a
        w_b = patches_dissimilarity(p0, p2, alpha, g)# new weight
        if w_b > heap_a[0][0] and not ((w_b, offs_b) in heap_a):
            heapq.heapreplace(heap_a, (w_b, offs_b))
    return heap_a



def build_new_offsets(idx, heap0, L, l, q, M, N):
    new_offsets = zeros(len(heap0))
    for k in range(0, len(heap0)):
        idx2 = int(idx) + int(heap0[k][1])
        [i2, j2] = idx1d_to_idx2d(idx2, M, N)
        [u, v] = (L*l**q)*(2*random.rand(2,) -1)
        [i3, j3] = array([i2, j2]) + array([u, v])
        i3 = int(i3)
        j3 = int(j3)
        i3 = max(0, i3)
        i3 = min(M-1, i3)
        j3 = max(0, j3)
        j3 = min(N-1, j3)
        idx3 = idx2d_to_idx1d(i3, j3, M, N)
        new_offsets[k] = idx3 - idx
    return new_offsets


def search_around(idx, heap0, patches_t, patches, M, N, alpha, g):
    L = 30
    l= 0.5
    q_range = arange(0, 3)
    cand_offsets = empty((q_range.shape[0], len(heap0)))
    c = 0
    for q in q_range:
        cand_offsets[c,] = build_new_offsets(idx, heap0, L, l, q, M, N)
        c = c+1
    for c in range(0,3):
        heap1 = []
        for k in range(0, len(heap0)):
            heap1.append((0, cand_offsets[c, k]))
        new_heap0 =  try_improve_a_from_b(idx, idx, heap0,
                                          heap1, patches_t, patches,
                                          M, N, alpha, g)
    return new_heap0


def initialize_offsets(M_t, N_t, M, N, k):
    n_t = M_t*N_t
    n = M*N
    offsets = floor((n-1)*random.rand(n_t,k)) - tile(arange(0, n_t), (k, 1)).T
    offsets.astype(int)
    return offsets

def initialize_weights(patches_t, patches, offsets, alpha, g):
    [n_t, k] = offsets.shape
    weights = ones([n_t, k])
    for i in range(0, n_t):
        p0 = patches_t[i, :, :]
        for j in range(0, k):
            i2 = int(i + offsets[i, j])
            p2 = patches[i2, :, :]
            weights[i, j] = patches_dissimilarity(p0, p2, alpha, g)
    return weights

def initialize_heap(offsets, weights):
    all_heaps = []
    [n_t, k] = offsets.shape
    for i in range(0,n_t):
        h = []
        for j in range(0, k):
            heapq.heappush(h, (weights[i, j], offsets[i, j]))
        all_heaps.append(h)
    return all_heaps


def propagate(iter_n, current_heaps, M_t, N_t, M, N, patches_t, patches, alpha, g):
    if iter_n % 2:
        Jrange = range(1, N_t)
        Irange = range(1, M_t)
        pix_shift = -1
    else:
        Jrange = arange(N_t-2, -1, -1)
        Irange = arange(M_t-2, -1, -1)
        pix_shift = 1

    for j0 in Jrange:
        for i0 in Irange:
            idx_0 = idx2d_to_idx1d(i0, j0, M_t, N_t)
            idx_1 = idx2d_to_idx1d(i0+pix_shift, j0, M_t, N_t)
            idx_2 = idx2d_to_idx1d(i0, j0+pix_shift, M_t, N_t)
            heap0 = current_heaps[idx_0]
            heap1 = current_heaps[idx_1]
            heap2 = current_heaps[idx_2]
            heap0 = try_improve_a_from_b(idx_0, idx_1, heap0,
                                          heap1, patches_t, patches,
                                          M, N, alpha, g)
            current_heaps[idx_0] = try_improve_a_from_b(idx_0, idx_2, heap0,
                                                         heap2, patches_t, patches,
                                                         M, N, alpha, g)
    return current_heaps

def random_search(current_heaps, M_t, N_t, M, N, patches_t, patches, alpha, g):
    n_t = M_t*N_t
    new_heaps = []
    for idx in range(0, n_t):
        heap_0 = current_heaps[idx]
        new_heap0 = search_around(idx, heap_0, patches_t, patches, M, N, alpha, g)
        new_heaps.append(new_heap0)
    return new_heaps

def heaps_to_weights_and_offsets(all_heaps):
    n = len(all_heaps)
    k = len(all_heaps[0])
    offsets = zeros((n, k), dtype=int)
    weights = zeros((n, k))
    for i in range(0,n):
        for j in range(0,k):
            weights[i, j] = all_heaps[i][j][0]
            offsets[i, j] = int(all_heaps[i][j][1])
    offsets.astype(int)
    return offsets, weights

def patch_match(im, im_t, m, knn):
    w = int((m-1)/2)
    alpha = 0.01
    g = dissimilarity_weights(m)
    im_bis = pad(im, [w, w], 'symmetric')
    im_bis_t = pad(im_t, [w, w], 'symmetric')
    [M, N] = im.shape
    n = M*N
    [M_t, N_t] = im_t.shape
    n_t = M_t*N_t
    #get list of patches for source and target images
    patches = image.extract_patches_2d(im_bis.T, (m, m))
    for i in range(0,n):
        patches[i]=patches[i].T
    patches_t = image.extract_patches_2d(im_bis_t.T, (m, m))
    for i in range(0,n_t):
        patches_t[i]=patches_t[i].T
    print(patches.shape)
    offsets_init = initialize_offsets(M_t, N_t, M, N, knn)
    weights_init = initialize_weights(patches_t, patches, offsets_init, alpha, g)
    all_heaps = initialize_heap(offsets_init, weights_init)
    new_heaps = propagate(1, all_heaps, M_t, N_t, M, N, patches_t, patches, alpha, g)
    new_heaps = random_search(new_heaps, M_t, N_t, M, N, patches_t, patches, alpha, g)
    new_heaps = propagate(2, new_heaps, M_t, N_t, M, N, patches_t, patches, alpha, g)
    offsets, weights = heaps_to_weights_and_offsets(all_heaps)
    return offsets
