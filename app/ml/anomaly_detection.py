"""
AgentAuth Anomaly Detection

Unsupervised anomaly detection for unusual patterns.
Detects novel fraud patterns without labeled data.

Algorithms:
- Isolation Forest (fast, interpretable)
- Autoencoder (deep learning, pattern capture)
- Statistical outlier detection
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import math
import random
from datetime import datetime, timezone


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    
    is_anomaly: bool
    anomaly_score: float  # 0.0 - 1.0 (higher = more anomalous)
    method: str  # "isolation_forest", "autoencoder", "statistical"
    
    # Details
    isolation_score: Optional[float] = None
    reconstruction_error: Optional[float] = None
    z_scores: Optional[Dict[str, float]] = None
    
    # Metadata
    inference_time_ms: float = 0.0
    
    def to_dict(self) -> dict:
        result = {
            "is_anomaly": self.is_anomaly,
            "anomaly_score": round(self.anomaly_score, 4),
            "method": self.method,
            "inference_time_ms": round(self.inference_time_ms, 2),
        }
        if self.isolation_score is not None:
            result["isolation_score"] = round(self.isolation_score, 4)
        if self.reconstruction_error is not None:
            result["reconstruction_error"] = round(self.reconstruction_error, 4)
        if self.z_scores:
            result["outlier_features"] = [
                k for k, v in self.z_scores.items() if abs(v) > 2.5
            ]
        return result


class IsolationForest:
    """
    Isolation Forest for anomaly detection.
    
    Key insight: Anomalies are easier to isolate (fewer splits needed).
    
    Advantages:
    - No training required on normal data
    - Fast inference O(log n)
    - Works well with high-dimensional data
    """
    
    def __init__(
        self,
        n_trees: int = 100,
        sample_size: int = 256,
        max_depth: Optional[int] = None
    ):
        self.n_trees = n_trees
        self.sample_size = sample_size
        self.max_depth = max_depth or int(math.ceil(math.log2(sample_size)))
        self.trees: List[dict] = []
        self._fitted = False
    
    def fit(self, feature_names: List[str]) -> None:
        """Initialize trees (can be used without explicit fitting)."""
        self.feature_names = feature_names
        self.n_features = len(feature_names)
        
        # Pre-generate random splits for consistency
        for _ in range(self.n_trees):
            tree = self._build_tree()
            self.trees.append(tree)
        
        self._fitted = True
    
    def _build_tree(self, depth: int = 0) -> dict:
        """Build a random isolation tree."""
        if depth >= self.max_depth:
            return {"type": "leaf", "depth": depth}
        
        # Random feature and split point
        feature_idx = random.randint(0, self.n_features - 1)
        split_value = random.uniform(0, 1)  # Assuming normalized features
        
        return {
            "type": "split",
            "feature_idx": feature_idx,
            "split_value": split_value,
            "left": self._build_tree(depth + 1),
            "right": self._build_tree(depth + 1),
        }
    
    def path_length(self, features: List[float], tree: dict, depth: int = 0) -> float:
        """Calculate path length for a point in a tree."""
        if tree["type"] == "leaf":
            return depth
        
        feature_val = features[tree["feature_idx"]] if tree["feature_idx"] < len(features) else 0
        
        if feature_val < tree["split_value"]:
            return self.path_length(features, tree["left"], depth + 1)
        else:
            return self.path_length(features, tree["right"], depth + 1)
    
    def score(self, features: List[float]) -> float:
        """
        Calculate anomaly score for a point.
        
        Returns: Score in [0, 1], higher = more anomalous
        """
        if not self._fitted:
            self.fit([f"f{i}" for i in range(len(features))])
        
        # Normalize features
        normalized = [max(0, min(1, f / 100 if abs(f) > 1 else f)) for f in features]
        
        # Average path length across all trees
        avg_path_length = sum(
            self.path_length(normalized, tree)
            for tree in self.trees
        ) / self.n_trees
        
        # Convert to anomaly score using expected path length formula
        # c(n) = 2 * (ln(n-1) + 0.5772) - 2*(n-1)/n for n = sample_size
        n = self.sample_size
        c_n = 2 * (math.log(n - 1) + 0.5772156649) - 2 * (n - 1) / n
        
        # Score = 2^(-E(h(x))/c(n))
        # Shorter path = higher score = more anomalous
        score = 2 ** (-avg_path_length / c_n)
        
        return min(1.0, max(0.0, score))


class SimpleAutoencoder:
    """
    Simple autoencoder for reconstruction-based anomaly detection.
    
    Architecture:
    - Encoder: Input -> 16 -> 8
    - Decoder: 8 -> 16 -> Input
    
    Anomalies have high reconstruction error.
    """
    
    def __init__(self, input_size: int, latent_size: int = 8):
        self.input_size = input_size
        self.latent_size = latent_size
        self.hidden_size = max(16, input_size // 2)
        
        # Initialize encoder weights
        self.enc_w1 = self._init_weights(input_size, self.hidden_size)
        self.enc_b1 = [0.0] * self.hidden_size
        self.enc_w2 = self._init_weights(self.hidden_size, latent_size)
        self.enc_b2 = [0.0] * latent_size
        
        # Initialize decoder weights
        self.dec_w1 = self._init_weights(latent_size, self.hidden_size)
        self.dec_b1 = [0.0] * self.hidden_size
        self.dec_w2 = self._init_weights(self.hidden_size, input_size)
        self.dec_b2 = [0.0] * input_size
    
    def _init_weights(self, fan_in: int, fan_out: int) -> List[List[float]]:
        """Xavier initialization."""
        scale = math.sqrt(2.0 / (fan_in + fan_out))
        return [
            [random.gauss(0, scale) for _ in range(fan_out)]
            for _ in range(fan_in)
        ]
    
    @staticmethod
    def relu(x: float) -> float:
        return max(0.0, x)
    
    def _forward_layer(
        self,
        inputs: List[float],
        weights: List[List[float]],
        biases: List[float],
        activation: bool = True
    ) -> List[float]:
        """Forward pass through a single layer."""
        outputs = []
        for j in range(len(biases)):
            total = biases[j]
            for i, inp in enumerate(inputs):
                if i < len(weights):
                    total += inp * weights[i][j]
            outputs.append(self.relu(total) if activation else total)
        return outputs
    
    def encode(self, features: List[float]) -> List[float]:
        """Encode input to latent space."""
        h1 = self._forward_layer(features, self.enc_w1, self.enc_b1)
        latent = self._forward_layer(h1, self.enc_w2, self.enc_b2)
        return latent
    
    def decode(self, latent: List[float]) -> List[float]:
        """Decode latent back to input space."""
        h1 = self._forward_layer(latent, self.dec_w1, self.dec_b1)
        reconstructed = self._forward_layer(h1, self.dec_w2, self.dec_b2, activation=False)
        return reconstructed
    
    def reconstruct(self, features: List[float]) -> List[float]:
        """Full forward pass: encode then decode."""
        latent = self.encode(features)
        return self.decode(latent)
    
    def reconstruction_error(self, features: List[float]) -> float:
        """Calculate MSE reconstruction error."""
        # Normalize inputs
        normalized = [max(0, min(1, f / 100 if abs(f) > 1 else f)) for f in features]
        
        reconstructed = self.reconstruct(normalized)
        
        # MSE
        mse = sum(
            (x - y) ** 2
            for x, y in zip(normalized, reconstructed)
        ) / len(features)
        
        return mse


class StatisticalDetector:
    """
    Statistical outlier detection using Z-scores and IQR.
    
    Fast and interpretable.
    """
    
    # Pre-computed statistics for common features
    FEATURE_STATS = {
        "amount": {"mean": 50.0, "std": 100.0},
        "amount_normalized": {"mean": 0.05, "std": 0.1},
        "txn_count_1h": {"mean": 1.0, "std": 2.0},
        "txn_count_24h": {"mean": 5.0, "std": 5.0},
        "txn_velocity_1h": {"mean": 0.02, "std": 0.05},
        "hour_of_day": {"mean": 12.0, "std": 6.0},
    }
    
    Z_SCORE_THRESHOLD = 2.5
    
    def __init__(self, feature_names: List[str]):
        self.feature_names = feature_names
    
    def compute_z_scores(self, features: Dict[str, float]) -> Dict[str, float]:
        """Compute Z-scores for each feature."""
        z_scores = {}
        
        for name, value in features.items():
            stats = self.FEATURE_STATS.get(name, {"mean": 0.5, "std": 0.5})
            mean = stats["mean"]
            std = stats["std"]
            
            if std > 0:
                z = (value - mean) / std
                z_scores[name] = z
        
        return z_scores
    
    def is_outlier(self, features: Dict[str, float]) -> Tuple[bool, Dict[str, float]]:
        """Check if point is an outlier based on Z-scores."""
        z_scores = self.compute_z_scores(features)
        
        # Count features with high Z-scores
        outlier_count = sum(1 for z in z_scores.values() if abs(z) > self.Z_SCORE_THRESHOLD)
        
        # Anomaly if multiple features are outliers
        is_outlier = outlier_count >= 2 or any(abs(z) > 4 for z in z_scores.values())
        
        return is_outlier, z_scores


class AnomalyDetectionService:
    """
    Combined anomaly detection using multiple methods.
    
    Ensemble approach for robustness.
    """
    
    ANOMALY_THRESHOLD = 0.6
    
    def __init__(self, feature_names: List[str]):
        self.feature_names = feature_names
        
        # Initialize detectors
        self.isolation_forest = IsolationForest(n_trees=50)
        self.isolation_forest.fit(feature_names)
        
        self.autoencoder = SimpleAutoencoder(len(feature_names))
        self.statistical = StatisticalDetector(feature_names)
    
    def detect(
        self,
        features: List[float],
        feature_dict: Dict[str, float]
    ) -> AnomalyResult:
        """
        Run anomaly detection using ensemble of methods.
        """
        import time
        start = time.perf_counter()
        
        # 1. Isolation Forest
        isolation_score = self.isolation_forest.score(features)
        
        # 2. Autoencoder
        reconstruction_error = self.autoencoder.reconstruction_error(features)
        # Normalize error to 0-1 (higher error = more anomalous)
        ae_score = min(1.0, reconstruction_error * 10)
        
        # 3. Statistical
        is_statistical_outlier, z_scores = self.statistical.is_outlier(feature_dict)
        stat_score = 0.7 if is_statistical_outlier else 0.3
        
        # Ensemble: weighted average
        ensemble_score = (
            0.4 * isolation_score +
            0.35 * ae_score +
            0.25 * stat_score
        )
        
        # Determine primary method
        scores = [
            ("isolation_forest", isolation_score),
            ("autoencoder", ae_score),
            ("statistical", stat_score),
        ]
        primary_method = max(scores, key=lambda x: x[1])[0]
        
        inference_time = (time.perf_counter() - start) * 1000
        
        return AnomalyResult(
            is_anomaly=ensemble_score >= self.ANOMALY_THRESHOLD,
            anomaly_score=ensemble_score,
            method=primary_method,
            isolation_score=isolation_score,
            reconstruction_error=reconstruction_error,
            z_scores=z_scores,
            inference_time_ms=inference_time,
        )


# Singleton instance
_anomaly_service: Optional[AnomalyDetectionService] = None


def get_anomaly_service(feature_names: Optional[List[str]] = None) -> AnomalyDetectionService:
    """Get singleton anomaly detection service."""
    global _anomaly_service
    if _anomaly_service is None:
        if feature_names is None:
            from app.ml.feature_store import get_feature_store
            feature_names = get_feature_store().feature_names
        _anomaly_service = AnomalyDetectionService(feature_names)
    return _anomaly_service


# Convenience function
async def detect_anomaly(
    features: List[float],
    feature_dict: Dict[str, float]
) -> AnomalyResult:
    """
    Quick anomaly detection.
    
    Usage:
        result = await detect_anomaly(features, feature_dict)
        if result.is_anomaly:
            # Flag for review
    """
    service = get_anomaly_service()
    return service.detect(features, feature_dict)
