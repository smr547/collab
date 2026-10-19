#pragma once

// GENERATED from DPP.collab; do not edit by hand.
// Regenerate with collabc.py.

#include "qpcpp.hpp"

enum AppSignals {
    PAUSE_SIG = QP::Q_USER_SIG,  // User -> Table
    SERVE_SIG,  // User -> Table
    HUNGRY_SIG,  // Philosopher -> Table
    DONE_SIG,  // Philosopher -> Table
    EAT_SIG,  // Table -> Philosopher
    TIMEOUT_SIG,  // PhilosopherTimer -> Philosopher

    MAX_APP_SIG
};
