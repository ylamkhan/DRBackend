# app/services/dataset_store.py

from typing import List, Dict
from sklearn.decomposition import PCA, TruncatedSVD, FastICA, FactorAnalysis, NMF, KernelPCA
from sklearn.manifold import TSNE, Isomap, LocallyLinearEmbedding, SpectralEmbedding
from sklearn.random_projection import GaussianRandomProjection
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.preprocessing import StandardScaler
import numpy as np
import warnings
import asyncio
from app.api.websocket import safe_notify_clients_projection_ready

warnings.filterwarnings("ignore")


class Dataset:
    def __init__(self, name: str, X: List[List[float]], y: List[str], defer_computation: bool = False):
        self.name = name
        self.X = np.array(X)
        self.y = y
        self.projections = {
            "kernel": {"2d": {}, "3d": {}},
            "reduced": {"2d": {}, "3d": {}}
        }
        self.ready = False
        self._cancel_flag = False

        if not defer_computation:
            asyncio.create_task(self.compute_projections())  # async launch if not deferred

    def cancel(self):
        print('cancell ', self.name)
        self._cancel_flag = True
        self.ready = False

    async def compute_projections(self):
        if self._cancel_flag:
            return
        try:
            await asyncio.to_thread(self._compute_all_projections)
        except Exception as e:
            print(f"Computation stopped: {e}")
            return

        if not self._cancel_flag:
            self.ready = True
            print(self.ready, self.name)
            safe_notify_clients_projection_ready(self.name)

    def get_data(self):
        return {
            "X": self.X.tolist(),
            "y": self.y,
            "projections": self.projections,
            "ready": self.ready
        }

    def _check_cancel(self):
        if self._cancel_flag:
            raise Exception("Cancelled")

    def _compute_all_projections(self):
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)

        # Reduced-dimension projections
        self._check_cancel()
        self._add_projection("reduced", "2d", "PCA", PCA(n_components=2).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "3d", "PCA", PCA(n_components=3).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "2d", "Truncated SVD", TruncatedSVD(n_components=2).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "3d", "Truncated SVD", TruncatedSVD(n_components=3).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "2d", "ICA", FastICA(n_components=2).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "3d", "ICA", FastICA(n_components=3).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "2d", "Factor Analysis", FactorAnalysis(n_components=2).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "3d", "Factor Analysis", FactorAnalysis(n_components=3).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "2d", "NMF", NMF(n_components=2, init='random', random_state=0).fit_transform(np.abs(X_scaled)))

        self._check_cancel()
        self._add_projection("reduced", "3d", "NMF", NMF(n_components=3, init='random', random_state=0).fit_transform(np.abs(X_scaled)))

        self._check_cancel()
        self._add_projection("reduced", "2d", "Random Projection", GaussianRandomProjection(n_components=2).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("reduced", "3d", "Random Projection", GaussianRandomProjection(n_components=3).fit_transform(X_scaled))

        self._check_cancel()
        if len(set(self.y)) < len(X_scaled):
            try:
                self._add_projection("reduced", "2d", "LDA", LDA(n_components=2).fit_transform(X_scaled, self.y))
                self._add_projection("reduced", "3d", "LDA", LDA(n_components=3).fit_transform(X_scaled, self.y))
            except Exception:
                pass

        # Kernel projections
        self._check_cancel()
        self._add_projection("kernel", "2d", "Kernel PCA", KernelPCA(n_components=2, kernel="rbf").fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "3d", "Kernel PCA", KernelPCA(n_components=3, kernel="rbf").fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "2d", "t-SNE", TSNE(n_components=2, perplexity=30).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "3d", "t-SNE", TSNE(n_components=3, perplexity=30).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "2d", "UMAP", self._try_umap(X_scaled, 2))

        self._check_cancel()
        self._add_projection("kernel", "3d", "UMAP", self._try_umap(X_scaled, 3))

        self._check_cancel()
        self._add_projection("kernel", "2d", "Isomap", Isomap(n_components=2).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "3d", "Isomap", Isomap(n_components=3).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "2d", "LLE", LocallyLinearEmbedding(n_components=2).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "3d", "LLE", LocallyLinearEmbedding(n_components=3).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "2d", "Spectral Embedding", SpectralEmbedding(n_components=2).fit_transform(X_scaled))

        self._check_cancel()
        self._add_projection("kernel", "3d", "Spectral Embedding", SpectralEmbedding(n_components=3).fit_transform(X_scaled))

    def _try_umap(self, X, n_components):
        try:
            import umap
            reducer = umap.UMAP(n_components=n_components)
            return reducer.fit_transform(X)
        except ImportError:
            return []

    def _add_projection(self, mix_type: str, dim: str, algo_name: str, data):
        if data is not None and len(data) > 0:
            self.projections[mix_type][dim][algo_name] = data.tolist()
