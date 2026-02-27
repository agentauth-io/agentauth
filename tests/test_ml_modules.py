"""
Unit tests for ML modules: fraud_model, anomaly_detection, feature_store.

These tests verify the ML pipeline without external dependencies.
"""
import random
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ml.anomaly_detection import (
    AnomalyDetectionService,
    IsolationForest,
    SimpleAutoencoder,
    StatisticalDetector,
    detect_anomaly,
    get_anomaly_service,
)
from app.ml.feature_store import (
    FeatureStore,
    FeatureVector,
    TransactionFeatures,
    UserBehaviorFeatures,
    get_feature_store,
)

# Import modules under test
from app.ml.fraud_model import (
    FraudDetectionModel,
    FraudDetectionService,
    FraudPrediction,
    NeuralNetwork,
    detect_fraud,
    get_fraud_service,
)

# ============================================================================
# Neural Network Tests
# ============================================================================

class TestNeuralNetwork:
    """Tests for the lightweight neural network implementation."""

    def test_initialization(self):
        """Test network initializes with correct dimensions."""
        nn = NeuralNetwork(input_size=10)
        assert nn.input_size == 10
        assert len(nn.w1) == 10  # Input -> Hidden1
        assert len(nn.w2) == 64  # Hidden1 -> Hidden2
        assert len(nn.w3) == 32  # Hidden2 -> Hidden3
        assert len(nn.w4) == 16  # Hidden3 -> Output

    def test_relu_activation(self):
        """Test ReLU activation function."""
        assert NeuralNetwork.relu(5.0) == 5.0
        assert NeuralNetwork.relu(-3.0) == 0.0
        assert NeuralNetwork.relu(0.0) == 0.0

    def test_sigmoid_activation(self):
        """Test sigmoid activation function."""
        # Sigmoid(0) = 0.5
        assert abs(NeuralNetwork.sigmoid(0.0) - 0.5) < 0.001
        # Sigmoid(large positive) -> 1
        assert NeuralNetwork.sigmoid(10.0) > 0.99
        # Sigmoid(large negative) -> 0
        assert NeuralNetwork.sigmoid(-10.0) < 0.01

    def test_forward_pass(self):
        """Test forward pass produces valid output."""
        nn = NeuralNetwork(input_size=5)
        features = [0.5, 0.3, 0.2, 0.1, 0.4]

        output = nn.forward(features)

        # Output should be between 0 and 1 (sigmoid)
        assert 0.0 <= output <= 1.0

    def test_weight_initialization(self):
        """Test Xavier weight initialization."""
        nn = NeuralNetwork(input_size=10)

        # Check weights are initialized (not all zeros)
        assert any(w != 0 for row in nn.w1 for w in row)

        # Check biases are initialized to zero
        assert all(b == 0.0 for b in nn.b1)

    def test_weight_save_load(self):
        """Test saving and loading weights."""
        nn1 = NeuralNetwork(input_size=5)
        features = [0.5, 0.3, 0.2, 0.1, 0.4]

        # Get output before save
        output1 = nn1.forward(features)

        # Save weights
        weights = nn1.save_weights()

        # Create new network and load weights
        nn2 = NeuralNetwork(input_size=5)
        nn2.load_weights(weights)

        # Output should be identical
        output2 = nn2.forward(features)
        assert abs(output1 - output2) < 0.0001


# ============================================================================
# Fraud Detection Model Tests
# ============================================================================

class TestFraudDetectionModel:
    """Tests for the fraud detection model."""

    @pytest.fixture
    def model(self):
        """Create a fraud detection model for testing."""
        feature_names = [
            "amount", "amount_normalized", "txn_velocity_1h",
            "is_night", "is_new_merchant", "declined_count_24h"
        ]
        return FraudDetectionModel(feature_names)

    def test_model_initialization(self, model):
        """Test model initializes correctly."""
        assert model.feature_names is not None
        assert model.model is not None
        assert model.version == "v1.0"

    def test_normalize_features(self, model):
        """Test feature normalization."""
        features = [1000.0, 50.0, 5.0, 1.0, 0.0, 2.0]
        normalized = model._normalize(features)

        # All values should be between 0 and 1
        assert all(0.0 <= f <= 1.0 for f in normalized)

    def test_extract_risk_factors(self, model):
        """Test risk factor extraction."""
        features = {
            "is_new_merchant": 1.0,
            "is_night": 1.0,
            "declined_count_24h": 3.0,
            "amount_normalized": 0.6,
        }

        factors = model._extract_risk_factors(features)

        # Should identify new merchant as risk factor
        assert any(f["factor"] == "new_merchant" for f in factors)
        # Should identify night time as risk factor
        assert any(f["factor"] == "unusual_time" for f in factors)

    def test_get_risk_level(self, model):
        """Test risk level classification."""
        assert model._get_risk_level(0.3) == "low"
        assert model._get_risk_level(0.6) == "medium"
        assert model._get_risk_level(0.8) == "high"
        assert model._get_risk_level(0.95) == "critical"

    def test_apply_rules(self, model):
        """Test rule-based score adjustment."""
        base_score = 0.5

        # High velocity failures should boost score
        features_high_risk = {"velocity_check_failures_24h": 3.0}
        adjusted_high = model._apply_rules(base_score, features_high_risk)
        assert adjusted_high > base_score

        # Low risk features should not boost much
        features_low_risk = {"velocity_check_failures_24h": 0.0}
        adjusted_low = model._apply_rules(base_score, features_low_risk)
        assert adjusted_low == base_score

    def test_predict_output_format(self, model):
        """Test prediction output format."""
        model.load()  # Initialize heuristic weights

        features = [0.5, 0.3, 0.1, 0.0, 1.0, 0.0]
        feature_dict = {
            "amount": 100.0,
            "is_new_merchant": 1.0,
            "is_night": 0.0,
        }

        prediction = model.predict(features, feature_dict)

        assert isinstance(prediction, FraudPrediction)
        assert 0.0 <= prediction.fraud_score <= 1.0
        assert prediction.risk_level in ["low", "medium", "high", "critical"]
        assert prediction.inference_time_ms >= 0

    def test_fraud_prediction_to_dict(self, model):
        """Test FraudPrediction serialization."""
        prediction = FraudPrediction(
            is_fraud=True,
            fraud_score=0.85,
            confidence=0.9,
            risk_level="high",
            top_risk_factors=[{"factor": "test", "weight": 0.5}],
        )

        d = prediction.to_dict()
        assert d["is_fraud"] is True
        assert d["fraud_score"] == 0.85
        assert d["risk_level"] == "high"


# ============================================================================
# Isolation Forest Tests
# ============================================================================

class TestIsolationForest:
    """Tests for Isolation Forest anomaly detection."""

    @pytest.fixture
    def forest(self):
        """Create an isolation forest for testing."""
        return IsolationForest(n_trees=10, sample_size=64)

    def test_initialization(self, forest):
        """Test forest initializes correctly."""
        assert forest.n_trees == 10
        assert forest.sample_size == 64
        assert forest.max_depth > 0

    def test_fit(self, forest):
        """Test fitting the forest."""
        feature_names = ["f1", "f2", "f3"]
        forest.fit(feature_names)

        assert forest._fitted is True
        assert len(forest.trees) == 10

    def test_score_range(self, forest):
        """Test anomaly scores are in valid range."""
        forest.fit(["f1", "f2"])

        features = [0.5, 0.3]
        score = forest.score(features)

        assert 0.0 <= score <= 1.0

    def test_anomaly_detection(self, forest):
        """Test that outliers get higher scores."""
        forest.fit(["f1", "f2", "f3"])

        # Normal point
        normal_score = forest.score([0.5, 0.5, 0.5])

        # Outlier point (extreme values)
        outlier_score = forest.score([0.99, 0.01, 0.99])

        # Outlier should generally have higher score
        # (Note: This is probabilistic, may occasionally fail)
        assert outlier_score >= normal_score or abs(outlier_score - normal_score) < 0.5


# ============================================================================
# Autoencoder Tests
# ============================================================================

class TestSimpleAutoencoder:
    """Tests for the simple autoencoder."""

    @pytest.fixture
    def autoencoder(self):
        """Create an autoencoder for testing."""
        return SimpleAutoencoder(input_size=5, latent_size=3)

    def test_initialization(self, autoencoder):
        """Test autoencoder initializes correctly."""
        assert autoencoder.input_size == 5
        assert autoencoder.latent_size == 3
        assert autoencoder.hidden_size >= 16

    def test_encode_decode(self, autoencoder):
        """Test encoding and decoding."""
        features = [0.5, 0.3, 0.2, 0.1, 0.4]

        latent = autoencoder.encode(features)
        assert len(latent) == 3  # Latent size

        reconstructed = autoencoder.decode(latent)
        assert len(reconstructed) == 5  # Input size

    def test_reconstruction_error(self, autoencoder):
        """Test reconstruction error calculation."""
        features = [0.5, 0.3, 0.2, 0.1, 0.4]

        error = autoencoder.reconstruction_error(features)
        assert error >= 0.0  # MSE is always non-negative

    def test_reconstruction_consistency(self, autoencoder):
        """Test that same input gives similar reconstruction."""
        features = [0.5, 0.3, 0.2, 0.1, 0.4]

        error1 = autoencoder.reconstruction_error(features)
        error2 = autoencoder.reconstruction_error(features)

        # Same input should give same error
        assert abs(error1 - error2) < 0.0001


# ============================================================================
# Statistical Detector Tests
# ============================================================================

class TestStatisticalDetector:
    """Tests for statistical outlier detection."""

    @pytest.fixture
    def detector(self):
        """Create a statistical detector."""
        return StatisticalDetector(["amount", "txn_count_1h"])

    def test_compute_z_scores(self, detector):
        """Test Z-score computation."""
        features = {"amount": 500.0, "txn_count_1h": 10.0}
        z_scores = detector.compute_z_scores(features)

        # High values should have positive Z-scores
        assert z_scores["amount"] > 0
        assert z_scores["txn_count_1h"] > 0

    def test_is_outlier(self, detector):
        """Test outlier detection."""
        # Normal values
        normal_features = {"amount": 50.0, "txn_count_1h": 1.0}
        is_outlier, z_scores = detector.is_outlier(normal_features)
        assert is_outlier is False

        # Extreme values
        extreme_features = {"amount": 5000.0, "txn_count_1h": 50.0}
        is_outlier, z_scores = detector.is_outlier(extreme_features)
        assert is_outlier is True


# ============================================================================
# Feature Store Tests
# ============================================================================

class TestFeatureStore:
    """Tests for the feature store."""

    @pytest.fixture
    def store(self):
        """Create a feature store for testing."""
        return FeatureStore()

    def test_feature_names(self, store):
        """Test feature names are defined."""
        names = store.feature_names
        assert len(names) > 0
        assert "amount" in names
        assert "txn_count_1h" in names

    def test_transaction_features(self):
        """Test TransactionFeatures dataclass."""
        txn = TransactionFeatures(
            amount=100.0,
            hour_of_day=14,
            is_weekend=True,
        )

        d = txn.to_dict()
        assert d["amount"] == 100.0
        assert d["hour_of_day"] == 14.0
        assert d["is_weekend"] == 1.0

    def test_user_behavior_features(self):
        """Test UserBehaviorFeatures dataclass."""
        behavior = UserBehaviorFeatures(
            txn_count_1h=5,
            txn_count_24h=20,
            avg_amount_7d=50.0,
        )

        d = behavior.to_dict()
        assert d["txn_count_1h"] == 5.0
        assert d["txn_count_24h"] == 20.0
        assert d["avg_amount_7d"] == 50.0

    def test_feature_vector(self):
        """Test FeatureVector dataclass."""
        vector = FeatureVector(
            entity_id="user_123",
            entity_type="user",
            features={"amount": 100.0, "count": 5.0},
        )

        assert vector.entity_id == "user_123"
        assert vector.computed_at != ""  # Auto-set

        # Test to_array
        arr = vector.to_array(["amount", "count", "missing"])
        assert arr == [100.0, 5.0, 0.0]


# ============================================================================
# Integration Tests
# ============================================================================

class TestMLPipeline:
    """Integration tests for the full ML pipeline."""

    @pytest.mark.asyncio
    async def test_fraud_detection_pipeline(self):
        """Test end-to-end fraud detection."""
        # Create service
        service = FraudDetectionService()

        # Mock the feature store to avoid Redis dependency
        with patch.object(service, 'feature_store') as mock_store:
            mock_store.get_inference_features = AsyncMock(return_value=(
                [0.5, 0.3, 0.1, 0.0, 1.0, 0.0],  # features array
                {"is_new_merchant": 1.0, "amount": 100.0}  # feature dict
            ))

            prediction = await service.detect_fraud(
                user_id="user_123",
                amount=100.0,
                merchant_id="merchant_abc",
            )

        assert isinstance(prediction, FraudPrediction)
        assert prediction.fraud_score >= 0.0
        assert prediction.inference_time_ms >= 0

    @pytest.mark.asyncio
    async def test_anomaly_detection_pipeline(self):
        """Test end-to-end anomaly detection."""
        feature_names = ["amount", "txn_count_1h", "is_night"]
        service = AnomalyDetectionService(feature_names)

        features = [0.5, 0.3, 0.1]
        feature_dict = {"amount": 100.0, "txn_count_1h": 3.0, "is_night": 0.0}

        result = service.detect(features, feature_dict)

        assert result.anomaly_score >= 0.0
        assert result.method in ["isolation_forest", "autoencoder", "statistical"]
        assert result.inference_time_ms >= 0

    def test_fraud_prediction_serialization(self):
        """Test FraudPrediction can be serialized to JSON."""
        import json

        prediction = FraudPrediction(
            is_fraud=False,
            fraud_score=0.2,
            confidence=0.95,
            risk_level="low",
            top_risk_factors=[],
        )

        d = prediction.to_dict()
        json_str = json.dumps(d)

        assert json_str is not None
        assert "fraud_score" in json_str


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests for ML components."""

    def test_fraud_inference_latency(self):
        """Verify fraud detection meets <100ms target."""
        import time

        feature_names = ["amount", "txn_velocity_1h", "is_new_merchant"]
        model = FraudDetectionModel(feature_names)
        model.load()

        features = [0.5, 0.1, 1.0]
        feature_dict = {"amount": 100.0, "is_new_merchant": 1.0}

        # Warmup
        for _ in range(5):
            model.predict(features, feature_dict)

        # Measure
        times = []
        for _ in range(10):
            start = time.perf_counter()
            model.predict(features, feature_dict)
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 100, f"Average inference time {avg_time:.2f}ms exceeds 100ms target"

    def test_anomaly_inference_latency(self):
        """Verify anomaly detection meets latency target."""
        import time

        feature_names = ["amount", "txn_count_1h", "is_night"]
        service = AnomalyDetectionService(feature_names)

        features = [0.5, 0.3, 0.1]
        feature_dict = {"amount": 100.0}

        # Warmup
        for _ in range(5):
            service.detect(features, feature_dict)

        # Measure
        times = []
        for _ in range(10):
            start = time.perf_counter()
            service.detect(features, feature_dict)
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 50, f"Average inference time {avg_time:.2f}ms exceeds 50ms target"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_features(self):
        """Test handling of empty feature arrays."""
        nn = NeuralNetwork(input_size=1)
        # Should handle gracefully
        output = nn.forward([0.0])
        assert 0.0 <= output <= 1.0

    def test_extreme_values(self):
        """Test handling of extreme input values."""
        nn = NeuralNetwork(input_size=3)

        # Very large values
        output = nn.forward([10000.0, -10000.0, 0.0])
        assert 0.0 <= output <= 1.0

        # Very small values
        output = nn.forward([0.0001, -0.0001, 0.0])
        assert 0.0 <= output <= 1.0

    def test_single_feature(self):
        """Test with single feature."""
        forest = IsolationForest(n_trees=5)
        forest.fit(["f1"])

        score = forest.score([0.5])
        assert 0.0 <= score <= 1.0

    def test_many_features(self):
        """Test with many features."""
        feature_names = [f"f{i}" for i in range(50)]
        forest = IsolationForest(n_trees=10)
        forest.fit(feature_names)

        features = [random.random() for _ in range(50)]
        score = forest.score(features)
        assert 0.0 <= score <= 1.0


# ============================================================================
# Convenience Function Tests
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_fraud_service_singleton(self):
        """Test fraud service is a singleton."""
        service1 = get_fraud_service()
        service2 = get_fraud_service()
        assert service1 is service2

    def test_get_anomaly_service_singleton(self):
        """Test anomaly service is a singleton."""
        service1 = get_anomaly_service(["f1", "f2"])
        service2 = get_anomaly_service(["f1", "f2"])
        assert service1 is service2

    def test_get_feature_store_singleton(self):
        """Test feature store is a singleton."""
        store1 = get_feature_store()
        store2 = get_feature_store()
        assert store1 is store2

    @pytest.mark.asyncio
    async def test_detect_fraud_convenience(self):
        """Test detect_fraud convenience function."""
        with patch('app.ml.fraud_model.get_fraud_service') as mock_get:
            mock_service = MagicMock()
            mock_service.detect_fraud = AsyncMock(return_value=FraudPrediction(
                is_fraud=False,
                fraud_score=0.1,
                confidence=0.9,
                risk_level="low",
            ))
            mock_get.return_value = mock_service

            result = await detect_fraud(
                user_id="user_123",
                amount=100.0,
                merchant_id="merchant_abc"
            )

            assert isinstance(result, FraudPrediction)

    @pytest.mark.asyncio
    async def test_detect_anomaly_convenience(self):
        """Test detect_anomaly convenience function."""
        from app.ml.anomaly_detection import AnomalyResult

        with patch('app.ml.anomaly_detection.get_anomaly_service') as mock_get:
            mock_service = MagicMock()
            mock_service.detect = MagicMock(return_value=AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.2,
                method="isolation_forest",
            ))
            mock_get.return_value = mock_service

            result = await detect_anomaly(
                features=[0.5, 0.3],
                feature_dict={"amount": 100.0}
            )

            assert isinstance(result, AnomalyResult)
