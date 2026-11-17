// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/VDA5050State.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/vda5050_state.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__VDA5050_STATE__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__VDA5050_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Constant 'ACTION_WAITING'.
/**
  * --- Action Status Constants ---------------------------------------
  * VDA5050 action execution states
  * Action is waiting to be executed
 */
static const char * const control_msgs__msg__VDA5050State__ACTION_WAITING = "WAITING";

/// Constant 'ACTION_INITIALIZING'.
/**
  * Action is being initialized
 */
static const char * const control_msgs__msg__VDA5050State__ACTION_INITIALIZING = "INITIALIZING";

/// Constant 'ACTION_RUNNING'.
/**
  * Action is currently executing
 */
static const char * const control_msgs__msg__VDA5050State__ACTION_RUNNING = "RUNNING";

/// Constant 'ACTION_PAUSED'.
/**
  * Action execution is paused
 */
static const char * const control_msgs__msg__VDA5050State__ACTION_PAUSED = "PAUSED";

/// Constant 'ACTION_FINISHED'.
/**
  * Action completed successfully
 */
static const char * const control_msgs__msg__VDA5050State__ACTION_FINISHED = "FINISHED";

/// Constant 'ACTION_FAILED'.
/**
  * Action execution failed
 */
static const char * const control_msgs__msg__VDA5050State__ACTION_FAILED = "FAILED";

/// Constant 'MODE_AUTOMATIC'.
/**
  * --- Operating Mode Constants -------------------------------------
  * VDA5050 vehicle operating modes
  * Vehicle operates autonomously
 */
static const char * const control_msgs__msg__VDA5050State__MODE_AUTOMATIC = "AUTOMATIC";

/// Constant 'MODE_SEMI_AUTOMATIC'.
/**
  * Vehicle requires operator confirmation
 */
static const char * const control_msgs__msg__VDA5050State__MODE_SEMI_AUTOMATIC = "SEMIAUTOMATIC";

/// Constant 'MODE_MANUAL'.
/**
  * Vehicle is under manual control
 */
static const char * const control_msgs__msg__VDA5050State__MODE_MANUAL = "MANUAL";

/// Constant 'MODE_SERVICE'.
/**
  * Vehicle is in service/maintenance mode
 */
static const char * const control_msgs__msg__VDA5050State__MODE_SERVICE = "SERVICE";

/// Constant 'MODE_EMERGENCY'.
/**
  * Vehicle is in emergency mode
 */
static const char * const control_msgs__msg__VDA5050State__MODE_EMERGENCY = "EMERGENCY";

/// Constant 'MODE_TEACHIN'.
/**
  * Vehicle is in teach-in mode for route learning
 */
static const char * const control_msgs__msg__VDA5050State__MODE_TEACHIN = "TEACHIN";

// Include directives for member types
// Member 'order_id'
// Member 'action_status'
// Member 'operating_mode'
// Member 'error_type'
// Member 'error_description'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/VDA5050State in the package control_msgs.
/**
  * This message presents VDA5050-specific vehicle state information
  * For AGVs and AMRs compliant with VDA5050, this provides a snapshot of the vehicle's high-level status
  * Refer Official Specification document for the VDA 5050 - https://github.com/VDA5050/VDA5050
 */
typedef struct control_msgs__msg__VDA5050State
{
  /// --- Order and Action Status ---------------------------------------
  /// ID of the currently executed order
  rosidl_runtime_c__String order_id;
  /// Current action execution status, see ActionStatus constants below
  rosidl_runtime_c__String action_status;
  /// ID of the last reached node in the topology
  uint32_t last_node_id;
  /// --- Vehicle State -------------------------------------------------
  /// True if the vehicle's drives are active and vehicle is in motion
  bool driving;
  /// Current battery charge level in percent (0.0 - 100.0)
  double battery_charge;
  /// Current operating mode of the vehicle, see OperatingMode constants below
  rosidl_runtime_c__String operating_mode;
  /// --- Error Reporting -----------------------------------------------
  /// Type/category of the current error, empty string if no error
  rosidl_runtime_c__String error_type;
  /// Human-readable description of the current error, empty string if no error
  rosidl_runtime_c__String error_description;
} control_msgs__msg__VDA5050State;

// Struct for a sequence of control_msgs__msg__VDA5050State.
typedef struct control_msgs__msg__VDA5050State__Sequence
{
  control_msgs__msg__VDA5050State * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__VDA5050State__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__VDA5050_STATE__STRUCT_H_
