// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/VDA5050SafetyState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/vda5050_safety_state.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__VDA5050_SAFETY_STATE__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__VDA5050_SAFETY_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Constant 'AUTO_ACK'.
/**
  * Enums for eStop
 */
static const char * const control_msgs__msg__VDA5050SafetyState__AUTO_ACK = "autoAck";

/// Constant 'MANUAL'.
static const char * const control_msgs__msg__VDA5050SafetyState__MANUAL = "manual";

/// Constant 'REMOTE'.
static const char * const control_msgs__msg__VDA5050SafetyState__REMOTE = "remote";

/// Constant 'NONE'.
static const char * const control_msgs__msg__VDA5050SafetyState__NONE = "none";

// Include directives for member types
// Member 'e_stop'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/VDA5050SafetyState in the package control_msgs.
typedef struct control_msgs__msg__VDA5050SafetyState
{
  /// Enum {autoAck, manual, remote, none} Acknowledge-Type of eStop:
  /// autoAck: autoacknowledgeable e-stop is activated e.g. by bumper or protective field
  /// manual: e-stop has to be acknowledged manually at the vehicle
  /// remote: facility estop has to be acknowledged remotely
  /// none: no e-stop activated
  rosidl_runtime_c__String e_stop;
  /// Protective field violation. True: field is violated False: field is not violated
  bool field_violation;
} control_msgs__msg__VDA5050SafetyState;

// Struct for a sequence of control_msgs__msg__VDA5050SafetyState.
typedef struct control_msgs__msg__VDA5050SafetyState__Sequence
{
  control_msgs__msg__VDA5050SafetyState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__VDA5050SafetyState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__VDA5050_SAFETY_STATE__STRUCT_H_
