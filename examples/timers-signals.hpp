#pragma once

// GENERATED from timers.collab; do not edit by hand.
// Regenerate with collabc.py.

#include "qpcpp.hpp"

enum AppSignals {
    CONSIDER_SLEEPING_SIG = QP::Q_USER_SIG,  // SleepTimer -> Control
    HEALTH_REPORT_DUE_SIG,  // HealthTimer -> Control

    MAX_APP_SIG
};
