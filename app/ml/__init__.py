"""
AgentAuth ML Package

Real-time ML for fraud detection and anomaly detection.
Target: <100ms end-to-end inference latency.
"""

from app.ml.feature_store import (
    FeatureStore,
    FeatureVector,
    UserBehaviorFeatures,
    TransactionFeatures,
    get_feature_store,
    get_fraud_features,
    record_transaction,
)
from app.ml.fraud_model import (
    FraudDetectionModel,
    FraudDetectionService,
    FraudPrediction,
    get_fraud_service,
    detect_fraud,
)
from app.ml.anomaly_detection import (
    AnomalyDetectionService,
    AnomalyResult,
    IsolationForest,
    get_anomaly_service,
    detect_anomaly,
)

__all__ = [
    # Feature Store
    "FeatureStore",
    "FeatureVector",
    "UserBehaviorFeatures",
    "TransactionFeatures",
    "get_feature_store",
    "get_fraud_features",
    "record_transaction",
    # Fraud Detection
    "FraudDetectionModel",
    "FraudDetectionService",
    "FraudPrediction",
    "get_fraud_service",
    "detect_fraud",
    # Anomaly Detection
    "AnomalyDetectionService",
    "AnomalyResult",
    "IsolationForest",
    "get_anomaly_service",
    "detect_anomaly",
]
