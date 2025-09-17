import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.datasets import make_classification, make_regression
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from mpl_toolkits.mplot3d import Axes3D

# Set style
plt.style.use('default')
sns.set_palette("husl")

# Generate the same datasets as before
def create_classification_dataset(n_samples=1000, n_features=50):
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=25,
        n_redundant=10,
        n_clusters_per_class=1,
        random_state=42
    )
    return X, y

def create_regression_dataset(n_samples=1000, n_features=50):
    X, y = make_regression(
        n_samples=n_samples,
        n_features=n_features,
        noise=0.1,
        random_state=42
    )
    return X, y

def create_mixed_dataset(n_samples=1000):
    np.random.seed(42)

    # Continuous features
    continuous_features = np.random.normal(0, 1, (n_samples, 30))

    # Categorical features (encoded as numbers)
    categorical_features = np.random.choice([0, 1, 2, 3, 4], size=(n_samples, 10))

    # Binary features
    binary_features = np.random.choice([0, 1], size=(n_samples, 10))

    # Combine all features
    X = np.hstack([continuous_features, categorical_features, binary_features])

    # Create target
    y = (continuous_features[:, 0] * 0.5 +
         continuous_features[:, 1] * 0.3 +
         binary_features[:, 0] * 0.2 +
         np.random.normal(0, 0.1, n_samples))

    return X, y

def create_ultra_high_dim_dataset(n_samples=1000, n_features=100):
    np.random.seed(42)

    # Different feature types
    normal_features = np.random.normal(0, 1, (n_samples, n_features//4))
    exp_features = np.random.exponential(1, (n_samples, n_features//4))
    uniform_features = np.random.uniform(-1, 1, (n_samples, n_features//4))
    poly_features = np.random.normal(0, 1, (n_samples, n_features//4)) ** 2

    X = np.hstack([normal_features, exp_features, uniform_features, poly_features])

    # Create target
    y = (X[:, 0] * 0.3 + X[:, 25] * 0.2 + X[:, 50] * 0.1 +
         np.random.normal(0, 0.1, n_samples))

    return X, y

# New manifold datasets
def create_swiss_roll(n_samples=1000, noise=0.1):
    """Create Swiss Roll manifold dataset"""
    np.random.seed(42)
    t = 1.5 * np.pi * (1 + 2 * np.random.random(n_samples))
    height = 21 * np.random.random(n_samples)

    X = np.zeros((n_samples, 3))
    X[:, 0] = t * np.cos(t)
    X[:, 1] = height
    X[:, 2] = t * np.sin(t)

    # Add noise
    X += noise * np.random.normal(size=X.shape)

    # Color based on position along the roll
    y = t

    return X, y

def create_sphere_dataset(n_samples=800, noise=0.1):
    """Create points on a sphere surface"""
    np.random.seed(42)

    # Generate random points on unit sphere
    u = np.random.random(n_samples)
    v = np.random.random(n_samples)

    theta = 2 * np.pi * u  # azimuthal angle
    phi = np.arccos(2 * v - 1)  # polar angle

    X = np.zeros((n_samples, 3))
    X[:, 0] = np.sin(phi) * np.cos(theta)
    X[:, 1] = np.sin(phi) * np.sin(theta)
    X[:, 2] = np.cos(phi)

    # Add noise
    X += noise * np.random.normal(size=X.shape)

    # Color based on z-coordinate
    y = X[:, 2]

    return X, y

def create_s_curve(n_samples=1000, noise=0.1):
    """Create S-curve manifold dataset"""
    np.random.seed(42)

    t = 3 * np.pi * (np.random.random(n_samples) - 0.5)
    height = 2 * np.random.random(n_samples)

    X = np.zeros((n_samples, 3))
    X[:, 0] = np.sin(t)
    X[:, 1] = height
    X[:, 2] = np.sign(t) * (np.cos(t) - 1)

    # Add noise
    X += noise * np.random.normal(size=X.shape)

    # Color based on parameter t
    y = t

    return X, y

def create_anilox_x(n_samples=1000):
    """Create Anilox X pattern - circular rings in X direction"""
    np.random.seed(42)

    # Create circular pattern
    theta = np.random.random(n_samples) * 2 * np.pi
    r = np.random.random(n_samples) * 3 + 1  # radius from 1 to 4

    X = np.zeros((n_samples, 3))
    X[:, 0] = r * np.cos(theta)  # X varies in circular pattern
    X[:, 1] = r * np.sin(theta)
    X[:, 2] = np.random.normal(0, 0.5, n_samples)  # Small Z variation

    # Color based on radius
    y = r

    return X, y

def create_anilox_y(n_samples=1000):
    """Create Anilox Y pattern - spiral in Y direction"""
    np.random.seed(42)

    # Create spiral pattern
    t = np.random.random(n_samples) * 4 * np.pi
    r = t / (2 * np.pi)  # radius increases with angle

    X = np.zeros((n_samples, 3))
    X[:, 0] = r * np.cos(t)
    X[:, 1] = r * np.sin(t) + t / 2  # Y varies with spiral
    X[:, 2] = np.random.normal(0, 0.3, n_samples)

    # Color based on spiral parameter
    y = t

    return X, y

def create_anilox_z(n_samples=1000):
    """Create Anilox Z pattern - helical structure in Z direction"""
    np.random.seed(42)

    # Create helical pattern
    t = np.random.random(n_samples) * 6 * np.pi
    r = 2 + np.sin(t * 2) * 0.5  # varying radius

    X = np.zeros((n_samples, 3))
    X[:, 0] = r * np.cos(t)
    X[:, 1] = r * np.sin(t)
    X[:, 2] = t / 2  # Z varies linearly with helix

    # Color based on height
    y = X[:, 2]

    return X, y