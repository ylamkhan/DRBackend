def normalize_algorithm_name(name: str) -> str:
    name = name.upper().replace("-", "")
    if name == "TSNE":
        return "TSNE"
    return name

def compute_continuity(X_high, X_low, n_neighbors=5):
    from sklearn.neighbors import NearestNeighbors
    nbrs_high = NearestNeighbors(n_neighbors=n_neighbors + 1).fit(X_high)
    _, indices_high = nbrs_high.kneighbors(X_high)
    nbrs_low = NearestNeighbors(n_neighbors=n_neighbors + 1).fit(X_low)
    _, indices_low = nbrs_low.kneighbors(X_low)

    continuity = 0.0
    n_samples = X_high.shape[0]
    for i in range(n_samples):
        neighbors_high = set(indices_high[i][1:])
        neighbors_low = set(indices_low[i][1:])
        common_neighbors = len(neighbors_high.intersection(neighbors_low))
        continuity += common_neighbors / n_neighbors
    return continuity / n_samples