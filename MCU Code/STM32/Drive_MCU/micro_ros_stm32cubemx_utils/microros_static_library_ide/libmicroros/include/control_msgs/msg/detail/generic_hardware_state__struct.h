// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/GenericHardwareState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/generic_hardware_state.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__GENERIC_HARDWARE_STATE__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__GENERIC_HARDWARE_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Constant 'HEALTH_UNKNOWN'.
/**
  * --- Health Status Constants -------------------------------------
  * High-level health indicators
 */
enum
{
  control_msgs__msg__GenericHardwareState__HEALTH_UNKNOWN = 0
};

/// Constant 'HEALTH_OK'.
enum
{
  control_msgs__msg__GenericHardwareState__HEALTH_OK = 1
};

/// Constant 'HEALTH_DEGRADED'.
enum
{
  control_msgs__msg__GenericHardwareState__HEALTH_DEGRADED = 2
};

/// Constant 'HEALTH_WARNING'.
enum
{
  control_msgs__msg__GenericHardwareState__HEALTH_WARNING = 3
};

/// Constant 'HEALTH_ERROR'.
/**
  * Hardware stops publishing state when it returns ERROR/FATAL, how are these set/updated?
 */
enum
{
  control_msgs__msg__GenericHardwareState__HEALTH_ERROR = 4
};

/// Constant 'HEALTH_FATAL'.
enum
{
  control_msgs__msg__GenericHardwareState__HEALTH_FATAL = 5
};

/// Constant 'ERROR_NONE'.
/**
  * --- Error Domain Constants --------------------------------------
  * Error categories
 */
enum
{
  control_msgs__msg__GenericHardwareState__ERROR_NONE = 0
};

/// Constant 'ERROR_UNKNOWN'.
enum
{
  control_msgs__msg__GenericHardwareState__ERROR_UNKNOWN = 1
};

/// Constant 'ERROR_HW'.
/**
  * generic hardware fault/error
 */
enum
{
  control_msgs__msg__GenericHardwareState__ERROR_HW = 2
};

/// Constant 'ERROR_SW'.
/**
  * generic software fault/error
 */
enum
{
  control_msgs__msg__GenericHardwareState__ERROR_SW = 3
};

/// Constant 'ERROR_OVER_TRAVEL'.
/**
  * Hardware stopped motion because position is over limits
 */
enum
{
  control_msgs__msg__GenericHardwareState__ERROR_OVER_TRAVEL = 4
};

/// Constant 'EMERGENCY_STOP_HW'.
/**
  * Hardware/Software emergency and safety states
  * state of the emergency stop hardware (i.e. e-stop button state)
 */
enum
{
  control_msgs__msg__GenericHardwareState__EMERGENCY_STOP_HW = 5
};

/// Constant 'EMERGENCY_STOP_SW'.
/**
  * state of the emergency stop software system (over travel, pinch point)
 */
enum
{
  control_msgs__msg__GenericHardwareState__EMERGENCY_STOP_SW = 6
};

/// Constant 'PROTECTIVE_STOP_HW'.
/**
  * state of the protective stop hardware (i.e. safety field state)
 */
enum
{
  control_msgs__msg__GenericHardwareState__PROTECTIVE_STOP_HW = 7
};

/// Constant 'PROTECTIVE_STOP_SW'.
/**
  * state of the software protective stop
 */
enum
{
  control_msgs__msg__GenericHardwareState__PROTECTIVE_STOP_SW = 8
};

/// Constant 'SAFETY_STOP'.
enum
{
  control_msgs__msg__GenericHardwareState__SAFETY_STOP = 9
};

/// Constant 'CALIBRATION_REQUIRED'.
enum
{
  control_msgs__msg__GenericHardwareState__CALIBRATION_REQUIRED = 10
};

/// Constant 'MODE_UNKNOWN'.
/**
  * --- Operational Mode Constants ----------------------------------
  * Mode of operation
 */
enum
{
  control_msgs__msg__GenericHardwareState__MODE_UNKNOWN = 0
};

/// Constant 'MODE_MANUAL'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_MANUAL = 1
};

/// Constant 'MODE_AUTO'.
/**
  * automatic mode when the driver is remote controlling the hardware
 */
enum
{
  control_msgs__msg__GenericHardwareState__MODE_AUTO = 2
};

/// Constant 'MODE_SAFE'.
/**
  * what is the expected use case for this mode?
 */
enum
{
  control_msgs__msg__GenericHardwareState__MODE_SAFE = 3
};

/// Constant 'MODE_MAINTENANCE'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_MAINTENANCE = 4
};

/// Constant 'MODE_JOG_MANUAL'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_JOG_MANUAL = 5
};

/// Constant 'MODE_ADMITTANCE'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_ADMITTANCE = 6
};

/// Constant 'MODE_MONITORED_STOP'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_MONITORED_STOP = 7
};

/// Constant 'MODE_HOLD_TO_RUN'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_HOLD_TO_RUN = 8
};

/// Constant 'MODE_CARTESIAN_TWIST'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_CARTESIAN_TWIST = 9
};

/// Constant 'MODE_CARTESIAN_POSE'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_CARTESIAN_POSE = 10
};

/// Constant 'MODE_TRAJECTORY_FORWARDING'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_TRAJECTORY_FORWARDING = 11
};

/// Constant 'MODE_TRAJECTORY_STREAMING'.
enum
{
  control_msgs__msg__GenericHardwareState__MODE_TRAJECTORY_STREAMING = 12
};

/// Constant 'POWER_UNKNOWN'.
/**
  * --- Power State Constants ---------------------------------------
  * Power states
 */
enum
{
  control_msgs__msg__GenericHardwareState__POWER_UNKNOWN = 0
};

/// Constant 'POWER_OFF'.
enum
{
  control_msgs__msg__GenericHardwareState__POWER_OFF = 1
};

/// Constant 'POWER_STANDBY'.
enum
{
  control_msgs__msg__GenericHardwareState__POWER_STANDBY = 2
};

/// Constant 'POWER_ON'.
enum
{
  control_msgs__msg__GenericHardwareState__POWER_ON = 3
};

/// Constant 'POWER_SLEEP'.
enum
{
  control_msgs__msg__GenericHardwareState__POWER_SLEEP = 4
};

/// Constant 'POWER_ERROR'.
enum
{
  control_msgs__msg__GenericHardwareState__POWER_ERROR = 5
};

/// Constant 'POWER_LEVEL_LOW'.
/**
  * Battery power states see BatteryState.msg
 */
enum
{
  control_msgs__msg__GenericHardwareState__POWER_LEVEL_LOW = 6
};

/// Constant 'POWER_LEVEL_CRITICAL'.
enum
{
  control_msgs__msg__GenericHardwareState__POWER_LEVEL_CRITICAL = 7
};

/// Constant 'POWER_CHARGING'.
enum
{
  control_msgs__msg__GenericHardwareState__POWER_CHARGING = 8
};

/// Constant 'POWER_CHARGING_ERROR'.
enum
{
  control_msgs__msg__GenericHardwareState__POWER_CHARGING_ERROR = 9
};

/// Constant 'CONNECT_UNKNOWN'.
/**
  * --- Connectivity Status Constants -------------------------------
  * Connectivity states
 */
enum
{
  control_msgs__msg__GenericHardwareState__CONNECT_UNKNOWN = 0
};

/// Constant 'CONNECT_UP'.
enum
{
  control_msgs__msg__GenericHardwareState__CONNECT_UP = 1
};

/// Constant 'CONNECT_DOWN'.
enum
{
  control_msgs__msg__GenericHardwareState__CONNECT_DOWN = 2
};

/// Constant 'CONNECT_FAILURE'.
enum
{
  control_msgs__msg__GenericHardwareState__CONNECT_FAILURE = 3
};

/// Constant 'CONNECTION_SLOW'.
/**
  * to tell the controlling system it is struggling to communicate at rate
 */
enum
{
  control_msgs__msg__GenericHardwareState__CONNECTION_SLOW = 4
};

// Include directives for member types
// Member 'error_domain'
#include "rosidl_runtime_c/primitives_sequence.h"
// Member 'manufacturer'
// Member 'model'
// Member 'firmware_version'
#include "rosidl_runtime_c/string.h"
// Member 'state_details'
#include "diagnostic_msgs/msg/detail/key_value__struct.h"

/// Struct defined in msg/GenericHardwareState in the package control_msgs.
/**
  * This message encapsulates the general-purpose status fields, serving as a baseline for any hardware component
 */
typedef struct control_msgs__msg__GenericHardwareState
{
  /// --- Health & Error ----------------------------------------------
  /// Overall health status of the device, see HealthStatus constants below
  uint8_t health_status;
  /// Array of device errors by category, see ErrorDomain constants below
  rosidl_runtime_c__uint8__Sequence error_domain;
  /// --- Operational State -------------------------------------------
  /// Current operational mode of the device, see ModeStatus constants below
  uint8_t operational_mode;
  /// Current power state of the device, see PowerState constants below
  uint8_t power_state;
  /// Current connectivity status of the device, see ConnectivityStatus constants below
  uint8_t connectivity_status;
  /// --- Vendor & Version Info ----------------------------------------
  /// Device manufacturer name, e.g. "Bosch"
  rosidl_runtime_c__String manufacturer;
  /// Device model identifier, e.g. "Lidar-XYZ-v2"
  rosidl_runtime_c__String model;
  /// Current firmware version, e.g. "1.2.3"
  rosidl_runtime_c__String firmware_version;
  /// --- Optional Details for Context ---------------------------------
  /// Provides specific quantitative values related to the enums above.
  /// e.g., for power_state, could have {key: "voltage", value: "24.1"}
  /// e.g., for connectivity, could have {key: "signal_strength", value: "-55dBm"}
  diagnostic_msgs__msg__KeyValue__Sequence state_details;
} control_msgs__msg__GenericHardwareState;

// Struct for a sequence of control_msgs__msg__GenericHardwareState.
typedef struct control_msgs__msg__GenericHardwareState__Sequence
{
  control_msgs__msg__GenericHardwareState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__GenericHardwareState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__GENERIC_HARDWARE_STATE__STRUCT_H_
