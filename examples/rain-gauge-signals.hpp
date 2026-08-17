#pragma once

// GENERATED from rain-gauge.collab; do not edit by hand.
// Regenerate with collabc.py.

#include "qpcpp.hpp"

enum AppSignals {
    BUCKET_TIPPED_SIG = QP::Q_USER_SIG,  // BucketSensorAO -> ControlAO
    BUCKET_SENSOR_BUSY_SIG,  // BucketSensorAO -> ControlAO
    BUCKET_SENSOR_IDLE_SIG,  // BucketSensorAO -> ControlAO
    RAIN_BUCKET_FAULT_SIG,  // BucketSensorAO -> ControlAO

    MAX_APP_SIG
};
