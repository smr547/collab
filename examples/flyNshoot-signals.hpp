#pragma once

// GENERATED from flyNshoot.collab; do not edit by hand.
// Regenerate with collabc.py.

#include "qpcpp.hpp"

enum AppSignals {
    BLINK_TIMEOUT_SIG = QP::Q_USER_SIG,  // BlinkTimer -> Tunnel
    SCREEN_TIMEOUT_SIG,  // ScreenTimer -> Tunnel
    // routes:
    //   Player -> Tunnel
    //   Player -> Ship
    PLAYER_TRIGGER_SIG,
    PLAYER_QUIT_SIG,  // Player -> Tunnel
    PLAYER_SHIP_MOVE_SIG,  // Player -> Ship
    // routes:
    //   TickTimer -> Ship
    //   TickTimer -> Missile
    //   TickTimer -> Tunnel
    //   Tunnel -> Mine
    TIME_TICK_SIG,
    MISSILE_FIRE_SIG,  // Ship -> Missile
    DESTROYED_MINE_SIG,  // Missile -> Ship
    // routes:
    //   Ship -> Tunnel
    //   Tunnel -> Mine
    SHIP_IMG_SIG,
    SCORE_SIG,  // Ship -> Tunnel
    // routes:
    //   Ship -> Tunnel
    //   Missile -> Tunnel
    //   Mine -> Tunnel
    EXPLOSION_SIG,
    GAME_OVER_SIG,  // Ship -> Tunnel
    HIT_WALL_SIG,  // Tunnel -> Ship
    TAKE_OFF_SIG,  // Tunnel -> Ship
    // routes:
    //   Missile -> Tunnel
    //   Tunnel -> Mine
    MISSILE_IMG_SIG,
    MINE_PLANT_SIG,  // Tunnel -> Mine
    MINE_RECYCLE_SIG,  // Tunnel -> Mine
    MINE_IMG_SIG,  // Mine -> Tunnel
    MINE_DISABLED_SIG,  // Mine -> Tunnel
    // routes:
    //   Mine -> Missile
    //   Mine -> Ship
    HIT_MINE_SIG,

    MAX_APP_SIG
};
